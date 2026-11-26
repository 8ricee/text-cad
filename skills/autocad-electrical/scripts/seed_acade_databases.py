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
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_AEDATA = Path(r"F:\OneDrive\Documents\Acade 2027\AeData\en-US")

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


def seed_footprint_mdb(fp_mdb: Path, fp_csv: Path) -> dict[str, int]:
    """Upsert verified_footprints_catalog.csv entries into footprint_lookup.mdb."""
    with fp_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    statements: list[str] = []
    for row in rows:
        mfg = _sql_esc(row.get("MFG", "").upper())
        cat = _sql_esc(row.get("CAT", "").upper())
        w = row.get("W_MM", "0").strip()
        h = row.get("H_MM", "0").strip()
        mnt = row.get("MOUNT_TYPE", "").strip()
        if not mfg or not cat:
            continue
        blknam = _sql_esc(f"PNL_{mfg}_{cat}".replace("-", "_"))
        desc = _sql_esc(f"{w}x{h}mm {mnt}")
        statements.append(f"DELETE FROM [{mfg}] WHERE CATALOG='{cat}'")
        statements.append(
            f"INSERT INTO [{mfg}] (CATALOG, ASSEMBLYCODE, BLKNAM, DESCRIPTION) "
            f"VALUES ({_sql_val(cat)}, NULL, {_sql_val(blknam)}, {_sql_val(desc)})"
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
    parser.add_argument("--aedata", type=Path, default=DEFAULT_AEDATA, help="Path to AeData\\en-US folder")
    args = parser.parse_args()

    cat_mdb = args.aedata / "Catalogs" / "default_cat.mdb"
    fp_mdb = args.aedata / "Catalogs" / "footprint_lookup.mdb"
    plc_mdb = args.aedata / "Plc" / "ace_plc.mdb"

    cat_res = seed_catalog_mdb(cat_mdb, SKILL_DIR / "templates" / "catalog_master_seed.csv")
    fp_res = seed_footprint_mdb(fp_mdb, SKILL_DIR / "templates" / "verified_footprints_catalog.csv")
    plc_res = verify_plc_codes(plc_mdb, SKILL_DIR / "templates" / "plc_io_import_template.csv")

    print(json.dumps({"catalog": cat_res, "footprint": fp_res, "plc": plc_res}, indent=2))
    if plc_res["missing"]:
        raise SystemExit(f"Missing PLC codes in ace_plc.mdb: {plc_res['missing']}")


if __name__ == "__main__":
    main()
