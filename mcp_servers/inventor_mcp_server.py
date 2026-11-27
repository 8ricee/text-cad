"""Global Zero-Dependency Stdio MCP Server for Direct Autodesk Inventor .NET Add-in Automation via Named Pipe.

Runs in the user's Windows Desktop session when spawned by Antigravity Language Server via mcp_config.json.
Communicates exclusively over Named Pipe (\\\\.\\pipe\\agy-inventor-direct) with Agy.InventorBridge (.NET 10 in-process Add-in).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from pipe_client import launch_on_desktop, pipe_available, pipe_call

SERVER_INFO = {"name": "inventor-direct", "version": "2.0.0"}
PROTOCOL_VERSION = "2024-11-05"
PIPE_NAME = "agy-inventor-direct"
INVENTOR_EXE = Path(r"C:\Program Files\Autodesk\Inventor 2027\Bin\Inventor.exe")


def _ensure_inventor_pipe(launch_if_closed: bool = True, timeout_s: float = 75.0) -> bool:
    if pipe_available(PIPE_NAME, wait_ms=200):
        return True
    if not launch_if_closed:
        return False
    if not INVENTOR_EXE.exists():
        raise FileNotFoundError(f"Inventor 2027 executable not found: {INVENTOR_EXE}")
    launch_on_desktop(f'"{INVENTOR_EXE}"', str(INVENTOR_EXE.parent))
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if pipe_available(PIPE_NAME, wait_ms=500):
            return True
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for Inventor Named Pipe '{PIPE_NAME}' after {timeout_s}s.")


def tool_inventor_status(_args: dict[str, Any]) -> dict[str, Any]:
    if not pipe_available(PIPE_NAME, wait_ms=200):
        return {"running": False, "transport": "named-pipe-inproc-dotnet10", "docCount": 0, "activeDocument": None}
    return pipe_call(PIPE_NAME, "status", {}, timeout_s=15.0)


def tool_inventor_create_or_open(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_inventor_pipe(launch_if_closed=True)
    return pipe_call(PIPE_NAME, "create_or_open", args, timeout_s=60.0)


def tool_inventor_run_script(args: dict[str, Any]) -> dict[str, Any]:
    script_body = str(args.get("ilogic_script") or args.get("script") or "").strip()
    if not script_body:
        raise ValueError("ilogic_script must not be empty.")
    _ensure_inventor_pipe(launch_if_closed=False)
    return pipe_call(PIPE_NAME, "run_script", {"ilogic_script": script_body}, timeout_s=90.0)


def tool_inventor_check_constraints_and_interference(_args: dict[str, Any]) -> dict[str, Any]:
    _ensure_inventor_pipe(launch_if_closed=False)
    return pipe_call(PIPE_NAME, "check_constraints_and_interference", {}, timeout_s=45.0)


def tool_inventor_update_parameters(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_inventor_pipe(launch_if_closed=False)
    return pipe_call(PIPE_NAME, "update_parameters", {"parameters": args.get("parameters", {})}, timeout_s=45.0)


def tool_inventor_export_flat_pattern_dxf(args: dict[str, Any]) -> dict[str, Any]:
    _ensure_inventor_pipe(launch_if_closed=False)
    return pipe_call(PIPE_NAME, "export_flat_pattern_dxf", {"out_path": args["out_path"]}, timeout_s=45.0)


TOOLS = [
    {"name": "inventor_status", "description": "Inspect running Autodesk Inventor 2027 via in-process .NET Add-in Named Pipe.", "inputSchema": {"type": "object", "properties": {}}},
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
        "description": "Execute an iLogic / VB.NET Inventor API script in-process inside Inventor.exe (ThisApplication & ThisDoc pre-bound) wrapped in an atomic Transaction.",
        "inputSchema": {"type": "object", "properties": {"ilogic_script": {"type": "string"}}, "required": ["ilogic_script"]},
    },
    {"name": "inventor_check_constraints_and_interference", "description": "Verify kFullyConstrained sketches, occurrence DOF=0, and Assembly AnalyzeInterference.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "inventor_update_parameters", "description": "Atomically update Inventor UserParameters/ModelParameters inside a Transaction, rebuild, and save.", "inputSchema": {"type": "object", "properties": {"parameters": {"type": "object"}}, "required": ["parameters"]}},
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
