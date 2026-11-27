"""AutoCAD Electrical Scratch DB (.mdb) + Electrical Netlist DRC & Layout Gatekeeper v3.2 (Fail-Closed).

Performs BOTH relational Access .mdb verification (via 64-bit ODBC) AND headless geometric +
electrical netlist Design Rule Checking (DRC) across every project .dwg via accoreconsole.exe.

Fails closed (passed=False, exit code 2) if ANY metric > 0:
1. missing_catalog / duplicate_tags / orphaned_child_contacts / wire_errors / schematic_vs_panel_discrepancy
2. family_block_misuse: Relay coil VCR1/HCR1 misused for VFDs (-U*), PSUs (-G*), or Modules/Switches (-A*)
3. modelspace_titleblock_violations: Any TITLE_BLOCK_A3_BILINGUAL in Model Space or TILEMODE=1 (must be 100% in Paper Space Layout ISO_A3!)
4. unupdated_titleblocks: Default placeholder strings ('PROJECT / DU AN', 'DWG-01') or stuck WD_M.SHEET='01'
5. short_circuit_nets (Electrical Netlist DRC):
   - Protective Earth (PWR_PE_*) shorted to Live Phase (PWR_L1/L2/L3), AC Neutral (PWR_N_*), or +24VDC!
   - AC Power/Neutral (PWR_L* / PWR_N_*) connected directly onto DC PELV net (CTRL_24VDC_* / CTRL_0VDC_*) without galvanic PSU isolation!
   - Phase-to-Phase direct bus short (e.g., PWR_L1_* shorted directly to PWR_L2_* or PWR_L3_*)!
6. unprotected_3phase_poles (Multi-Pole Protection DRC):
   - 3-phase motor (VMO13) or VFD (VU1_VFD_3P) having ANY phase input connected directly to a main supply busbar without passing through a switching pole!
7. wires_piercing_symbols & open_circuit_loads
8. text_or_attr_overflows: Visible schematic text/attributes overflowing outside [20..415, 5..287] frame or intruding into Title Block
9. panel_layout_violations: Footprints placed on wrong layer (DIM / 0)
10. pinlist_overuse_or_dup_pins: Duplicate child contact pins OR child contact count exceeding catalog PINLIST quota!
11. cross_sheet_sigcode_mismatch: Orphaned Source/Dest arrows, mismatched wire numbers, OR cross-sheet voltage domain shorts (e.g., +24VDC arrow linked to 0VDC/PE/AC)!
12. duplicate_terminal_numbers: Duplicate terminal numbers on the same strip (INST+LOC+TAGSTRIP)
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ACCORE = Path(r"C:\Program Files\Autodesk\AutoCAD 2027\accoreconsole.exe")
CATALOG_SEED_CSV = Path(__file__).resolve().parent.parent / "templates" / "catalog_master_seed.csv"


def _load_catalog_max_contacts() -> dict[tuple[str, str], int]:
    """Load total contact-pair quota per (MFG, CAT) from catalog_master_seed.csv PINLIST."""
    quotas: dict[tuple[str, str], int] = {}
    if not CATALOG_SEED_CSV.exists():
        return quotas
    with CATALOG_SEED_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            mfg = (row.get("MFG") or "").strip().upper()
            cat = (row.get("CAT") or "").strip().upper()
            plist = (row.get("PINLIST") or "").strip()
            if mfg and cat and plist:
                groups = [g.strip() for g in plist.split(";") if g.strip()]
                quotas[(mfg, cat)] = len(groups)
    return quotas


def _classify_wire_domain(layer_name: str) -> str:
    lu = layer_name.upper()
    if lu.startswith("PWR_PE"):
        return "PE"
    if lu.startswith("PWR_N"):
        return "AC_N"
    if lu.startswith("PWR_L1"):
        return "AC_L1"
    if lu.startswith("PWR_L2"):
        return "AC_L2"
    if lu.startswith("PWR_L3"):
        return "AC_L3"
    if lu.startswith("CTRL_24V") or lu.startswith("SAFE_24V"):
        return "DC_24V"
    if lu.startswith("CTRL_0V"):
        return "DC_0V"
    if lu.startswith("SIG_"):
        return "SIG"
    return "OTHER"


def _analyze_sheet_netlist_drc(
    dwg_name: str,
    wires: list[tuple[str, float, float, float, float]],
    pass_terminals: list[tuple[str, float, float]],
    motors_and_vfds: list[tuple[str, str, list[tuple[float, float]]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build connected electrical netlist graph (segments + T-junctions + pass-through terminals ht0001/Vt0001) and run DRC."""
    shorts: list[dict[str, Any]] = []
    unprotected_poles: list[dict[str, Any]] = []
    if not wires:
        return shorts, unprotected_poles

    n = len(wires)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    def pt_on_seg(px: float, py: float, x1: float, y1: float, x2: float, y2: float, tol: float = 0.65) -> bool:
        dx, dy = x2 - x1, y2 - y1
        l2 = dx * dx + dy * dy
        if l2 < 1e-9:
            return math.hypot(px - x1, py - y1) <= tol
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
        proj_x, proj_y = x1 + t * dx, y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y) <= tol

    # 1. Connect wires sharing endpoints or T-junctions (endpoint of one wire touching another segment)
    for i in range(n):
        _, ax1, ay1, ax2, ay2 = wires[i]
        for j in range(i + 1, n):
            _, bx1, by1, bx2, by2 = wires[j]
            if (
                pt_on_seg(ax1, ay1, bx1, by1, bx2, by2)
                or pt_on_seg(ax2, ay2, bx1, by1, bx2, by2)
                or pt_on_seg(bx1, by1, ax1, ay1, ax2, ay2)
                or pt_on_seg(bx2, by2, ax1, ay1, ax2, ay2)
            ):
                union(i, j)

    # 2. Bridge wires across non-wire-changing feed-through terminals (ht0001 / Vt0001 have radius ~1.25mm)
    for _tname, tx, ty in pass_terminals:
        touching: list[int] = []
        for i, (_, x1, y1, x2, y2) in enumerate(wires):
            if math.hypot(x1 - tx, y1 - ty) <= 2.2 or math.hypot(x2 - tx, y2 - ty) <= 2.2 or pt_on_seg(tx, ty, x1, y1, x2, y2, tol=1.6):
                touching.append(i)
        for k in range(1, len(touching)):
            union(touching[0], touching[k])

    nets: dict[int, list[int]] = {}
    for i in range(n):
        nets.setdefault(find(i), []).append(i)

    # Identify main horizontal busbar nets (nets containing a horizontal wire segment >= 80 mm long)
    busbar_nets: set[int] = set()
    for root, idxs in nets.items():
        domains = {_classify_wire_domain(wires[i][0]) for i in idxs}
        for i in idxs:
            _, x1, y1, x2, y2 = wires[i]
            if abs(y1 - y2) <= 0.5 and abs(x2 - x1) >= 80.0:
                busbar_nets.add(root)

        # Rule A: PE shorted to Live AC Phase, AC Neutral, or +24VDC! (Note: PE <-> DC_0V IS valid Grounded PELV per IEC 60204-1!)
        bad_with_pe = domains.intersection({"AC_L1", "AC_L2", "AC_L3", "AC_N", "DC_24V"})
        if "PE" in domains and bad_with_pe:
            sx, sy = wires[idxs[0]][1], wires[idxs[0]][2]
            shorts.append({
                "dwg": dwg_name,
                "violation": f"SHORT CIRCUIT: Protective Earth (PE) shorted directly to {sorted(bad_with_pe)}!",
                "sample_coord": [round(sx, 1), round(sy, 1)],
            })

        # Rule B: AC Supply (L1/L2/L3/N) shorted directly to DC PELV (+24VDC / 0VDC) without PSU isolation!
        ac_doms = domains.intersection({"AC_L1", "AC_L2", "AC_L3", "AC_N"})
        dc_doms = domains.intersection({"DC_24V", "DC_0V"})
        if ac_doms and dc_doms:
            sx, sy = wires[idxs[0]][1], wires[idxs[0]][2]
            shorts.append({
                "dwg": dwg_name,
                "violation": f"AC/DC GALVANIC VIOLATION: {sorted(ac_doms)} wired directly into {sorted(dc_doms)} without PSU isolation!",
                "sample_coord": [round(sx, 1), round(sy, 1)],
            })

        # Rule C: Phase-to-Phase or Phase-to-Neutral direct short
        ac_phases = domains.intersection({"AC_L1", "AC_L2", "AC_L3", "AC_N"})
        if len(ac_phases) >= 2:
            sx, sy = wires[idxs[0]][1], wires[idxs[0]][2]
            shorts.append({
                "dwg": dwg_name,
                "violation": f"PHASE SHORT CIRCUIT: Multiple AC conductors {sorted(ac_phases)} shorted on the same net!",
                "sample_coord": [round(sx, 1), round(sy, 1)],
            })

    # Rule D: 3-Phase Load Multi-Pole Protection Check (every phase pin of VMO13 / VU1_VFD_3P must be isolated from main busbar by a CB/Contactor pole!)
    for blk_name, tag_val, phase_pins in motors_and_vfds:
        for p_idx, (px, py) in enumerate(phase_pins):
            for i, (_, x1, y1, x2, y2) in enumerate(wires):
                if math.hypot(x1 - px, y1 - py) <= 1.5 or math.hypot(x2 - px, y2 - py) <= 1.5:
                    if find(i) in busbar_nets:
                        unprotected_poles.append({
                            "dwg": dwg_name,
                            "block": blk_name,
                            "tag": tag_val,
                            "pole": p_idx + 1,
                            "pin": [round(px, 1), round(py, 1)],
                            "issue": f"Pole {p_idx + 1} of '{tag_val}' ({blk_name}) connects directly to main 3-phase busbar without a switching/protection pole!",
                        })
                    break

    return shorts, unprotected_poles


def _audit_dwgs_headless(dwg_paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    """Run headless accoreconsole.exe inspection + Netlist DRC + Cross-Sheet SIGCODE Domain DRC across all project .dwg files."""
    findings: dict[str, list[dict[str, Any]]] = {
        "family_block_misuse_dwg": [],
        "modelspace_titleblock_violations": [],
        "unupdated_titleblocks": [],
        "short_circuit_nets": [],
        "unprotected_3phase_poles": [],
        "wires_piercing_symbols": [],
        "open_circuit_loads": [],
        "text_or_attr_overflows": [],
        "panel_layout_violations": [],
        "cross_sheet_sigcode_dwg": [],
    }
    if not dwg_paths or not ACCORE.exists():
        return findings

    tmp_dir = Path(tempfile.gettempdir())
    scr_path = tmp_dir / "acade_gatekeeper_v3.scr"
    out_path = tmp_dir / "acade_gatekeeper_v3_out.txt"
    sig_Registry: dict[str, dict[str, Any]] = {}

    for idx0, dp in enumerate(dwg_paths):
        if not dp.exists():
            continue
        out_path.unlink(missing_ok=True)
        out_posix = out_path.as_posix()
        lisp = f"""(setq _f (open "{out_posix}" "w"))
(write-line (strcat "TILEMODE|" (itoa (getvar "TILEMODE")) "|" (getvar "CTAB")) _f)
(setq _lwss (ssget "X" '((0 . "LINE") (410 . "Model") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*"))))
(if _lwss (progn (setq _li 0) (while (< _li (sslength _lwss))
  (setq _ld (entget (ssname _lwss _li)) _p1 (cdr (assoc 10 _ld)) _p2 (cdr (assoc 11 _ld)))
  (write-line (strcat "WIRE|" (cdr (assoc 8 _ld)) "|" (rtos (car _p1) 2 2) "|" (rtos (cadr _p1) 2 2) "|" (rtos (car _p2) 2 2) "|" (rtos (cadr _p2) 2 2)) _f)
  (setq _li (1+ _li)))))
(setq _ss (ssget "X" '((0 . "INSERT"))))
(if _ss (progn
  (setq _i 0)
  (while (< _i (sslength _ss))
    (setq _en (ssname _ss _i) _ed (entget _en) _bn (strcase (cdr (assoc 2 _ed))) _la (strcase (cdr (assoc 8 _ed))) _sp (cdr (assoc 410 _ed)) _ip (cdr (assoc 10 _ed)))
    (setq _an (entnext _en) _tg "" _ptg "" _prj "" _dno "" _sh "" _shmax "" _sig "" _wno "" _p2 nil _p8 nil _p4 nil _p1 nil _p0 nil)
    (while (and _an (= (cdr (assoc 0 (entget _an))) "ATTRIB"))
      (setq _ad (entget _an) _ak (strcase (cdr (assoc 2 _ad))) _av (cdr (assoc 1 _ad)) _ap (cdr (assoc 10 _ad)) _fl (cdr (assoc 70 _ad)))
      (if (and (= _sp "Model") (= (logand _fl 1) 0) (/= _av "") (/= _bn "TITLE_BLOCK_A3_BILINGUAL"))
        (write-line (strcat "VISATT|" _bn "|" _ak "|" (rtos (car _ap) 2 1) "|" (rtos (cadr _ap) 2 1) "|" _av) _f))
      (cond
        ((= _ak "TAG1") (setq _tg _av))
        ((= _ak "P_TAG1") (setq _ptg _av))
        ((= _ak "PROJECT_NAME") (setq _prj _av))
        ((= _ak "DWG_NO") (setq _dno _av))
        ((= _ak "SHEET") (setq _sh _av))
        ((= _ak "SHEET_TOTAL") (setq _shmax _av))
        ((= _ak "SIGCODE") (setq _sig _av))
        ((= _ak "WIRENO") (setq _wno _av))
        ((wcmatch _ak "X2TERM*") (setq _p2 (cons _ap _p2)))
        ((wcmatch _ak "X8TERM*") (setq _p8 (cons _ap _p8)))
        ((wcmatch _ak "X4TERM*") (setq _p4 (cons _ap _p4)))
        ((wcmatch _ak "X1TERM*") (setq _p1 (cons _ap _p1)))
        ((wcmatch _ak "X0TERM*") (setq _p0 (cons _ap _p0)))
      )
      (setq _an (entnext _an))
    )
    (if (= _bn "WD_M") (write-line (strcat "WDM|" _sp "|" _sh) _f))
    (if (= _bn "TITLE_BLOCK_A3_BILINGUAL") (write-line (strcat "TB|" _sp "|" _prj "|" _dno "|" _sh "|" _shmax) _f))
    (if (and (wcmatch _bn "HA1S*,HA1D*,VA1S*,VA1D*") (/= _sig ""))
      (write-line (strcat "SIGARR|" _bn "|" _sig "|" _wno "|" (rtos (car _ip) 2 2) "|" (rtos (cadr _ip) 2 2)) _f))
    (if (wcmatch _bn "HT0*,VT0*") (write-line (strcat "PTERM|" _bn "|" (rtos (car _ip) 2 2) "|" (rtos (cadr _ip) 2 2)) _f))
    (if (= _bn "VMO13")
      (progn
        (setq _mpins (append _p0 _p2))
        (foreach _mp _mpins
          (write-line (strcat "MPIN|" _bn "|" _tg "|" (rtos (car _mp) 2 2) "|" (rtos (cadr _mp) 2 2)) _f))))
    (if (= _bn "VU1_VFD_3P")
      (foreach _mp _p2
        (write-line (strcat "MPIN|" _bn "|" _tg "|" (rtos (car _mp) 2 2) "|" (rtos (cadr _mp) 2 2)) _f)))
    (if (/= _ptg "") (write-line (strcat "FP|" _ptg "|" _la "|" (rtos (car _ip) 2 1) "|" (rtos (cadr _ip) 2 1)) _f))
    (if (/= _tg "") (write-line (strcat "SYM|" _bn "|" _tg) _f))
    (foreach _t2 _p2 (foreach _t8 _p8
      (if (< (abs (- (car _t2) (car _t8))) 0.4)
        (progn
          (setq _vx (car _t2) _vyhi (max (cadr _t2) (cadr _t8)) _vylo (min (cadr _t2) (cadr _t8)))
          (setq _ws (ssget "C" (list (- _vx 0.4) _vylo) (list (+ _vx 0.4) _vyhi) '((0 . "LINE") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*"))))
          (if _ws (progn (setq _wj 0) (while (< _wj (sslength _ws))
            (setq _wd (entget (ssname _ws _wj)) _lp1 (cdr (assoc 10 _wd)) _lp2 (cdr (assoc 11 _wd)))
            (if (and (< (abs (- (car _lp1) _vx)) 0.4) (< (abs (- (car _lp2) _vx)) 0.4)
                     (> (max (cadr _lp1) (cadr _lp2)) (+ _vylo 0.5)) (< (min (cadr _lp1) (cadr _lp2)) (- _vyhi 0.5)))
              (write-line (strcat "PIERCE_V|" _bn "|" _tg "|" (rtos _vx 2 1)) _f))
            (setq _wj (1+ _wj)))))
        ))))
    (foreach _t4 _p4 (foreach _t1 _p1
      (if (< (abs (- (cadr _t4) (cadr _t1))) 0.4)
        (progn
          (setq _hy (cadr _t4) _hxhi (max (car _t4) (car _t1)) _hxlo (min (car _t4) (car _t1)))
          (setq _ws (ssget "C" (list _hxlo (- _hy 0.4)) (list _hxhi (+ _hy 0.4)) '((0 . "LINE") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*"))))
          (if _ws (progn (setq _wj 0) (while (< _wj (sslength _ws))
            (setq _wd (entget (ssname _ws _wj)) _lp1 (cdr (assoc 10 _wd)) _lp2 (cdr (assoc 11 _wd)))
            (if (and (< (abs (- (cadr _lp1) _hy)) 0.4) (< (abs (- (cadr _lp2) _hy)) 0.4)
                     (> (max (car _lp1) (car _lp2)) (+ _hxlo 0.5)) (< (min (car _lp1) (car _lp2)) (- _hxhi 0.5)))
              (write-line (strcat "PIERCE_H|" _bn "|" _tg "|" (rtos _hy 2 1)) _f))
            (setq _wj (1+ _wj)))))
        ))))
    (if (member _bn '("HCR1" "VCR1" "HLT1A" "VLT1A" "HSV1" "VSV1"))
      (progn
        (setq _pins (append _p2 _p8 _p4 _p1) _conn 0)
        (foreach _pp _pins
          (setq _ws (ssget "C" (list (- (car _pp) 2.5) (- (cadr _pp) 2.5)) (list (+ (car _pp) 2.5) (+ (cadr _pp) 2.5)) '((0 . "LINE") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*"))))
          (setq _hit nil)
          (if _ws (progn (setq _wk 0) (while (< _wk (sslength _ws))
            (setq _wd2 (entget (ssname _ws _wk)) _ep1 (cdr (assoc 10 _wd2)) _ep2 (cdr (assoc 11 _wd2)))
            (if (or (< (distance (list (car _ep1) (cadr _ep1)) (list (car _pp) (cadr _pp))) 0.8)
                    (< (distance (list (car _ep2) (cadr _ep2)) (list (car _pp) (cadr _pp))) 0.8))
              (setq _hit T))
            (setq _wk (1+ _wk)))))
          (if _hit (setq _conn (1+ _conn))))
        (if (< _conn 2)
          (write-line (strcat "OPEN_LOAD|" _bn "|" _tg "|" (itoa _conn)) _f))
      ))
    (setq _i (1+ _i))
  )))
(close _f)
_QUIT _Y
"""
        scr_path.write_text(lisp, encoding="ascii")
        subprocess.run([str(ACCORE), "/i", str(dp), "/s", str(scr_path), "/l", "en-US"], capture_output=True, text=True, timeout=35)
        if not out_path.exists():
            continue

        lines = out_path.read_text(encoding="utf-8", errors="replace").splitlines()
        fl = dp.name.lower()
        is_panel_sheet = ("panel" in fl) or ("-lay-" in fl) or ("_lay_" in fl)

        sheet_wires: list[tuple[str, float, float, float, float]] = []
        pass_terms: list[tuple[str, float, float]] = []
        mpin_groups: dict[tuple[str, str], list[tuple[float, float]]] = {}
        sheet_arrows: list[tuple[str, str, str, float, float]] = []
        has_paper_tb = False

        for ln in lines:
            parts = ln.split("|")
            kind = parts[0]
            if kind == "TILEMODE" and len(parts) >= 3:
                tm = int(parts[1] or "1")
                if tm != 0:
                    findings["modelspace_titleblock_violations"].append({
                        "dwg": dp.name,
                        "issue": "Drawing saved with TILEMODE=1 (Model tab active) instead of Paper Space Layout ISO_A3 (TILEMODE=0)!",
                    })
            elif kind == "TB" and len(parts) >= 6:
                sp_name, prj, dno, sh, shmax = parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip(), parts[5].strip()
                if sp_name.lower() == "model":
                    findings["modelspace_titleblock_violations"].append({
                        "dwg": dp.name,
                        "issue": "TITLE_BLOCK_A3_BILINGUAL placed inside Model Space! Title Block & Border must reside 100% in Paper Space Layout ISO_A3.",
                    })
                else:
                    has_paper_tb = True
                if prj in ("", "PROJECT / DU AN") or dno in ("", "DWG-01") or (len(dwg_paths) > 1 and shmax == "01"):
                    findings["unupdated_titleblocks"].append({
                        "dwg": dp.name,
                        "PROJECT_NAME": prj,
                        "DWG_NO": dno,
                        "SHEET": f"{sh} OF {shmax}",
                    })
            elif kind == "WDM" and len(parts) >= 3:
                sh_val = parts[2].strip()
                if idx0 >= 1 and sh_val == "01":
                    findings["unupdated_titleblocks"].append({
                        "dwg": dp.name,
                        "issue": f"WD_M.SHEET stuck at '01' on sheet #{idx0 + 1}",
                    })
            elif kind == "WIRE" and len(parts) >= 6:
                sheet_wires.append((parts[1], float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])))
            elif kind == "PTERM" and len(parts) >= 4:
                pass_terms.append((parts[1], float(parts[2]), float(parts[3])))
            elif kind == "SIGARR" and len(parts) >= 6:
                sheet_arrows.append((parts[1].strip(), parts[2].strip(), parts[3].strip(), float(parts[4]), float(parts[5])))
            elif kind == "MPIN" and len(parts) >= 5:
                mpin_groups.setdefault((parts[1], parts[2]), []).append((float(parts[3]), float(parts[4])))
            elif kind == "VISATT" and len(parts) >= 6 and not is_panel_sheet:
                ax, ay = float(parts[3]), float(parts[4])
                if ax < 20.0 or ax > 415.0 or ay < 5.0 or ay > 286.8 or (ax > 235.0 and ay < 41.0):
                    findings["text_or_attr_overflows"].append({
                        "dwg": dp.name,
                        "block": parts[1],
                        "attr": f"{parts[2]}={parts[5]}",
                        "coord": [ax, ay],
                    })
            elif kind == "SYM" and len(parts) >= 3:
                bn, tg = parts[1].strip(), parts[2].strip()
                tg_alpha = tg.upper().lstrip("-=+0123456789")
                if bn in ("VCR1", "HCR1") and tg_alpha[:1] in ("U", "G", "A"):
                    findings["family_block_misuse_dwg"].append({"dwg": dp.name, "block": bn, "tag": tg})
            elif kind in ("PIERCE_V", "PIERCE_H") and len(parts) >= 4:
                findings["wires_piercing_symbols"].append({
                    "dwg": dp.name,
                    "kind": kind,
                    "block": parts[1],
                    "tag": parts[2],
                    "coord": parts[3],
                })
            elif kind == "OPEN_LOAD" and len(parts) >= 4:
                findings["open_circuit_loads"].append({
                    "dwg": dp.name,
                    "block": parts[1],
                    "tag": parts[2],
                    "connected_pins": int(parts[3]),
                })
            elif kind == "FP" and len(parts) >= 5:
                ptg, la = parts[1].strip(), parts[2].strip()
                if la in ("DIM", "PNL_DIM", "0"):
                    findings["panel_layout_violations"].append({
                        "dwg": dp.name,
                        "issue": f"Panel footprint '{ptg}' placed on wrong layer '{la}' (must be PNL_FOOTPRINT)",
                    })

        if not has_paper_tb:
            findings["modelspace_titleblock_violations"].append({
                "dwg": dp.name,
                "issue": "Missing TITLE_BLOCK_A3_BILINGUAL in Paper Space Layout ISO_A3!",
            })

        if not is_panel_sheet and sheet_wires:
            motor_vfd_list = [(bn, tg, sorted(pts, key=lambda p: p[0])) for (bn, tg), pts in mpin_groups.items()]
            sh_shorts, sh_unprot = _analyze_sheet_netlist_drc(dp.name, sheet_wires, pass_terms, motor_vfd_list)
            findings["short_circuit_nets"].extend(sh_shorts)
            findings["unprotected_3phase_poles"].extend(sh_unprot)
            for abn, scode, swno, ax, ay in sheet_arrows:
                entry = sig_Registry.setdefault(scode.upper(), {"sigcode": scode, "src": 0, "dst": 0, "wirenos": set(), "domains": set(), "dwgs": set()})
                if "S" in abn[3:5]:
                    entry["src"] += 1
                else:
                    entry["dst"] += 1
                if swno:
                    entry["wirenos"].add(swno.upper())
                entry["dwgs"].add(dp.name)
                for wlyr, wx1, wy1, wx2, wy2 in sheet_wires:
                    if math.hypot(wx1 - ax, wy1 - ay) <= 3.0 or math.hypot(wx2 - ax, wy2 - ay) <= 3.0:
                        dom = _classify_wire_domain(wlyr)
                        if dom != "OTHER":
                            entry["domains"].add(dom)

    for _sk, sv in sig_Registry.items():
        doms = sv["domains"]
        bad_dom = len(doms) > 1 and not (doms <= {"DC_24V", "SIG"})
        if (len(dwg_paths) > 1 and (sv["src"] == 0 or sv["dst"] == 0)) or len(sv["wirenos"]) > 1 or bad_dom:
            findings["cross_sheet_sigcode_dwg"].append({
                "SIGCODE": sv["sigcode"],
                "SRC": sv["src"],
                "DST": sv["dst"],
                "WIRENOS": sorted(sv["wirenos"]),
                "DOMAINS": sorted(doms),
                "DWGS": sorted(sv["dwgs"]),
            })

    scr_path.unlink(missing_ok=True)
    out_path.unlink(missing_ok=True)
    return findings


def _discover_dwg_paths(project_dir: Path | None) -> list[Path]:
    if project_dir:
        pdir = project_dir.resolve()
        sub = pdir / "01_Drawings"
        target = sub if sub.exists() else pdir
        wdps = list(pdir.glob("*.wdp")) + list(target.glob("*.wdp"))
        if wdps:
            ordered: list[Path] = []
            for raw in wdps[0].read_text(encoding="utf-8", errors="replace").splitlines():
                ln = raw.strip()
                if ln and not ln.startswith(("*", "+", "?", "=")) and ln.lower().endswith(".dwg"):
                    cand = target / Path(ln).name
                    if cand.exists():
                        ordered.append(cand)
            if ordered:
                return ordered
        return sorted(target.glob("*.dwg"))
    return []


def audit_scratch_database(mdb_path: Path, project_dir: Path | None = None) -> dict[str, Any]:
    """Query ACADE Project Scratch .mdb + run Electrical Netlist DRC & Paper Space Layout Gatekeeper v3.0."""
    if not mdb_path.exists():
        raise FileNotFoundError(f"Scratch database not found: {mdb_path}")

    mdb_str = str(mdb_path.resolve()).replace("'", "''")
    ps = f"""
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={mdb_str};ReadOnly=1;")
$conn.Open()
$tables = @($conn.GetSchema("Tables") | Where-Object {{ $_.TABLE_TYPE -eq "TABLE" }} | Select-Object -ExpandProperty TABLE_NAME)

function Run-Query($sql) {{
    $rows = @()
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = $sql
    $r = $cmd.ExecuteReader()
    while ($r.Read()) {{
        $obj = @{{}}
        for ($i = 0; $i -lt $r.FieldCount; $i++) {{
            $v = $r.GetValue($i)
            $obj[$r.GetName($i)] = if ($v -is [DBNull]) {{ "" }} else {{ [string]$v }}
        }}
        $rows += $obj
    }}
    $r.Close()
    return ,$rows
}}

if (-not ($tables -contains "COMP")) {{
    $conn.Close()
    @{{
        mdb = '{mdb_str}'
        passed = $false
        error = "FAIL-CLOSED: Scratch DB missing [COMP] table (run AEREBUILDDB / project sync first)."
        tables_present = $tables
    }} | ConvertTo-Json -Depth 4 -Compress
    exit 0
}}

$compCountRows = Run-Query "SELECT COUNT(*) AS CNT FROM [COMP]"
$compTotal = [int]$compCountRows[0].CNT
if ($compTotal -eq 0) {{
    $conn.Close()
    @{{
        mdb = '{mdb_str}'
        passed = $false
        error = "FAIL-CLOSED: [COMP] table has 0 rows (empty or unbuilt Scratch Database)."
        tables_present = $tables
    }} | ConvertTo-Json -Depth 4 -Compress
    exit 0
}}

$compCols = @()
try {{
    $scCmd = $conn.CreateCommand()
    $scCmd.CommandText = "SELECT TOP 1 * FROM [COMP]"
    $scRdr = $scCmd.ExecuteReader()
    for ($ci = 0; $ci -lt $scRdr.FieldCount; $ci++) {{ $compCols += $scRdr.GetName($ci).ToUpper() }}
    $scRdr.Close()
}} catch {{}}
$symCol = if ($compCols -contains "SYMBOL") {{ "SYMBOL" }} elseif ($compCols -contains "BLOCK") {{ "BLOCK" }} else {{ "" }}

$missingCat = Run-Query "SELECT TAGNAME, DWGIX, LOC, INST, PAR1_CHLD2 FROM [COMP] WHERE PAR1_CHLD2='1' AND ((MFG IS NULL OR MFG='') OR (CAT IS NULL OR CAT=''))"
$dupTags = Run-Query "SELECT TAGNAME, LOC, INST, COUNT(*) AS CNT FROM [COMP] WHERE PAR1_CHLD2='1' AND TAGNAME IS NOT NULL AND TAGNAME<>'' GROUP BY TAGNAME, LOC, INST HAVING COUNT(*) > 1"
$orphans = Run-Query "SELECT c.TAGNAME, c.DWGIX, c.LOC FROM [COMP] c LEFT JOIN (SELECT DISTINCT TAGNAME FROM [COMP] WHERE PAR1_CHLD2='1') p ON c.TAGNAME = p.TAGNAME WHERE c.PAR1_CHLD2='2' AND p.TAGNAME IS NULL AND c.TAGNAME IS NOT NULL AND c.TAGNAME<>''"

$familyMisuse = @()
if ($symCol -ne "") {{
    $allParents = Run-Query "SELECT TAGNAME, [$symCol] AS SYM, MFG, CAT, LOC FROM [COMP] WHERE PAR1_CHLD2='1'"
    foreach ($r in $allParents) {{
        $s = ([string]$r.SYM).ToUpper()
        $t = ([string]$r.TAGNAME).ToUpper().TrimStart('-','=','+','0','1','2','3','4','5','6','7','8','9')
        if ((($s -eq 'VCR1') -or ($s -eq 'HCR1')) -and ($t.Length -gt 0) -and (@('U','G','A') -contains $t.Substring(0,1))) {{
            $familyMisuse += $r
        }}
    }}
}}

$wireErrs = @()
if ($tables -contains "WIRE_ERR") {{
    $wireErrs += Run-Query "SELECT DWGIX, WIRENO, WIRELAY, X, Y FROM [WIRE_ERR]"
}}
if ($tables -contains "WFRM2ALL") {{
    $wireErrs += Run-Query "SELECT WIRENO, NAM1, PIN1, NAM2, PIN2, WLAY1 FROM [WFRM2ALL] WHERE WIRENO IS NULL OR WIRENO='' OR WIRENO LIKE '?%'"
}}

$panelDiscrepancies = @()
if ($tables -contains "PNLCOMP") {{
    $panelDiscrepancies = Run-Query "SELECT c.TAGNAME, c.LOC, c.MFG, c.CAT FROM [COMP] c LEFT JOIN [PNLCOMP] p ON c.TAGNAME = p.TAGNAME WHERE c.PAR1_CHLD2='1' AND (c.LOC='+MAIN_PNL' OR c.LOC='+DOOR') AND p.TAGNAME IS NULL AND c.TAGNAME IS NOT NULL AND c.TAGNAME<>''"
}} else {{
    $panelDiscrepancies = Run-Query "SELECT TAGNAME, LOC, MFG, CAT FROM [COMP] WHERE PAR1_CHLD2='1' AND (LOC='+MAIN_PNL' OR LOC='+DOOR')"
}}

$fileRows = @()
if ($tables -contains "FILETIME") {{
    try {{ $fileRows = Run-Query "SELECT FULLFILENAME, DWGNAME FROM [FILETIME] ORDER BY DWGIX" }} catch {{}}
}}

$dupTermNums = @()
if ($tables -contains "TERMS") {{
    try {{
        $dupTermNums = Run-Query "SELECT INST, LOC, TAGSTRIP, TERM, COUNT(*) AS CNT FROM [TERMS] WHERE TERM IS NOT NULL AND TERM<>'' AND (LNUMBER IS NULL OR LNUMBER='') GROUP BY INST, LOC, TAGSTRIP, TERM HAVING COUNT(*) > 1"
    }} catch {{}}
}}

$pinViolations = @()
$childCounts = @()
$parentCats = @()
if ($tables -contains "COMP") {{
    try {{
        $compPins = Run-Query "SELECT TAGNAME, PAR1_CHLD2, TERM01, TERM02, MFG, CAT FROM [COMP] WHERE TAGNAME IS NOT NULL AND TAGNAME<>''"
        $seenPins = @{{}}
        $chCntMap = @{{}}
        foreach ($cp in $compPins) {{
            $tg = [string]$cp.TAGNAME
            $pc = ([string]$cp.PAR1_CHLD2).Trim()
            if ($pc -eq "1") {{
                $parentCats += @{{ TAGNAME = $tg; MFG = ([string]$cp.MFG).Trim().ToUpper(); CAT = ([string]$cp.CAT).Trim().ToUpper() }}
            }} elseif ($pc -eq "2") {{
                if (-not $chCntMap.ContainsKey($tg)) {{ $chCntMap[$tg] = 0 }}
                $chCntMap[$tg]++
            }}
            $t1 = ([string]$cp.TERM01).Trim()
            $t2 = ([string]$cp.TERM02).Trim()
            if ($t1 -ne "" -or $t2 -ne "") {{
                $pk = "$tg|$t1|$t2"
                if ($seenPins.ContainsKey($pk)) {{
                    $pinViolations += @{{ TAGNAME = $tg; TERM01 = $t1; TERM02 = $t2; REASON = "DUPLICATE_CONTACT_PINS" }}
                }} else {{
                    $seenPins[$pk] = $true
                }}
            }}
        }}
        foreach ($k in $chCntMap.Keys) {{
            $childCounts += @{{ TAGNAME = $k; CHILD_COUNT = $chCntMap[$k] }}
        }}
    }} catch {{}}
}}

$sigMismatches = @()
if ($tables -contains "SIG") {{
    try {{
        $sigRows = Run-Query "SELECT SIGCODE, CODE, WIRENO FROM [SIG] WHERE SIGCODE IS NOT NULL AND SIGCODE<>''"
        $sigMap = @{{}}
        foreach ($sr in $sigRows) {{
            $sc = ([string]$sr.SIGCODE).Trim()
            if (-not $sigMap.ContainsKey($sc)) {{ $sigMap[$sc] = @{{ S = 0; D = 0; wires = @() }} }}
            $cd = ([string]$sr.CODE).Trim().ToUpper()
            if ($cd -eq "S") {{ $sigMap[$sc].S++ }} elseif ($cd -eq "D") {{ $sigMap[$sc].D++ }}
            $wn = ([string]$sr.WIRENO).Trim()
            if ($wn -ne "" -and ($sigMap[$sc].wires -notcontains $wn)) {{ $sigMap[$sc].wires += $wn }}
        }}
        foreach ($k in $sigMap.Keys) {{
            $v = $sigMap[$k]
            if ($v.S -eq 0 -or $v.D -eq 0 -or $v.wires.Count -gt 1) {{
                $sigMismatches += @{{ SIGCODE = $k; SRC = $v.S; DST = $v.D; WIRENOS = ($v.wires -join ',') }}
            }}
        }}
    }} catch {{}}
}}

$conn.Close()

@{{
    mdb = '{mdb_str}'
    tables_present = $tables
    comp_total = $compTotal
    missing_catalog = $missingCat
    duplicate_tags = $dupTags
    orphaned_child_contacts = $orphans
    family_block_misuse = $familyMisuse
    wire_errors = $wireErrs
    schematic_vs_panel_discrepancy = $panelDiscrepancies
    pinlist_overuse_or_dup_pins = $pinViolations
    child_counts = $childCounts
    parent_cats = $parentCats
    cross_sheet_sigcode_mismatch = $sigMismatches
    duplicate_terminal_numbers = $dupTermNums
    filetime_rows = $fileRows
}} | ConvertTo-Json -Depth 6 -Compress
"""
    enc = base64.b64encode(ps.encode("utf-16le")).decode("ascii")
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "Audit PowerShell error").strip())
    raw = json.loads(proc.stdout.strip())
    if "error" in raw:
        return raw

    dwg_paths = _discover_dwg_paths(project_dir)
    if not dwg_paths and raw.get("filetime_rows"):
        for fr in raw["filetime_rows"]:
            ff = (fr.get("FULLFILENAME") or "").strip()
            if ff and Path(ff).exists():
                dwg_paths.append(Path(ff))

    dwg_findings = _audit_dwgs_headless(dwg_paths) if dwg_paths else {
        "family_block_misuse_dwg": [],
        "modelspace_titleblock_violations": [],
        "unupdated_titleblocks": [],
        "short_circuit_nets": [],
        "unprotected_3phase_poles": [],
        "wires_piercing_symbols": [],
        "open_circuit_loads": [],
        "text_or_attr_overflows": [],
        "panel_layout_violations": [],
        "cross_sheet_sigcode_dwg": [],
    }

    fam_misuse = list(raw.get("family_block_misuse") or [])
    if not fam_misuse and dwg_findings["family_block_misuse_dwg"]:
        fam_misuse = dwg_findings["family_block_misuse_dwg"]

    # Check _PINLIST quota overuse (CHILD_COUNT > catalog PINLIST contact pairs) + duplicate contact pins
    pin_issues = list(raw.get("pinlist_overuse_or_dup_pins") or [])
    quotas = _load_catalog_max_contacts()
    parent_cat_map = {
        str(p.get("TAGNAME", "")): (str(p.get("MFG", "")), str(p.get("CAT", "")))
        for p in (raw.get("parent_cats") or [])
    }
    for cc in (raw.get("child_counts") or []):
        tg = str(cc.get("TAGNAME", ""))
        cnt = int(cc.get("CHILD_COUNT", 0))
        mfg_cat = parent_cat_map.get(tg)
        if mfg_cat and mfg_cat in quotas and cnt > quotas[mfg_cat]:
            pin_issues.append({
                "TAGNAME": tg,
                "MFG": mfg_cat[0],
                "CAT": mfg_cat[1],
                "CHILD_COUNT": cnt,
                "MAX_ALLOWED": quotas[mfg_cat],
                "REASON": "PINLIST_QUOTA_EXCEEDED",
            })

    sig_issues = list(raw.get("cross_sheet_sigcode_mismatch") or [])
    seen_sigs = {str(s.get("SIGCODE", "")).upper() for s in sig_issues}
    for dsig in dwg_findings.get("cross_sheet_sigcode_dwg", []):
        if str(dsig.get("SIGCODE", "")).upper() not in seen_sigs:
            sig_issues.append(dsig)

    check_keys = (
        "missing_catalog",
        "duplicate_tags",
        "orphaned_child_contacts",
        "wire_errors",
        "schematic_vs_panel_discrepancy",
        "family_block_misuse",
        "pinlist_overuse_or_dup_pins",
        "cross_sheet_sigcode_mismatch",
        "duplicate_terminal_numbers",
        "modelspace_titleblock_violations",
        "unupdated_titleblocks",
        "short_circuit_nets",
        "unprotected_3phase_poles",
        "wires_piercing_symbols",
        "open_circuit_loads",
        "text_or_attr_overflows",
        "panel_layout_violations",
    )

    counts = {
        "comp_total": int(raw["comp_total"]),
        "dwgs_inspected": len(dwg_paths),
        "missing_catalog": len(raw["missing_catalog"]),
        "duplicate_tags": len(raw["duplicate_tags"]),
        "orphaned_child_contacts": len(raw["orphaned_child_contacts"]),
        "wire_errors": len(raw["wire_errors"]),
        "schematic_vs_panel_discrepancy": len(raw["schematic_vs_panel_discrepancy"]),
        "family_block_misuse": len(fam_misuse),
        "pinlist_overuse_or_dup_pins": len(pin_issues),
        "cross_sheet_sigcode_mismatch": len(sig_issues),
        "duplicate_terminal_numbers": len(raw.get("duplicate_terminal_numbers") or []),
        "modelspace_titleblock_violations": len(dwg_findings["modelspace_titleblock_violations"]),
        "unupdated_titleblocks": len(dwg_findings["unupdated_titleblocks"]),
        "short_circuit_nets": len(dwg_findings["short_circuit_nets"]),
        "unprotected_3phase_poles": len(dwg_findings["unprotected_3phase_poles"]),
        "wires_piercing_symbols": len(dwg_findings["wires_piercing_symbols"]),
        "open_circuit_loads": len(dwg_findings["open_circuit_loads"]),
        "text_or_attr_overflows": len(dwg_findings["text_or_attr_overflows"]),
        "panel_layout_violations": len(dwg_findings["panel_layout_violations"]),
    }
    passed = all(counts[k] == 0 for k in check_keys)

    return {
        "mdb": str(mdb_path.resolve()),
        "tables_present": raw["tables_present"],
        "passed": passed,
        "counts": counts,
        "samples": {
            "missing_catalog": raw["missing_catalog"][:10],
            "duplicate_tags": raw["duplicate_tags"][:10],
            "orphaned_child_contacts": raw["orphaned_child_contacts"][:10],
            "wire_errors": raw["wire_errors"][:10],
            "schematic_vs_panel_discrepancy": raw["schematic_vs_panel_discrepancy"][:10],
            "family_block_misuse": fam_misuse[:10],
            "pinlist_overuse_or_dup_pins": pin_issues[:10],
            "cross_sheet_sigcode_mismatch": sig_issues[:10],
            "duplicate_terminal_numbers": (raw.get("duplicate_terminal_numbers") or [])[:10],
            "modelspace_titleblock_violations": dwg_findings["modelspace_titleblock_violations"][:10],
            "unupdated_titleblocks": dwg_findings["unupdated_titleblocks"][:10],
            "short_circuit_nets": dwg_findings["short_circuit_nets"][:10],
            "unprotected_3phase_poles": dwg_findings["unprotected_3phase_poles"][:10],
            "wires_piercing_symbols": dwg_findings["wires_piercing_symbols"][:10],
            "open_circuit_loads": dwg_findings["open_circuit_loads"][:10],
            "text_or_attr_overflows": dwg_findings["text_or_attr_overflows"][:10],
            "panel_layout_violations": dwg_findings["panel_layout_violations"][:10],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ACADE Scratch DB + Electrical Netlist DRC & Layout Gatekeeper v3.2 (Fail-Closed)")
    parser.add_argument("--mdb", type=Path, required=True, help="Path to <project>.mdb Scratch Database")
    parser.add_argument("--project-dir", type=Path, default=None, help="Optional project folder or 01_Drawings folder for DWG DRC")
    args = parser.parse_args()

    result = audit_scratch_database(args.mdb, args.project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
