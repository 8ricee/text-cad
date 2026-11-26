"""AutoCAD Electrical Project Scratch Database (.mdb) Gatekeeper Audit (Fail-Closed).

Queries the real ACADE 2027 Project Scratch Database (<project>.mdb):
- COMP (PAR1_CHLD2=1 Parent, PAR1_CHLD2=2 Child)
- PNLCOMP (Panel Footprint components)
- WIRE_ERR (Wire errors)
- WFRM2ALL (From/To wire list)
via 64-bit Windows ODBC (System.Data.Odbc).

Fails closed (passed=False, exit code 2) if:
1. COMP table is missing or empty (unbuilt/unlinked Scratch DB)
2. missing_catalog (MFG or CAT empty) > 0
3. duplicate_tags (same TAGNAME+LOC+INST among PAR1_CHLD2='1' Parents) > 0
4. orphaned_child_contacts (PAR1_CHLD2='2' Child without matching Parent in COMP) > 0
5. wire_errors (rows in WIRE_ERR or '?' wire numbers in WFRM2ALL) > 0
6. schematic_vs_panel_discrepancy (+MAIN_PNL / +DOOR Parents missing in PNLCOMP) > 0
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
from pathlib import Path
from typing import Any


def audit_scratch_database(mdb_path: Path) -> dict[str, Any]:
    """Query ACADE Project Scratch .mdb (Fail-Closed) and return structured audit findings."""
    if not mdb_path.exists():
        raise FileNotFoundError(f"Scratch database not found: {mdb_path}")

    mdb_str = str(mdb_path.resolve()).replace("'", "''")
    ps = f"""
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq=$mdb_str;")
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

$missingCat = Run-Query "SELECT TAGNAME, DWGIX, LOC, INST, PAR1_CHLD2 FROM [COMP] WHERE PAR1_CHLD2='1' AND ((MFG IS NULL OR MFG='') OR (CAT IS NULL OR CAT=''))"
$dupTags = Run-Query "SELECT TAGNAME, LOC, INST, COUNT(*) AS CNT FROM [COMP] WHERE PAR1_CHLD2='1' AND TAGNAME IS NOT NULL AND TAGNAME<>'' GROUP BY TAGNAME, LOC, INST HAVING COUNT(*) > 1"
$orphans = Run-Query "SELECT c.TAGNAME, c.DWGIX, c.LOC FROM [COMP] c LEFT JOIN (SELECT DISTINCT TAGNAME FROM [COMP] WHERE PAR1_CHLD2='1') p ON c.TAGNAME = p.TAGNAME WHERE c.PAR1_CHLD2='2' AND p.TAGNAME IS NULL AND c.TAGNAME IS NOT NULL AND c.TAGNAME<>''"

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

$conn.Close()

$counts = @{{
    comp_total = $compTotal
    missing_catalog = $missingCat.Count
    duplicate_tags = $dupTags.Count
    orphaned_child_contacts = $orphans.Count
    wire_errors = $wireErrs.Count
    schematic_vs_panel_discrepancy = $panelDiscrepancies.Count
}}
$passed = ($counts.missing_catalog -eq 0) -and ($counts.duplicate_tags -eq 0) -and ($counts.orphaned_child_contacts -eq 0) -and ($counts.wire_errors -eq 0) -and ($counts.schematic_vs_panel_discrepancy -eq 0)

@{{
    mdb = '{mdb_str}'
    tables_present = $tables
    passed = $passed
    counts = $counts
    samples = @{{
        missing_catalog = ($missingCat | Select-Object -First 10)
        duplicate_tags = ($dupTags | Select-Object -First 10)
        orphaned_child_contacts = ($orphans | Select-Object -First 10)
        wire_errors = ($wireErrs | Select-Object -First 10)
        schematic_vs_panel_discrepancy = ($panelDiscrepancies | Select-Object -First 10)
    }}
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
    return json.loads(proc.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="ACADE Project Scratch Database (.mdb) Gatekeeper Audit (Fail-Closed)")
    parser.add_argument("--mdb", type=Path, required=True, help="Path to <project>.mdb Scratch Database")
    args = parser.parse_args()

    result = audit_scratch_database(args.mdb)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
