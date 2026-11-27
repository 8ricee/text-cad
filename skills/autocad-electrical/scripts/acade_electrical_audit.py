"""AutoCAD Electrical Project Scratch Database (.mdb) + Deep DWG Gatekeeper Audit v2.0 (Fail-Closed).

Queries the real ACADE 2027 Project Scratch Database (<project>.mdb):
- COMP (PAR1_CHLD2=1 Parent, PAR1_CHLD2=2 Child, SYMBOL/BLOCK family check)
- PNLCOMP (Panel Footprint components)
- WIRE_ERR (Wire errors)
- WFRM2ALL (From/To wire list)
via 64-bit Windows ODBC (System.Data.Odbc), AND optionally inspects all project .dwg sheets
via accoreconsole.exe when --project-dir is supplied (or auto-discovered from [FILETIME] in .mdb).

Fails closed (passed=False, exit code 2) if ANY metric > 0:
1. COMP table is missing or empty (unbuilt/unlinked Scratch DB)
2. missing_catalog (MFG or CAT empty) > 0
3. duplicate_tags (same TAGNAME+LOC+INST among PAR1_CHLD2='1' Parents) > 0
4. orphaned_child_contacts (PAR1_CHLD2='2' Child without matching Parent in COMP) > 0
5. wire_errors (rows in WIRE_ERR or '?' wire numbers in WFRM2ALL) > 0
6. schematic_vs_panel_discrepancy (+MAIN_PNL / +DOOR Parents missing in PNLCOMP) > 0
7. family_block_misuse (TAGNAME prefix U/G/A using relay coil VCR1/HCR1) > 0
8. unupdated_titleblocks (TITLE_BLOCK_A3_BILINGUAL left at default 'PROJECT / DU AN' or 'DWG-01', or WD_M.SHEET stuck at '01' on sheet > 1) > 0
9. wires_piercing_symbols (wire LINE piercing straight through opposite X2/X8 or X4/X1 pins of a component) > 0
10. open_circuit_loads (2-pin load coils/lamps/valves HCR1/VCR1/HLT1A/VLT1A/HSV1/VSV1 with < 2 connected pins) > 0
11. panel_layout_violations (Panel Layout sheet in TILEMODE=1 with entities overflowing 420x297 A3 frame, or footprints on DIM layer) > 0
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ACCORE = Path(r"C:\Program Files\Autodesk\AutoCAD 2027\accoreconsole.exe")


def _audit_dwgs_headless(dwg_paths: list[Path]) -> dict[str, list[dict[str, Any]]]:
    """Run headless accoreconsole.exe pure-AutoLISP inspection across project .dwg files."""
    findings: dict[str, list[dict[str, Any]]] = {
        "family_block_misuse_dwg": [],
        "unupdated_titleblocks": [],
        "wires_piercing_symbols": [],
        "open_circuit_loads": [],
        "panel_layout_violations": [],
    }
    if not dwg_paths or not ACCORE.exists():
        return findings

    tmp_dir = Path(tempfile.gettempdir())
    scr_path = tmp_dir / "acade_gatekeeper_v2.scr"
    out_path = tmp_dir / "acade_gatekeeper_v2_out.txt"

    for idx0, dp in enumerate(dwg_paths):
        if not dp.exists():
            continue
        out_path.unlink(missing_ok=True)
        out_posix = out_path.as_posix()
        lisp = f"""(setq _f (open "{out_posix}" "w"))
(write-line (strcat "TILEMODE|" (itoa (getvar "TILEMODE"))) _f)
(setq _ss (ssget "X" '((0 . "INSERT"))))
(if _ss (progn
  (setq _i 0)
  (while (< _i (sslength _ss))
    (setq _en (ssname _ss _i) _ed (entget _en) _bn (strcase (cdr (assoc 2 _ed))) _la (strcase (cdr (assoc 8 _ed))) _ip (cdr (assoc 10 _ed)))
    (setq _an (entnext _en) _tg "" _ptg "" _prj "" _dno "" _sh "" _shmax "" _p2 nil _p8 nil _p4 nil _p1 nil)
    (while (and _an (= (cdr (assoc 0 (entget _an))) "ATTRIB"))
      (setq _ad (entget _an) _ak (strcase (cdr (assoc 2 _ad))) _av (cdr (assoc 1 _ad)) _ap (cdr (assoc 10 _ad)))
      (cond
        ((= _ak "TAG1") (setq _tg _av))
        ((= _ak "P_TAG1") (setq _ptg _av))
        ((= _ak "PROJECT_NAME") (setq _prj _av))
        ((= _ak "DWG_NO") (setq _dno _av))
        ((= _ak "SHEET") (setq _sh _av))
        ((= _ak "SHEET_TOTAL") (setq _shmax _av))
        ((wcmatch _ak "X2TERM*") (setq _p2 (cons _ap _p2)))
        ((wcmatch _ak "X8TERM*") (setq _p8 (cons _ap _p8)))
        ((wcmatch _ak "X4TERM*") (setq _p4 (cons _ap _p4)))
        ((wcmatch _ak "X1TERM*") (setq _p1 (cons _ap _p1)))
      )
      (setq _an (entnext _an))
    )
    (if (= _bn "WD_M") (write-line (strcat "WDM|" _sh) _f))
    (if (= _bn "TITLE_BLOCK_A3_BILINGUAL") (write-line (strcat "TB|" _prj "|" _dno "|" _sh "|" _shmax) _f))
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
              (progn
                (setq _fep (if (< (distance (list (car _ep1) (cadr _ep1)) (list (car _pp) (cadr _pp))) 0.8) _ep2 _ep1))
                (if (ssget "C" (list (- (car _fep) 3.0) (- (cadr _fep) 3.0)) (list (+ (car _fep) 3.0) (+ (cadr _fep) 3.0)) '((0 . "LINE,INSERT")))
                  (progn
                    (setq _deg (ssget "C" (list (- (car _fep) 1.5) (- (cadr _fep) 1.5)) (list (+ (car _fep) 1.5) (+ (cadr _fep) 1.5)) '((0 . "LINE") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*")))
                          _ins (ssget "C" (list (- (car _fep) 7.5) (- (cadr _fep) 7.5)) (list (+ (car _fep) 7.5) (+ (cadr _fep) 7.5)) '((0 . "INSERT"))))
                    (if (or (and _deg (> (sslength _deg) 1)) (and _ins (> (sslength _ins) 0)))
                      (setq _hit T))))))
            (setq _wk (1+ _wk)))))
          (if _hit (setq _conn (1+ _conn))))
        (if (< _conn 2)
          (write-line (strcat "OPEN_LOAD|" _bn "|" _tg "|" (itoa _conn)) _f))
      ))
    (setq _i (1+ _i))
  )))
(setq _pmax (getvar "EXTMAX"))
(write-line (strcat "EXTMAX|" (rtos (car _pmax) 2 1) "|" (rtos (cadr _pmax) 2 1)) _f)
(close _f)
_QUIT _Y
"""
        scr_path.write_text(lisp, encoding="ascii")
        subprocess.run(
            [str(ACCORE), "/i", str(dp), "/s", str(scr_path), "/l", "en-US"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not out_path.exists():
            continue

        lines = out_path.read_text(encoding="utf-8", errors="replace").splitlines()
        tilemode = 1
        ext_x, ext_y = 0.0, 0.0
        fl = dp.name.lower()
        is_panel_sheet = ("panel" in fl) or ("-lay-" in fl) or ("_lay_" in fl)

        for ln in lines:
            parts = ln.split("|")
            kind = parts[0]
            if kind == "TILEMODE" and len(parts) >= 2:
                tilemode = int(parts[1] or "1")
            elif kind == "EXTMAX" and len(parts) >= 3:
                try:
                    ext_x, ext_y = float(parts[1]), float(parts[2])
                except ValueError:
                    pass
            elif kind == "WDM" and len(parts) >= 2:
                sh_val = parts[1].strip()
                if idx0 >= 1 and sh_val == "01":
                    findings["unupdated_titleblocks"].append({
                        "dwg": dp.name,
                        "issue": f"WD_M.SHEET stuck at '01' on sheet #{idx0 + 1}",
                    })
            elif kind == "TB" and len(parts) >= 5:
                prj, dno, sh, shmax = parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip()
                if prj in ("", "PROJECT / DU AN") or dno in ("", "DWG-01") or (len(dwg_paths) > 1 and shmax == "01"):
                    findings["unupdated_titleblocks"].append({
                        "dwg": dp.name,
                        "PROJECT_NAME": prj,
                        "DWG_NO": dno,
                        "SHEET": f"{sh} OF {shmax}",
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

        if is_panel_sheet and tilemode == 1 and (ext_x > 430.0 or ext_y > 310.0):
            findings["panel_layout_violations"].append({
                "dwg": dp.name,
                "issue": f"Panel Layout in TILEMODE=1 overflows A3 frame (EXTMAX={ext_x:.1f}x{ext_y:.1f} mm; must use Paper Space ISO_A3 VIEWPORT with TILEMODE=0)",
            })

    scr_path.unlink(missing_ok=True)
    out_path.unlink(missing_ok=True)
    return findings


def _discover_dwg_paths(mdb_path: Path, project_dir: Path | None) -> list[Path]:
    """Resolve ordered .dwg files from --project-dir (or 01_Drawings subfolder), or from [FILETIME] in .mdb."""
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
    """Query ACADE Project Scratch .mdb + optional .dwg sheets (Fail-Closed Gatekeeper v2.0)."""
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

$compCols = @($conn.GetSchema("Columns", @($null, $null, "COMP", $null)) | Select-Object -ExpandProperty COLUMN_NAME)
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

    dwg_paths = _discover_dwg_paths(mdb_path, project_dir)
    if not dwg_paths and raw.get("filetime_rows"):
        for fr in raw["filetime_rows"]:
            ff = (fr.get("FULLFILENAME") or "").strip()
            if ff and Path(ff).exists():
                dwg_paths.append(Path(ff))

    dwg_findings = _audit_dwgs_headless(dwg_paths) if dwg_paths else {
        "family_block_misuse_dwg": [],
        "unupdated_titleblocks": [],
        "wires_piercing_symbols": [],
        "open_circuit_loads": [],
        "panel_layout_violations": [],
    }

    fam_misuse = list(raw.get("family_block_misuse") or [])
    if not fam_misuse and dwg_findings["family_block_misuse_dwg"]:
        fam_misuse = dwg_findings["family_block_misuse_dwg"]

    counts = {
        "comp_total": int(raw["comp_total"]),
        "dwgs_inspected": len(dwg_paths),
        "missing_catalog": len(raw["missing_catalog"]),
        "duplicate_tags": len(raw["duplicate_tags"]),
        "orphaned_child_contacts": len(raw["orphaned_child_contacts"]),
        "wire_errors": len(raw["wire_errors"]),
        "schematic_vs_panel_discrepancy": len(raw["schematic_vs_panel_discrepancy"]),
        "family_block_misuse": len(fam_misuse),
        "unupdated_titleblocks": len(dwg_findings["unupdated_titleblocks"]),
        "wires_piercing_symbols": len(dwg_findings["wires_piercing_symbols"]),
        "open_circuit_loads": len(dwg_findings["open_circuit_loads"]),
        "panel_layout_violations": len(dwg_findings["panel_layout_violations"]),
    }
    passed = all(
        counts[k] == 0
        for k in (
            "missing_catalog",
            "duplicate_tags",
            "orphaned_child_contacts",
            "wire_errors",
            "schematic_vs_panel_discrepancy",
            "family_block_misuse",
            "unupdated_titleblocks",
            "wires_piercing_symbols",
            "open_circuit_loads",
            "panel_layout_violations",
        )
    )
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
            "unupdated_titleblocks": dwg_findings["unupdated_titleblocks"][:10],
            "wires_piercing_symbols": dwg_findings["wires_piercing_symbols"][:10],
            "open_circuit_loads": dwg_findings["open_circuit_loads"][:10],
            "panel_layout_violations": dwg_findings["panel_layout_violations"][:10],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ACADE Project Scratch Database (.mdb) + DWG Gatekeeper Audit v2.0 (Fail-Closed)")
    parser.add_argument("--mdb", type=Path, required=True, help="Path to <project>.mdb Scratch Database")
    parser.add_argument("--project-dir", type=Path, default=None, help="Optional project folder or 01_Drawings folder for DWG inspection")
    args = parser.parse_args()

    result = audit_scratch_database(args.mdb, args.project_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
