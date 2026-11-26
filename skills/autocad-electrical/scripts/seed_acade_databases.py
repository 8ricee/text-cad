"""Seed AutoCAD Electrical Access Databases (.mdb) via 64-bit Windows ODBC.

Idempotently upserts:
1. templates/catalog_master_seed.csv -> default_cat.mdb (family tables + _PINLIST)
2. templates/verified_footprints_catalog.csv -> footprint_lookup.mdb (MFG tables)
3. Verifies Siemens S7-1500/S7-1200 module codes in ace_plc.mdb

Uses PowerShell System.Data.Odbc (zero external Python ODBC dependencies required).
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def detect_aedata_dir() -> Path:
    """Auto-detect Acade 2027 AeData\\en-US path from OneDrive, Documents, or UserDataCache."""
    candidates = [
        Path.home() / "OneDrive" / "Documents" / "Acade 2027" / "AeData" / "en-US",
        Path(r"F:\OneDrive\Documents\Acade 2027\AeData\en-US"),
        Path.home() / "Documents" / "Acade 2027" / "AeData" / "en-US",
        Path(r"C:\Program Files\Autodesk\AutoCAD 2027\Acade\UserDataCache\My Documents\Acade 2027\AeData\en-US"),
    ]
    for p in candidates:
        if (p / "Catalogs" / "default_cat.mdb").exists():
            return p
    return candidates[0]


def detect_panel_libs_dir() -> Path:
    """Auto-detect ACADE Libs\\panel folder from registry or standard paths."""
    candidates = [
        Path(r"F:\Projects\CAD\Libraries\AutoCAD-Electrical\2027\Libs\panel"),
        Path(r"C:\Users\Public\Documents\Autodesk\Acade 2027\Libs\panel"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


def backup_mdb(mdb_path: Path) -> Path:
    """Create a .mdb.bak safety backup before mutating an Access database."""
    bak = mdb_path.with_suffix(".mdb.bak")
    if not bak.exists():
        shutil.copy2(mdb_path, bak)
    return bak

FAMILY_TO_TABLE = {
    "Q": "CB",
    "F": "FU",
    "K": "CR",
    "M": "MO",
    "G": "PS",
    "A": "PLCIO",
    "U": "DR",
    "S": "PB",
    "H": "LT",
    "X": "TRMS",
}


def _run_ps_odbc(ps_script: str) -> str:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "ODBC PowerShell error").strip())
    return proc.stdout.strip()


def _sql_esc(val: str) -> str:
    return (val or "").replace("'", "''").strip()


def _sql_val(val: str) -> str:
    cleaned = _sql_esc(val)
    return f"'{cleaned}'" if cleaned else "NULL"


def seed_catalog_mdb(cat_mdb: Path, seed_csv: Path) -> dict[str, int]:
    """Upsert catalog_master_seed.csv rows into default_cat.mdb family tables and _PINLIST."""
    backup_mdb(cat_mdb)
    with seed_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    statements: list[str] = []
    for row in rows:
        cat = _sql_esc(row.get("CAT", ""))
        mfg = _sql_esc(row.get("MFG", "").upper())
        desc = _sql_esc(row.get("DESCRIPTION", ""))
        fam = (row.get("FAMILY", "") or "MISC_CAT").strip().upper()
        tbl = FAMILY_TO_TABLE.get(fam, "MISC_CAT")
        coilpins = _sql_esc(row.get("COILPINS", ""))
        pinlist = _sql_esc(row.get("PINLIST", ""))
        assy = _sql_esc(row.get("ASSYCODE", ""))
        wdblknam = _sql_esc(row.get("WDBLKNAM", ""))
        web = _sql_esc(row.get("WEB", ""))
        rating = _sql_esc(" ".join(filter(None, [row.get("RATING1", ""), row.get("RATING2", ""), row.get("RATING3", "")])))

        if not cat or not mfg:
            continue

        statements.append(
            f"DELETE FROM [{tbl}] WHERE CATALOG='{cat}' AND MANUFACTURER='{mfg}'"
        )
        if tbl in ("CB", "FU"):
            statements.append(
                f"INSERT INTO [{tbl}] (CATALOG, MANUFACTURER, DESCRIPTION, RATING, ASSEMBLYCODE, WDBLKNAM, WEBLINK) "
                f"VALUES ({_sql_val(cat)}, {_sql_val(mfg)}, {_sql_val(desc)}, {_sql_val(rating)}, {_sql_val(assy)}, {_sql_val(wdblknam)}, {_sql_val(web)})"
            )
        else:
            statements.append(
                f"INSERT INTO [{tbl}] (CATALOG, MANUFACTURER, DESCRIPTION, ASSEMBLYCODE, WDBLKNAM, WEBLINK) "
                f"VALUES ({_sql_val(cat)}, {_sql_val(mfg)}, {_sql_val(desc)}, {_sql_val(assy)}, {_sql_val(wdblknam)}, {_sql_val(web)})"
            )
        if pinlist:
            statements.append(
                f"DELETE FROM [_PINLIST] WHERE CATALOG='{cat}' AND MANUFACTURER='{mfg}'"
            )
            statements.append(
                f"INSERT INTO [_PINLIST] (MANUFACTURER, CATALOG, ASSEMBLYCODE, COILPINS, PINLIST) "
                f"VALUES ({_sql_val(mfg)}, {_sql_val(cat)}, {_sql_val(assy)}, {_sql_val(coilpins)}, {_sql_val(pinlist)})"
            )

    payload_json = json.dumps(statements)
    ps = f"""
$ErrorActionPreference = 'Stop'
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={cat_mdb};")
$conn.Open()
$stmts = ConvertFrom-Json '{payload_json.replace("'", "''")}'
$applied = 0
foreach ($sql in $stmts) {{
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = $sql
    $null = $cmd.ExecuteNonQuery()
    $applied++
}}
$conn.Close()
Write-Output $applied
"""
    applied = int(_run_ps_odbc(ps) or "0")
    return {"catalog_rows": len(rows), "sql_statements": applied}


def convert_dxf_to_dwg(dxf_path: Path, dwg_path: Path) -> Path:
    """Convert a DXF file to native AutoCAD .dwg using accoreconsole.exe."""
    accore = Path(r"C:\Program Files\Autodesk\AutoCAD 2027\accoreconsole.exe")
    if not accore.exists():
        raise FileNotFoundError(f"accoreconsole.exe not found: {accore}")
    scr = dxf_path.with_suffix(".scr")
    dwg_posix = dwg_path.as_posix()
    scr.write_text(f'(setvar "FILEDIA" 0)\n(setvar "EXPERT" 5)\n_.SAVEAS\n2018\n{dwg_posix}\n_QUIT _Y\n', encoding="ascii")
    proc = subprocess.run([str(accore), "/i", str(dxf_path), "/s", str(scr), "/l", "en-US"], capture_output=True, text=True, timeout=30)
    scr.unlink(missing_ok=True)
    if proc.returncode != 0 or not dwg_path.exists():
        raise RuntimeError(f"Failed converting {dxf_path.name} -> .dwg (rc={proc.returncode})")
    return dwg_path


def _build_panel_footprint_dwg_if_missing(panel_dir: Path, mfg: str, blknam: str, row: dict[str, str]) -> Path:
    """Create a 5-detail 1:1 mm Smart Panel Footprint .dwg (outer body, bezel, terminals, screw holes, DIN/base mount + P_TAG1)."""
    import ezdxf

    w_mm = float(row.get("W_MM", "0") or 0)
    h_mm = float(row.get("H_MM", "0") or 0)
    cat = _sql_esc(row.get("CAT", "").upper())
    mnt = (row.get("MOUNT_TYPE", "") or "DIN_TS35").strip().upper()
    hole_dx = float(row.get("HOLE_DX_MM", "0") or 0)
    hole_dy = float(row.get("HOLE_DY_MM", "0") or 0)
    hole_dia = float(row.get("HOLE_DIA_MM", "0") or 0)
    esc_w = float(row.get("ESCUTCHEON_W_MM", "0") or 0)
    esc_h = float(row.get("ESCUTCHEON_H_MM", "0") or 0)

    out_dir = panel_dir / "CUSTOM" / mfg
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dwg = out_dir / f"{blknam}.dwg"
    old_dxf = out_dir / f"{blknam}.dxf"
    if old_dxf.exists():
        old_dxf.unlink()
    if out_dwg.exists():
        return out_dwg

    tmp_dxf = out_dir / f"{blknam}_tmp.dxf"
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    msp = doc.modelspace()

    # 1. Outer body outline
    msp.add_lwpolyline([(0, 0), (w_mm, 0), (w_mm, h_mm), (0, h_mm), (0, 0)])
    # 2. Inner bezel / escutcheon collar
    bw = esc_w if esc_w > 0 else max(6.0, w_mm - 6.0)
    bh = esc_h if esc_h > 0 else max(10.0, h_mm * 0.56)
    bx0, by0 = (w_mm - bw) / 2.0, (h_mm - bh) / 2.0
    msp.add_lwpolyline([(bx0, by0), (bx0 + bw, by0), (bx0 + bw, by0 + bh), (bx0, by0 + bh), (bx0, by0)])
    # 3. Top & bottom terminal cavities + screw circles
    n_poles = max(2, min(6, int(round(w_mm / 18.0))))
    step_x = (w_mm - 8.0) / n_poles
    for i in range(n_poles):
        tx = 4.0 + (i + 0.5) * step_x
        msp.add_circle((tx, h_mm - 6.0), radius=2.4)
        msp.add_circle((tx, 6.0), radius=2.4)
    # 4. Mounting screw holes (Base-mounted) or 5. DIN rail latch tabs
    if mnt in ("BASE", "DOOR") and hole_dx > 0 and hole_dy > 0:
        r_h = max(1.5, hole_dia / 2.0)
        cx, cy = w_mm / 2.0, h_mm / 2.0
        for hx in (cx - hole_dx / 2.0, cx + hole_dx / 2.0):
            for hy in (cy - hole_dy / 2.0, cy + hole_dy / 2.0):
                msp.add_circle((hx, hy), radius=r_h)
    else:
        msp.add_lwpolyline([(w_mm / 2 - 6, h_mm), (w_mm / 2 + 6, h_mm), (w_mm / 2 + 6, h_mm + 4), (w_mm / 2 - 6, h_mm + 4), (w_mm / 2 - 6, h_mm)])
        msp.add_lwpolyline([(w_mm / 2 - 6, 0), (w_mm / 2 + 6, 0), (w_mm / 2 + 6, -4), (w_mm / 2 - 6, -4), (w_mm / 2 - 6, 0)])

    msp.add_attdef("P_TAG1", insert=(2.0, h_mm - 5.0), text="", height=3.0)
    msp.add_attdef("MFG", insert=(2.0, 2.0), text=mfg, height=2.0, dxfattribs={"flags": 1})
    msp.add_attdef("CAT", insert=(2.0, 5.0), text=cat, height=2.0, dxfattribs={"flags": 1})
    msp.add_attdef("LOC", insert=(2.0, 8.0), text="+MAIN_PNL", height=2.0, dxfattribs={"flags": 1})
    msp.add_attdef("ASSYCODE", insert=(2.0, 11.0), text="", height=2.0, dxfattribs={"flags": 1})
    doc.saveas(tmp_dxf)
    convert_dxf_to_dwg(tmp_dxf, out_dwg)
    tmp_dxf.unlink(missing_ok=True)
    return out_dwg


def seed_footprint_mdb(fp_mdb: Path, fp_csv: Path, panel_dir: Path) -> dict[str, int]:
    """Upsert verified_footprints_catalog.csv entries into footprint_lookup.mdb and ensure real .dwg footprint blocks exist."""
    backup_mdb(fp_mdb)
    with fp_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    statements: list[str] = []
    for row in rows:
        mfg = _sql_esc(row.get("MFG", "").upper())
        cat = _sql_esc(row.get("CAT", "").upper())
        w = float(row.get("W_MM", "0") or 0)
        h = float(row.get("H_MM", "0") or 0)
        mnt = row.get("MOUNT_TYPE", "").strip()
        if not mfg or not cat:
            continue
        blknam = _sql_esc(f"PNL_{mfg}_{cat}".replace("-", "_"))
        _build_panel_footprint_dwg_if_missing(panel_dir, mfg, blknam, row)
        rel_blk = _sql_esc(f"CUSTOM/{mfg}/{blknam}")
        desc = _sql_esc(f"{w}x{h}mm {mnt}")
        statements.append(f"DELETE FROM [{mfg}] WHERE CATALOG='{cat}'")
        statements.append(
            f"INSERT INTO [{mfg}] (CATALOG, ASSEMBLYCODE, BLKNAM, DESCRIPTION) "
            f"VALUES ({_sql_val(cat)}, NULL, {_sql_val(rel_blk)}, {_sql_val(desc)})"
        )

    payload_json = json.dumps(statements)
    ps = f"""
$ErrorActionPreference = 'Stop'
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={fp_mdb};")
$conn.Open()
$stmts = ConvertFrom-Json '{payload_json.replace("'", "''")}'
$applied = 0
foreach ($sql in $stmts) {{
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = $sql
    $null = $cmd.ExecuteNonQuery()
    $applied++
}}
$conn.Close()
Write-Output $applied
"""
    applied = int(_run_ps_odbc(ps) or "0")
    return {"footprint_rows": len(rows), "sql_statements": applied}


def verify_plc_codes(plc_mdb: Path, plc_csv: Path) -> dict[str, list[str]]:
    """Verify all CODE values in plc_io_import_template.csv exist in ace_plc.mdb."""
    with plc_csv.open("r", encoding="utf-8-sig", newline="") as f:
        codes = sorted({(r.get("CODE") or "").strip() for r in csv.DictReader(f) if (r.get("CODE") or "").strip()})

    codes_json = json.dumps(codes)
    ps = f"""
$ErrorActionPreference = 'Stop'
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={plc_mdb};ReadOnly=1;")
$conn.Open()
$tbls = $conn.GetSchema("Tables") | Where-Object {{ $_.TABLE_TYPE -eq "TABLE" -and $_.TABLE_NAME -like "Siemens_SIMATIC_S7-*" -and $_.TABLE_NAME -notlike "*_Data" }} | Select-Object -ExpandProperty TABLE_NAME
$codes = ConvertFrom-Json '{codes_json}'
$missing = @()
$found = @()
foreach ($c in $codes) {{
    $ok = $false
    foreach ($t in $tbls) {{
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = "SELECT TOP 1 CODE FROM [$t] WHERE CODE='$c'"
        $r = $cmd.ExecuteReader()
        if ($r.Read()) {{ $ok = $true }}
        $r.Close()
        if ($ok) {{ break }}
    }}
    if ($ok) {{ $found += $c }} else {{ $missing += $c }}
}}
$conn.Close()
@{{ found = $found; missing = $missing }} | ConvertTo-Json -Compress
"""
    res = json.loads(_run_ps_odbc(ps))
    return {"found": res.get("found", []), "missing": res.get("missing", [])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ACADE 2027 Access Databases (.mdb) from skill templates")
    parser.add_argument("--aedata", type=Path, default=detect_aedata_dir(), help="Path to AeData\\en-US folder")
    parser.add_argument("--panel-libs", type=Path, default=detect_panel_libs_dir(), help="Path to Libs\\panel folder")
    args = parser.parse_args()

    cat_mdb = args.aedata / "Catalogs" / "default_cat.mdb"
    fp_mdb = args.aedata / "Catalogs" / "footprint_lookup.mdb"
    plc_mdb = args.aedata / "Plc" / "ace_plc.mdb"

    cat_res = seed_catalog_mdb(cat_mdb, SKILL_DIR / "templates" / "catalog_master_seed.csv")
    fp_res = seed_footprint_mdb(fp_mdb, SKILL_DIR / "templates" / "verified_footprints_catalog.csv", args.panel_libs)
    plc_res = verify_plc_codes(plc_mdb, SKILL_DIR / "templates" / "plc_io_import_template.csv")

    print(json.dumps({"catalog": cat_res, "footprint": fp_res, "plc": plc_res}, indent=2))
    if plc_res["missing"]:
        raise SystemExit(f"Missing PLC codes in ace_plc.mdb: {plc_res['missing']}")


if __name__ == "__main__":
    main()
