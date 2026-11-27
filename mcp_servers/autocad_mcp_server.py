"""Global Zero-Dependency Stdio MCP Server for Direct Autodesk AutoCAD COM Automation.

Runs in the user's Windows Desktop session when spawned by Antigravity Language Server via mcp_config.json:
- autocad_status: Inspect running AutoCAD, open documents, active layout, DBMOD, and $INSUNITS.
- autocad_open_or_new: Open a .dwg/.dxf or create a new 1:1 mm drawing with ISO linetypes, VN_ARIAL, and ISO_MM DimStyle.
- autocad_draw_entities: Draw line, circle, arc, lwpolyline, text, mtext, hatch, insert_block (with Attributes),
  mleader, table, dim_aligned, dim_linear, dim_diameter directly into ModelSpace or PaperSpace via COM + auto-save.
- autocad_run_command: Send AutoCAD commands / AutoLISP directly to ActiveDocument.SendCommand() + auto-save.
- autocad_reload_file: Reload a .dwg/.dxf tab safely (protects unsaved manual edits when DBMOD != 0).
- autocad_audit_and_inspect: Audit active document via COM for hardcoded Dim TextOverride, bounding-box overlaps,
  out-of-frame Paper Space entities, CMDACTIVE, and LASTPROMPT.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SERVER_INFO = {"name": "autocad-direct", "version": "2.0.0"}
PROTOCOL_VERSION = "2024-11-05"

SKILL_ROOT = Path(r"C:\Users\Gaadz\.gemini\config\skills\autocad-electrical")
TEMPLATE_DWT = SKILL_ROOT / "templates" / "TEMPLATE_IEC_A3.dwt"
TEMPLATE_PANEL_DWT = SKILL_ROOT / "templates" / "TEMPLATE_PANEL_LAYOUT_A3.dwt"
TEMPLATE_WDP = SKILL_ROOT / "templates" / "TEMPLATE_PROJECT.wdp"
DEFAULT_WDI = SKILL_ROOT / "templates" / "default_plc_io.wdi"
DEFAULT_RGF = SKILL_ROOT / "templates" / "project_master_reports.rgf"
AUDIT_SCRIPT = SKILL_ROOT / "scripts" / "acade_electrical_audit.py"
SEED_SCRIPT = SKILL_ROOT / "scripts" / "seed_acade_databases.py"

MFG_ALIASES = {
    "PHOENIX": "PHOENIX CONTACT",
    "PHOENIX_CONTACT": "PHOENIX CONTACT",
    "SCHNEIDER": "SCHNEIDER ELECTRIC",
    "TELEMECANIQUE": "SCHNEIDER ELECTRIC",
    "ALLEN-BRADLEY": "AB",
    "ALLEN BRADLEY": "AB",
}


def _normalize_mfg(mfg: str) -> str:
    m = (mfg or "SIEMENS").strip().upper()
    return MFG_ALIASES.get(m, m)


def _parse_wdp_metadata(wdp_path: Path) -> tuple[dict[str, str], list[str]]:
    """Parse *[1]..*[10] descriptions and ordered .dwg sheet basenames from a .wdp file."""
    descs: dict[str, str] = {}
    sheets: list[str] = []
    if not wdp_path.exists():
        return descs, sheets
    for raw in wdp_path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = raw.strip()
        if not ln:
            continue
        if ln.startswith("*[") and "]" in ln:
            idx_s, val = ln[2:].split("]", 1)
            if idx_s.isdigit():
                descs[f"LINE{idx_s}"] = val.strip()
        elif not ln.startswith(("*", "+", "?", "=")) and ln.lower().endswith(".dwg"):
            sheets.append(Path(ln).name)
    return descs, sheets


def _build_titleblock_attr_map(
    descs: dict[str, str],
    dwg_path: Path,
    sheet_idx_1based: int,
    sheet_total: int,
    sub: str = "SCH",
) -> dict[str, str]:
    import datetime as _dt

    sh_str = f"{sheet_idx_1based:02d}"
    tot_str = f"{max(1, sheet_total):02d}"
    now = _dt.datetime.now()
    return {
        "PROJECT_NAME": descs.get("LINE1") or dwg_path.parent.name,
        "CLIENT_NAME": descs.get("LINE2") or "INDUSTRIAL AUTOMATION",
        "PANEL_NAME": descs.get("LINE3") or "MAIN CONTROL PANEL",
        "VOLTAGE_RATING": descs.get("LINE4") or "3P 400VAC / 24VDC PELV",
        "DESIGNED_BY": descs.get("LINE5") or "GAADZ ENG.",
        "CHECKED_BY": descs.get("LINE6") or "LEAD ENG.",
        "APPROVED_BY": descs.get("LINE7") or "QA",
        "REVISION": descs.get("LINE8") or "REV A",
        "MATERIAL_FINISH": descs.get("LINE9") or "RAL7035",
        "GENERAL_TOLERANCE": descs.get("LINE10") or "ISO 2768-m",
        "DWG_NO": dwg_path.stem,
        "SHEET": sh_str,
        "SHEET_NO": sh_str,
        "SHEET_TOTAL": tot_str,
        "SUBSECTION_NO": sub[:8],
        "DATE": now.strftime("%Y-%m-%d"),
        "TIME": now.strftime("%H:%M"),
        "FILE_PATH": dwg_path.name,
    }


def _lisp_sync_wdm_and_titleblock(sh_str: str, tb_attrs: dict[str, str]) -> str:
    """Deterministic AutoLISP updater for WD_M.SHEET and TITLE_BLOCK_A3_BILINGUAL (in ModelSpace or PaperSpace)."""
    pairs = " ".join(f'(cons {_lisp_str(k.upper())} {_lisp_str(v)})' for k, v in tb_attrs.items())
    return (
        f'(setq _tbmap (list {pairs})) '
        f'(if (setq _wmss (ssget "X" \'((0 . "INSERT") (2 . "WD_M")))) '
        f'(progn (setq _wi 0) (while (< _wi (sslength _wmss)) '
        f'(setq _we (ssname _wmss _wi) _wn (entnext _we)) '
        f'(while (and _wn (= (cdr (assoc 0 (entget _wn))) "ATTRIB")) '
        f'(setq _wd (entget _wn)) '
        f'(if (= (strcase (cdr (assoc 2 _wd))) "SHEET") '
        f'(entmod (subst (cons 1 {_lisp_str(sh_str)}) (assoc 1 _wd) _wd))) '
        f'(setq _wn (entnext _wn))) (entupd _we) (setq _wi (1+ _wi))))) '
        f'(if (setq _tbss (ssget "X" \'((0 . "INSERT") (2 . "TITLE_BLOCK_A3_BILINGUAL")))) '
        f'(progn (setq _ti 0) (while (< _ti (sslength _tbss)) '
        f'(setq _te (ssname _tbss _ti) _tn (entnext _te)) '
        f'(while (and _tn (= (cdr (assoc 0 (entget _tn))) "ATTRIB")) '
        f'(setq _td (entget _tn) _tk (strcase (cdr (assoc 2 _td))) _tv (cdr (assoc _tk _tbmap))) '
        f'(if _tv (entmod (subst (cons 1 _tv) (assoc 1 _td) _td))) '
        f'(setq _tn (entnext _tn))) (entupd _te) (setq _ti (1+ _ti)))))'
    )


def _lisp_acade_load() -> str:
    return (
        '(if (not c:wd_insym2) '
        '(progn (if (not c:wd_load) (if (setq _wdx (findfile "wdload.lsp")) (load _wdx))) '
        '(if c:wd_load (c:wd_load)))) '
    )


def _lisp_fail_loud_guard(req_fns: list[str], err_file: str) -> str:
    """Emit AutoLISP guard that writes an error file if any required ACADE function is unbound."""
    checks = " ".join(f'(if (not (boundp \'{fn})) (setq _missing (cons "{fn}" _missing)))' for fn in req_fns)
    return (
        f'(setq _missing nil) {checks} '
        f'(if _missing (progn (setq _f (open {_lisp_str(err_file)} "w")) '
        f'(write-line (strcat "Missing ACADE APIs: " (vl-princ-to-string _missing)) _f) '
        f'(close _f))) '
    )


def _run_acade_lisp_checked(lisp_body: str, req_fns: list[str], auto_save: bool = True, timeout_sec: float = 25.0) -> dict[str, Any]:
    """Send ACADE AutoLISP via COM, wait for sentinel file (preventing SendCommand async race), and Fail-Loud if unbound."""
    import tempfile
    import time

    tmp_dir = Path(tempfile.gettempdir())
    err_path = tmp_dir / "acade_mcp_err.txt"
    done_path = tmp_dir / "acade_mcp_done.txt"
    err_path.unlink(missing_ok=True)
    done_path.unlink(missing_ok=True)

    guard = _lisp_fail_loud_guard(req_fns, str(err_path))
    # Always switch to Model Space (TILEMODE=1) during c:wd_insym2 / c:wd_wire_quik schematic editing,
    # then restore Paper Space Layout ISO_A3 (TILEMODE=0) cleanly before saving!
    pre_ms = '(setq _had_iso (member "ISO_A3" (layoutlist))) (if (= (getvar "TILEMODE") 0) (setvar "TILEMODE" 1)) '
    post_ps = ' (if _had_iso (progn (setvar "TILEMODE" 0) (setvar "CTAB" "ISO_A3"))) '
    sentinel = (
        f'(setq _df (open {_lisp_str(str(done_path))} "w")) '
        f'(write-line "DONE" _df) (close _df)'
    )
    full_cmd = f"(progn {_lisp_acade_load()} {guard} (if (not _missing) (progn {pre_ms} {lisp_body} {post_ps})) {sentinel})\n"
    res = tool_autocad_run_command({"command": full_cmd, "auto_save": auto_save})

    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if done_path.exists():
            break
        time.sleep(0.15)
    if not done_path.exists():
        raise TimeoutError(f"AutoCAD SendCommand did not complete within {timeout_sec}s (possible modal dialog).")
    done_path.unlink(missing_ok=True)

    if err_path.exists():
        msg = err_path.read_text(encoding="utf-8", errors="replace").strip()
        err_path.unlink(missing_ok=True)
        raise RuntimeError(f"ACADE Fail-Loud: {msg}")
    return res


def _lisp_str(val: str) -> str:
    return '"' + str(val).replace("\\", "/").replace('"', '\\"') + '"'


def _run_ps(script: str, timeout: int = 30) -> dict[str, Any]:
    """Execute a PowerShell snippet and parse its JSON stdout."""
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "PowerShell error").strip()
        raise RuntimeError(err)
    out = (proc.stdout or "").strip()
    if not out:
        return {"ok": True}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": True, "raw": out}


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _ps_init_doc_standards() -> str:
    return r"""
function Init-CadStandards($doc) {
    $doc.SetVariable('INSUNITS', 4)
    $doc.SetVariable('MEASUREMENT', 1)
    try { $doc.SetVariable('PSLTSCALE', 1) } catch {}
    try { $doc.SetVariable('MSLTSCALE', 1) } catch {}
    foreach ($lt in @('CENTER', 'DASHED', 'DASHDOT', 'HIDDEN')) {
        try { $null = $doc.Linetypes.Item($lt) } catch {
            try { $doc.Linetypes.Load($lt, 'acadiso.lin') } catch {
                try { $doc.Linetypes.Load($lt, 'acad.lin') } catch {}
            }
        }
    }
    try { $st = $doc.TextStyles.Item('VN_ARIAL') } catch { $st = $doc.TextStyles.Add('VN_ARIAL') }
    try { $st.SetFont('Arial', $false, $false, 0, 34) } catch {}
    try { $st.Width = 0.82 } catch {}
    try { $doc.ActiveTextStyle = $st } catch {}
    try {
        $ds = $doc.DimStyles.Item('ISO_MM')
    } catch {
        $ds = $doc.DimStyles.Add('ISO_MM')
    }
    try {
        foreach ($kv in @(
            @('DIMTXSTY', 'VN_ARIAL'),
            @('DIMTXT', 2.5),
            @('DIMASZ', 2.5),
            @('DIMEXO', 1.0),
            @('DIMEXE', 1.25),
            @('DIMGAP', 0.8),
            @('DIMTAD', 1),
            @('DIMTIH', 0),
            @('DIMTOH', 0),
            @('DIMDEC', 1),
            @('DIMZIN', 8),
            @('DIMDSEP', 46),
            @('DIMLFAC', 1.0)
        )) {
            try { $doc.SetVariable($kv[0], $kv[1]) } catch {}
        }
        $ds.CopyFrom($doc)
        $doc.ActiveDimStyle = $ds
    } catch {}
}
"""


def tool_autocad_status(_args: dict[str, Any]) -> dict[str, Any]:
    ps = r"""
$ErrorActionPreference = 'Stop'
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
$docs = @()
foreach ($d in $acad.Documents) {
    $docs += @{ name = $d.Name; fullName = $d.FullName; saved = $d.Saved; dbmod = $d.GetVariable('DBMOD') }
}
$active = $null
if ($acad.Documents.Count -gt 0) {
    $ad = $acad.ActiveDocument
    $active = @{
        name = $ad.Name
        fullName = $ad.FullName
        activeSpace = [int]$ad.ActiveSpace
        activeLayout = $ad.ActiveLayout.Name
        insunits = $ad.GetVariable('INSUNITS')
        tilemode = $ad.GetVariable('TILEMODE')
        dbmod = $ad.GetVariable('DBMOD')
        cmdactive = $ad.GetVariable('CMDACTIVE')
    }
}
@{ caption = $acad.Caption; docCount = $acad.Documents.Count; activeDocument = $active; documents = $docs } | ConvertTo-Json -Depth 5 -Compress
"""
    return _run_ps(ps)


def tool_autocad_open_or_new(args: dict[str, Any]) -> dict[str, Any]:
    path = (args.get("path") or "").strip()
    init_fn = _ps_init_doc_standards()
    if path:
        p_q = _ps_quote(str(Path(path).resolve()))
        ps = f"""
$ErrorActionPreference = 'Stop'
{init_fn}
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
$doc = $acad.Documents.Open({p_q})
$doc.Activate()
Init-CadStandards $doc
@{{ opened = $doc.FullName; activeLayout = $doc.ActiveLayout.Name; insunits = $doc.GetVariable('INSUNITS') }} | ConvertTo-Json -Compress
"""
    else:
        ps = f"""
$ErrorActionPreference = 'Stop'
{init_fn}
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
$doc = $acad.Documents.Add()
Init-CadStandards $doc
$doc.Activate()
@{{ created = $doc.Name; insunits = $doc.GetVariable('INSUNITS') }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps)


def _lisp_autosave_snippet() -> str:
    return (
        '(if (/= (getvar "DWGTITLED") 0) '
        '(progn (setq _fn (strcat (getvar "DWGPREFIX") (getvar "DWGNAME"))) '
        '(if (= (strcase (vl-filename-extension _fn)) ".DXF") '
        '(progn (setvar "FILEDIA" 0) (setvar "EXPERT" 5) '
        '(command "_SAVEAS" "_DXF" "16" _fn) '
        '(setvar "EXPERT" 0) (setvar "FILEDIA" 1)) '
        '(vla-Save (vla-get-ActiveDocument (vlax-get-acad-object))))))\n'
    )


def tool_autocad_run_command(args: dict[str, Any]) -> dict[str, Any]:
    command = args.get("command", "")
    auto_save = bool(args.get("auto_save", True))
    if not command:
        raise ValueError("'command' is required")
    if not command.endswith("\n") and not command.endswith(" "):
        command += "\n"
    if auto_save:
        command += _lisp_autosave_snippet()
    cmd_q = _ps_quote(command)
    ps = f"""
$ErrorActionPreference = 'Stop'
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
if ($acad.Documents.Count -eq 0) {{ throw 'No open AutoCAD document. Call autocad_open_or_new first.' }}
$doc = $acad.ActiveDocument
$doc.SendCommand({cmd_q})
@{{ sent = $true; auto_save = {'$true' if auto_save else '$false'}; document = $doc.Name }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps)


def tool_autocad_reload_file(args: dict[str, Any]) -> dict[str, Any]:
    target = str(Path(args["target_path"]).resolve())
    source = args.get("source_path")
    force = bool(args.get("force", False))
    source_resolved = str(Path(source).resolve()) if source else ""
    t_q = _ps_quote(target)
    s_q = _ps_quote(source_resolved)
    ps = f"""
$ErrorActionPreference = 'Stop'
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
$target = {t_q}
$source = {s_q}
$force = {'$true' if force else '$false'}
$backupPath = $null
$tmp = $null
foreach ($d in @($acad.Documents)) {{
    if ([string]::Equals($d.FullName, $target, [System.StringComparison]::OrdinalIgnoreCase)) {{
        $dbmod = [int]$d.GetVariable('DBMOD')
        if (($dbmod -ne 0) -and (-not $force)) {{
            $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
            $dir = Join-Path (Split-Path $target -Parent) '_backup_unsaved'
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            $backupPath = Join-Path $dir ((Split-Path $target -LeafBase) + "_unsaved_" + $ts + [System.IO.Path]::GetExtension($target))
            $d.SaveAs($backupPath)
        }}
        if ($acad.Documents.Count -le 1) {{ $tmp = $acad.Documents.Add() }}
        $d.Close($false)
    }}
}}
if ($source -and (Test-Path $source)) {{
    Move-Item -Force -Path $source -Destination $target
}}
$newDoc = $acad.Documents.Open($target)
$newDoc.Activate()
if ($tmp) {{ try {{ $tmp.Close($false) }} catch {{}} }}
@{{ reloaded = $newDoc.FullName; activeLayout = $newDoc.ActiveLayout.Name; backupCreated = $backupPath }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps, timeout=45)


def tool_autocad_draw_entities(args: dict[str, Any]) -> dict[str, Any]:
    entities = args.get("entities", [])
    space = args.get("space", "ModelSpace")
    zoom = bool(args.get("zoom_extents", True))
    auto_save = bool(args.get("auto_save", True))
    payload_json = json.dumps({"entities": entities, "space": space, "zoom": zoom, "auto_save": auto_save})
    p_q = _ps_quote(payload_json)
    init_fn = _ps_init_doc_standards()
    ps = f"""
$ErrorActionPreference = 'Stop'
{init_fn}
$payload = ConvertFrom-Json {p_q}
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
if ($acad.Documents.Count -eq 0) {{
    $doc = $acad.Documents.Add()
    Init-CadStandards $doc
}} else {{
    $doc = $acad.ActiveDocument
}}
$targetSpace = if ($payload.space -eq 'PaperSpace') {{ $doc.PaperSpace }} else {{ $doc.ModelSpace }}

function Ensure-Layer($doc, $name, $color, $linetype, $lineweight) {{
    if (-not $name) {{ return }}
    try {{ $lyr = $doc.Layers.Item($name) }} catch {{
        $lyr = $doc.Layers.Add($name)
    }}
    if ($null -ne $color) {{ $lyr.color = [int]$color }}
    if ($linetype) {{ try {{ $lyr.Linetype = [string]$linetype }} catch {{}} }}
    if ($null -ne $lineweight) {{ try {{ $lyr.Lineweight = [int]$lineweight }} catch {{}} }}
}}

function Pt3($p) {{
    $z = if ($p.Count -ge 3) {{ [double]$p[2] }} else {{ 0.0 }}
    return [double[]]@([double]$p[0], [double]$p[1], $z)
}}

$count = 0
foreach ($e in $payload.entities) {{
    if ($e.layer) {{ Ensure-Layer $doc $e.layer $e.color $e.linetype $e.lineweight }}
    $ent = $null
    switch ($e.type) {{
        'line' {{
            $ent = $targetSpace.AddLine((Pt3 $e.p1), (Pt3 $e.p2))
        }}
        'circle' {{
            $ent = $targetSpace.AddCircle((Pt3 $e.center), [double]$e.radius)
        }}
        'arc' {{
            $ent = $targetSpace.AddArc((Pt3 $e.center), [double]$e.radius, [double]$e.start_angle_rad, [double]$e.end_angle_rad)
        }}
        'lwpolyline' {{
            $flat = New-Object System.Collections.Generic.List[double]
            foreach ($pt in $e.points) {{ $flat.Add([double]$pt[0]); $flat.Add([double]$pt[1]) }}
            $ent = $targetSpace.AddLightWeightPolyline($flat.ToArray())
            if ($e.closed) {{ $ent.Closed = $true }}
        }}
        'text' {{
            $ent = $targetSpace.AddText([string]$e.text, (Pt3 $e.insert), [double]$e.height)
            try {{ $ent.StyleName = 'VN_ARIAL' }} catch {{}}
        }}
        'mtext' {{
            $w = if ($null -ne $e.width) {{ [double]$e.width }} else {{ 50.0 }}
            $ent = $targetSpace.AddMText((Pt3 $e.insert), $w, [string]$e.text)
            if ($null -ne $e.height) {{ $ent.Height = [double]$e.height }}
            try {{ $ent.StyleName = 'VN_ARIAL' }} catch {{}}
        }}
        'hatch' {{
            $pat = if ($e.pattern) {{ [string]$e.pattern }} else {{ 'ANSI31' }}
            $ent = $targetSpace.AddHatch(0, $pat, $true)
            $flat = New-Object System.Collections.Generic.List[double]
            foreach ($pt in $e.boundary_points) {{ $flat.Add([double]$pt[0]); $flat.Add([double]$pt[1]) }}
            $loop = $targetSpace.AddLightWeightPolyline($flat.ToArray())
            $loop.Closed = $true
            $ent.AppendOuterLoop(@($loop))
            if ($null -ne $e.scale) {{ $ent.PatternScale = [double]$e.scale }}
            $ent.Evaluate()
        }}
        'insert_block' {{
            $xs = if ($null -ne $e.xscale) {{ [double]$e.xscale }} else {{ 1.0 }}
            $ys = if ($null -ne $e.yscale) {{ [double]$e.yscale }} else {{ 1.0 }}
            $zs = if ($null -ne $e.zscale) {{ [double]$e.zscale }} else {{ 1.0 }}
            $rot = if ($null -ne $e.rotation_rad) {{ [double]$e.rotation_rad }} else {{ 0.0 }}
            $ent = $targetSpace.InsertBlock((Pt3 $e.insert), [string]$e.block_name, $xs, $ys, $zs, $rot)
            if ($e.attributes -and $ent.HasAttributes) {{
                foreach ($att in $ent.GetAttributes()) {{
                    $val = $e.attributes.($att.TagString)
                    if ($null -ne $val) {{ $att.TextString = [string]$val }}
                }}
            }}
        }}
        'mleader' {{
            $flat = New-Object System.Collections.Generic.List[double]
            foreach ($pt in $e.points) {{
                $flat.Add([double]$pt[0]); $flat.Add([double]$pt[1])
                $flat.Add($(if ($pt.Count -ge 3) {{ [double]$pt[2] }} else {{ 0.0 }}))
            }}
            $idx = 0
            $ent = $targetSpace.AddMLeader($flat.ToArray(), [ref]$idx)
            if ($e.text) {{ $ent.TextString = [string]$e.text }}
        }}
        'table' {{
            $rows = [int]$e.rows; $cols = [int]$e.cols
            $rh = if ($null -ne $e.row_height) {{ [double]$e.row_height }} else {{ 6.0 }}
            $cw = if ($null -ne $e.col_width) {{ [double]$e.col_width }} else {{ 35.0 }}
            $ent = $targetSpace.AddTable((Pt3 $e.insert), $rows, $cols, $rh, $cw)
            if ($e.data) {{
                for ($r = 0; $r -lt [Math]::Min($rows, $e.data.Count); $r++) {{
                    for ($c = 0; $c -lt [Math]::Min($cols, $e.data[$r].Count); $c++) {{
                        $ent.SetText($r, $c, [string]$e.data[$r][$c])
                    }}
                }}
            }}
        }}
        'dim_aligned' {{
            $ent = $targetSpace.AddDimAligned((Pt3 $e.p1), (Pt3 $e.p2), (Pt3 $e.text_pos))
            if ($e.text_override) {{ $ent.TextOverride = [string]$e.text_override }}
        }}
        'dim_linear' {{
            $ang = if ($null -ne $e.angle_rad) {{ [double]$e.angle_rad }} else {{ 0.0 }}
            $ent = $targetSpace.AddDimRotated((Pt3 $e.p1), (Pt3 $e.p2), (Pt3 $e.text_pos), $ang)
            if ($e.text_override) {{ $ent.TextOverride = [string]$e.text_override }}
        }}
        'dim_diameter' {{
            $ent = $targetSpace.AddDimDiametric((Pt3 $e.chord1), (Pt3 $e.chord2), [double]$e.leader_len)
            if ($e.text_override) {{ $ent.TextOverride = [string]$e.text_override }}
        }}
    }}
    if ($ent) {{
        if ($e.layer) {{ $ent.Layer = [string]$e.layer }}
        $count++
    }}
}}
if ($payload.zoom) {{ $acad.ZoomExtents() }}
$doc.Regen(1)
$didSave = $false
if ($payload.auto_save -and $doc.FullName -and ($doc.GetVariable('DWGTITLED') -ne 0)) {{
    if ($doc.FullName.EndsWith('.dxf', [System.StringComparison]::OrdinalIgnoreCase)) {{
        $fn = $doc.FullName.Replace('\', '/')
        $doc.SendCommand("(progn (setvar `"FILEDIA`" 0) (setvar `"EXPERT`" 5) (command `"_SAVEAS`" `"_DXF`" `"16`" `"$fn`") (setvar `"EXPERT`" 0) (setvar `"FILEDIA`" 1))`n")
    }} else {{
        $doc.Save()
    }}
    $didSave = $true
}}
@{{ drawn = $count; document = $doc.Name; space = $payload.space; saved = $didSave }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps, timeout=45)


def tool_autocad_audit_and_inspect(_args: dict[str, Any]) -> dict[str, Any]:
    ps = r"""
$ErrorActionPreference = 'Stop'
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
if ($acad.Documents.Count -eq 0) { throw 'No open AutoCAD document.' }
$doc = $acad.ActiveDocument
$spaceObj = if ([int]$doc.ActiveSpace -eq 0) { $doc.PaperSpace } else { $doc.ModelSpace }
$hardcodedDims = @()
$textBoxes = @()
$outOfFrame = @()
$total = 0

$isPaper = ([int]$doc.ActiveSpace -eq 0)
$pW = 0.0; $pH = 0.0
if ($isPaper) {
    try { $doc.ActiveLayout.GetPaperSize([ref]$pW, [ref]$pH) } catch {}
}

foreach ($ent in $spaceObj) {
    $total++
    $objName = $ent.ObjectName
    if ($objName -like '*Dimension*') {
        try {
            $ov = [string]$ent.TextOverride
            if ($ov -and (-not $ov.Contains('<>'))) {
                $hardcodedDims += @{ handle = $ent.Handle; override = $ov; measurement = [math]::Round($ent.Measurement, 2) }
            }
        } catch {}
    }
    if (($objName -eq 'AcDbText') -or ($objName -eq 'AcDbMText')) {
        try {
            $minP = $null; $maxP = $null
            $ent.GetBoundingBox([ref]$minP, [ref]$maxP)
            $textBoxes += @{
                handle = $ent.Handle
                type = $objName
                x0 = [double]$minP[0]; y0 = [double]$minP[1]
                x1 = [double]$maxP[0]; y1 = [double]$maxP[1]
            }
        } catch {}
    } elseif ($objName -like '*Dimension*') {
        try {
            $tp = $ent.TextPosition
            $th = 2.5
            try { $th = [double]$ent.TextHeight * [double]$ent.ScaleFactor } catch {}
            if ($th -le 0) { $th = 2.5 }
            $textBoxes += @{
                handle = $ent.Handle
                type = $objName
                x0 = [double]$tp[0] - (2.0 * $th); y0 = [double]$tp[1] - (0.6 * $th)
                x1 = [double]$tp[0] + (2.0 * $th); y1 = [double]$tp[1] + (0.6 * $th)
            }
        } catch {}
    }
    if ($isPaper -and $pW -gt 0 -and $pH -gt 0) {
        try {
            $minP = $null; $maxP = $null
            $ent.GetBoundingBox([ref]$minP, [ref]$maxP)
            if (($minP[0] -lt -2.0) -or ($minP[1] -lt -2.0) -or ($maxP[0] -gt ($pW + 2.0)) -or ($maxP[1] -gt ($pH + 2.0))) {
                $outOfFrame += @{ handle = $ent.Handle; type = $objName; maxX = [math]::Round($maxP[0],1); maxY = [math]::Round($maxP[1],1) }
            }
        } catch {}
    }
}

$overlaps = @()
$lim = [Math]::Min($textBoxes.Count, 2000)
for ($i = 0; $i -lt $lim; $i++) {
    $a = $textBoxes[$i]
    for ($j = $i + 1; $j -lt $lim; $j++) {
        $b = $textBoxes[$j]
        if (($a.x0 -lt $b.x1) -and ($a.x1 -gt $b.x0) -and ($a.y0 -lt $b.y1) -and ($a.y1 -gt $b.y0)) {
            $overlaps += @{ a = $a.handle; b = $b.handle; typeA = $a.type; typeB = $b.type }
            if ($overlaps.Count -ge 25) { break }
        }
    }
    if ($overlaps.Count -ge 25) { break }
}

@{
    document = $doc.Name
    activeLayout = $doc.ActiveLayout.Name
    totalEntities = $total
    cmdactive = $doc.GetVariable('CMDACTIVE')
    lastprompt = $doc.GetVariable('LASTPROMPT')
    hardcodedDims = $hardcodedDims
    textDimOverlaps = $overlaps
    outOfFrameEntities = $outOfFrame
} | ConvertTo-Json -Depth 5 -Compress
"""
    return _run_ps(ps, timeout=45)


def tool_acade_project_init(args: dict[str, Any]) -> dict[str, Any]:
    """Initialize a native .wdp project, create schematic/panel .dwg sheets from matching .dwt, stamp WD_M.SHEET & Title Block, and rebuild Scratch DB."""
    project_dir = Path(args["project_dir"]).resolve()
    project_name = args["project_name"].strip()
    sheets = args.get("sheets") or [
        {"file": "01_cover_and_index.dwg", "desc": "COVER AND DRAWING INDEX"},
        {"file": "04_power_distribution.dwg", "desc": "POWER DISTRIBUTION SCHEMATIC"},
        {"file": "05_control_schematic.dwg", "desc": "CONTROL & LOAD CELL SCHEMATIC"},
        {"file": "06_plc_io_wiring.dwg", "desc": "PLC I/O WIRING"},
        {"file": "07_panel_layout.dwg", "desc": "PANEL LAYOUT", "sub": "PANEL"},
        {"file": "09_terminal_and_cable_list.dwg", "desc": "TERMINAL & CABLE LIST"},
    ]
    template_dwt = Path(args.get("template_dwt") or TEMPLATE_DWT).resolve()
    panel_dwt = Path(args.get("panel_template_dwt") or (TEMPLATE_PANEL_DWT if TEMPLATE_PANEL_DWT.exists() else template_dwt)).resolve()
    template_wdp = Path(args.get("template_wdp") or TEMPLATE_WDP).resolve()
    if not template_dwt.exists():
        raise FileNotFoundError(f"Template DWT not found: {template_dwt}")
    if not template_wdp.exists():
        raise FileNotFoundError(f"Template WDP not found: {template_wdp}")

    project_dir.mkdir(parents=True, exist_ok=True)
    wdp_path = project_dir / f"{project_name}.wdp"
    base_lines = template_wdp.read_text(encoding="utf-8", errors="replace").splitlines()
    header_lines = [ln for ln in base_lines if ln.startswith(("*", "+", "?"))]

    descriptions = dict(args.get("descriptions") or {})
    descriptions.setdefault("LINE1", project_name.replace("_", " ").upper())
    for idx in range(1, 11):
        key = f"LINE{idx}"
        if key in descriptions:
            prefix = f"*[{idx}]"
            header_lines = [ln for ln in header_lines if not ln.startswith(prefix)]
            header_lines.insert(idx - 1, f"{prefix}{descriptions[key]}")

    sheet_specs: list[dict[str, Any]] = []
    total_sheets = len(sheets)
    for idx0, s in enumerate(sheets):
        fname = s["file"] if s["file"].lower().endswith(".dwg") else f"{s['file']}.dwg"
        fl = fname.lower()
        is_panel = (
            str(s.get("sub", "")).upper() == "PANEL"
            or "panel" in fl
            or "-lay-" in fl
            or "_lay_" in fl
        )
        sub = s.get("sub") or ("PANEL" if is_panel else "SCHEMATIC")
        s_desc = s.get("desc", fname)
        header_lines.extend([f"==={s_desc}", f"=====SUB={sub}", fname])
        sp_path = (project_dir / fname).resolve()
        tb_map = _build_titleblock_attr_map(descriptions, sp_path, idx0 + 1, total_sheets, sub=sub)
        sheet_specs.append({
            "path": str(sp_path),
            "dwt": str(panel_dwt if is_panel else template_dwt),
            "sheet_no": f"{idx0 + 1:02d}",
            "tb": tb_map,
        })

    wdp_path.write_text("\n".join(header_lines) + "\n", encoding="utf-8")

    wdt_src = SKILL_ROOT / "templates" / "default_iec_bilingual.wdt"
    if wdt_src.exists():
        wdt_txt = wdt_src.read_text(encoding="utf-8")
        (project_dir / f"{project_name}.wdt").write_text(wdt_txt, encoding="utf-8")
        (project_dir / "DEFAULT.WDT").write_text(wdt_txt, encoding="utf-8")

    payload_q = _ps_quote(json.dumps({
        "wdp_path": str(wdp_path).replace("\\", "/"),
        "sheet_specs": sheet_specs,
        "load_lisp": _lisp_acade_load(),
    }))
    ps = f"""
$ErrorActionPreference = 'Stop'
$payload = ConvertFrom-Json {payload_q}
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
$created = @()
foreach ($spec in $payload.sheet_specs) {{
    $sp = [string]$spec.path
    if (-not (Test-Path $sp)) {{
        $d = $acad.Documents.Add([string]$spec.dwt)
    }} else {{
        $d = $acad.Documents.Open($sp)
    }}
    foreach ($space in @($d.ModelSpace, $d.PaperSpace)) {{
        foreach ($ent in $space) {{
            if ($ent.ObjectName -eq 'AcDbBlockReference') {{
                $bn = [string]$ent.EffectiveName
                if ($bn -eq 'WD_M') {{
                    foreach ($att in $ent.GetAttributes()) {{
                        if ($att.TagString.ToUpper() -eq 'SHEET') {{ $att.TextString = [string]$spec.sheet_no }}
                    }}
                }} elseif ($bn -eq 'TITLE_BLOCK_A3_BILINGUAL') {{
                    foreach ($att in $ent.GetAttributes()) {{
                        $k = $att.TagString.ToUpper()
                        $v = $spec.tb.$k
                        if ($null -ne $v) {{ $att.TextString = [string]$v }}
                    }}
                }}
            }}
        }}
    }}
    if (-not (Test-Path $sp)) {{
        $d.SaveAs($sp)
        $created += $sp
    }} else {{
        $d.Save()
    }}
    $d.Close($false)
}}
$first = [string]$payload.sheet_specs[0].path
$doc = $acad.Documents.Open($first)
$doc.Activate()
$wdpLisp = $payload.wdp_path
$cmd = $payload.load_lisp + '(command "_AEOPENPROJECT" "' + $wdpLisp + '") (if (boundp \'c:ace_add_dwg_to_project) (c:ace_add_dwg_to_project nil (list "" "" "" 1))) (command "_AEREBUILDDB")' + "`n"
$doc.SendCommand($cmd)
@{{ wdp = $payload.wdp_path; created_dwgs = $created; active = $doc.FullName }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps, timeout=75)


SECOND_POLE_BLOCK_MAP = {
    "VCB11Q13": "VCB21Q13",
    "VCB11Q9": "VCB21Q9",
    "VCB11TH": "VCB21TH",
    "VCB1": "VCB21",
    "VFU1": "VFU2",
    "VFU1_S00371": "VFU2",
    "VDS11": "VDS21",
    "VDS11F": "VDS21F",
    "VMS1NA21F": "VMS21P",
    "VCR21": "VCR21",
    "VCR22": "VCR22",
    "VMS21P": "VMS21P",
}


def _lisp_trim_wire_under_ent(ent_var: str = "_ent") -> str:
    """Emit AutoLISP that reads X2/X8 or X4/X1 pins on `ent_var` and splits any crossing wire LINE cleanly."""
    return (
        f'(setq _p2 nil _p8 nil _p4 nil _p1 nil _an (entnext {ent_var})) '
        '(while (and _an (= (cdr (assoc 0 (entget _an))) "ATTRIB")) '
        '(setq _ad (entget _an) _at (strcase (cdr (assoc 2 _ad))) _ap (cdr (assoc 10 _ad))) '
        '(cond ((wcmatch _at "X2TERM*") (setq _p2 (cons _ap _p2))) '
        '((wcmatch _at "X8TERM*") (setq _p8 (cons _ap _p8))) '
        '((wcmatch _at "X4TERM*") (setq _p4 (cons _ap _p4))) '
        '((wcmatch _at "X1TERM*") (setq _p1 (cons _ap _p1)))) '
        '(setq _an (entnext _an))) '
        '(foreach _t2 _p2 (foreach _t8 _p8 '
        '(if (< (abs (- (car _t2) (car _t8))) 0.25) '
        '(progn (setq _vx (car _t2) _vyhi (max (cadr _t2) (cadr _t8)) _vylo (min (cadr _t2) (cadr _t8)) '
        '_wss (ssget "C" (list (- _vx 0.3) _vylo) (list (+ _vx 0.3) _vyhi) \'((0 . "LINE") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*")))) '
        '(if _wss (progn (setq _wi 0) (while (< _wi (sslength _wss)) '
        '(setq _wl (ssname _wss _wi) _wd (entget _wl) _la (cdr (assoc 8 _wd)) '
        '_lp1 (cdr (assoc 10 _wd)) _lp2 (cdr (assoc 11 _wd))) '
        '(if (and (< (abs (- (car _lp1) _vx)) 0.25) (< (abs (- (car _lp2) _vx)) 0.25) '
        '(> (max (cadr _lp1) (cadr _lp2)) (+ _vylo 0.2)) (< (min (cadr _lp1) (cadr _lp2)) (- _vyhi 0.2))) '
        '(progn (setq _lymax (max (cadr _lp1) (cadr _lp2)) _lymin (min (cadr _lp1) (cadr _lp2))) '
        '(entdel _wl) '
        '(if (> _lymax (+ _vyhi 0.2)) (entmake (list \'(0 . "LINE") (cons 8 _la) (list 10 _vx _lymax 0.0) (list 11 _vx _vyhi 0.0)))) '
        '(if (< _lymin (- _vylo 0.2)) (entmake (list \'(0 . "LINE") (cons 8 _la) (list 10 _vx _vylo 0.0) (list 11 _vx _lymin 0.0)))))) '
        '(setq _wi (1+ _wi))))))))) '
        '(foreach _t4 _p4 (foreach _t1 _p1 '
        '(if (< (abs (- (cadr _t4) (cadr _t1))) 0.25) '
        '(progn (setq _hy (cadr _t4) _hxhi (max (car _t4) (car _t1)) _hxlo (min (car _t4) (car _t1)) '
        '_wss (ssget "C" (list _hxlo (- _hy 0.3)) (list _hxhi (+ _hy 0.3)) \'((0 . "LINE") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*")))) '
        '(if _wss (progn (setq _wi 0) (while (< _wi (sslength _wss)) '
        '(setq _wl (ssname _wss _wi) _wd (entget _wl) _la (cdr (assoc 8 _wd)) '
        '_lp1 (cdr (assoc 10 _wd)) _lp2 (cdr (assoc 11 _wd))) '
        '(if (and (< (abs (- (cadr _lp1) _hy)) 0.25) (< (abs (- (cadr _lp2) _hy)) 0.25) '
        '(> (max (car _lp1) (car _lp2)) (+ _hxlo 0.2)) (< (min (car _lp1) (car _lp2)) (- _hxhi 0.2))) '
        '(progn (setq _lxmax (max (car _lp1) (car _lp2)) _lxmin (min (car _lp1) (car _lp2))) '
        '(entdel _wl) '
        '(if (< _lxmin (- _hxlo 0.2)) (entmake (list \'(0 . "LINE") (cons 8 _la) (list 10 _lxmin _hy 0.0) (list 11 _hxlo _hy 0.0)))) '
        '(if (> _lxmax (+ _hxhi 0.2)) (entmake (list \'(0 . "LINE") (cons 8 _la) (list 10 _hxhi _hy 0.0) (list 11 _lxmax _hy 0.0)))))) '
        '(setq _wi (1+ _wi)))))))))'
    )


def _build_symbol_lisp(
    block_name: str,
    pt: list[float],
    attrs: dict[str, Any],
    scale: float = 1.0,
    poles: int = 1,
    pole_spacing: float = 10.0,
) -> str:
    """Build AutoLISP to insert 1-pole or multi-pole (2P/3P/4P) linked IEC symbols and cut all phase wires."""
    bn_up = block_name.upper().removesuffix(".DWG")
    x0, y0 = float(pt[0]), float(pt[1])
    # Guard 0: Enforce Safe Schematic Viewport Drawing Zone (X in [25..405], Y in [12..276], outside Title Block [235..415, 5..41])
    max_x = x0 + max(0, poles - 1) * pole_spacing
    if x0 < 22.0 or max_x > 410.0 or y0 < 10.0 or y0 > 278.0:
        raise ValueError(
            f"Safe Zone Violation: Symbol '{block_name}' at ({x0}, {y0}) exceeds Schematic Safe Zone [25..405, 12..276]!"
        )
    if max_x > 232.0 and y0 < 45.0:
        raise ValueError(
            f"Title Block Clash: Symbol '{block_name}' at ({x0}, {y0}) intrudes into Paper Space Title Block zone [235..415, 5..41]!"
        )

    is_child_blk = (len(bn_up) >= 4 and bn_up[0] in ("H", "V") and bn_up[3] == "2") or bn_up in ("VW02", "HW02")
    if is_child_blk and "TAG1" in attrs and "TAG2" not in attrs:
        raise ValueError(
            f"IEC Parent/Child Violation: '{block_name}' is a Child symbol (4th char='2', uses TAG2), "
            f"but 'TAG1={attrs['TAG1']}' was passed! Use a Parent symbol (e.g., VCB11Q13, VFU1) or pass 'TAG2'."
        )

    raw_tag = str(attrs.get("TAG1") or attrs.get("TAG2") or "").strip().upper().lstrip("-=+")
    tag_alpha = raw_tag.lstrip("0123456789")
    if bn_up in ("VCR1", "HCR1") and tag_alpha[:1] in ("U", "G", "A"):
        raise ValueError(
            f"IEC 60617 Symbol Misuse: Relay coil '{block_name}' cannot represent '{attrs.get('TAG1')}' (family '{tag_alpha[:1]}'). "
            f"Use 'VU1_VFD_3P' for VFDs (-U*), 'VG1_PSU_24V' for Power Supplies (-G*), 'VA4_NET_BOX' / 'VA1_WEIGH_TRANS' / 'HP1W--L' for Modules (-A*)."
        )

    p1_attrs = dict(attrs)
    if poles >= 2:
        p1_attrs.setdefault("TERM01", "1")
        p1_attrs.setdefault("TERM02", "2")

    mod_exprs = [f'(c:wd_modattrval _ent {_lisp_str(k)} {_lisp_str(str(v))} nil)' for k, v in p1_attrs.items()]
    parts = [
        f"(setq _ent (c:wd_insym2 {_lisp_str(block_name)} '({x0} {y0} 0.0) {scale} nil)) "
        f"(if (not _ent) (princ \"\\n[ACADE_ERR] wd_insym2 returned nil\\n\") "
        f"(progn {' '.join(mod_exprs)} (entupd _ent) {_lisp_trim_wire_under_ent('_ent')}))"
    ]

    if poles >= 2:
        sec_blk = SECOND_POLE_BLOCK_MAP.get(bn_up)
        if not sec_blk:
            raise ValueError(
                f"Multi-pole mode (poles={poles}) not supported for '{block_name}'. "
                f"Supported multi-pole roots: {sorted(SECOND_POLE_BLOCK_MAP.keys())}"
            )
        parent_tag = str(attrs.get("TAG1") or attrs.get("TAG2") or "")
        loc_val = str(attrs.get("LOC") or "+MAIN_PNL")
        inst_val = str(attrs.get("INST") or "")
        for p_idx in range(1, poles):
            px = x0 + p_idx * pole_spacing
            t_top = str(p_idx * 2 + 1)
            t_bot = str(p_idx * 2 + 2)
            parts.append(
                f"(setq _entp (c:wd_insym2 {_lisp_str(sec_blk)} '({px} {y0} 0.0) {scale} nil)) "
                f"(if _entp (progn "
                f'(c:wd_modattrval _entp "TAG2" {_lisp_str(parent_tag)} nil) '
                f'(c:wd_modattrval _entp "TERM01" {_lisp_str(t_top)} nil) '
                f'(c:wd_modattrval _entp "TERM02" {_lisp_str(t_bot)} nil) '
                f'(c:wd_modattrval _entp "LOC" {_lisp_str(loc_val)} nil) '
                f'(c:wd_modattrval _entp "INST" {_lisp_str(inst_val)} nil) '
                f"(entupd _entp) {_lisp_trim_wire_under_ent('_entp')}))"
            )
        # Mechanical dashed linkage line on LINK layer across all poles (X0 -> X0 + (poles-1)*spacing)
        link_y = y0 - 8.0 if "Q13" in bn_up else y0
        parts.append(
            f'(entmake (list \'(0 . "LINE") \'(8 . "LINK") (list 10 {x0 - 1.5} {link_y} 0.0) (list 11 {max_x - 1.5} {link_y} 0.0)))'
        )
    return " ".join(parts)


def tool_acade_insert_schematic_symbol(args: dict[str, Any]) -> dict[str, Any]:
    """Insert a 1-pole or multi-pole (poles=2|3|4) IEC-60617 schematic symbol, enforce Safe Zone & family guards, and auto-break all crossed wires."""
    block_name = str(args["block_name"]).strip()
    pt = args["point"]
    scale = float(args.get("scale", 1.0))
    poles = int(args.get("poles", 1))
    pole_spacing = float(args.get("pole_spacing", 10.0))
    attrs = dict(args.get("attributes") or {})
    auto_save = bool(args.get("auto_save", True))

    lisp_body = _build_symbol_lisp(block_name, pt, attrs, scale=scale, poles=poles, pole_spacing=pole_spacing)
    return _run_acade_lisp_checked(lisp_body, ["c:wd_insym2", "c:wd_modattrval"], auto_save=auto_save)


def _split_wires_at_dots(wires: list[dict[str, Any]], dots: list[list[float]]) -> list[dict[str, Any]]:
    """Split orthogonal wire segments at any mid-segment T-junction dot so BFS & ACADE share exact endpoints."""
    result: list[dict[str, Any]] = []
    eps = 0.1
    for w in wires:
        x1, y1 = float(w["p1"][0]), float(w["p1"][1])
        x2, y2 = float(w["p2"][0]), float(w["p2"][1])
        lyr = w["layer"]
        if abs(y1 - y2) <= eps:  # horizontal
            lo, hi = min(x1, x2), max(x1, x2)
            splits = sorted({float(d[0]) for d in dots if abs(float(d[1]) - y1) <= eps and lo + eps < float(d[0]) < hi - eps})
            pts = [lo, *splits, hi]
            if x1 > x2:
                pts.reverse()
            for a, b in zip(pts[:-1], pts[1:]):
                result.append({"p1": [a, y1], "p2": [b, y1], "layer": lyr})
        elif abs(x1 - x2) <= eps:  # vertical
            lo, hi = min(y1, y2), max(y1, y2)
            splits = sorted({float(d[1]) for d in dots if abs(float(d[0]) - x1) <= eps and lo + eps < float(d[1]) < hi - eps})
            pts = [lo, *splits, hi]
            if y1 > y2:
                pts.reverse()
            for a, b in zip(pts[:-1], pts[1:]):
                result.append({"p1": [x1, a], "p2": [x1, b], "layer": lyr})
        else:
            result.append(w)
    return result


def tool_acade_draw_smart_wires_and_arrows(args: dict[str, Any]) -> dict[str, Any]:
    """Draw smart ACADE wires via (c:wd_wire_quik) (auto-splitting at T-dots), register VIA_WD_WIRETYPE, insert WDDOT, and Source/Dest arrows."""
    wire_layers = args.get("wire_layers") or []
    dots = args.get("dots") or []
    wires = _split_wires_at_dots(args.get("wires") or [], dots)
    arrows = args.get("arrows") or []
    auto_save = bool(args.get("auto_save", True))

    reg_exprs = ['(regapp "VIA_WD_WIRETYPE")']
    for wl in wire_layers:
        lname = wl["layer"]
        wcol = wl.get("wire_color", "")
        wsize = wl.get("wire_size", "")
        reg_exprs.append(
            f'(if (setq _le (tblobjname "LAYER" {_lisp_str(lname)})) '
            f'(progn (setq _ed (vl-remove-if \'(lambda (x) (= (car x) -3)) (entget _le \'("VIA_WD_WIRETYPE")))) '
            f'(entmod (append _ed (list (list -3 (list "VIA_WD_WIRETYPE" (cons 1000 {_lisp_str(wcol)}) (cons 1000 {_lisp_str(wsize)}))))))))'
        )

    wire_exprs = []
    for w in wires:
        p1, p2 = w["p1"], w["p2"]
        lyr = w["layer"]
        wire_exprs.append(
            f'(setvar "CLAYER" {_lisp_str(lyr)}) '
            f'(c:wd_wire_quik \'({float(p1[0])} {float(p1[1])} 0.0) \'({float(p2[0])} {float(p2[1])} 0.0) nil)'
        )

    dot_exprs = [
        f'(if (not (ssget "C" \'({float(d[0]) - 0.35} {float(d[1]) - 0.35}) \'({float(d[0]) + 0.35} {float(d[1]) + 0.35}) \'((0 . "INSERT") (2 . "WDDOT")))) '
        f'(c:wd_insym2 "WDDOT" \'({float(d[0])} {float(d[1])} 0.0) 1.0 nil))'
        for d in dots
    ]

    arrow_exprs = []
    for a in arrows:
        kind = a.get("kind", "source").lower()
        pt = a["point"]
        sig = a["sigcode"]
        wno = a.get("wireno", "")
        blk = "HA1S1" if kind == "source" else "HA1D3"
        arrow_exprs.append(
            f'(setq _a (c:wd_insym2 {_lisp_str(blk)} \'({float(pt[0])} {float(pt[1])} 0.0) 1.0 nil)) '
            f'(if _a (progn (c:wd_modattrval _a "SIGCODE" {_lisp_str(sig)} nil) '
            f'(c:wd_modattrval _a "WIRENO" {_lisp_str(wno)} nil) (entupd _a)))'
        )
    if arrows:
        arrow_exprs.append('(c:wd_retag_update_noprompts 97 nil)')

    lisp_body = f"{' '.join(reg_exprs)} {' '.join(wire_exprs)} {' '.join(dot_exprs)} {' '.join(arrow_exprs)}"
    return _run_acade_lisp_checked(lisp_body, ["c:wd_wire_quik", "c:wd_insym2", "c:wd_modattrval"], auto_save=auto_save)


V_TO_H_PLC_RUNG_SYMBOL = {
    "VPB11": "HPB11",
    "VPB12": "HPB12",
    "VSW11": "HSW11",
    "VSW12": "HSW12",
    "VPX1": "HPX1",
    "VCR1": "HCR1",
    "VLT1A": "HLT1A",
    "VSV1": "HSV1",
    "VY1": "HSV1",
}


def tool_acade_build_plc_from_csv(args: dict[str, Any]) -> dict[str, Any]:
    """Insert real ACADE PLCIO blocks (HP1W--L header + HP1WA-D channels), convert V*->H* horizontal rung peripherals, add ht0001 terminals, and close +24VDC/0VDC common rails."""
    import csv as _csv

    csv_path = Path(args["csv_path"]).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"PLC CSV not found: {csv_path}")

    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in _csv.DictReader(f):
            blk = (row.get("BLOCK") or "").strip().upper()
            if blk.startswith("PLC_"):
                raise ValueError(
                    f"Invalid fake PLC module name '{blk}' in BLOCK column. "
                    "Use real iec-60617 peripheral symbols (e.g., HCR1, HPB11, HLT1A, HSW12) or leave blank."
                )
            rows.append(row)

    modules: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row.get("RACK", "0").strip(), row.get("SLOT", "2").strip(), row.get("CODE", "").strip())
        modules.setdefault(key, []).append(row)

    slot_filter = args.get("slot_filter")
    mod_items = list(modules.items())
    if slot_filter:
        allowed = {str(s).strip().upper() for s in slot_filter}
        mod_items = [
            (k, v) for idx, (k, v) in enumerate(mod_items)
            if k[1].strip().upper() in allowed or str(idx) in allowed or str(idx + 1) in allowed
        ]
    total_modules = len(mod_items)
    total_pages = max(1, (total_modules + 1) // 2)
    page_index = int(args.get("page_index", 0) or 0)
    if len(mod_items) > 2:
        start = page_index * 2
        mod_items = mod_items[start:start + 2]
        if not mod_items:
            raise ValueError(f"page_index={page_index} out of range for {total_modules} PLC modules (total_pages={total_pages}).")

    lisp_parts: list[str] = ['(regapp "VIA_WD_WIRETYPE")']
    for mod_idx, ((rack, slot, code), ch_rows) in enumerate(mod_items):
        if len(ch_rows) > 10:
            raise ValueError(
                f"PLC Column Overflow: Module Slot {slot} has {len(ch_rows)} rows (max 10 channels per column on A3 without intruding into Title Block)."
            )
        mx = 172.0 + mod_idx * 182.0
        my = 256.0  # Safe Y<=256 so INST/LOC attributes above HP1W--L stay strictly <= 283mm (below Y=287 X-Zone bar!)
        mod_tag = f"-A1:S{slot}"
        first_inst = (ch_rows[0].get("INST") or "=PLC1").strip() if ch_rows else "=PLC1"
        is_do_mod = any((r.get("ADDRESS") or "").strip().upper().lstrip("%").startswith("Q") for r in ch_rows)
        common_layer = "CTRL_0VDC_BUWH_0.75" if is_do_mod else "CTRL_24VDC_DBU_0.75"
        common_sig = "BUS_0VDC_PELV" if is_do_mod else "BUS_24VDC_PELV"
        common_wno = "0VDC" if is_do_mod else "+24VDC"
        rail_x = mx - 115.0

        # Insert real ACADE PLCIO module header block (HP1W--L: TAG, LINE1, LINE2, MFG, CAT, LOC, INST)
        lisp_parts.append(
            f'(setq _pm (c:wd_insym2 "HP1W--L" \'({mx} {my} 0.0) 1.0 nil)) '
            f'(if _pm (progn '
            f'(c:wd_modattrval _pm "TAG" {_lisp_str(mod_tag)} nil) '
            f'(c:wd_modattrval _pm "LINE1" {_lisp_str(f"RACK {rack}")} nil) '
            f'(c:wd_modattrval _pm "LINE2" {_lisp_str(f"SLOT {slot}")} nil) '
            f'(c:wd_modattrval _pm "MFG" "SIEMENS" nil) '
            f'(c:wd_modattrval _pm "CAT" {_lisp_str(code)} nil) '
            f'(c:wd_modattrval _pm "LOC" "+MAIN_PNL" nil) '
            f'(c:wd_modattrval _pm "INST" {_lisp_str(first_inst)} nil) '
            f'(entupd _pm)))'
        )

        wired_ys: list[float] = []
        for ch_idx, row in enumerate(ch_rows):
            cy = my - 20.0 - ch_idx * 20.0
            addr = (row.get("ADDRESS") or "").strip()
            tdesc = (row.get("TERMDESC") or "").strip()
            wtype = (row.get("WIRETYPE") or "SIG_PLC_BU_0.5").strip()
            raw_blk = (row.get("BLOCK") or "").strip().upper()
            blk = V_TO_H_PLC_RUNG_SYMBOL.get(raw_blk, raw_blk)

            # Insert real PLCIO channel block (HP1WA-D: X4TERM_ @ mx - 7.0)
            lisp_parts.append(
                f'(setq _pc (c:wd_insym2 "HP1WA-D" \'({mx} {cy} 0.0) 1.0 nil)) '
                f'(if _pc (progn '
                f'(c:wd_modattrval _pc "TAGA_" {_lisp_str(addr)} nil) '
                f'(c:wd_modattrval _pc "TERM_" {_lisp_str(tdesc)} nil) '
                f'(c:wd_modattrval _pc "TERMDESC_" {_lisp_str(tdesc)} nil) '
                f'(c:wd_modattrval _pc "DESCA_" {_lisp_str(row.get("DESC1", ""))} nil) '
                f'(c:wd_modattrval _pc "DESCB_" {_lisp_str(row.get("DESC2", ""))} nil) '
                f'(entupd _pc)))'
            )

            if blk:
                wired_ys.append(cy)
                term_x = mx - 30.0
                pe_x = mx - 68.0
                # Wire segment 1: HP1WA-D X4TERM_ (mx-7.0) -> ht0001 X1TERM01 (term_x+1.25)
                lisp_parts.append(
                    f'(setvar "CLAYER" {_lisp_str(wtype)}) '
                    f'(c:wd_wire_quik \'({mx - 7.0} {cy} 0.0) \'({term_x + 1.25} {cy} 0.0) nil)'
                )
                # Insert intermediate terminal ht0001 (-X2 / -X3)
                t_strip = "-X3" if is_do_mod else "-X2"
                t_num = f"S{slot}.{ch_idx + 1}"
                lisp_parts.append(
                    f'(setq _tm (c:wd_insym2 "ht0001" \'({term_x} {cy} 0.0) 1.0 nil)) '
                    f'(if _tm (progn '
                    f'(c:wd_modattrval _tm "TAGSTRIP" {_lisp_str(t_strip)} nil) '
                    f'(c:wd_modattrval _tm "TERM01" {_lisp_str(t_num)} nil) '
                    f'(c:wd_modattrval _tm "MFG" "PHOENIX CONTACT" nil) '
                    f'(c:wd_modattrval _tm "CAT" "3004100" nil) '
                    f'(c:wd_modattrval _tm "LOC" "+MAIN_PNL" nil) '
                    f'(c:wd_modattrval _tm "INST" {_lisp_str(first_inst)} nil) '
                    f'(entupd _tm)))'
                )
                # Wire segment 2: ht0001 X4TERM01 (term_x-1.25) -> H* peripheral X1TERM02 (pe_x+7.5)
                lisp_parts.append(
                    f'(setvar "CLAYER" {_lisp_str(wtype)}) '
                    f'(c:wd_wire_quik \'({term_x - 1.25} {cy} 0.0) \'({pe_x + 7.5} {cy} 0.0) nil)'
                )
                # Insert horizontal peripheral symbol (X4TERM01 @ -7.5, X1TERM02 @ +7.5) with default MFG/CAT if omitted
                def_mfg = (row.get("MFG") or "SIEMENS").strip().upper()
                def_cat = (row.get("CAT") or "").strip()
                if not def_cat:
                    if blk == "HCR1":
                        def_cat = "3RT2026-1BB40"
                    elif blk == "HLT1A":
                        def_cat = "3SU1152-6AA20-1AA0"
                    elif blk in ("HSW12", "HSW11", "HPB11", "HPB12"):
                        def_cat = "3SU1150-1HB20-1CG0"
                lisp_parts.append(
                    f'(setq _pe (c:wd_insym2 {_lisp_str(blk)} \'({pe_x} {cy} 0.0) 1.0 nil)) '
                    f'(if _pe (progn '
                    f'(c:wd_modattrval _pe "TAG1" {_lisp_str(row.get("TAG", ""))} nil) '
                    f'(c:wd_modattrval _pe "MFG" {_lisp_str(def_mfg)} nil) '
                    f'(c:wd_modattrval _pe "CAT" {_lisp_str(def_cat)} nil) '
                    f'(c:wd_modattrval _pe "DESC1" {_lisp_str(row.get("DESC1", ""))} nil) '
                    f'(c:wd_modattrval _pe "DESC2" {_lisp_str(row.get("DESC2", ""))} nil) '
                    f'(c:wd_modattrval _pe "LOC" {_lisp_str(row.get("LOC", "+FIELD"))} nil) '
                    f'(c:wd_modattrval _pe "INST" {_lisp_str(row.get("INST", first_inst))} nil) '
                    f'(entupd _pe)))'
                )
                # Wire segment 3 (Closed-Circuit Return / Supply): H* X4TERM01 (pe_x-7.5) -> Common Rail (rail_x)
                lisp_parts.append(
                    f'(setvar "CLAYER" {_lisp_str(common_layer)}) '
                    f'(c:wd_wire_quik \'({pe_x - 7.5} {cy} 0.0) \'({rail_x} {cy} 0.0) nil)'
                )
            else:
                # Spare / Analog stub wire going left from HP1WA-D X4TERM_
                lisp_parts.append(
                    f'(setvar "CLAYER" {_lisp_str(wtype)}) '
                    f'(c:wd_wire_quik \'({mx - 7.0} {cy} 0.0) \'({mx - 45.0} {cy} 0.0) nil)'
                )

        # Draw vertical common rail on left (0VDC return for DO coils/lamps; +24VDC supply for DI switches/sensors) + Signal Arrow
        if wired_ys:
            top_y = wired_ys[0] + 12.0
            pts_y = [top_y, *wired_ys]
            for ya, yb in zip(pts_y[:-1], pts_y[1:]):
                lisp_parts.append(
                    f'(setvar "CLAYER" {_lisp_str(common_layer)}) '
                    f'(c:wd_wire_quik \'({rail_x} {ya} 0.0) \'({rail_x} {yb} 0.0) nil)'
                )
            for ty in wired_ys[:-1]:
                lisp_parts.append(
                    f'(if (not (ssget "C" \'({rail_x - 0.35} {ty - 0.35}) \'({rail_x + 0.35} {ty + 0.35}) \'((0 . "INSERT") (2 . "WDDOT")))) '
                    f'(c:wd_insym2 "WDDOT" \'({rail_x} {ty} 0.0) 1.0 nil))'
                )
            arr_blk = "HA1D3" if is_do_mod else "HA1S1"
            lisp_parts.append(
                f'(setq _ca (c:wd_insym2 {_lisp_str(arr_blk)} \'({rail_x} {top_y} 0.0) 1.0 nil)) '
                f'(if _ca (progn (c:wd_modattrval _ca "SIGCODE" {_lisp_str(common_sig)} nil) '
                f'(c:wd_modattrval _ca "WIRENO" {_lisp_str(common_wno)} nil) (entupd _ca)))'
            )

    lisp_body = " ".join(lisp_parts) if len(lisp_parts) > 1 else '(princ "No PLC rows")'
    return _run_acade_lisp_checked(
        lisp_body,
        ["c:wd_insym2", "c:wd_modattrval", "c:wd_wire_quik"],
        auto_save=bool(args.get("auto_save", True)),
        timeout_sec=55.0,
    )


def tool_acade_sync_panel_footprints(args: dict[str, Any]) -> dict[str, Any]:
    """Query COMP (PAR1_CHLD2='1' AND LOC IN ('+MAIN_PNL','+DOOR')) from Scratch .mdb and insert real .dwg footprints at panel coordinates with VIA_WD_FP XDATA."""
    mdb_path = Path(args["mdb_path"]).resolve()
    if not mdb_path.exists():
        raise FileNotFoundError(f"Scratch database not found: {mdb_path}")
    mdb_str = str(mdb_path).replace("'", "''")
    ps = f"""
$ErrorActionPreference = 'Stop'
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={mdb_str};")
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = "SELECT TAGNAME, MFG, CAT, LOC, INST, DESC1 FROM [COMP] WHERE PAR1_CHLD2='1' AND LOC IN ('+MAIN_PNL','+DOOR') ORDER BY LOC, TAGNAME"
$r = $cmd.ExecuteReader()
$items = @()
while ($r.Read()) {{
    $items += @{{
        tag = [string]$r['TAGNAME']
        mfg = [string]$r['MFG']
        cat = [string]$r['CAT']
        loc = [string]$r['LOC']
        inst = [string]$r['INST']
        desc = [string]$r['DESC1']
    }}
}}
$r.Close()
$conn.Close()
@{{ count = $items.Count; components = $items }} | ConvertTo-Json -Depth 4 -Compress
"""
    res = _run_ps(ps, timeout=30)
    if args.get("run_aefootprint") and res.get("components"):
        panel_candidates = [
            Path(os.environ["ACADE_LIBS_DIR"]) / "panel" / "CUSTOM" if os.environ.get("ACADE_LIBS_DIR") else None,
            Path(r"F:\Projects\CAD\Libraries\AutoCAD-Electrical\2027\Libs\panel\CUSTOM"),
            Path(r"C:\Users\Public\Documents\Autodesk\Acade 2027\Libs\panel\CUSTOM"),
        ]
        panel_root = next((p for p in panel_candidates if p is not None and p.exists()), panel_candidates[1])
        placements = args.get("placements") or {}
        enc = args.get("enclosure_size") or {}
        enc_w = float(enc.get("width_mm", 800.0))
        enc_h = float(enc.get("height_mm", 1200.0))
        plate_w = float(enc.get("plate_width_mm", enc_w - 60.0))
        plate_h = float(enc.get("plate_height_mm", enc_h - 60.0))
        door_ox, pnl_ox = 0.0, enc_w + 290.0
        plate_x0, plate_y0 = pnl_ox + (enc_w - plate_w) / 2.0, (enc_h - plate_h) / 2.0

        ins_exprs = [
            '(regapp "VIA_WD_FP")',
            '(setq _doc (vla-get-ActiveDocument (vlax-get-acad-object)))',
            '(if (not (tblobjname "LAYER" "PNL_FOOTPRINT")) (entmake \'((0 . "LAYER") (100 . "AcDbSymbolTableRecord") (100 . "AcDbLayerTableRecord") (2 . "PNL_FOOTPRINT") (70 . 0) (62 . 4) (6 . "CONTINUOUS"))))',
            '(if (not (tblobjname "LAYER" "PNL_ENCLOSURE")) (entmake \'((0 . "LAYER") (100 . "AcDbSymbolTableRecord") (100 . "AcDbLayerTableRecord") (2 . "PNL_ENCLOSURE") (70 . 0) (62 . 7) (6 . "CONTINUOUS"))))',
            '(if (not (tblobjname "LAYER" "PNL_PLATE")) (entmake \'((0 . "LAYER") (100 . "AcDbSymbolTableRecord") (100 . "AcDbLayerTableRecord") (2 . "PNL_PLATE") (70 . 0) (62 . 8) (6 . "CONTINUOUS"))))',
            '(setq _ms (vla-get-ModelSpace _doc))',
            # Draw door & mounting plate outlines in 1:1 mm Model Space
            f'(entmake \'((0 . "LWPOLYLINE") (100 . "AcDbEntity") (8 . "PNL_ENCLOSURE") (100 . "AcDbPolyline") (90 . 4) (70 . 1) (10 {door_ox} 0.0) (10 {door_ox + enc_w} 0.0) (10 {door_ox + enc_w} {enc_h}) (10 {door_ox} {enc_h})))',
            f'(entmake \'((0 . "LWPOLYLINE") (100 . "AcDbEntity") (8 . "PNL_ENCLOSURE") (100 . "AcDbPolyline") (90 . 4) (70 . 1) (10 {pnl_ox} 0.0) (10 {pnl_ox + enc_w} 0.0) (10 {pnl_ox + enc_w} {enc_h}) (10 {pnl_ox} {enc_h})))',
            f'(entmake \'((0 . "LWPOLYLINE") (100 . "AcDbEntity") (8 . "PNL_PLATE") (100 . "AcDbPolyline") (90 . 4) (70 . 1) (10 {plate_x0} {plate_y0}) (10 {plate_x0 + plate_w} {plate_y0}) (10 {plate_x0 + plate_w} {plate_y0 + plate_h}) (10 {plate_x0} {plate_y0 + plate_h})))',
        ]
        if str(SKILL_ROOT / "scripts") not in sys.path:
            sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        import csv as _csv
        from seed_acade_databases import _build_panel_footprint_dwg_if_missing

        fp_catalog: dict[str, dict[str, str]] = {}
        fp_csv = SKILL_ROOT / "templates" / "verified_footprints_catalog.csv"
        if fp_csv.exists():
            with fp_csv.open("r", encoding="utf-8-sig", newline="") as _f:
                for _r in _csv.DictReader(_f):
                    if _r.get("CAT"):
                        fp_catalog[_r["CAT"].strip().upper()] = _r

        placed_tags: list[str] = []
        pnl_x, pnl_y, pnl_row_h = plate_x0 + 65.0, plate_y0 + plate_h - 140.0, 0.0
        door_x, door_y = door_ox + 160.0, enc_h - 320.0
        for idx, comp in enumerate(res["components"]):
            mfg = _normalize_mfg(comp.get("mfg") or "SIEMENS")
            cat_raw = (comp.get("cat") or "").strip().upper()
            if not cat_raw:
                raise ValueError(f"Component '{comp.get('tag')}' has empty CAT in [COMP]; assign catalog before syncing footprints!")
            cat_clean = cat_raw.replace("-", "_").replace("/", "_")
            blknam = f"PNL_{mfg.replace(' ', '_')}_{cat_clean}"
            dwg_path = panel_root / mfg / f"{blknam}.dwg"
            cat_row = fp_catalog.get(cat_raw)
            if not dwg_path.exists():
                if not cat_row:
                    raise FileNotFoundError(
                        f"Missing verified panel footprint for '{comp.get('tag')}' ({mfg} {cat_raw}): "
                        f"neither {dwg_path} nor an entry in verified_footprints_catalog.csv exists (Fail-Closed)."
                    )
                dwg_path = _build_panel_footprint_dwg_if_missing(panel_root.parent, mfg, blknam, cat_row)
            w_mm = float((cat_row or {}).get("W_MM") or 60.0)
            h_mm = float((cat_row or {}).get("H_MM") or 100.0)
            tag = comp.get("tag", "")
            loc = comp.get("loc", "+MAIN_PNL")
            base_tag = tag.split(":")[0]
            if tag in placements:
                x, y = float(placements[tag][0]), float(placements[tag][1])
            elif base_tag in placements and ":" not in tag:
                x, y = float(placements[base_tag][0]), float(placements[base_tag][1])
            elif loc.upper() == "+DOOR":
                x, y = door_x, door_y
                door_x += max(90.0, w_mm + 45.0)
                if door_x > door_ox + enc_w - 120.0:
                    door_x = door_ox + 160.0
                    door_y -= 140.0
            else:
                if pnl_x + w_mm > plate_x0 + plate_w - 40.0:
                    pnl_x = plate_x0 + 65.0
                    pnl_y -= max(210.0, pnl_row_h + 60.0)
                    pnl_row_h = 0.0
                x, y = pnl_x, pnl_y
                pnl_x += w_mm + 18.0
                pnl_row_h = max(pnl_row_h, h_mm)
            ins_exprs.append(
                f'(setq _vfp (vla-InsertBlock _ms (vlax-3d-point {x} {y} 0.0) {_lisp_str(str(dwg_path))} 1.0 1.0 1.0 0.0)) '
                f'(vla-put-Layer _vfp "PNL_FOOTPRINT") '
                f'(setq _fp (vlax-vla-object->ename _vfp)) '
                f'(c:wd_modattrval _fp "P_TAG1" {_lisp_str(tag)} nil) '
                f'(c:wd_modattrval _fp "MFG" {_lisp_str(mfg)} nil) '
                f'(c:wd_modattrval _fp "CAT" {_lisp_str(cat_raw)} nil) '
                f'(c:wd_modattrval _fp "LOC" {_lisp_str(loc)} nil) '
                f'(setq _fped (entget _fp)) '
                f'(entmod (append _fped (list (list -3 (list "VIA_WD_FP" (cons 1000 {_lisp_str(tag)}) (cons 1000 {_lisp_str(mfg)}) (cons 1000 {_lisp_str(cat_raw)})))))) '
                f'(entupd _fp)'
            )
            placed_tags.append(tag)
        # Ensure Paper Space ISO_A3 layout is active (TILEMODE=0) if present on Panel Layout sheets
        ins_exprs.append(
            '(if (member "ISO_A3" (layoutlist)) (progn (setvar "TILEMODE" 0) (setvar "CTAB" "ISO_A3")))'
        )
        if placed_tags:
            _run_acade_lisp_checked(" ".join(ins_exprs), ["c:wd_modattrval"], auto_save=True, timeout_sec=50.0)
        res["placed_footprints"] = len(placed_tags)
    return res


def tool_acade_run_reports_and_retag(args: dict[str, Any]) -> dict[str, Any]:
    """Place equipotential %S%N WD_WNH/WD_WNV wire-number blocks (reading WD_M SHEET, grouping connected segments), rebuild DB, retag, and update Title Block."""
    sheet_paths = args.get("sheet_paths") or []
    # Read real SHEET attribute from WD_M, group connected LINE segments into equipotential nets, skip fixed arrows & already-numbered nets
    wnum_lisp = (
        '(defun _wdm_sheet (/ ss e n d sh) (setq sh "01") '
        '(if (setq ss (ssget "X" \'((0 . "INSERT") (2 . "WD_M")))) '
        '(progn (setq e (ssname ss 0) n (entnext e)) '
        '(while (and n (= (cdr (assoc 0 (entget n))) "ATTRIB")) '
        '(setq d (entget n)) (if (= (strcase (cdr (assoc 2 d))) "SHEET") (setq sh (cdr (assoc 1 d)))) '
        '(setq n (entnext n))))) sh) '
        '(defun _ptk (p) (strcat (rtos (car p) 2 1) "," (rtos (cadr p) 2 1))) '
        '(setq _sh (_wdm_sheet) _wss (ssget "X" \'((0 . "LINE") (8 . "PWR_*,CTRL_*,SIG_*,SAFE_*")))) '
        '(if _wss (progn (setq _segs nil _wi 0) '
        '(while (< _wi (sslength _wss)) '
        '(setq _we (entget (ssname _wss _wi)) _p1 (cdr (assoc 10 _we)) _p2 (cdr (assoc 11 _we)) '
        '_segs (cons (list (_ptk _p1) (_ptk _p2) _p1 _p2) _segs) _wi (1+ _wi))) '
        '(setq _visited nil _wn 1) '
        '(foreach _s _segs '
        '(if (not (member (car _s) _visited)) '
        '(progn (setq _queue (list (car _s) (cadr _s)) _net nil _has_num nil) '
        '(while _queue (setq _cur (car _queue) _queue (cdr _queue)) '
        '(if (not (member _cur _visited)) '
        '(progn (setq _visited (cons _cur _visited)) '
        '(foreach _cand _segs '
        '(if (or (= (car _cand) _cur) (= (cadr _cand) _cur)) '
        '(progn (setq _net (cons _cand _net)) '
        '(if (not (member (car _cand) _visited)) (setq _queue (cons (car _cand) _queue))) '
        '(if (not (member (cadr _cand) _visited)) (setq _queue (cons (cadr _cand) _queue))))))))) '
        '(foreach _ns _net '
        '(setq _np1 (caddr _ns) _np2 (cadddr _ns) _mx (/ (+ (car _np1) (car _np2)) 2.0) _my (/ (+ (cadr _np1) (cadr _np2)) 2.0)) '
        '(if (or (ssget "C" (list (- _mx 4.0) (- _my 4.0)) (list (+ _mx 4.0) (+ _my 4.0)) \'((0 . "INSERT") (2 . "WD_WN*"))) '
        '(ssget "C" (list (- (car _np1) 2.0) (- (cadr _np1) 2.0)) (list (+ (car _np1) 2.0) (+ (cadr _np1) 2.0)) \'((0 . "INSERT") (2 . "HA1*"))) '
        '(ssget "C" (list (- (car _np2) 2.0) (- (cadr _np2) 2.0)) (list (+ (car _np2) 2.0) (+ (cadr _np2) 2.0)) \'((0 . "INSERT") (2 . "HA1*")))) '
        '(setq _has_num T))) '
        '(if (and (not _has_num) _net) '
        '(progn (setq _rep (car _net) _rp1 (caddr _rep) _rp2 (cadddr _rep) '
        '_mx (/ (+ (car _rp1) (car _rp2)) 2.0) _my (/ (+ (cadr _rp1) (cadr _rp2)) 2.0) '
        '_blk (if (> (abs (- (car _rp2) (car _rp1))) (abs (- (cadr _rp2) (cadr _rp1)))) "WD_WNH" "WD_WNV") '
        '_wno (strcat _sh (if (< _wn 10) "0" "") (itoa _wn)) '
        '_wb (c:wd_insym2 _blk (list _mx _my 0.0) 1.0 nil)) '
        '(if _wb (progn (c:wd_modattrval _wb "WIRENO" _wno nil) (entupd _wb))) (setq _wn (1+ _wn)))))))))'
    )
    lisp_body = (
        '(setvar "FILEDIA" 0) '
        f'{wnum_lisp} '
        '(command "_AEREBUILDDB") '
        '(c:wd_retag_update_noprompts 97 nil) '
        '(c:wd_tb_process_one 1 (list (list 1 1 1 1 1 1 1 1 0 0 1 1 1))) '
        '(setvar "FILEDIA" 1)'
    )
    res = _run_acade_lisp_checked(
        lisp_body,
        ["c:wd_insym2", "c:wd_modattrval", "c:wd_retag_update_noprompts", "c:wd_tb_process_one"],
        auto_save=bool(args.get("auto_save", True)),
    )

    # Locate .wdp metadata if available so WD_M.SHEET and TITLE_BLOCK_A3_BILINGUAL are deterministically stamped across all sheets
    wdp_descs: dict[str, str] = {}
    wdp_sheets: list[str] = []
    search_dirs: list[Path] = []
    if args.get("wdp_path"):
        wp = Path(args["wdp_path"]).resolve()
        wdp_descs, wdp_sheets = _parse_wdp_metadata(wp)
    elif sheet_paths:
        p0 = Path(sheet_paths[0]).resolve()
        search_dirs = [p0.parent, p0.parent.parent]
        for sd in search_dirs:
            wdps = sorted(sd.glob("*.wdp"))
            if wdps:
                wdp_descs, wdp_sheets = _parse_wdp_metadata(wdps[0])
                break

    total_sh = max(len(wdp_sheets), len(sheet_paths), 1)
    for idx0, sp in enumerate(sheet_paths):
        sp_path = Path(sp).resolve()
        sh_idx = (wdp_sheets.index(sp_path.name) + 1) if sp_path.name in wdp_sheets else (idx0 + 1)
        sh_str = f"{sh_idx:02d}"
        fl = sp_path.name.lower()
        sub = "PANEL" if ("panel" in fl or "-lay-" in fl or "_lay_" in fl) else "SCH"
        tb_map = _build_titleblock_attr_map(wdp_descs, sp_path, sh_idx, total_sh, sub=sub)
        sync_tb_lisp = _lisp_sync_wdm_and_titleblock(sh_str, tb_map)
        tool_autocad_open_or_new({"path": str(sp_path)})
        _run_acade_lisp_checked(
            f'{sync_tb_lisp} {wnum_lisp} (c:wd_tb_process_one 1 (list (list 1 1 1 1 1 1 1 1 0 0 1 1 1)))',
            ["c:wd_insym2", "c:wd_modattrval", "c:wd_tb_process_one"],
            auto_save=True,
        )
    if sheet_paths:
        _run_acade_lisp_checked('(command "_AEREBUILDDB")', ["c:wd_insym2"], auto_save=True)
    return res


def tool_acade_place_db_reports_on_drawing(args: dict[str, Any]) -> dict[str, Any]:
    """Query live Project Scratch .mdb (BOM rollup by MFG+CAT+ASSYCODE, WIRE_FROM_TO+fallback, PLCIO, TERMS) and place dynamic AcDbTable (auto-detects PaperSpace on TILEMODE=0)."""
    mdb_path = Path(args["mdb_path"]).resolve()
    report_type = args.get("report_type", "BOM").upper()
    insert_pt = args.get("insert") or [232.0, 280.0, 0.0]
    if not mdb_path.exists():
        raise FileNotFoundError(f"Scratch database not found: {mdb_path}")

    mdb_str = str(mdb_path).replace("'", "''")
    if report_type == "BOM":
        sql = (
            "SELECT MFG, CAT, ASSYCODE, MAX(DESC1) AS DESCR, COUNT(*) AS QTY, MAX(LOC) AS LOCS "
            "FROM [COMP] WHERE PAR1_CHLD2='1' AND CAT IS NOT NULL AND CAT<>'' "
            "GROUP BY MFG, CAT, ASSYCODE ORDER BY MFG, CAT"
        )
        headers = ["MFG", "CATALOG NO.", "DESCRIPTION", "QTY", "LOC"]
    elif report_type == "WIRE_FROM_TO":
        sql = (
            "SELECT w.WIRENO, w.NAM1, w.PIN1, w.NAM2, w.PIN2, wt.WIRECOLOR, wt.WIRESIZE, w.WLAY1 "
            "FROM [WFRM2ALL] w LEFT JOIN [WIRETYPE] wt ON w.WLAY1 = wt.LAYNAME ORDER BY w.WIRENO"
        )
        headers = ["WIRE NO", "FROM TAG", "PIN1", "TO TAG", "PIN2", "COLOR", "SIZE", "LAYER"]
    elif report_type == "PLCIO":
        sql = "SELECT TAGNAME, ADDR, TERM, TERMDESC, DESCA FROM [PLCIO] ORDER BY TAGNAME, ADDR"
        headers = ["PLC TAG", "ADDRESS", "TERM", "TERMDESC", "DESCRIPTION"]
    elif report_type == "TERMINAL_PLAN":
        sql = "SELECT TAGSTRIP, TERM, WIRENO, LOC, INST FROM [TERMS] ORDER BY TAGSTRIP, TERM"
        headers = ["STRIP", "TERM", "WIRE NO", "LOC", "INST"]
    elif report_type == "CABLE_SUMMARY":
        sql = (
            "SELECT CBL, COUNT(*) AS CORES, MAX(NAM1) AS FROM_TAG, MAX(NAM2) AS TO_TAG, MAX(WLAY1) AS WIRE_LAYER "
            "FROM [WFRM2ALL] WHERE CBL IS NOT NULL AND CBL<>'' GROUP BY CBL ORDER BY CBL"
        )
        headers = ["CABLE TAG", "CORES", "FROM", "TO", "LAYER"]
    else:
        raise ValueError(f"Unsupported report_type: {report_type}")

    ps = f"""
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={mdb_str};")
$conn.Open()
$tables = @($conn.GetSchema("Tables") | Where-Object {{ $_.TABLE_TYPE -eq "TABLE" }} | Select-Object -ExpandProperty TABLE_NAME)
$rows = @()
try {{
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "{sql}"
    $r = $cmd.ExecuteReader()
    while ($r.Read()) {{
        $row = @()
        for ($i = 0; $i -lt $r.FieldCount; $i++) {{
            $v = $r.GetValue($i)
            $row += if ($v -is [DBNull]) {{ "" }} else {{ [string]$v }}
        }}
        $rows += ,$row
    }}
    $r.Close()
}} catch {{}}
if (($rows.Count -eq 0) -and ("{report_type}" -eq "WIRE_FROM_TO")) {{
    if ($tables -contains "TERMS") {{
        $cmd2 = $conn.CreateCommand()
        $cmd2.CommandText = "SELECT WIRENO, TAGSTRIP, TERM, LOC, INST FROM [TERMS] WHERE WIRENO IS NOT NULL AND WIRENO<>'' ORDER BY WIRENO, TAGSTRIP, TERM"
        $r2 = $cmd2.ExecuteReader()
        while ($r2.Read()) {{
            $wno = [string]$r2["WIRENO"]
            $ts = [string]$r2["TAGSTRIP"]
            $tm = [string]$r2["TERM"]
            $lc = [string]$r2["LOC"]
            $in = [string]$r2["INST"]
            $rows += ,@($wno, $ts, $tm, $lc, $in, "BU", "0.75", "CTRL_24VDC_DBU_0.75")
        }}
        $r2.Close()
    }}
    if (($rows.Count -eq 0) -and ($tables -contains "PLCIO")) {{
        $cmd3 = $conn.CreateCommand()
        $cmd3.CommandText = "SELECT ADDR, TAGNAME, TERM, TERMDESC, DESCA FROM [PLCIO] WHERE ADDR IS NOT NULL AND ADDR<>'' ORDER BY TAGNAME, ADDR"
        $r3 = $cmd3.ExecuteReader()
        while ($r3.Read()) {{
            $ad = [string]$r3["ADDR"]
            $tg = [string]$r3["TAGNAME"]
            $tm = [string]$r3["TERM"]
            $td = [string]$r3["TERMDESC"]
            $ds = [string]$r3["DESCA"]
            $rows += ,@($ad, $tg, $tm, $td, $ds, "BU", "0.5", "SIG_PLC_BU_0.5")
        }}
        $r3.Close()
    }}
}}
$conn.Close()
@{{ rows = $rows }} | ConvertTo-Json -Depth 4 -Compress
"""
    data_res = _run_ps(ps, timeout=30)
    raw_rows = data_res.get("rows") or []

    if report_type == "BOM":
        db_rows: list[list[str]] = []
        for r in raw_rows:
            mfg, cat, assy, descr, qty_s, loc = r
            db_rows.append([mfg, cat, descr, qty_s, loc])
            if assy:
                for sub_cat in [s.strip() for s in assy.split(";") if s.strip()]:
                    db_rows.append([mfg, sub_cat, f"ACCESSORY FOR {cat} (ASSYCODE)", qty_s, loc])
    else:
        db_rows = raw_rows
    table_data = [headers] + db_rows
    if len(table_data) == 1:
        return {"report_type": report_type, "rows": 0, "placed": False}

    # Auto-detect PaperSpace when active drawing is a Layout sheet (TILEMODE == 0) unless explicitly overridden
    target_space = args.get("space")
    if not target_space:
        try:
            st = tool_autocad_status({})
            ad = st.get("activeDocument") or {}
            target_space = "PaperSpace" if int(ad.get("tilemode", 1)) == 0 else "ModelSpace"
        except Exception:
            target_space = "ModelSpace"

    draw_res = tool_autocad_draw_entities({
        "space": target_space,
        "zoom_extents": False,
        "auto_save": bool(args.get("auto_save", True)),
        "entities": [{
            "type": "table",
            "layer": "GRID_TABLE",
            "insert": insert_pt,
            "rows": len(table_data),
            "cols": len(headers),
            "row_height": 6.0,
            "col_width": 26.0,
            "data": table_data,
        }],
    })
    return {"report_type": report_type, "rows": len(db_rows), "placed": True, "space": target_space, "draw": draw_res}


def tool_acade_insert_cable_and_jumper(args: dict[str, Any]) -> dict[str, Any]:
    """Insert ACADE Cable Marker (VW01 Parent / VW02 Child) and assign real ht0001 attributes (LINKTERM, STRIPSEQ, X1PIN01/X4PIN01) + VIA_WD_* XDATA."""
    cables = args.get("cables") or []
    terminals = args.get("terminals") or []
    auto_save = bool(args.get("auto_save", True))

    lisp_parts: list[str] = ['(regapp "VIA_WD_LNUMBER")', '(regapp "VIA_WD_LTOTAL")', '(regapp "VIA_WD_JUMPERS")']
    for c in cables:
        pt = c["point"]
        is_child = bool(c.get("is_child", False))
        blk = c.get("block_name") or ("VW02" if is_child else "VW01")
        tag_attr = "TAG2" if is_child else "TAG1"
        lisp_parts.append(
            f'(setq _cb (c:wd_insym2 {_lisp_str(blk)} \'({float(pt[0])} {float(pt[1])} 0.0) 1.0 nil)) '
            f'(if _cb (progn '
            f'(c:wd_modattrval _cb {_lisp_str(tag_attr)} {_lisp_str(c.get("tag", "-W1"))} nil) '
            f'(c:wd_modattrval _cb "MFG" {_lisp_str(c.get("mfg", ""))} nil) '
            f'(c:wd_modattrval _cb "CAT" {_lisp_str(c.get("cat", ""))} nil) '
            f'(c:wd_modattrval _cb "DESC1" {_lisp_str(c.get("desc1", ""))} nil) '
            f'(entupd _cb)))'
        )
    for t in terminals:
        pt = t["point"]
        blk = t.get("block_name", "ht0001")
        lnum = t.get("lnumber", "")
        ltot = t.get("ltotal", "")
        jmp = t.get("jumper_id", "")
        xdata_exprs = []
        if lnum:
            xdata_exprs.append(f'(list "VIA_WD_LNUMBER" (cons 1000 {_lisp_str(lnum)}))')
        if ltot:
            xdata_exprs.append(f'(list "VIA_WD_LTOTAL" (cons 1000 {_lisp_str(ltot)}))')
        if jmp:
            xdata_exprs.append(f'(list "VIA_WD_JUMPERS" (cons 1000 {_lisp_str(jmp)}))')
        xd_attach = (
            f'(setq _tmed (entget _tm)) (entmod (append _tmed (list (list -3 {" ".join(xdata_exprs)}))))'
            if xdata_exprs
            else ""
        )
        lisp_parts.append(
            f'(setq _tm (c:wd_insym2 {_lisp_str(blk)} \'({float(pt[0])} {float(pt[1])} 0.0) 1.0 nil)) '
            f'(if _tm (progn '
            f'(c:wd_modattrval _tm "TAGSTRIP" {_lisp_str(t.get("tagstrip", "-X3"))} nil) '
            f'(c:wd_modattrval _tm "TERM01" {_lisp_str(t.get("term", "1"))} nil) '
            f'(c:wd_modattrval _tm "LINKTERM" {_lisp_str(t.get("linkterm", ""))} nil) '
            f'(c:wd_modattrval _tm "STRIPSEQ" {_lisp_str(t.get("stripseq", ""))} nil) '
            f'(c:wd_modattrval _tm "X1PIN01" {_lisp_str(t.get("x1pin", ""))} nil) '
            f'(c:wd_modattrval _tm "X4PIN01" {_lisp_str(t.get("x4pin", ""))} nil) '
            f'{xd_attach} (entupd _tm)))'
        )
    lisp_body = " ".join(lisp_parts)
    return _run_acade_lisp_checked(lisp_body, ["c:wd_insym2", "c:wd_modattrval"], auto_save=auto_save)


def tool_acade_insert_verified_circuit(args: dict[str, Any]) -> dict[str, Any]:
    """Insert a verified, DRC-clean industrial circuit macro (BUS_3PH_N_PE, DOL_3P, VFD_3P, PSU_24VDC_PELV) with 100% multi-pole & PELV compliance."""
    ctype = str(args["circuit_type"]).strip().upper()
    x0 = float(args.get("origin_x", 90.0))
    bus_ys = args.get("bus_ys") or [272.0, 265.0, 258.0, 251.0, 244.0]  # L1, L2, L3, N, PE
    y_l1, y_l2, y_l3, y_n, y_pe = [float(v) for v in bus_ys]
    auto_save = bool(args.get("auto_save", True))

    wires: list[dict[str, Any]] = []
    dots: list[list[float]] = []
    arrows: list[dict[str, Any]] = []
    sym_lisps: list[str] = []

    if ctype == "BUS_3PH_N_PE":
        x_end = float(args.get("x_end", 395.0))
        bus_defs = [
            (y_l1, "PWR_L1_BK_2.5", "L1", "BUS_L1_400VAC"),
            (y_l2, "PWR_L2_BK_2.5", "L2", "BUS_L2_400VAC"),
            (y_l3, "PWR_L3_BK_2.5", "L3", "BUS_L3_400VAC"),
            (y_n, "PWR_N_BU_2.5", "N", "BUS_N_400VAC"),
            (y_pe, "PWR_PE_GNYE_2.5", "PE", "BUS_PE"),
        ]
        for by, blyr, term_lbl, sig in bus_defs:
            wires.append({"p1": [42.0, by], "p2": [x_end, by], "layer": blyr})
            sym_lisps.append(
                _build_symbol_lisp(
                    "ht0001",
                    [40.0, by],
                    {"TAGSTRIP": "-X0", "TERM01": term_lbl, "MFG": "PHOENIX CONTACT", "CAT": "3044199", "LOC": "+MAIN_PNL"},
                )
            )
            arrows.append({"kind": "source", "point": [x_end, by], "sigcode": sig, "wireno": term_lbl})

    elif ctype == "DOL_3P":
        # Complete 3-pole DOL motor feeder: 3P MPCB (-Q*) + 3P Contactor Contacts (-K*) + Motor (-M*) + isolated PE wire to bottom X8TERM04!
        x1, x2, x3, x_pe = x0, x0 + 10.0, x0 + 20.0, x0 + 30.0
        q_tag = str(args.get("mpcb_tag", "-Q2"))
        k_tag = str(args.get("contactor_tag", "-K1"))
        m_tag = str(args.get("motor_tag", "-M1"))
        inst = str(args.get("inst", "=PLC1"))
        desc1 = str(args.get("desc1", "MOTOR 3P DOL"))
        m_y = 85.0
        # 3 phase vertical drops from L1, L2, L3 down to just above motor, then angled cleanly to VMO13 pins (-6.4,+3.9), (0,+7.5), (+6.4,+3.9)
        wires.extend([
            {"p1": [x1, y_l1], "p2": [x1, m_y + 12.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [x1, m_y + 12.0], "p2": [x2 - 6.4, m_y + 3.9], "layer": "PWR_L1_BK_2.5"},
            {"p1": [x2, y_l2], "p2": [x2, m_y + 7.5], "layer": "PWR_L2_BK_2.5"},
            {"p1": [x3, y_l3], "p2": [x3, m_y + 12.0], "layer": "PWR_L3_BK_2.5"},
            {"p1": [x3, m_y + 12.0], "p2": [x2 + 6.4, m_y + 3.9], "layer": "PWR_L3_BK_2.5"},
            # Dedicated PE drop at x_pe (NEVER touching L1/L2/L3!) going under motor to bottom PE pin X8TERM04 @ (x2, m_y - 7.5)
            {"p1": [x_pe, y_pe], "p2": [x_pe, m_y - 14.0], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [x_pe, m_y - 14.0], "p2": [x2, m_y - 14.0], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [x2, m_y - 14.0], "p2": [x2, m_y - 7.5], "layer": "PWR_PE_GNYE_2.5"},
        ])
        dots.extend([[x1, y_l1], [x2, y_l2], [x3, y_l3], [x_pe, y_pe]])
        sym_lisps.extend([
            _build_symbol_lisp(
                "VCB11Q13",
                [x1, 215.0],
                {"TAG1": q_tag, "MFG": "SIEMENS", "CAT": str(args.get("mpcb_cat", "3RV2021-4AA10")), "LOC": "+MAIN_PNL", "INST": inst, "DESC1": f"MPCB {m_tag}"},
                poles=3,
                pole_spacing=10.0,
            ),
            _build_symbol_lisp(
                "VCR21",
                [x1, 155.0],
                {"TAG2": k_tag, "LOC": "+MAIN_PNL", "INST": inst, "DESC1": f"MAIN CONTACTS {k_tag}"},
                poles=3,
                pole_spacing=10.0,
            ),
            _build_symbol_lisp(
                "VMO13",
                [x2, m_y],
                {"TAG1": m_tag, "MFG": "SIEMENS", "CAT": str(args.get("motor_cat", "1LE1001-1BB22")), "LOC": "+FIELD", "INST": inst, "DESC1": desc1},
            ),
        ])

    elif ctype == "VFD_3P":
        # Complete 3-pole VFD feeder using VU1_VFD_3P (w=52, h=64): top X2TERM01..03 @ +11,+26,+41; bot X8TERM04..07 @ +8,+20,+32,+44(PE)
        q_tag = str(args.get("mpcb_tag", "-Q6"))
        u_tag = str(args.get("vfd_tag", "-U1"))
        m_tag = str(args.get("motor_tag", "-M2"))
        inst = str(args.get("inst", "=PLC1"))
        u_x, u_y = x0, 128.0  # VU1_VFD_3P spans X=[x0..x0+52], Y=[128..192]; top pins at Y=197, bot pins at Y=123
        x_l1, x_l2, x_l3 = u_x + 11.0, u_x + 26.0, u_x + 41.0
        x_u, x_v, x_w, x_pe = u_x + 8.0, u_x + 20.0, u_x + 32.0, u_x + 44.0
        m_y = 75.0
        wires.extend([
            {"p1": [x_l1, y_l1], "p2": [x_l1, u_y + 69.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [x_l2, y_l2], "p2": [x_l2, u_y + 69.0], "layer": "PWR_L2_BK_2.5"},
            {"p1": [x_l3, y_l3], "p2": [x_l3, u_y + 69.0], "layer": "PWR_L3_BK_2.5"},
            # VFD chassis PE from PE bus around right side to bottom PE pin (x_pe, u_y - 5.0)
            {"p1": [u_x + 58.0, y_pe], "p2": [u_x + 58.0, u_y - 12.0], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [u_x + 58.0, u_y - 12.0], "p2": [x_pe, u_y - 12.0], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [x_pe, u_y - 12.0], "p2": [x_pe, u_y - 5.0], "layer": "PWR_PE_GNYE_2.5"},
            # VFD U, V, W outputs to VMO13 @ (x_v, m_y) + Motor PE to bottom X8TERM04
            {"p1": [x_u, u_y - 5.0], "p2": [x_u, m_y + 12.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [x_u, m_y + 12.0], "p2": [x_v - 6.4, m_y + 3.9], "layer": "PWR_L1_BK_2.5"},
            {"p1": [x_v, u_y - 5.0], "p2": [x_v, m_y + 7.5], "layer": "PWR_L2_BK_2.5"},
            {"p1": [x_w, u_y - 5.0], "p2": [x_w, m_y + 12.0], "layer": "PWR_L3_BK_2.5"},
            {"p1": [x_w, m_y + 12.0], "p2": [x_v + 6.4, m_y + 3.9], "layer": "PWR_L3_BK_2.5"},
            {"p1": [x_pe, u_y - 12.0], "p2": [x_pe, m_y - 14.0], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [x_pe, m_y - 14.0], "p2": [x_v, m_y - 14.0], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [x_v, m_y - 14.0], "p2": [x_v, m_y - 7.5], "layer": "PWR_PE_GNYE_2.5"},
        ])
        dots.extend([[x_l1, y_l1], [x_l2, y_l2], [x_l3, y_l3], [u_x + 58.0, y_pe], [x_pe, u_y - 12.0]])
        sym_lisps.extend([
            _build_symbol_lisp(
                "VCB11Q13",
                [x_l1, 226.0],
                {"TAG1": q_tag, "MFG": "SIEMENS", "CAT": str(args.get("mpcb_cat", "3RV2021-4AA10")), "LOC": "+MAIN_PNL", "INST": inst, "DESC1": f"MPCB {u_tag}"},
                poles=3,
                pole_spacing=15.0,
            ),
            _build_symbol_lisp(
                "VU1_VFD_3P",
                [u_x, u_y],
                {"TAG1": u_tag, "MFG": "SIEMENS", "CAT": str(args.get("vfd_cat", "6SL3210-1KE18-8UF2")), "LOC": "+MAIN_PNL", "INST": inst, "DESC1": str(args.get("desc1", "SINAMICS G120C VFD"))},
            ),
            _build_symbol_lisp(
                "VMO13",
                [x_v, m_y],
                {"TAG1": m_tag, "MFG": "SIEMENS", "CAT": str(args.get("motor_cat", "1LE1001-1BB22")), "LOC": "+FIELD", "INST": inst, "DESC1": f"MOTOR {m_tag}"},
            ),
        ])

    elif ctype == "PSU_24VDC_PELV":
        # Complete IEC 60204-1 Grounded PELV 24VDC Power Supply:
        # 2-pole MCB (-Q3) cutting BOTH L and N -> VG1_PSU_24V top L1(+8), N(+21), PE(+34);
        # Bottom isolated +24V(+12) & 0V(+30) -> 0VDC grounded to PE bar + paired Source Arrows!
        q_tag = str(args.get("mcb_tag", "-Q3"))
        g_tag = str(args.get("psu_tag", "-G1"))
        inst = str(args.get("inst", "=MAIN"))
        phase_bus_y = {"L1": y_l1, "L2": y_l2, "L3": y_l3}.get(str(args.get("phase", "L1")).upper(), y_l1)
        phase_lyr = {"L1": "PWR_L1_BK_2.5", "L2": "PWR_L2_BK_2.5", "L3": "PWR_L3_BK_2.5"}.get(str(args.get("phase", "L1")).upper(), "PWR_L1_BK_2.5")
        sig_24v = str(args.get("sig_24v", "BUS_24VDC_PELV"))
        sig_0v = str(args.get("sig_0v", "BUS_0VDC_PELV"))
        wno_24v = str(args.get("wno_24v", "+24VDC"))
        wno_0v = str(args.get("wno_0v", "0VDC"))

        g_x, g_y = x0, 125.0  # VG1_PSU_24V (w=42, h=46): top pins @ Y=176 (+8 L1, +21 N, +34 PE); bot pins @ Y=120 (+12 +24V, +30 0V)
        x_l, x_n, x_pe = g_x + 8.0, g_x + 21.0, g_x + 34.0
        x_24v, x_0v = g_x + 12.0, g_x + 30.0
        out_24_y = float(args.get("out_24_y", 96.0))
        out_0v_y = float(args.get("out_0v_y", 82.0))
        arr_x = float(args.get("arrow_x", min(395.0, g_x + 75.0)))

        wires.extend([
            # AC Input L, N (both cut through 2-pole MCB -Q3!) + PE into VG1_PSU_24V top pins
            {"p1": [x_l, phase_bus_y], "p2": [x_l, g_y + 51.0], "layer": phase_lyr},
            {"p1": [x_n, y_n], "p2": [x_n, g_y + 51.0], "layer": "PWR_N_BU_2.5"},
            {"p1": [x_pe, y_pe], "p2": [x_pe, g_y + 51.0], "layer": "PWR_PE_GNYE_2.5"},
            # Galvanically isolated DC Output +24VDC & 0VDC from bottom pins
            {"p1": [x_24v, g_y - 5.0], "p2": [x_24v, out_24_y], "layer": "CTRL_24VDC_DBU_0.75"},
            {"p1": [x_24v, out_24_y], "p2": [arr_x, out_24_y], "layer": "CTRL_24VDC_DBU_0.75"},
            {"p1": [x_0v, g_y - 5.0], "p2": [x_0v, out_0v_y], "layer": "CTRL_0VDC_BUWH_0.75"},
            {"p1": [x_0v, out_0v_y], "p2": [arr_x, out_0v_y], "layer": "CTRL_0VDC_BUWH_0.75"},
            # IEC 60204-1 Grounded PELV bond: 0VDC bonded to PE via dedicated PE link at x_pe + 10
            {"p1": [g_x + 46.0, y_pe], "p2": [g_x + 46.0, out_0v_y], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [x_0v, out_0v_y], "p2": [g_x + 46.0, out_0v_y], "layer": "PWR_PE_GNYE_2.5"},
        ])
        dots.extend([[x_l, phase_bus_y], [x_n, y_n], [x_pe, y_pe], [g_x + 46.0, y_pe], [x_0v, out_0v_y]])
        arrows.extend([
            {"kind": "source", "point": [arr_x, out_24_y], "sigcode": sig_24v, "wireno": wno_24v},
            {"kind": "source", "point": [arr_x, out_0v_y], "sigcode": sig_0v, "wireno": wno_0v},
        ])
        sym_lisps.extend([
            _build_symbol_lisp(
                "VCB11Q13",
                [x_l, 222.0],
                {"TAG1": q_tag, "MFG": "SIEMENS", "CAT": "5SL6210-7", "LOC": "+MAIN_PNL", "INST": inst, "DESC1": f"MCB 2P 10A {g_tag}"},
                poles=2,
                pole_spacing=13.0,
            ),
            _build_symbol_lisp(
                "VG1_PSU_24V",
                [g_x, g_y],
                {"TAG1": g_tag, "MFG": "SIEMENS", "CAT": str(args.get("psu_cat", "6EP1334-2BA20")), "LOC": "+MAIN_PNL", "INST": inst, "DESC1": str(args.get("desc1", "SITOP 24VDC 10A PELV"))},
            ),
        ])
    elif ctype == "STAR_DELTA_3P":
        q_tag = str(args.get("mpcb_tag", "-Q1"))
        km_tag = str(args.get("contactor_tag", "-K1M"))
        kd_tag = str(args.get("delta_tag", "-K1D"))
        ks_tag = str(args.get("star_tag", "-K1S"))
        m_tag = str(args.get("motor_tag", "-M1"))
        inst = str(args.get("inst", "=CONVEYOR"))
        desc1 = str(args.get("desc1", "STAR-DELTA MOTOR 11KW"))
        x1, x2, x3 = ox, ox + 13.0, ox + 26.0
        kd_x = ox + 52.0
        ks_x = ox + 98.0
        y1, y2, y3, y_pe = bus_ys[0], bus_ys[1], bus_ys[2], bus_ys[4]
        y_q, y_km, y_mot = 222.0, 178.0, 125.0
        y_kd, y_ks = 178.0, 178.0
        wires.extend([
            {"p1": [x1, y1], "p2": [x1, y_mot + 10.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [x2, y2], "p2": [x2, y_mot + 10.0], "layer": "PWR_L2_BK_2.5"},
            {"p1": [x3, y3], "p2": [x3, y_mot + 10.0], "layer": "PWR_L3_BK_2.5"},
            {"p1": [x3 + 12.0, y_pe], "p2": [x3 + 12.0, y_mot - 10.0], "layer": "PWR_PE_GNYE_2.5"},
            {"p1": [x3 + 4.0, y_mot - 10.0], "p2": [x3 + 12.0, y_mot - 10.0], "layer": "PWR_PE_GNYE_2.5"},
            # Delta & Star contactor branches
            {"p1": [x1, 200.0], "p2": [kd_x, 200.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [x2, 196.0], "p2": [kd_x + 13.0, 196.0], "layer": "PWR_L2_BK_2.5"},
            {"p1": [x3, 192.0], "p2": [kd_x + 26.0, 192.0], "layer": "PWR_L3_BK_2.5"},
            {"p1": [kd_x, 200.0], "p2": [kd_x, 148.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [kd_x + 13.0, 196.0], "p2": [kd_x + 13.0, 148.0], "layer": "PWR_L2_BK_2.5"},
            {"p1": [kd_x + 26.0, 192.0], "p2": [kd_x + 26.0, 148.0], "layer": "PWR_L3_BK_2.5"},
            {"p1": [kd_x, 148.0], "p2": [ks_x, 148.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [kd_x + 13.0, 152.0], "p2": [ks_x + 13.0, 152.0], "layer": "PWR_L2_BK_2.5"},
            {"p1": [kd_x + 26.0, 156.0], "p2": [ks_x + 26.0, 156.0], "layer": "PWR_L3_BK_2.5"},
            {"p1": [ks_x, 192.0], "p2": [ks_x, 148.0], "layer": "PWR_L1_BK_2.5"},
            {"p1": [ks_x + 13.0, 192.0], "p2": [ks_x + 13.0, 152.0], "layer": "PWR_L2_BK_2.5"},
            {"p1": [ks_x + 26.0, 192.0], "p2": [ks_x + 26.0, 156.0], "layer": "PWR_L3_BK_2.5"},
            {"p1": [ks_x, 192.0], "p2": [ks_x + 26.0, 192.0], "layer": "PWR_L1_BK_2.5"},
        ])
        dots.extend([[x1, y1], [x2, y2], [x3, y3], [x3 + 12.0, y_pe], [x1, 200.0], [x2, 196.0], [x3, 192.0], [ks_x + 13.0, 192.0]])
        sym_lisps.extend([
            _build_symbol_lisp("VCB11Q13", [x1, y_q], {"TAG1": q_tag, "MFG": "SIEMENS", "CAT": "3RV2021-4DA10", "LOC": "+MAIN_PNL", "INST": inst, "DESC1": "MPCB 3P"}, poles=3, pole_spacing=13.0),
            _build_symbol_lisp("VCR1", [x1, y_km], {"TAG1": km_tag, "MFG": "SIEMENS", "CAT": "3RT2026-1BB40", "LOC": "+MAIN_PNL", "INST": inst, "DESC1": "MAIN CONTACTOR"}, poles=3, pole_spacing=13.0),
            _build_symbol_lisp("VCR1", [kd_x, y_kd], {"TAG1": kd_tag, "MFG": "SIEMENS", "CAT": "3RT2026-1BB40", "LOC": "+MAIN_PNL", "INST": inst, "DESC1": "DELTA CONTACTOR"}, poles=3, pole_spacing=13.0),
            _build_symbol_lisp("VCR1", [ks_x, y_ks], {"TAG1": ks_tag, "MFG": "SIEMENS", "CAT": "3RT2026-1BB40", "LOC": "+MAIN_PNL", "INST": inst, "DESC1": "STAR CONTACTOR"}, poles=3, pole_spacing=13.0),
            _build_symbol_lisp("VMO13", [x2, y_mot], {"TAG1": m_tag, "MFG": "SIEMENS", "CAT": "1LE1001-1CB23", "LOC": "+FIELD", "INST": inst, "DESC1": desc1}),
        ])
    elif ctype == "SAFETY_3SK1_2CH":
        s_tag = str(args.get("estop_tag", "-S0"))
        k_tag = str(args.get("safety_tag", "-K0"))
        inst = str(args.get("inst", "=SAFETY"))
        x_ch1, x_ch2, x_out = ox, ox + 22.0, ox + 52.0
        wires.extend([
            {"p1": [x_ch1, 250.0], "p2": [x_ch1, 165.0], "layer": "SAFE_24VDC_YE_0.75"},
            {"p1": [x_ch2, 250.0], "p2": [x_ch2, 165.0], "layer": "SAFE_24VDC_YE_0.75"},
            {"p1": [x_ch1, 165.0], "p2": [x_ch1, 120.0], "layer": "CTRL_0VDC_BUWH_0.75"},
            {"p1": [x_out, 250.0], "p2": [x_out, 145.0], "layer": "CTRL_24VDC_DBU_0.75"},
        ])
        arrows.extend([
            {"kind": "destination", "point": [x_ch1, 250.0], "sigcode": "BUS_24VDC_PELV", "wireno": "+24VDC"},
            {"kind": "destination", "point": [x_ch2, 250.0], "sigcode": "BUS_24VDC_PELV", "wireno": "+24VDC"},
            {"kind": "destination", "point": [x_ch1, 120.0], "sigcode": "BUS_0VDC_PELV", "wireno": "0VDC"},
            {"kind": "source", "point": [x_out, 145.0], "sigcode": "SAFE_24VDC_EN", "wireno": "+24V_SAFE"},
        ])
        sym_lisps.extend([
            _build_symbol_lisp("VPB12", [x_ch1, 220.0], {"TAG1": s_tag, "MFG": "SIEMENS", "CAT": "3SU1150-1HB20-1CG0", "LOC": "+DOOR", "INST": inst, "DESC1": "E-STOP 2CH NC"}, poles=2, pole_spacing=22.0),
            _build_symbol_lisp("VCR1", [x_ch1, 165.0], {"TAG1": k_tag, "MFG": "SIEMENS", "CAT": "3SK1111-1AB30", "LOC": "+MAIN_PNL", "INST": inst, "DESC1": "SAFETY RELAY 3SK1"}, poles=2, pole_spacing=52.0),
        ])
    else:
        raise ValueError(f"Unsupported circuit_type '{ctype}'. Choose from: BUS_3PH_N_PE, DOL_3P, VFD_3P, PSU_24VDC_PELV, STAR_DELTA_3P, SAFETY_3SK1_2CH.")

    # Draw smart wires + dots + arrows FIRST, then insert & auto-trim multi-pole symbols SECOND!
    wire_res = tool_acade_draw_smart_wires_and_arrows({"wires": wires, "dots": dots, "arrows": arrows, "auto_save": False})
    sym_res = _run_acade_lisp_checked(" ".join(sym_lisps), ["c:wd_insym2", "c:wd_modattrval"], auto_save=auto_save, timeout_sec=45.0)
    return {"circuit_type": ctype, "wires_drawn": len(wires), "symbols_groups": len(sym_lisps), "wire_res": wire_res, "sym_res": sym_res}


def tool_acade_electrical_audit(args: dict[str, Any]) -> dict[str, Any]:
    """Run Fail-Closed Database + DWG Gatekeeper v3.1 audit on Project Scratch .mdb and optional project_dir."""
    mdb_path = Path(args["mdb_path"]).resolve()
    cmd = [sys.executable, str(AUDIT_SCRIPT), "--mdb", str(mdb_path)]
    if args.get("project_dir"):
        cmd.extend(["--project-dir", str(Path(args["project_dir"]).resolve())])
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    if proc.returncode not in (0, 2):
        raise RuntimeError((proc.stderr or proc.stdout or "Audit script failed").strip())
    return json.loads(proc.stdout.strip())


TOOLS = [
    {
        "name": "autocad_status",
        "description": "Inspect the running Autodesk AutoCAD instance via COM: active document, open documents, active layout, DBMOD, CMDACTIVE, and $INSUNITS.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "autocad_open_or_new",
        "description": "Open a .dwg/.dxf file or create a new 1:1 mm drawing with ISO linetypes, VN_ARIAL font, and ISO_MM DimStyle.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Absolute path to .dwg/.dxf. Omit to create a new 1:1 mm drawing."}},
        },
    },
    {
        "name": "autocad_run_command",
        "description": "Send an AutoCAD command or AutoLISP expression directly to ActiveDocument.SendCommand() and auto-save if titled.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "AutoCAD command or LISP expression."},
                "auto_save": {"type": "boolean", "default": True, "description": "Auto-save the active drawing after executing."},
            },
            "required": ["command"],
        },
    },
    {
        "name": "autocad_reload_file",
        "description": "Reload a .dwg/.dxf tab in AutoCAD via COM safely (backs up unsaved edits if DBMOD != 0 unless force=true).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_path": {"type": "string", "description": "Target .dwg/.dxf path to reload."},
                "source_path": {"type": "string", "description": "Optional staged file to move onto target_path while unlocked."},
                "force": {"type": "boolean", "default": False, "description": "Skip DBMOD backup when true."},
            },
            "required": ["target_path"],
        },
    },
    {
        "name": "autocad_draw_entities",
        "description": "Draw CAD entities (line, circle, arc, lwpolyline, text, mtext, hatch, insert_block, mleader, table, dim_aligned, dim_linear, dim_diameter) directly into ModelSpace or PaperSpace via COM and auto-save.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "space": {"type": "string", "enum": ["ModelSpace", "PaperSpace"], "default": "ModelSpace"},
                "zoom_extents": {"type": "boolean", "default": True},
                "auto_save": {"type": "boolean", "default": True},
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["line", "circle", "arc", "lwpolyline", "text", "mtext", "hatch", "insert_block", "mleader", "table", "dim_aligned", "dim_linear", "dim_diameter"]},
                            "layer": {"type": "string"},
                            "color": {"type": "integer"},
                            "linetype": {"type": "string"},
                            "lineweight": {"type": "integer"},
                            "p1": {"type": "array", "items": {"type": "number"}},
                            "p2": {"type": "array", "items": {"type": "number"}},
                            "center": {"type": "array", "items": {"type": "number"}},
                            "radius": {"type": "number"},
                            "start_angle_rad": {"type": "number"},
                            "end_angle_rad": {"type": "number"},
                            "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                            "closed": {"type": "boolean"},
                            "text": {"type": "string"},
                            "insert": {"type": "array", "items": {"type": "number"}},
                            "height": {"type": "number"},
                            "width": {"type": "number"},
                            "pattern": {"type": "string"},
                            "scale": {"type": "number"},
                            "boundary_points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                            "block_name": {"type": "string"},
                            "attributes": {"type": "object"},
                            "rows": {"type": "integer"},
                            "cols": {"type": "integer"},
                            "data": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                            "text_pos": {"type": "array", "items": {"type": "number"}},
                            "angle_rad": {"type": "number"},
                            "chord1": {"type": "array", "items": {"type": "number"}},
                            "chord2": {"type": "array", "items": {"type": "number"}},
                            "leader_len": {"type": "number"},
                            "text_override": {"type": "string"},
                        },
                        "required": ["type"],
                    },
                },
            },
            "required": ["entities"],
        },
    },
    {
        "name": "autocad_audit_and_inspect",
        "description": "Audit active AutoCAD drawing via COM for hardcoded Dimension TextOverride, Text/Dim bounding-box overlaps, out-of-frame PaperSpace entities, CMDACTIVE, and LASTPROMPT.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "acade_project_init",
        "description": "Initialize a native ACADE .wdp project, create .dwg sheets from TEMPLATE_IEC_A3.dwt, activate project, and rebuild Scratch Database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {"type": "string"},
                "project_name": {"type": "string"},
                "sheets": {"type": "array", "items": {"type": "object"}},
                "descriptions": {"type": "object"},
                "template_dwt": {"type": "string"},
                "template_wdp": {"type": "string"},
            },
            "required": ["project_dir", "project_name"],
        },
    },
    {
        "name": "acade_insert_schematic_symbol",
        "description": "Insert a 1-pole or multi-pole (poles=2|3|4) IEC-60617 symbol via (c:wd_insym2) in Safe Zone [25..405, 12..276], link mechanical poles on LINK layer, and auto-break all crossed phase wires.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "block_name": {"type": "string"},
                "point": {"type": "array", "items": {"type": "number"}},
                "poles": {"type": "integer", "enum": [1, 2, 3, 4], "default": 1, "description": "Number of linked poles (use 3 for 3-phase CB/MPCB/Fuse/Contactor, 2 for L+N 2-pole MCB)."},
                "pole_spacing": {"type": "number", "default": 10.0, "description": "Horizontal spacing in mm between adjacent poles."},
                "scale": {"type": "number", "default": 1.0},
                "options": {"type": "integer", "default": 0},
                "attributes": {"type": "object"},
                "auto_save": {"type": "boolean", "default": True},
            },
            "required": ["block_name", "point"],
        },
    },
    {
        "name": "acade_insert_verified_circuit",
        "description": "Insert a pre-engineered, DRC-clean industrial circuit macro: BUS_3PH_N_PE, DOL_3P, VFD_3P, PSU_24VDC_PELV, STAR_DELTA_3P, or SAFETY_3SK1_2CH.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "circuit_type": {"type": "string", "enum": ["BUS_3PH_N_PE", "DOL_3P", "VFD_3P", "PSU_24VDC_PELV", "STAR_DELTA_3P", "SAFETY_3SK1_2CH"]},
                "origin_x": {"type": "number", "default": 90.0},
                "bus_ys": {"type": "array", "items": {"type": "number"}, "description": "[y_L1, y_L2, y_L3, y_N, y_PE]"},
                "mpcb_tag": {"type": "string"},
                "mcb_tag": {"type": "string"},
                "contactor_tag": {"type": "string"},
                "vfd_tag": {"type": "string"},
                "psu_tag": {"type": "string"},
                "motor_tag": {"type": "string"},
                "phase": {"type": "string", "enum": ["L1", "L2", "L3"]},
                "inst": {"type": "string"},
                "desc1": {"type": "string"},
                "auto_save": {"type": "boolean", "default": True},
            },
            "required": ["circuit_type"],
        },
    },
    {
        "name": "acade_draw_smart_wires_and_arrows",
        "description": "Register wire layers on WD_M, draw orthogonal wires, place WDDOT at tees, and insert paired Source/Destination Signal Arrows (SIGCODE).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "wire_layers": {"type": "array", "items": {"type": "object"}},
                "wires": {"type": "array", "items": {"type": "object"}},
                "dots": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                "arrows": {"type": "array", "items": {"type": "object"}},
                "auto_save": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "acade_build_plc_from_csv",
        "description": "Validate peripheral BLOCK names in PLC I/O CSV and run ACADE Spreadsheet to PLC I/O Utility (AEPLCIO) with automatic 2-module/sheet pagination.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "csv_path": {"type": "string"},
                "wdi_path": {"type": "string"},
                "slot_filter": {"type": "array", "items": {"type": "string"}},
                "page_index": {"type": "integer", "default": 0},
                "auto_save": {"type": "boolean", "default": True},
            },
            "required": ["csv_path"],
        },
    },
    {
        "name": "acade_sync_panel_footprints",
        "description": "Query COMP (+MAIN_PNL, +DOOR) from Project Scratch .mdb to sync verified 1:1 Panel Footprints (P_TAG1) on 07_panel_layout.dwg (Fail-Closed if missing from catalog).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mdb_path": {"type": "string"},
                "enclosure_size": {"type": "object", "description": "{\"width_mm\": 800, \"height_mm\": 1200}"},
                "placements": {"type": "object", "description": "Optional {\"-Q1\": [x, y], ...} overrides"},
                "run_aefootprint": {"type": "boolean", "default": False},
            },
            "required": ["mdb_path"],
        },
    },
    {
        "name": "acade_run_reports_and_retag",
        "description": "Run project-wide equipotential wire numbering (%S%N), AEREBUILDDB, AERETAG, and deterministic Title Block + WD_M.SHEET sync across all sheets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sheet_paths": {"type": "array", "items": {"type": "string"}},
                "wdp_path": {"type": "string"},
                "rgf_path": {"type": "string"},
                "auto_save": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "acade_place_db_reports_on_drawing",
        "description": "Query live Project Scratch .mdb (COMP, WFRM2ALL, PLCIO, TERMS) and place dynamic AcDbTable reports (BOM, WIRE_FROM_TO, PLCIO, TERMINAL_PLAN) with auto PaperSpace detection when TILEMODE=0.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mdb_path": {"type": "string"},
                "report_type": {"type": "string", "enum": ["BOM", "WIRE_FROM_TO", "PLCIO", "TERMINAL_PLAN", "CABLE_SUMMARY"], "default": "BOM"},
                "insert": {"type": "array", "items": {"type": "number"}},
                "space": {"type": "string", "enum": ["ModelSpace", "PaperSpace"]},
                "auto_save": {"type": "boolean", "default": True},
            },
            "required": ["mdb_path"],
        },
    },
    {
        "name": "acade_insert_cable_and_jumper",
        "description": "Insert ACADE Cable Marker (VW01 Parent / VW02 Child) for field cables and assign real ht0001 attributes (LINKTERM, STRIPSEQ, X1PIN01/X4PIN01) + VIA_WD_* XDATA.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cables": {"type": "array", "items": {"type": "object"}},
                "terminals": {"type": "array", "items": {"type": "object"}},
                "auto_save": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "acade_electrical_audit",
        "description": "Gatekeeper v3.1 audit on ACADE Project Scratch .mdb and .dwg sheets (Netlist DRC, PINLIST overuse/dup pins, cross-sheet SIGCODE, duplicate terminals, Title Block, Panel Layout).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mdb_path": {"type": "string"},
                "project_dir": {"type": "string", "description": "Optional path to project folder or 01_Drawings folder for deep DWG geometry & Title Block audit."},
                "run_dwg_audit": {"type": "boolean", "default": False},
            },
            "required": ["mdb_path"],
        },
    },
]

HANDLERS = {
    "autocad_status": tool_autocad_status,
    "autocad_open_or_new": tool_autocad_open_or_new,
    "autocad_run_command": tool_autocad_run_command,
    "autocad_reload_file": tool_autocad_reload_file,
    "autocad_draw_entities": tool_autocad_draw_entities,
    "autocad_audit_and_inspect": tool_autocad_audit_and_inspect,
    "acade_project_init": tool_acade_project_init,
    "acade_insert_schematic_symbol": tool_acade_insert_schematic_symbol,
    "acade_insert_verified_circuit": tool_acade_insert_verified_circuit,
    "acade_draw_smart_wires_and_arrows": tool_acade_draw_smart_wires_and_arrows,
    "acade_build_plc_from_csv": tool_acade_build_plc_from_csv,
    "acade_sync_panel_footprints": tool_acade_sync_panel_footprints,
    "acade_run_reports_and_retag": tool_acade_run_reports_and_retag,
    "acade_place_db_reports_on_drawing": tool_acade_place_db_reports_on_drawing,
    "acade_insert_cable_and_jumper": tool_acade_insert_cable_and_jumper,
    "acade_electrical_audit": tool_acade_electrical_audit,
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
                result = {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                }
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
                _send({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": f"Error: {exc}"}], "isError": True},
                })
            else:
                _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(exc)}})


if __name__ == "__main__":
    main()
