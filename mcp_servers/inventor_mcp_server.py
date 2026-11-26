"""Global Zero-Dependency Stdio MCP Server for Direct Autodesk Inventor COM Automation.

Runs in the user's Windows Desktop session when spawned by Antigravity Language Server via mcp_config.json:
- inventor_status: Inspect active Inventor document, parameters, and sheet-metal FlatPattern status.
- inventor_check_constraints_and_interference: Audit Sketch constraint status (kFullyConstrained) and Assembly interference.
- inventor_update_parameters: Update UserParameters/ModelParameters in active .ipt/.iam and rebuild + save.
- inventor_export_flat_pattern_dxf: Unfold Sheet Metal part and export layered DXF (OUTER_PROFILE, INNER_CUTS, BEND_UP, BEND_DOWN).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SERVER_INFO = {"name": "inventor-direct", "version": "1.1.0"}
PROTOCOL_VERSION = "2024-11-05"


def _run_ps(script: str, timeout: int = 45) -> dict[str, Any]:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "PowerShell error").strip())
    out = (proc.stdout or "").strip()
    if not out:
        return {"ok": True}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": True, "raw": out}


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def tool_inventor_status(_args: dict[str, Any]) -> dict[str, Any]:
    ps = r"""
$ErrorActionPreference = 'Stop'
$inv = [Runtime.InteropServices.Marshal]::GetActiveObject('Inventor.Application')
$active = $null
if ($inv.ActiveDocument) {
    $d = $inv.ActiveDocument
    $active = @{ name = $d.DisplayName; fullName = $d.FullFileName; type = [int]$d.DocumentType; dirty = $d.Dirty }
}
@{ caption = $inv.Caption; docCount = $inv.Documents.Count; activeDocument = $active } | ConvertTo-Json -Depth 4 -Compress
"""
    return _run_ps(ps)


def tool_inventor_create_or_open(args: dict[str, Any]) -> dict[str, Any]:
    doc_type = args.get("doc_type", "part_sheet_metal")
    save_path = args.get("save_path", "")
    ipj_path = args.get("ipj_path", "")
    open_path = args.get("open_path", "")
    save_q = _ps_quote(str(Path(save_path).resolve())) if save_path else "''"
    ipj_q = _ps_quote(str(Path(ipj_path).resolve())) if ipj_path else "''"
    open_q = _ps_quote(str(Path(open_path).resolve())) if open_path else "''"
    ps = f"""
$ErrorActionPreference = 'Stop'
$inv = [Runtime.InteropServices.Marshal]::GetActiveObject('Inventor.Application')
if ({ipj_q}) {{
    $pm = $inv.DesignProjectManager
    $proj = $pm.DesignProjects.AddExisting({ipj_q})
    $proj.Activate($true)
}}
if ({open_q}) {{
    $d = $inv.Documents.Open({open_q}, $true)
}} else {{
    $typeEnum = switch ('{doc_type}') {{
        'assembly' {{ 12291 }}
        'drawing'  {{ 12292 }}
        default    {{ 12290 }}
    }}
    $tpl = ''
    if ('{doc_type}' -eq 'part_sheet_metal') {{
        $tpl = $inv.FileManager.GetTemplateFile(12290, 9729, 9729, '{{9C464203-9BAE-11D3-8BAD-0060B0CE6BB4}}')
    }} else {{
        $tpl = $inv.FileManager.GetTemplateFile($typeEnum, 9729)
    }}
    $d = $inv.Documents.Add($typeEnum, $tpl, $true)
    if ({save_q}) {{
        $dir = Split-Path -Parent {save_q}
        if ($dir -and -not (Test-Path $dir)) {{ New-Item -ItemType Directory -Path $dir -Force | Out-Null }}
        $d.SaveAs({save_q}, $false)
    }}
}}
@{{ displayName = $d.DisplayName; fullFileName = $d.FullFileName; documentType = [int]$d.DocumentType }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps, timeout=60)


def tool_inventor_run_script(args: dict[str, Any]) -> dict[str, Any]:
    script_body = str(args.get("powershell_script", "")).strip()
    if not script_body:
        raise ValueError("powershell_script must not be empty.")
    ps = f"""
$ErrorActionPreference = 'Stop'
$inv = [Runtime.InteropServices.Marshal]::GetActiveObject('Inventor.Application')
$doc = $inv.ActiveDocument
{script_body}
"""
    return _run_ps(ps, timeout=90)


def tool_inventor_check_constraints_and_interference(_args: dict[str, Any]) -> dict[str, Any]:
    ps = r"""
$ErrorActionPreference = 'Stop'
$inv = [Runtime.InteropServices.Marshal]::GetActiveObject('Inventor.Application')
$d = $inv.ActiveDocument
if (-not $d) { throw 'No active Inventor document.' }
$unconstrained = @()
$interferences = 0
$ungroundedDof = @()
if ($d.DocumentType -eq 12290) {
    foreach ($sk in $d.ComponentDefinition.Sketches) {
        if ([int]$sk.ConstraintStatus -ne 51713) { $unconstrained += $sk.Name }
    }
} elseif ($d.DocumentType -eq 12291) {
    $set1 = $inv.TransientObjects.CreateObjectCollection()
    foreach ($occ in $d.ComponentDefinition.Occurrences) {
        $set1.Add($occ) | Out-Null
        if (-not $occ.Grounded) {
            try {
                $tDof = 0; $rDof = 0; $tVec = $null; $rVec = $null
                $occ.GetDegreesOfFreedom([ref]$tDof, [ref]$tVec, [ref]$rDof, [ref]$rVec)
                if (($tDof + $rDof) -gt 0) {
                    $ungroundedDof += @{ name = $occ.Name; transDof = $tDof; rotDof = $rDof }
                }
            } catch {}
        }
    }
    if ($set1.Count -ge 2) {
        $res = $d.ComponentDefinition.AnalyzeInterference($set1)
        $interferences = $res.Count
    }
}
@{ document = $d.DisplayName; unconstrainedSketches = $unconstrained; ungroundedDof = $ungroundedDof; assemblyInterferences = $interferences } | ConvertTo-Json -Depth 5 -Compress
"""
    return _run_ps(ps)


def tool_inventor_update_parameters(args: dict[str, Any]) -> dict[str, Any]:
    updates = args.get("parameters", {})
    payload_q = _ps_quote(json.dumps(updates))
    ps = f"""
$ErrorActionPreference = 'Stop'
$updates = ConvertFrom-Json {payload_q}
$inv = [Runtime.InteropServices.Marshal]::GetActiveObject('Inventor.Application')
$d = $inv.ActiveDocument
if (-not $d) {{ throw 'No active Inventor document.' }}
$cd = $d.ComponentDefinition
$changed = @()
foreach ($prop in $updates.PSObject.Properties) {{
    $p = $null
    try {{ $p = $cd.Parameters.UserParameters.Item($prop.Name) }} catch {{
        try {{ $p = $cd.Parameters.ModelParameters.Item($prop.Name) }} catch {{}}
    }}
    if ($p) {{
        $p.Expression = [string]$prop.Value
        $changed += $prop.Name
    }}
}}
$d.Update2($true)
$d.Save()
@{{ document = $d.DisplayName; updated = $changed; saved = $true }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps)


def tool_inventor_export_flat_pattern_dxf(args: dict[str, Any]) -> dict[str, Any]:
    out_path = str(Path(args["out_path"]).resolve())
    out_q = _ps_quote(out_path)
    ps = f"""
$ErrorActionPreference = 'Stop'
$inv = [Runtime.InteropServices.Marshal]::GetActiveObject('Inventor.Application')
$d = $inv.ActiveDocument
if (-not $d -or $d.DocumentType -ne 12290) {{ throw 'Active document must be an Inventor Part (.ipt).' }}
$cd = $d.ComponentDefinition
if (-not $cd.HasFlatPattern) {{ $cd.Unfold() }}
$fmt = 'FLAT PATTERN DXF?AcadVersion=2018&OuterProfileLayer=OUTER_PROFILE&InteriorProfilesLayer=INNER_CUTS&BendUpLayer=BEND_UP&BendUpLayerLineType=37633&BendDownLayer=BEND_DOWN&BendDownLayerLineType=37634&InvisibleLayers=IV_TANGENT;IV_TOOL_CENTER;IV_ARC_CENTERS'
$cd.DataIO.WriteDataToFile($fmt, {out_q})
@{{ exported = {out_q} }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps)


TOOLS = [
    {"name": "inventor_status", "description": "Inspect running Autodesk Inventor via COM.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "inventor_create_or_open",
        "description": "Create a new Metric (.ipt Standard/SheetMetal, .iam, .idw) document or open/activate an existing .ipj/document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "doc_type": {"type": "string", "enum": ["part_standard", "part_sheet_metal", "assembly", "drawing"], "default": "part_sheet_metal"},
                "save_path": {"type": "string"},
                "ipj_path": {"type": "string"},
                "open_path": {"type": "string"},
            },
        },
    },
    {
        "name": "inventor_run_script",
        "description": "Execute a PowerShell Inventor COM script ($inv and $doc pre-bound) to build Sketches, Extrude, Sheet Metal Flanges, Corner Relief, Assembly Constraints, or IDW Views.",
        "inputSchema": {"type": "object", "properties": {"powershell_script": {"type": "string"}}, "required": ["powershell_script"]},
    },
    {"name": "inventor_check_constraints_and_interference", "description": "Verify kFullyConstrained sketches, occurrence DOF=0, and Assembly AnalyzeInterference.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "inventor_update_parameters", "description": "Update Inventor UserParameters/ModelParameters, rebuild, and save.", "inputSchema": {"type": "object", "properties": {"parameters": {"type": "object"}}, "required": ["parameters"]}},
    {"name": "inventor_export_flat_pattern_dxf", "description": "Export Sheet Metal FlatPattern DXF with OUTER_PROFILE, INNER_CUTS, BEND_UP (Continuous), BEND_DOWN (Dashed) layers.", "inputSchema": {"type": "object", "properties": {"out_path": {"type": "string"}}, "required": ["out_path"]}},
]

HANDLERS = {
    "inventor_status": tool_inventor_status,
    "inventor_create_or_open": tool_inventor_create_or_open,
    "inventor_run_script": tool_inventor_run_script,
    "inventor_check_constraints_and_interference": tool_inventor_check_constraints_and_interference,
    "inventor_update_parameters": tool_inventor_update_parameters,
    "inventor_export_flat_pattern_dxf": tool_inventor_export_flat_pattern_dxf,
}


def _send(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main() -> None:
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}
        if req_id is None:
            continue
        try:
            if method == "initialize":
                result = {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                tname = params.get("name", "")
                targs = params.get("arguments") or {}
                if tname not in HANDLERS:
                    raise ValueError(f"Unknown tool: {tname}")
                out = HANDLERS[tname](targs)
                result = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}], "isError": False}
            else:
                _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})
                continue
            _send({"jsonrpc": "2.0", "id": req_id, "result": result})
        except Exception as exc:
            if method == "tools/call":
                _send({"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Error: {exc}"}], "isError": True}})
            else:
                _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(exc)}})


if __name__ == "__main__":
    main()
