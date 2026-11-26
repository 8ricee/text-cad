"""AutoCAD Electrical Project Scratch Database (.mdb) Gatekeeper Audit.

Queries the ACADE Project Scratch Database (<project>.mdb: COMP, TERMS, WIRENO, XREF, PNLCOMP)
via 64-bit Windows ODBC (System.Data.Odbc) and fails hard (exit code 2) if any violation is found:
1. bogus_wires / unconnected_wire_stubs > 0
2. orphaned_child_contacts > 0
3. duplicate_component_tags > 0
4. missing_catalog_data (MFG or CAT empty) > 0
5. schematic_vs_panel_discrepancy (+MAIN_PNL / +DOOR missing in PNLCOMP) > 0
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def audit_scratch_database(mdb_path: Path) -> dict[str, Any]:
    """Query ACADE Project Scratch .mdb and return structured audit findings + pass/fail."""
    if not mdb_path.exists():
        raise FileNotFoundError(f"Scratch database not found: {mdb_path}")

    mdb_str = str(mdb_path.resolve()).replace("'", "''")
    ps = f"""
$ErrorActionPreference = 'Stop'
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq=$mdb_str;ReadOnly=1;")
$conn.Open()
$tables = $conn.GetSchema("Tables") | Where-Object {{ $_.TABLE_TYPE -eq "TABLE" }} | Select-Object -ExpandProperty TABLE_NAME

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

$missingCat = @()
$dupTags = @()
$orphans = @()
$unconnectedStubs = @()
$panelDiscrepancies = @()

if ($tables -contains "COMP") {{
    $missingCat = Run-Query "SELECT TAGNAME, SHEET, LOC, INST FROM [COMP] WHERE (MFG IS NULL OR MFG='') OR (CAT IS NULL OR CAT='')"
    $dupTags = Run-Query "SELECT TAGNAME, LOC, INST, COUNT(*) AS CNT FROM [COMP] WHERE TAGNAME IS NOT NULL AND TAGNAME<>'' GROUP BY TAGNAME, LOC, INST HAVING COUNT(*) > 1"
    if ($tables -contains "XREF") {{
        $orphans = Run-Query "SELECT x.TAGNAME, x.SHEET FROM [XREF] x LEFT JOIN [COMP] c ON x.TAGNAME = c.TAGNAME WHERE c.TAGNAME IS NULL AND x.TAGNAME IS NOT NULL AND x.TAGNAME<>''"
    }}
    if ($tables -contains "PNLCOMP") {{
        $panelDiscrepancies = Run-Query "SELECT c.TAGNAME, c.LOC, c.MFG, c.CAT FROM [COMP] c LEFT JOIN [PNLCOMP] p ON c.TAGNAME = p.TAGNAME WHERE (c.LOC='+MAIN_PNL' OR c.LOC='+DOOR') AND p.TAGNAME IS NULL AND c.TAGNAME IS NOT NULL AND c.TAGNAME<>''"
    }}
}}

if ($tables -contains "WIRENO") {{
    $unconnectedStubs = Run-Query "SELECT WIRENO, SHEET, DWGIX FROM [WIRENO] WHERE WIRENO IS NULL OR WIRENO='' OR WIRENO LIKE '?%'"
}}

$conn.Close()

$counts = @{{
    missing_catalog = $missingCat.Count
    duplicate_tags = $dupTags.Count
    orphaned_child_contacts = $orphans.Count
    unconnected_wire_stubs = $unconnectedStubs.Count
    schematic_vs_panel_discrepancy = $panelDiscrepancies.Count
}}
$passed = ($counts.missing_catalog -eq 0) -and ($counts.duplicate_tags -eq 0) -and ($counts.orphaned_child_contacts -eq 0) -and ($counts.unconnected_wire_stubs -eq 0) -and ($counts.schematic_vs_panel_discrepancy -eq 0)

@{{
    mdb = '{mdb_str}'
    tables_present = $tables
    passed = $passed
    counts = $counts
    samples = @{{
        missing_catalog = ($missingCat | Select-Object -First 10)
        duplicate_tags = ($dupTags | Select-Object -First 10)
        orphaned_child_contacts = ($orphans | Select-Object -First 10)
        unconnected_wire_stubs = ($unconnectedStubs | Select-Object -First 10)
        schematic_vs_panel_discrepancy = ($panelDiscrepancies | Select-Object -First 10)
    }}
}} | ConvertTo-Json -Depth 6 -Compress
"""
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "Audit PowerShell error").strip())
    return json.loads(proc.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="ACADE Project Scratch Database (.mdb) Gatekeeper Audit")
    parser.add_argument("--mdb", type=Path, required=True, help="Path to <project>.mdb Scratch Database")
    args = parser.parse_args()

    result = audit_scratch_database(args.mdb)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
