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
TEMPLATE_WDP = SKILL_ROOT / "templates" / "TEMPLATE_PROJECT.wdp"
DEFAULT_WDI = SKILL_ROOT / "templates" / "default_plc_io.wdi"
DEFAULT_RGF = SKILL_ROOT / "templates" / "project_master_reports.rgf"
AUDIT_SCRIPT = SKILL_ROOT / "scripts" / "acade_electrical_audit.py"
SEED_SCRIPT = SKILL_ROOT / "scripts" / "seed_acade_databases.py"


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


def _run_acade_lisp_checked(lisp_body: str, req_fns: list[str], auto_save: bool = True) -> dict[str, Any]:
    """Send ACADE AutoLISP via COM and raise RuntimeError if any required function is unbound."""
    import tempfile

    err_path = Path(tempfile.gettempdir()) / "acade_mcp_err.txt"
    if err_path.exists():
        err_path.unlink()
    guard = _lisp_fail_loud_guard(req_fns, str(err_path))
    full_cmd = f"(progn {_lisp_acade_load()} {guard} (if (not _missing) (progn {lisp_body})))\n"
    res = tool_autocad_run_command({"command": full_cmd, "auto_save": auto_save})
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
    """Initialize a native .wdp project, copy sheets from TEMPLATE_IEC_A3.dwt, activate it, and rebuild Scratch DB."""
    project_dir = Path(args["project_dir"]).resolve()
    project_name = args["project_name"].strip()
    sheets = args.get("sheets") or [
        {"file": "01_cover_and_index.dwg", "desc": "COVER AND DRAWING INDEX"},
        {"file": "04_power_distribution.dwg", "desc": "POWER DISTRIBUTION SCHEMATIC"},
        {"file": "05_control_schematic.dwg", "desc": "CONTROL & LOAD CELL SCHEMATIC"},
        {"file": "06_plc_io_wiring.dwg", "desc": "PLC I/O WIRING"},
        {"file": "07_panel_layout.dwg", "desc": "PANEL LAYOUT"},
        {"file": "09_terminal_and_cable_list.dwg", "desc": "TERMINAL & CABLE LIST"},
    ]
    template_dwt = Path(args.get("template_dwt") or TEMPLATE_DWT).resolve()
    template_wdp = Path(args.get("template_wdp") or TEMPLATE_WDP).resolve()
    if not template_dwt.exists():
        raise FileNotFoundError(f"Template DWT not found: {template_dwt}")
    if not template_wdp.exists():
        raise FileNotFoundError(f"Template WDP not found: {template_wdp}")

    project_dir.mkdir(parents=True, exist_ok=True)
    wdp_path = project_dir / f"{project_name}.wdp"
    base_lines = template_wdp.read_text(encoding="utf-8", errors="replace").splitlines()
    header_lines = [ln for ln in base_lines if ln.startswith(("*", "+", "?"))]

    descriptions = args.get("descriptions") or {}
    for idx in range(1, 11):
        key = f"LINE{idx}"
        if key in descriptions:
            prefix = f"*[{idx}]"
            header_lines = [ln for ln in header_lines if not ln.startswith(prefix)]
            header_lines.insert(idx - 1, f"{prefix}{descriptions[key]}")

    for s in sheets:
        fname = s["file"] if s["file"].lower().endswith(".dwg") else f"{s['file']}.dwg"
        s_desc = s.get("desc", fname)
        sub = s.get("sub", "PANEL" if "panel" in fname.lower() else "SCHEMATIC")
        header_lines.extend([f"==={s_desc}", f"=====SUB={sub}", fname])

    wdp_path.write_text("\n".join(header_lines) + "\n", encoding="utf-8")

    # Copy WDT mapping alongside .wdp
    wdt_src = SKILL_ROOT / "templates" / "default_iec_bilingual.wdt"
    if wdt_src.exists():
        (project_dir / f"{project_name}.wdt").write_text(wdt_src.read_text(encoding="utf-8"), encoding="utf-8")

    sheet_paths = [str((project_dir / (s["file"] if s["file"].lower().endswith(".dwg") else f"{s['file']}.dwg")).resolve()) for s in sheets]
    payload_q = _ps_quote(json.dumps({
        "template_dwt": str(template_dwt),
        "wdp_path": str(wdp_path).replace("\\", "/"),
        "sheets": sheet_paths,
        "load_lisp": _lisp_acade_load(),
    }))
    ps = f"""
$ErrorActionPreference = 'Stop'
$payload = ConvertFrom-Json {payload_q}
$acad = [Runtime.InteropServices.Marshal]::GetActiveObject('AutoCAD.Application')
$created = @()
foreach ($sp in $payload.sheets) {{
    if (-not (Test-Path $sp)) {{
        $d = $acad.Documents.Add($payload.template_dwt)
        $d.SaveAs($sp)
        $d.Close($false)
        $created += $sp
    }}
}}
$first = $payload.sheets[0]
$doc = $acad.Documents.Open($first)
$doc.Activate()
$wdpLisp = $payload.wdp_path
$cmd = $payload.load_lisp + '(command "_AEOPENPROJECT" "' + $wdpLisp + '") (if (boundp \'c:ace_add_dwg_to_project) (c:ace_add_dwg_to_project nil (list "" "" "" 1))) (command "_AEREBUILDDB")' + "`n"
$doc.SendCommand($cmd)
@{{ wdp = $payload.wdp_path; created_dwgs = $created; active = $doc.FullName }} | ConvertTo-Json -Compress
"""
    return _run_ps(ps, timeout=60)


def tool_acade_insert_schematic_symbol(args: dict[str, Any]) -> dict[str, Any]:
    """Insert a real IEC-60617 schematic symbol via (c:wd_insym2) and populate TAG/MFG/CAT/LOC/INST/DESC/TERM."""
    block_name = args["block_name"]
    pt = args["point"]
    scale = float(args.get("scale", 1.0))
    attrs = args.get("attributes") or {}
    auto_save = bool(args.get("auto_save", True))

    mod_exprs = [f'(c:wd_modattrval _ent {_lisp_str(k)} {_lisp_str(v)} nil)' for k, v in attrs.items()]
    lisp_body = (
        f"(setq _ent (c:wd_insym2 {_lisp_str(block_name)} '({float(pt[0])} {float(pt[1])} 0.0) {scale} nil)) "
        f"(if (not _ent) (princ \"\\n[ACADE_ERR] wd_insym2 returned nil\\n\") "
        f"(progn {' '.join(mod_exprs)} (entupd _ent)))"
    )
    return _run_acade_lisp_checked(lisp_body, ["c:wd_insym2", "c:wd_modattrval"], auto_save=auto_save)


def tool_acade_draw_smart_wires_and_arrows(args: dict[str, Any]) -> dict[str, Any]:
    """Draw smart ACADE wires via (c:wd_wire_quik), register VIA_WD_WIRETYPE XDATA, insert WDDOT, and Source/Dest arrows."""
    wire_layers = args.get("wire_layers") or []
    wires = args.get("wires") or []
    dots = args.get("dots") or []
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

    dot_exprs = [f'(c:wd_insym2 "WDDOT" \'({float(d[0])} {float(d[1])} 0.0) 1.0 nil)' for d in dots]

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
        arrow_exprs.append('(command "_AEUPDATESIGREF")')

    lisp_body = f"{' '.join(reg_exprs)} {' '.join(wire_exprs)} {' '.join(dot_exprs)} {' '.join(arrow_exprs)}"
    return _run_acade_lisp_checked(lisp_body, ["c:wd_wire_quik", "c:wd_insym2", "c:wd_modattrval"], auto_save=auto_save)


def tool_acade_build_plc_from_csv(args: dict[str, Any]) -> dict[str, Any]:
    """Validate peripheral BLOCK column in PLC I/O CSV and run ACADE Spreadsheet to PLC I/O Utility."""
    import csv as _csv

    csv_path = Path(args["csv_path"]).resolve()
    wdi_path = Path(args.get("wdi_path") or DEFAULT_WDI).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"PLC CSV not found: {csv_path}")

    invalid_blocks = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in _csv.DictReader(f):
            blk = (row.get("BLOCK") or "").strip().upper()
            if blk.startswith("PLC_"):
                invalid_blocks.append(blk)
    if invalid_blocks:
        raise ValueError(
            f"Invalid fake PLC module names in BLOCK column ({set(invalid_blocks)}). "
            "Use real iec-60617 peripheral symbols (e.g., VCR1, VPB11, VLT1A, VSW12) or leave blank."
        )

    lisp_body = f'(command "_AEPLCIO" {_lisp_str(str(csv_path))} {_lisp_str(str(wdi_path))})'
    return _run_acade_lisp_checked(lisp_body, ["c:wd_inplc_nd"], auto_save=bool(args.get("auto_save", True)))


def tool_acade_sync_panel_footprints(args: dict[str, Any]) -> dict[str, Any]:
    """Query COMP (PAR1_CHLD2='1' AND LOC IN ('+MAIN_PNL','+DOOR')) from Scratch .mdb to sync Panel Footprints."""
    mdb_path = Path(args["mdb_path"]).resolve()
    if not mdb_path.exists():
        raise FileNotFoundError(f"Scratch database not found: {mdb_path}")
    mdb_str = str(mdb_path).replace("'", "''")
    ps = f"""
$ErrorActionPreference = 'Stop'
$conn = New-Object System.Data.Odbc.OdbcConnection("Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq=$mdb_str;")
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
    if args.get("run_aefootprint"):
        _run_acade_lisp_checked('(command "_AEFOOTPRINT")', ["c:wd_insym2"], auto_save=True)
    return res


def tool_acade_run_reports_and_retag(args: dict[str, Any]) -> dict[str, Any]:
    """Run project-wide AEREBUILDDB, c:wd_retag_update_noprompts, AEWIRENO, c:wd_tb_process_one, and AEREPORTGROUP (.rgf)."""
    rgf_path = Path(args.get("rgf_path") or DEFAULT_RGF).resolve()
    lisp_body = (
        '(command "_AEREBUILDDB") '
        '(c:wd_retag_update_noprompts 97 nil) '
        '(command "_AEWIRENO") '
        '(c:wd_tb_process_one 1 (list (list 1 1 1 1 1 1 1 1 0 0 1 1 1))) '
        f'(if (findfile {_lisp_str(str(rgf_path))}) (command "_AEREPORTGROUP" {_lisp_str(str(rgf_path))}))'
    )
    return _run_acade_lisp_checked(
        lisp_body,
        ["c:wd_retag_update_noprompts", "c:wd_tb_process_one"],
        auto_save=bool(args.get("auto_save", True)),
    )


def tool_acade_electrical_audit(args: dict[str, Any]) -> dict[str, Any]:
    """Run Database Gatekeeper audit on Project Scratch .mdb + AEAUDIT/AEDWGAUDIT."""
    mdb_path = Path(args["mdb_path"]).resolve()
    proc = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--mdb", str(mdb_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
    )
    if proc.returncode not in (0, 2):
        raise RuntimeError((proc.stderr or proc.stdout or "Audit script failed").strip())
    audit_res = json.loads(proc.stdout.strip())
    if args.get("run_dwg_audit"):
        tool_autocad_run_command({"command": f"(progn {_lisp_acade_load()}(command \"_AEDWGAUDIT\"))\n", "auto_save": False})
    return audit_res


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
        "description": "Insert a real IEC-60617 symbol via (c:wd_insym2) (auto-breaks wire at X?TERM??) and populate TAG1/TAG2, MFG, CAT, LOC, INST, DESC1..3, TERM01, ASSYCODE.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "block_name": {"type": "string"},
                "point": {"type": "array", "items": {"type": "number"}},
                "scale": {"type": "number", "default": 1.0},
                "options": {"type": "integer", "default": 0},
                "attributes": {"type": "object"},
                "auto_save": {"type": "boolean", "default": True},
            },
            "required": ["block_name", "point"],
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
        "description": "Validate peripheral BLOCK names in PLC I/O CSV and run ACADE Spreadsheet to PLC I/O Utility (AEPLCIO).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "csv_path": {"type": "string"},
                "wdi_path": {"type": "string"},
                "auto_save": {"type": "boolean", "default": True},
            },
            "required": ["csv_path"],
        },
    },
    {
        "name": "acade_sync_panel_footprints",
        "description": "Query COMP (+MAIN_PNL, +DOOR) from Project Scratch .mdb to sync Panel Footprints (P_TAG1) on 07_panel_layout.dwg.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mdb_path": {"type": "string"},
                "run_aefootprint": {"type": "boolean", "default": False},
            },
            "required": ["mdb_path"],
        },
    },
    {
        "name": "acade_run_reports_and_retag",
        "description": "Run project-wide AERETAG, AEWIRENO, AEUPDATETITLEBLOCK, and AEREPORTGROUP (.rgf).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rgf_path": {"type": "string"},
                "auto_save": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "acade_electrical_audit",
        "description": "Gatekeeper audit on ACADE Project Scratch .mdb (missing catalog, duplicate tags, orphaned child contacts, bogus wires, schematic vs panel discrepancy).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mdb_path": {"type": "string"},
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
    "acade_draw_smart_wires_and_arrows": tool_acade_draw_smart_wires_and_arrows,
    "acade_build_plc_from_csv": tool_acade_build_plc_from_csv,
    "acade_sync_panel_footprints": tool_acade_sync_panel_footprints,
    "acade_run_reports_and_retag": tool_acade_run_reports_and_retag,
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
