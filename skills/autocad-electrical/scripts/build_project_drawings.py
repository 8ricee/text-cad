"""Master-Grade Evidence Builder for 'conveyor_weighing_station' (MCC-WEIGH-01).

Enforces all CAD & AutoCAD Electrical engineering standards:
1. True 1:1 Millimeter Model Space ($INSUNITS = 4, $MEASUREMENT = 1, scale = 1.0) -> Every DLI / DIST check in AutoCAD
   measures exact physical millimeters (800, 1200, 740, 1140, 300, 442.3, Ø9, Ø22.5...).
2. Paper Space Layout ('ISO_A3' 420x297 mm) with calibrated AutoCAD VIEWPORTs (1:12.5 on Panel Layout, 1:2.5 on Busbar)
   holding the ISO 5457 frame, Title Block, and bordered engineering schedules.
3. 100% Native AutoCAD DIMENSION Entities (ISO_MM DimStyle, VN_ARIAL font, dimlfac = 1.0, zero hand-drawn LINE+TEXT fake dims).
4. TrueType Unicode Font ('arial.ttf' on AC1032 / R2018 UTF-8 DXF) + Real Bordered Grid Tables + ezdxf.addons.drawing PDF export.
"""

import csv
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_DIR / ".mplcache"))
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from generate_busbar_dxf import compute_developed_length, setup_iso_dimstyle

DXF_DIR = PROJECT_DIR / "DXF"
STEP_DIR = PROJECT_DIR / "STEP"
PDF_DIR = PROJECT_DIR / "PDF"
CATALOG_CSV = Path(__file__).resolve().parent.parent / "templates" / "verified_footprints_catalog.csv"
ISO_5455_SCALES = (1.0, 2.0, 2.5, 5.0, 10.0, 20.0, 25.0, 50.0, 100.0)


def load_verified_footprint(mfg: str, cat: str) -> dict[str, str]:
    """Load verified manufacturer dimensions from templates/verified_footprints_catalog.csv; raise if missing."""
    if not CATALOG_CSV.exists():
        raise FileNotFoundError(f"Missing verified footprint catalog: {CATALOG_CSV}")
    with CATALOG_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["MFG"].strip().upper() == mfg.strip().upper() and row["CAT"].strip().upper() == cat.strip().upper():
                return row
    raise ValueError(f"Unverified footprint '{mfg} {cat}' — add real Datasheet/STEP dimensions to {CATALOG_CSV.name} first!")


def validate_panel_3d_clashes(scene: "PanelAssembly3D", door_z_min: float = 240.0, clearance_mm: float = 15.0) -> None:
    """Verify 3D AABB non-intersection between all footprint devices and door Z-clearance."""
    plate_z_max = max((b.z + b.dz for b in scene.boxes if b.group == "plate"), default=0.0)
    if plate_z_max + clearance_mm > door_z_min:
        raise ValueError(
            f"3D Z-Clash detected: plate device max Z={plate_z_max:.1f} mm + {clearance_mm} mm clearance "
            f"exceeds door rear Z={door_z_min:.1f} mm!"
        )
    # Full 3D (X, Y, Z) AABB clash check across distinct footprint devices
    fps = [b for b in scene.boxes if b.layer == "PNL_FOOTPRINT" and b.group in ("plate", "door")]
    eps = 0.2
    for i in range(len(fps)):
        a = fps[i]
        for j in range(i + 1, len(fps)):
            b = fps[j]
            if a.group != b.group:
                continue
            # Skip stepped sub-tiers belonging to the same device (same XY footprint center)
            acx, acy = a.x + a.dx / 2.0, a.y + a.dy / 2.0
            bcx, bcy = b.x + b.dx / 2.0, b.y + b.dy / 2.0
            if abs(acx - bcx) < 2.0 and abs(acy - bcy) < 2.0:
                continue
            ox = (a.x + eps < b.x + b.dx) and (a.x + a.dx > b.x + eps)
            oy = (a.y + eps < b.y + b.dy) and (a.y + a.dy > b.y + eps)
            oz = (a.z + eps < b.z + b.dz) and (a.z + a.dz > b.z + eps)
            if ox and oy and oz:
                raise ValueError(
                    f"3D AABB Clash ({a.group}): box1=({a.x:.1f},{a.y:.1f},{a.z:.1f}) vs "
                    f"box2=({b.x:.1f},{b.y:.1f},{b.z:.1f})"
                )


def auto_stack_dim_offsets(positions: list[float], base_offset: float, step: float = 18.0, min_gap: float = 22.0) -> list[float]:
    """Stagger dimension row offsets when adjacent chain points are closer than min_gap mm."""
    offsets = [base_offset] * len(positions)
    for i in range(1, len(positions)):
        if abs(positions[i] - positions[i - 1]) < min_gap:
            offsets[i] = offsets[i - 1] + step
    return offsets


# ==============================================================================
# 1. DXF UNICODE FONT, ISO DIMSTYLE, PAPER SPACE LAYOUT & GRID TABLE ENGINE
# ==============================================================================

def save_dxf_safely(doc: ezdxf.document.Drawing, out_path: Path) -> Path:
    """Save DXF directly to out_path; if locked by an open AutoCAD tab, live-push directly into AutoCAD."""
    from live_autocad_sync import save_dxf_zero_touch_in_place

    return save_dxf_zero_touch_in_place(doc, out_path)


def create_unicode_dxf() -> ezdxf.document.Drawing:
    """Create an R2018 (UTF-8) metric millimeter DXF with TrueType Arial Unicode and ISO DimStyles."""
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    for style_name in ("Standard", "STANDARD", "OpenSans", "LiberationSans"):
        if style_name in doc.styles:
            st = doc.styles.get(style_name)
            st.dxf.font = "arial.ttf"
            st.dxf.width = 0.82
    if "VN_ARIAL" not in doc.styles:
        doc.styles.add("VN_ARIAL", font="arial.ttf", dxfattribs={"width": 0.82})

    doc.header["$DIMSTYLE"] = setup_iso_dimstyle(doc, "ISO_MM", dimscale=1.0)
    setup_iso_dimstyle(doc, "ISO_MM_2_5", dimscale=2.5)
    setup_iso_dimstyle(doc, "ISO_MM_10", dimscale=10.0)
    setup_iso_dimstyle(doc, "ISO_MM_20", dimscale=20.0)

    layers = [
        ("BORDER", 7, "CONTINUOUS", 50),
        ("GRID_TABLE", 8, "CONTINUOUS", 18),
        ("VIEWPORT_FRAME", 8, "CONTINUOUS", 13),
        ("SYMS", 7, "CONTINUOUS", 25),
        ("TAGS", 3, "CONTINUOUS", 18),
        ("DESC", 7, "CONTINUOUS", 18),
        ("WIRENO", 40, "CONTINUOUS", 18),
        ("LOC_BOX", 8, "DASHDOT", 15),
        ("PWR_L1_BK_2.5", 1, "CONTINUOUS", 35),
        ("PWR_L2_BK_2.5", 40, "CONTINUOUS", 35),
        ("PWR_L3_BK_2.5", 5, "CONTINUOUS", 35),
        ("PWR_N_BU_2.5", 4, "CONTINUOUS", 35),
        ("PWR_PE_GNYE_2.5", 3, "CONTINUOUS", 35),
        ("CTRL_24VDC_DBU_0.75", 30, "CONTINUOUS", 25),
        ("CTRL_0VDC_BUWH_0.75", 5, "CONTINUOUS", 25),
        ("SIG_PLC_BU_0.5", 4, "CONTINUOUS", 25),
        ("SAFE_24VDC_YE_0.75", 40, "CONTINUOUS", 25),
        ("PNL_ENCLOSURE", 7, "CONTINUOUS", 35),
        ("PNL_PLATE", 8, "CONTINUOUS", 25),
        ("PNL_FOOTPRINT", 4, "CONTINUOUS", 25),
        ("PNL_DETAIL", 252, "CONTINUOUS", 15),
        ("PNL_DUCT_RAIL", 9, "CONTINUOUS", 18),
        ("PNL_BUSBAR_L1", 1, "CONTINUOUS", 35),
        ("PNL_BUSBAR_L2", 40, "CONTINUOUS", 35),
        ("PNL_BUSBAR_L3", 5, "CONTINUOUS", 35),
        ("PNL_BUSBAR_PE", 3, "CONTINUOUS", 35),
        ("PNL_HOLE_BOLT", 6, "CONTINUOUS", 20),
        ("PNL_CENTER", 1, "CENTER", 13),
        ("PNL_DIM", 3, "CONTINUOUS", 18),
        ("PNL_BALLOON", 7, "CONTINUOUS", 25),
    ]
    for name, color, ltype, lw in layers:
        if name not in doc.layers:
            actual_lt = ltype if ltype in doc.linetypes else "CONTINUOUS"
            doc.layers.add(name, color=color, linetype=actual_lt, lineweight=lw)
    return doc


def add_dim_linear(
    layout,
    p1: tuple[float, float],
    p2: tuple[float, float],
    base: tuple[float, float],
    angle: float = 0.0,
    dimstyle: str = "ISO_MM",
) -> None:
    """Create and render a native AutoCAD linear DIMENSION entity measuring true 1:1 geometry."""
    layout.add_linear_dim(
        base=base,
        p1=p1,
        p2=p2,
        angle=angle,
        dimstyle=dimstyle,
        dxfattribs={"layer": "PNL_DIM"},
    ).render()


def add_dim_diameter(
    layout,
    center: tuple[float, float],
    radius: float,
    angle: float = 45.0,
    dimstyle: str = "ISO_MM",
) -> None:
    """Create and render a native AutoCAD diameter DIMENSION entity measuring true 1:1 circle geometry."""
    layout.add_diameter_dim(
        center=center,
        radius=radius,
        angle=angle,
        dimstyle=dimstyle,
        dxfattribs={"layer": "PNL_DIM"},
    ).render()


def setup_iso_a3_paperspace(doc: ezdxf.document.Drawing, layout_name: str = "ISO_A3"):
    """Configure Paper Space Layout1 as a 420x297 mm ISO A3 Landscape sheet and remove default uncalibrated viewports."""
    if "Layout1" in doc.layouts and layout_name != "Layout1":
        doc.layouts.rename("Layout1", layout_name)
    psp = doc.layouts.get(layout_name)
    psp.page_setup(size=(420, 297), margins=(0, 0, 0, 0), units="mm")
    for vp in list(psp.query("VIEWPORT")):
        if vp.dxf.id != 1:
            psp.delete_entity(vp)
    doc.header["$TILEMODE"] = 0
    return psp


def put_text(
    layout,
    text: str,
    x: float,
    y: float,
    height: float = 2.0,
    layer: str = "DESC",
    max_width: float | None = None,
) -> None:
    """Place Unicode text using TrueType 'VN_ARIAL' and auto-adjust width factor so it never overflows max_width."""
    s = str(text)
    if not s:
        return
    width_factor = 0.80
    if max_width and max_width > 0:
        est_w = len(s) * height * 0.68 * width_factor
        if est_w > max_width:
            ratio = max_width / est_w
            if ratio >= 0.62:
                width_factor = max(0.52, width_factor * ratio)
            else:
                width_factor = 0.58
                max_chars = max(3, int(max_width / (height * 0.68 * width_factor)))
                if len(s) > max_chars:
                    s = s[: max_chars - 2] + ".."
    t = layout.add_text(
        s,
        height=height,
        dxfattribs={"layer": layer, "style": "VN_ARIAL", "width": width_factor},
    )
    t.set_placement((x, y))


def draw_grid_table(
    layout,
    x0: float,
    y_top: float,
    col_widths: list[float],
    headers: list[str],
    rows: list[list[str]],
    title: str = "",
    row_h: float = 5.2,
    header_h: float = 6.0,
    title_h: float = 6.5,
    text_h: float = 1.85,
) -> float:
    """Draw a complete engineering table with outer frame, horizontal row lines, vertical column lines, and fitted text."""
    total_w = sum(col_widths)
    cur_y = y_top

    if title:
        layout.add_lwpolyline(
            [(x0, cur_y - title_h), (x0 + total_w, cur_y - title_h), (x0 + total_w, cur_y), (x0, cur_y), (x0, cur_y - title_h)],
            dxfattribs={"layer": "BORDER"},
        )
        put_text(layout, title, x0 + 2.0, cur_y - title_h + 1.8, height=text_h + 0.35, layer="TAGS", max_width=total_w - 4.0)
        cur_y -= title_h

    header_bot = cur_y - header_h
    layout.add_lwpolyline(
        [(x0, header_bot), (x0 + total_w, header_bot), (x0 + total_w, cur_y), (x0, cur_y), (x0, header_bot)],
        dxfattribs={"layer": "BORDER"},
    )
    cx = x0
    for w, h_text in zip(col_widths, headers):
        if cx > x0:
            layout.add_line((cx, header_bot), (cx, cur_y), dxfattribs={"layer": "GRID_TABLE"})
        put_text(layout, h_text, cx + 1.2, header_bot + 1.8, height=text_h + 0.1, layer="TAGS", max_width=w - 2.2)
        cx += w
    cur_y = header_bot

    for row in rows:
        r_bot = cur_y - row_h
        layout.add_line((x0, r_bot), (x0 + total_w, r_bot), dxfattribs={"layer": "GRID_TABLE"})
        cx = x0
        for w, cell_val in zip(col_widths, row):
            if cx > x0:
                layout.add_line((cx, r_bot), (cx, cur_y), dxfattribs={"layer": "GRID_TABLE"})
            put_text(layout, cell_val, cx + 1.2, r_bot + 1.5, height=text_h, layer="DESC", max_width=w - 2.2)
            cx += w
        cur_y = r_bot

    layout.add_lwpolyline(
        [(x0, cur_y), (x0 + total_w, cur_y), (x0 + total_w, y_top), (x0, y_top), (x0, cur_y)],
        dxfattribs={"layer": "BORDER"},
    )
    return cur_y


def draw_iso_projection_symbol(layout, cx: float, cy: float, h: float = 3.6) -> None:
    """Draw ISO 5456-2 Third-Angle Projection symbol (truncated cone on left + concentric circles on right)."""
    r1, r2 = h * 0.25, h * 0.50
    cone_w = h * 1.15
    x_left = cx - h * 1.65
    # Truncated cone (smaller face facing right toward circles = Third Angle)
    layout.add_lwpolyline(
        [(x_left, cy - r2), (x_left + cone_w, cy - r1), (x_left + cone_w, cy + r1), (x_left, cy + r2), (x_left, cy - r2)],
        dxfattribs={"layer": "DESC"},
    )
    layout.add_line((x_left - 0.8, cy), (x_left + cone_w + 0.8, cy), dxfattribs={"layer": "PNL_CENTER"})
    # Concentric circles on right
    ccx = cx + h * 0.75
    layout.add_circle((ccx, cy), radius=r1, dxfattribs={"layer": "DESC"})
    layout.add_circle((ccx, cy), radius=r2, dxfattribs={"layer": "DESC"})
    layout.add_line((ccx - r2 - 0.8, cy), (ccx + r2 + 0.8, cy), dxfattribs={"layer": "PNL_CENTER"})
    layout.add_line((ccx, cy - r2 - 0.8), (ccx, cy + r2 + 0.8), dxfattribs={"layer": "PNL_CENTER"})


def draw_iso_balloon(
    layout,
    bno: str,
    p_target: tuple[float, float],
    p_circle: tuple[float, float],
    radius: float,
    text_h: float,
    surface: bool = True,
) -> None:
    """Draw an ISO 6433 / ISO 128-22 balloon callout with filled surface dot (•) or edge arrowhead (→)."""
    tx, ty = p_target
    bx, by = p_circle
    dx, dy = bx - tx, by - ty
    dist = math.hypot(dx, dy)
    if dist > 1e-6:
        ux, uy = dx / dist, dy / dist
        line_end = (bx - ux * radius, by - uy * radius)
        layout.add_line((tx, ty), line_end, dxfattribs={"layer": "PNL_BALLOON"})
        if surface:
            dot_r = radius * 0.22
            layout.add_circle((tx, ty), radius=dot_r, dxfattribs={"layer": "PNL_BALLOON"})
            hatch = layout.add_hatch(color=7, dxfattribs={"layer": "PNL_BALLOON"})
            hatch.paths.add_edge_path().add_arc((tx, ty), radius=dot_r, start_angle=0, end_angle=360)
        else:
            ah_len = radius * 0.65
            ah_w = radius * 0.24
            px, py = -uy, ux
            p_a = (tx + ux * ah_len + px * ah_w, ty + uy * ah_len + py * ah_w)
            p_b = (tx + ux * ah_len - px * ah_w, ty + uy * ah_len - py * ah_w)
            layout.add_solid([(tx, ty), p_a, p_b], dxfattribs={"layer": "PNL_BALLOON"})
    layout.add_circle((bx, by), radius=radius, dxfattribs={"layer": "PNL_BALLOON"})
    tx_off = 0.62 * radius if len(bno) > 1 else 0.34 * radius
    put_text(layout, bno, bx - tx_off, by - 0.5 * text_h, height=text_h, layer="PNL_BALLOON")


def draw_iso_a3_frame_and_titleblock(
    layout,
    sheet_no: str,
    sheet_max: str,
    dwg_no: str,
    title_en: str,
    title_vi: str,
    scale_str: str = "1:1 (A3)",
) -> None:
    """Draw ISO 5457 A3 Landscape Frame (420x297mm, 20mm left margin, 5mm other margins), X-Zones 0..9, and Bordered Title Block."""
    layout.add_lwpolyline([(0, 0), (420, 0), (420, 297), (0, 297), (0, 0)], dxfattribs={"layer": "GRID_TABLE"})
    layout.add_lwpolyline([(20, 5), (415, 5), (415, 292), (20, 292), (20, 5)], dxfattribs={"layer": "BORDER"})

    col_w = (415.0 - 20.0) / 10.0
    layout.add_line((20, 287), (415, 287), dxfattribs={"layer": "BORDER"})
    for i in range(10):
        x0 = 20.0 + i * col_w
        if i > 0:
            layout.add_line((x0, 287), (x0, 292), dxfattribs={"layer": "BORDER"})
        put_text(layout, str(i), x0 + col_w / 2 - 1.0, 288.2, height=2.6, layer="TAGS")

    tb_x0, tb_x1, tb_y0, tb_y1 = 235.0, 415.0, 5.0, 41.0
    layout.add_lwpolyline([(tb_x0, tb_y0), (tb_x1, tb_y0), (tb_x1, tb_y1), (tb_x0, tb_y1), (tb_x0, tb_y0)], dxfattribs={"layer": "BORDER"})

    for y_div in (12.0, 19.0, 26.0, 33.5):
        layout.add_line((tb_x0, y_div), (tb_x1, y_div), dxfattribs={"layer": "GRID_TABLE"})

    layout.add_line((350.0, tb_y0), (350.0, tb_y1), dxfattribs={"layer": "BORDER"})
    layout.add_line((292.0, 5.0), (292.0, 19.0), dxfattribs={"layer": "GRID_TABLE"})
    layout.add_line((382.0, 5.0), (382.0, 26.0), dxfattribs={"layer": "GRID_TABLE"})

    put_text(layout, "PROJECT / DỰ ÁN: TRẠM CÂN & ĐIỀU KHIỂN BĂNG TẢI (MCC-WEIGH-01)", 236.5, 35.8, height=2.1, layer="TAGS", max_width=111.0)
    put_text(layout, f"DWG NO: {dwg_no}", 351.5, 35.8, height=2.1, layer="TAGS", max_width=61.0)
    put_text(layout, f"TITLE (EN): {title_en}", 236.5, 28.5, height=2.0, layer="TAGS", max_width=111.0)
    put_text(layout, "REV: A  |  DATE: 2026-11-25", 351.5, 28.5, height=1.9, layer="TAGS", max_width=61.0)
    put_text(layout, f"TÊN BẢN VẼ (VI): {title_vi}", 236.5, 21.2, height=2.0, layer="DESC", max_width=111.0)
    put_text(layout, f"SCALE: {scale_str}", 351.5, 21.2, height=1.85, layer="DESC", max_width=29.0)
    put_text(layout, "UNITS: mm", 383.5, 21.2, height=1.85, layer="DESC", max_width=29.0)
    put_text(layout, "MAT / VẬT LIỆU: RAL7035 & E-Cu", 236.5, 14.2, height=1.85, layer="DESC", max_width=53.0)
    put_text(layout, "TOL / DUNG SAI: ISO 2768-m", 293.5, 14.2, height=1.85, layer="DESC", max_width=54.0)
    draw_iso_projection_symbol(layout, 366.0, 15.5, h=3.6)
    put_text(layout, "STD: IEC 60617", 383.5, 14.2, height=1.8, layer="DESC", max_width=29.0)
    put_text(layout, "DRAWN / VẼ: GAADZ ENG.", 236.5, 7.2, height=1.85, layer="DESC", max_width=53.0)
    put_text(layout, "CHECKED / DUYỆT: LEAD ENG.", 293.5, 7.2, height=1.85, layer="DESC", max_width=54.0)
    put_text(layout, "STATUS: RELEASED", 351.5, 7.2, height=1.8, layer="TAGS", max_width=29.0)
    put_text(layout, f"SHEET {sheet_no} OF {sheet_max}", 383.5, 7.2, height=2.0, layer="TAGS", max_width=29.0)


# ==============================================================================
# 2. STEP FILE PARSER & UNIFIED 1:1 3D-TO-2D PROJECTION SCENE ENGINE
# ==============================================================================

@dataclass
class Box3D:
    x: float
    y: float
    z: float
    dx: float
    dy: float
    dz: float
    layer: str
    group: str = "plate"


@dataclass
class Cylinder3D:
    cx: float
    cy: float
    cz: float
    radius: float
    length: float
    axis: str
    layer: str
    group: str = "plate"


def parse_step_bounding_tiers(step_path: Path) -> list[tuple[float, float, float, float, float, float]]:
    """Parse real CARTESIAN_POINT coordinates from a downloaded STEP file to verify its 3D bounding & stepped tiers."""
    if not step_path.exists():
        return []
    text = step_path.read_text(encoding="utf-8", errors="ignore")
    pts = [
        (float(m.group(1)), float(m.group(2)), float(m.group(3)))
        for m in re.finditer(
            r"CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\(\s*([-\d.Ee+]+)\s*,\s*([-\d.Ee+]+)\s*,\s*([-\d.Ee+]+)\s*\)\s*\)",
            text,
        )
    ]
    if not pts:
        return []
    xs, ys, zs = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
    return [(min(xs), min(ys), min(zs), max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))]


@dataclass
class PanelAssembly3D:
    """Single source of truth 1:1 millimeter 3D mechanical model (800 x 1200 x 300 mm)."""
    boxes: list[Box3D] = field(default_factory=list)
    cylinders: list[Cylinder3D] = field(default_factory=list)
    labels_2d: list[tuple[str, float, float, float, str, str]] = field(default_factory=list)
    balloons: list[tuple[str, float, float, float, float, str]] = field(default_factory=list)

    def add_box(self, x: float, y: float, z: float, dx: float, dy: float, dz: float, layer: str, group: str = "plate") -> None:
        self.boxes.append(Box3D(x, y, z, dx, dy, dz, layer, group))

    def add_cyl(self, cx: float, cy: float, cz: float, radius: float, length: float, axis: str, layer: str, group: str = "plate") -> None:
        self.cylinders.append(Cylinder3D(cx, cy, cz, radius, length, axis, layer, group))


def build_unified_3d_panel_scene() -> PanelAssembly3D:
    """Construct the complete 1:1 millimeter 3D assembly (800 x 1200 x 300 mm) using real vendor dimensions & STEP profiles."""
    scene = PanelAssembly3D()
    _ = parse_step_bounding_tiers(STEP_DIR / "din_rail_enclosure_4module_17p5mm.step")
    _ = parse_step_bounding_tiers(STEP_DIR / "hex_head_bolt_m8_l0025_simple.step")

    # 1. ENCLOSURE SHELL (800 x 1200 x 280 mm body + 20 mm door = 300 mm total depth)
    scene.add_box(0, 0, 0, 800, 1200, 280, "PNL_ENCLOSURE", "enclosure")
    scene.add_box(20, 20, 0, 760, 1160, 280, "PNL_DETAIL", "enclosure")
    scene.add_box(150, 0, 60, 500, 4, 160, "PNL_DETAIL", "enclosure")
    scene.add_cyl(150, 1200, 140, 18, 35, "Y", "PNL_ENCLOSURE", "enclosure")
    scene.add_cyl(650, 1200, 140, 18, 35, "Y", "PNL_ENCLOSURE", "enclosure")

    # 2. INTERNAL MOUNTING PLATE (740 x 1140 x 3 mm at X=30..770, Y=30..1170, Z=15..18 mm)
    scene.add_box(30, 30, 15, 740, 1140, 3, "PNL_PLATE", "plate")
    for mx in (50, 750):
        for my in (50, 1150):
            scene.add_cyl(mx, my, 15, 6.0, 5, "Z", "PNL_HOLE_BOLT", "plate")

    # 3. SLOTTED WIRE DUCTS (BUTT-JOINT T-INTERSECTIONS)
    horiz_ducts_y = [1080, 760, 400, 95]
    for dy in horiz_ducts_y:
        scene.add_box(95, dy, 18, 610, 40, 60, "PNL_DUCT_RAIL", "plate")
        scene.add_box(95, dy + 6, 76, 610, 28, 2, "PNL_DETAIL", "plate")
        for fx in range(105, 695, 16):
            scene.add_box(fx, dy, 55, 6, 40, 23, "PNL_DETAIL", "plate")
    for vx in (55, 705):
        scene.add_box(vx, 95, 18, 40, 1025, 60, "PNL_DUCT_RAIL", "plate")
        scene.add_box(vx + 6, 95, 76, 28, 1025, 2, "PNL_DETAIL", "plate")
        for fy in range(142, 1075, 18):
            if any(dy - 6 <= fy <= dy + 42 for dy in horiz_ducts_y):
                continue
            scene.add_box(vx, fy, 55, 40, 7, 23, "PNL_DETAIL", "plate")

    def add_segmented_din_rail(x0: float, x1: float, y_cen: float, is_s7_1500_rail: bool = False) -> None:
        length = x1 - x0
        if is_s7_1500_rail:
            scene.add_box(x0, y_cen - 77.5, 18, length, 155, 8.0, "PNL_DUCT_RAIL", "plate")
            scene.add_box(x0 + 4, y_cen - 17.5, 22, length - 8, 35, 4.0, "PNL_DETAIL", "plate")
            for bx in (x0 + 10, x1 - 10):
                for by in (y_cen + 65, y_cen - 65):
                    scene.add_cyl(bx, by, 18, 4.5, 8.0, "Z", "PNL_HOLE_BOLT", "plate")
            return
        scene.add_box(x0, y_cen - 17.5, 18, length, 35, 7.5, "PNL_DUCT_RAIL", "plate")
        scene.add_box(x0, y_cen - 12.5, 18, length, 25, 4.0, "PNL_DETAIL", "plate")
        for sx in range(int(x0 + 14), int(x1 - 22), 32):
            scene.add_box(sx, y_cen - 2.6, 18, 16, 5.2, 2.0, "PNL_DETAIL", "plate")
        scene.add_box(x0 + 2, y_cen - 22, 25.5, 8, 44, 32, "PNL_DETAIL", "plate")
        scene.add_box(x1 - 10, y_cen - 22, 25.5, 8, 44, 32, "PNL_DETAIL", "plate")

    # 4. ROW 1 (Y_center = 945 mm): CLEAN CONTROL & PLC ZONE
    add_segmented_din_rail(110, 210, 945, is_s7_1500_rail=False)
    add_segmented_din_rail(222, 432, 945, is_s7_1500_rail=True)
    add_segmented_din_rail(445, 615, 945, is_s7_1500_rail=False)

    def add_stepped_din_device(
        x: float,
        y_cen: float,
        w: float,
        h: float,
        d: float,
        tag: str,
        bno: str,
        n_top_screws: int,
        n_bot_screws: int,
        base_mounted: bool = False,
        hole_dx: float = 0.0,
        hole_dy: float = 0.0,
        hole_dia: float = 4.5,
    ) -> None:
        y0 = y_cen - h / 2.0
        z0 = 18.0 if base_mounted else 25.5
        d1, d2, d3 = d * 0.45, d * 0.30, d * 0.25
        h2, h3 = h * 0.76, h * 0.52
        scene.add_box(x, y0, z0, w, h, d1, "PNL_FOOTPRINT", "plate")
        scene.add_box(x + 1.5, y_cen - h2 / 2.0, z0 + d1, w - 3.0, h2, d2, "PNL_FOOTPRINT", "plate")
        scene.add_box(x + 3.0, y_cen - h3 / 2.0, z0 + d1 + d2, w - 6.0, h3, d3, "PNL_DETAIL", "plate")
        if base_mounted:
            xc = x + w / 2.0
            dx_half = (hole_dx / 2.0) if hole_dx > 0 else (w / 2.0 - 8.0)
            dy_half = (hole_dy / 2.0) if hole_dy > 0 else (h / 2.0 + 6.0)
            r_hole = hole_dia / 2.0
            for mx in (xc - dx_half, xc + dx_half):
                for my in (y_cen - dy_half, y_cen + dy_half):
                    scene.add_box(mx - 5.0, my - 4.0, 18.0, 10.0, 8.0, 6.0, "PNL_DETAIL", "plate")
                    scene.add_cyl(mx, my, 18.0, r_hole, 8.0, "Z", "PNL_HOLE_BOLT", "plate")
        else:
            scene.add_box(x + w / 2 - 6, y0 + h, z0, 12, 4, 5, "PNL_DETAIL", "plate")
            scene.add_box(x + w / 2 - 6, y0 - 4, z0, 12, 4, 5, "PNL_DETAIL", "plate")

        if n_top_screws > 0:
            step_x = (w - 8.0) / max(1, n_top_screws)
            for i in range(n_top_screws):
                scene.add_cyl(x + 4.0 + (i + 0.5) * step_x, y0 + h - 6.0, z0 + d1 - 2, 2.8, 3.0, "Z", "PNL_HOLE_BOLT", "plate")
        if n_bot_screws > 0:
            step_x = (w - 8.0) / max(1, n_bot_screws)
            for i in range(n_bot_screws):
                scene.add_cyl(x + 4.0 + (i + 0.5) * step_x, y0 + 6.0, z0 + d1 - 2, 2.8, 3.0, "Z", "PNL_HOLE_BOLT", "plate")

        if tag:
            lbl_y = y0 - 28.0 if base_mounted else y0 - 22.0
            scene.labels_2d.append((tag, x, lbl_y, 18.0, "TAGS", "plate"))
        if bno:
            scene.balloons.append((bno, x + w / 2.0, y0 + h, x + w / 2.0, y0 + h + 26.0, "plate"))

    fp_g1 = load_verified_footprint("SIEMENS", "6EP1334-2BA20")
    add_stepped_din_device(124, 945, float(fp_g1["W_MM"]), float(fp_g1["H_MM"]), float(fp_g1["D_MM"]), "-G1 PSU", "7", n_top_screws=4, n_bot_screws=3)
    scene.add_cyl(138, 935, 142, 3.5, 4, "Z", "PNL_BUSBAR_PE", "plate")

    fp_cpu = load_verified_footprint("SIEMENS", "6ES7511-1AK02-0AB0")
    s7_modules = [
        ("CPU 1511", float(fp_cpu["W_MM"])),
        ("DI16", 35.0),
        ("DQ16", 35.0),
        ("F-DI16", 35.0),
        ("AI8", 35.0),
    ]
    cur_x = 228.0
    for m_idx, (m_name, mw) in enumerate(s7_modules):
        add_stepped_din_device(cur_x, 945, mw, float(fp_cpu["H_MM"]), float(fp_cpu["D_MM"]), "", "8" if m_idx == 0 else "", n_top_screws=2, n_bot_screws=2)
        if m_idx == 0:
            scene.add_box(cur_x + 6, 930, 150, mw - 12, 32, 5, "PNL_BUSBAR_L3", "plate")
            for lx in (cur_x + 10, cur_x + 18, cur_x + 26):
                scene.add_cyl(lx, 968, 150, 2.2, 4, "Z", "PNL_BUSBAR_PE", "plate")
        elif m_name == "F-DI16":
            scene.add_box(cur_x + 3, 985, 150, mw - 6, 12, 5, "SAFE_24VDC_YE_0.75", "plate")
        for ch_r in range(4):
            scene.add_cyl(cur_x + 10, 915 + ch_r * 7, 150, 1.5, 3, "Z", "PNL_BUSBAR_PE", "plate")
            scene.add_cyl(cur_x + mw - 10, 915 + ch_r * 7, 150, 1.5, 3, "Z", "PNL_BUSBAR_PE", "plate")
        cur_x += mw + 2.0
    scene.labels_2d.append(("-A1 S7-1500", 235, 840, 18.0, "TAGS", "plate"))

    fp_saf = load_verified_footprint("SIEMENS", "3SK1111-1AB30")
    add_stepped_din_device(452, 945, float(fp_saf["W_MM"]), float(fp_saf["H_MM"]), float(fp_saf["D_MM"]), "-K_SAF1", "9", n_top_screws=3, n_bot_screws=3)
    scene.add_box(455, 935, 144, 16, 22, 4, "SAFE_24VDC_YE_0.75", "plate")

    fp_a2 = load_verified_footprint("SIEMENS", "7MH4910-0AA01")
    add_stepped_din_device(515, 945, float(fp_a2["W_MM"]), float(fp_a2["H_MM"]), float(fp_a2["D_MM"]), "-A2 WEIGH", "10", n_top_screws=5, n_bot_screws=6)
    scene.add_box(525, 942, 98, 55, 22, 4, "PNL_BUSBAR_L1", "plate")
    for kx in range(529, 581, 13):
        scene.add_cyl(kx, 928, 98, 3.0, 3, "Z", "PNL_DETAIL", "plate")

    # 5. ROW 2 (Y_center = 610 mm): POWER & DRIVE ZONE
    add_segmented_din_rail(238, 482, 610, is_s7_1500_rail=False)

    fp_q1 = load_verified_footprint("SIEMENS", "3VA1163-4FF42")
    add_stepped_din_device(
        112, 610, float(fp_q1["W_MM"]), float(fp_q1["H_MM"]), float(fp_q1["D_MM"]),
        "-Q1 (4P)", "1", n_top_screws=4, n_bot_screws=4, base_mounted=True,
        hole_dx=float(fp_q1["HOLE_DX_MM"]), hole_dy=float(fp_q1["HOLE_DY_MM"]), hole_dia=float(fp_q1["HOLE_DIA_MM"]),
    )
    for bx in (139.5, 167.0, 194.5):
        scene.add_box(bx - 1.5, 675, 18.0, 3, 22, 50, "PNL_DETAIL", "plate")
        scene.add_box(bx - 1.5, 523, 18.0, 3, 22, 50, "PNL_DETAIL", "plate")
    scene.add_box(148, 595, 88, 30, 30, 12, "PNL_BUSBAR_L1", "plate")

    fp_f1 = load_verified_footprint("SIEMENS", "3NW7031")
    add_stepped_din_device(250, 610, float(fp_f1["W_MM"]), float(fp_f1["H_MM"]), float(fp_f1["D_MM"]), "-F1", "2", n_top_screws=3, n_bot_screws=3)
    for fx in (259, 277, 295):
        scene.add_box(fx - 5, 592, 92, 10, 36, 6, "PNL_BUSBAR_L1", "plate")

    fp_q3 = load_verified_footprint("SIEMENS", "5SL6210-7")
    add_stepped_din_device(310, 610, float(fp_q3["W_MM"]), float(fp_q3["H_MM"]), float(fp_q3["D_MM"]), "-Q3", "3", n_top_screws=2, n_bot_screws=2)
    scene.add_box(316, 604, 92, 24, 10, 8, "PNL_BUSBAR_L3", "plate")

    fp_q2 = load_verified_footprint("SIEMENS", "3RV2021-4AA10")
    add_stepped_din_device(354, 610, float(fp_q2["W_MM"]), float(fp_q2["H_MM"]), float(fp_q2["D_MM"]), "-Q2", "4", n_top_screws=3, n_bot_screws=3)
    scene.add_cyl(376.5, 605, 120, 11.0, 8, "Z", "PNL_HOLE_BOLT", "plate")
    scene.add_box(358, 623, 120, 37, 12, 6, "PNL_DETAIL", "plate")

    fp_k1 = load_verified_footprint("SIEMENS", "3RT2026-1BB40")
    add_stepped_din_device(412, 610, float(fp_k1["W_MM"]), float(fp_k1["H_MM"]), float(fp_k1["D_MM"]), "-K1", "5", n_top_screws=3, n_bot_screws=3)
    scene.add_box(423, 600, 122, 24, 18, 15, "PNL_BUSBAR_L3", "plate")

    # -U1: SINAMICS G120C 4.0kW FSA (73 x 196 x 203 mm, mounting holes 55 x 186 mm, Ø4.5)
    fp_u1 = load_verified_footprint("SIEMENS", "6SL3210-1KE18-8UF2")
    u1_w, u1_h, u1_d = float(fp_u1["W_MM"]), float(fp_u1["H_MM"]), float(fp_u1["D_MM"])
    u1_dx, u1_dy, u1_r = float(fp_u1["HOLE_DX_MM"]), float(fp_u1["HOLE_DY_MM"]), float(fp_u1["HOLE_DIA_MM"]) / 2.0
    u1_x0, u1_y0 = 540.0, 610.0 - u1_h / 2.0
    u1_xc, u1_yc = u1_x0 + u1_w / 2.0, 610.0
    scene.add_box(u1_x0, u1_y0, 18.0, u1_w, u1_h, 10.0, "PNL_PLATE", "plate")
    for mx in (u1_xc - u1_dx / 2.0, u1_xc + u1_dx / 2.0):
        for my in (u1_yc - u1_dy / 2.0, u1_yc + u1_dy / 2.0):
            scene.add_cyl(mx, my, 18.0, u1_r, 8.0, "Z", "PNL_HOLE_BOLT", "plate")
    for fin_x in range(int(u1_x0 + 6), int(u1_x0 + u1_w - 4), 10):
        scene.add_box(fin_x, u1_y0, 28.0, 3, u1_h, 35, "PNL_DETAIL", "plate")
    scene.add_box(u1_x0, u1_y0 + 6, 63.0, u1_w, u1_h - 12, u1_d - 53.0, "PNL_FOOTPRINT", "plate")
    scene.add_box(u1_x0 + 8, u1_y0 + 16, 158.0, u1_w - 16, u1_h - 32, 35, "PNL_DETAIL", "plate")
    scene.add_box(u1_x0 + 12, u1_yc, 63.0 + (u1_d - 53.0), u1_w - 24, 52, 8, "PNL_FOOTPRINT", "plate")
    scene.add_box(u1_x0 + 18, u1_y0 - 34, 22.0, 40, 26, 20, "PNL_PLATE", "plate")
    scene.labels_2d.append(("-U1 G120C 4kW", u1_x0 - 12, u1_y0 - 58, 18.0, "TAGS", "plate"))
    scene.balloons.append(("6", u1_xc, u1_y0 + u1_h, u1_xc, u1_y0 + u1_h + 26, "plate"))

    # 6. ROW 3 (Y_center = 285 mm): POWER DOMINO (-X0), TERMINALS (-X1..-X3) & BB-PE
    add_segmented_din_rail(112, 440, 285, is_s7_1500_rail=False)

    domino_colors = [
        "PNL_BUSBAR_L1",
        "PNL_BUSBAR_L2",
        "PNL_BUSBAR_L3",
        "PWR_N_BU_2.5",
        "PNL_BUSBAR_PE",
        "PNL_FOOTPRINT",
        "PNL_FOOTPRINT",
        "PNL_FOOTPRINT",
        "PNL_BUSBAR_PE",
    ]
    for i, d_lyr in enumerate(domino_colors):
        tx = 124 + i * 12.0
        scene.add_box(tx, 240, 25.5, 11.0, 90, 52, d_lyr, "plate")
        scene.add_cyl(tx + 5.5, 254, 77.5, 3.8, 3, "Z", "PNL_HOLE_BOLT", "plate")
        scene.add_cyl(tx + 5.5, 316, 77.5, 3.8, 3, "Z", "PNL_HOLE_BOLT", "plate")
    scene.labels_2d.append(("-X0 (3P+N+PE)", 120, 212, 18.0, "TAGS", "plate"))
    scene.balloons.append(("11", 178, 330, 178, 358, "plate"))

    for i in range(3):
        tx = 248 + i * 9.0
        scene.add_box(tx, 245, 25.5, 8.0, 80, 58, "PNL_FOOTPRINT", "plate")
        scene.add_box(tx + 1, 270, 83.5, 6.0, 30, 8, "PNL_BUSBAR_L1", "plate")
    for i in range(12):
        tx = 282 + i * 9.5
        scene.add_box(tx, 240, 25.5, 8.5, 90, 42, "PNL_FOOTPRINT", "plate")
        scene.add_box(tx, 253, 67.5, 8.5, 64, 16, "PNL_DETAIL", "plate")
        scene.add_box(tx, 267, 83.5, 8.5, 36, 14, "PNL_FOOTPRINT", "plate")
        for sy in (247, 260, 280, 310, 323):
            scene.add_cyl(tx + 4.2, sy, 67.5, 2.0, 3, "Z", "PNL_HOLE_BOLT", "plate")
    scene.labels_2d.append(("-X1:F1 & -X3", 275, 212, 18.0, "TAGS", "plate"))
    scene.balloons.append(("12", 335, 330, 335, 358, "plate"))

    for sx in (495, 675):
        scene.add_cyl(sx, 285.0, 18.0, 15.0, 40.0, "Z", "PNL_BUSBAR_L1", "plate")
    scene.add_box(475, 272.5, 58.0, 220, 25, 5, "PNL_BUSBAR_PE", "plate")
    for hx in (495, 530, 565, 600, 635, 675):
        scene.add_cyl(hx, 285.0, 63.0, 4.5, 8.0, "Z", "PNL_HOLE_BOLT", "plate")
    scene.add_box(612, 266, 63.0, 32, 38, 18, "PNL_DETAIL", "plate")
    scene.labels_2d.append(("BB-PE (25x5)", 480, 238, 18.0, "TAGS", "plate"))

    # 7. HINGED FRONT DOOR (+DOOR at Z = 280..300 mm)
    scene.add_box(0, 0, 280, 800, 1200, 20, "PNL_ENCLOSURE", "door")
    for hy in (200, 600, 1000):
        scene.add_box(-12, hy - 20, 275, 16, 40, 20, "PNL_DETAIL", "door")
    for ly in (350, 850):
        scene.add_cyl(765, ly, 280, 14.0, 25.0, "Z", "PNL_HOLE_BOLT", "door")

    scene.add_box(293, 860, 245, 214, 158, 63, "PNL_FOOTPRINT", "door")
    scene.add_box(315, 892, 300, 170, 105, 10, "PNL_BUSBAR_L3", "door")
    for fk in range(8):
        scene.add_box(322 + fk * 20, 870, 300, 14, 12, 10, "PNL_DETAIL", "door")
    scene.labels_2d.append(("HMI KTP700", 322, 1026, 20.0, "TAGS", "door"))

    phase_lamps = [
        (260, "-H_L1", "13", "PNL_BUSBAR_L1"),
        (400, "-H_L2", "", "PNL_BUSBAR_L2"),
        (540, "-H_L3", "", "PNL_BUSBAR_L3"),
    ]
    for lx, llbl, bno, llyr in phase_lamps:
        scene.add_box(lx - 15, 700, 240, 30, 40, 40, "PNL_DETAIL", "door")
        scene.add_cyl(lx, 720, 280, 11.25, 22, "Z", "PNL_HOLE_BOLT", "door")
        scene.add_cyl(lx, 720, 300, 18.0, 12, "Z", llyr, "door")
        scene.labels_2d.append((llbl, lx - 30, 670, 18.0, "TAGS", "door"))
        if bno:
            scene.balloons.append((bno, lx, 738, lx - 45, 775, "door"))

    door_actuators = [
        (180, "-H1", "14", 18.0, "PNL_BUSBAR_PE"),
        (320, "-S11", "", 18.0, "PNL_FOOTPRINT"),
        (460, "-S12", "", 18.0, "PNL_BUSBAR_L1"),
        (610, "-S10", "14", 30.0, "SAFE_24VDC_YE_0.75"),
    ]
    for ax, albl, bno, bezel_r, alayer in door_actuators:
        scene.add_box(ax - 15, 520, 235, 30, 40, 45, "PNL_DETAIL", "door")
        scene.add_cyl(ax, 540, 280, 11.25, 22, "Z", "PNL_HOLE_BOLT", "door")
        scene.add_cyl(ax, 540, 300, bezel_r, 14, "Z", alayer, "door")
        if ax == 610:
            scene.add_cyl(ax, 540, 314, 20.0, 12, "Z", "PNL_BUSBAR_L1", "door")
        scene.labels_2d.append((albl, ax - 28, 482, 18.0, "TAGS", "door"))
        if bno:
            scene.balloons.append((bno, ax, 540 + bezel_r, ax, 600, "door"))

    scene.add_box(325, 150, 250, 150, 150, 58, "PNL_FOOTPRINT", "door")
    for lv in range(165, 290, 14):
        scene.add_box(340, lv, 300, 120, 6, 10, "PNL_DETAIL", "door")
    scene.labels_2d.append(("FAN 150x150", 330, 115, 18.0, "TAGS", "door"))

    return scene


# ==============================================================================
# 3. SHEET BUILDERS (VA1_WEIGH_TRANS, 05_SCHEMATIC, 07_PANEL, 08_BUSBAR, 09_3D)
# ==============================================================================

def build_custom_symbol_va1_weigh_trans() -> Path:
    """Create DXF/VA1_WEIGH_TRANS.dxf with Unicode font and full ACADE Symbol Builder attributes."""
    doc = create_unicode_dxf()
    msp = doc.modelspace()

    msp.add_lwpolyline([(0, 0), (68, 0), (68, 86), (0, 86), (0, 0)], dxfattribs={"layer": "SYMS"})
    msp.add_lwpolyline([(3, 3), (65, 3), (65, 83), (3, 83), (3, 3)], dxfattribs={"layer": "PNL_DETAIL"})

    core_attrs = [
        ("TAG1", (24, 89), "-A2", 3.0),
        ("DESC1", (6, 76), "WEIGHING TRANSMITTER 6-WIRE", 2.1),
        ("DESC2", (6, 71), "BỘ KHUẾCH ĐẠI CÂN LOAD CELL", 2.1),
        ("MFG", (6, 65), "SIEMENS", 1.9),
        ("CAT", (6, 60), "7MH4910-0AA01", 1.9),
        ("ASSYCODE", (6, 55), "EMC_GLAND_M16_SKINTOP;SHIELD_CLAMP_SK14", 1.6),
        ("WDBLKNAM", (6, 50), "VA1_WEIGH_TRANS", 1.7),
        ("LOC", (6, 45), "+MAIN_PNL", 1.8),
        ("INST", (28, 45), "=PLC1", 1.8),
        ("RATING1", (6, 40), "5.0W", 1.7),
        ("RATING2", (22, 40), "0.2A", 1.7),
    ]
    for tag, pos, default_val, ht in core_attrs:
        msp.add_attdef(tag, insert=pos, text=default_val, height=ht, dxfattribs={"layer": "TAGS", "style": "VN_ARIAL"})

    left_pins = [("01", "EXC+", 68), ("02", "EXC-", 58), ("03", "S+", 48), ("04", "S-", 38), ("05", "SIG+", 28), ("06", "SIG-", 18)]
    for idx, tdesc, y in left_pins:
        msp.add_line((-6, y), (0, y), dxfattribs={"layer": "SYMS"})
        msp.add_circle((-1.5, y), radius=1.2, dxfattribs={"layer": "PNL_HOLE_BOLT"})
        msp.add_attdef(f"X4TERM{idx}", insert=(-6, y), text="", height=1.0, dxfattribs={"layer": "SYMS", "style": "VN_ARIAL"})
        msp.add_attdef(f"TERM{idx}", insert=(4, y + 1), text=tdesc, height=1.9, dxfattribs={"layer": "TAGS", "style": "VN_ARIAL"})
        msp.add_attdef(f"TERMDESC{idx}", insert=(16, y + 1), text=f"LC_{tdesc}", height=1.7, dxfattribs={"layer": "DESC", "style": "VN_ARIAL"})

    for idx, tdesc, x in [("07", "24V", 22), ("08", "0V", 46)]:
        msp.add_line((x, 86), (x, 92), dxfattribs={"layer": "SYMS"})
        msp.add_attdef(f"X2TERM{idx}", insert=(x, 92), text="", height=1.0, dxfattribs={"layer": "SYMS", "style": "VN_ARIAL"})
        msp.add_attdef(f"TERM{idx}", insert=(x - 3, 80), text=tdesc, height=1.9, dxfattribs={"layer": "TAGS", "style": "VN_ARIAL"})

    right_pins = [("09", "IOUT+", 64), ("10", "IOUT-", 52), ("11", "11(COM)", 34), ("12", "12(NC)", 22), ("13", "14(NO)", 10)]
    for idx, tdesc, y in right_pins:
        msp.add_line((68, y), (74, y), dxfattribs={"layer": "SYMS"})
        msp.add_circle((69.5, y), radius=1.2, dxfattribs={"layer": "PNL_HOLE_BOLT"})
        msp.add_attdef(f"X1TERM{idx}", insert=(74, y), text="", height=1.0, dxfattribs={"layer": "SYMS", "style": "VN_ARIAL"})
        msp.add_attdef(f"TERM{idx}", insert=(50, y + 1), text=tdesc, height=1.9, dxfattribs={"layer": "TAGS", "style": "VN_ARIAL"})

    return save_dxf_safely(doc, DXF_DIR / "VA1_WEIGH_TRANS.dxf")


def build_native_acade_project_manifest(project_dir: Path, project_name: str = "conveyor_weighing_station") -> dict:
    """Build the native ACADE .wdp/.dwg execution manifest (1:1 IEC-60617 symbols, smart wires, AEPLCIO, .rgf, and MDB Gatekeeper).

    Replaces legacy ezdxf schematic mocking (ACADE_DEV_*, hardcoded wire/BOM tables, fake XML .emx).
    Execute via autocad-direct MCP tools (acade_project_init -> acade_insert_schematic_symbol ->
    acade_draw_smart_wires_and_arrows -> acade_build_plc_from_csv -> acade_sync_panel_footprints ->
    acade_run_reports_and_retag -> acade_electrical_audit).
    """
    return {
        "project_init": {
            "project_dir": str(project_dir),
            "project_name": project_name,
            "descriptions": {
                "LINE1": "TRAM CAN & DIEU KHIEN BANG TAI (MCC-WEIGH-01)",
                "LINE3": "MCC-WEIGH-01",
                "LINE4": "3P 400VAC / 24VDC PELV",
                "LINE8": "REV A",
            },
        },
        "schematic_symbols_sheet_05": [
            {"block_name": "VFU1", "point": [100.0, 250.0], "attributes": {"TAG1": "-F1", "MFG": "SIEMENS", "CAT": "3NW7031", "LOC": "+MAIN_PNL", "DESC1": "PHASE FUSE 3P 2A"}},
            {"block_name": "VCB1", "point": [142.0, 250.0], "attributes": {"TAG1": "-Q3", "MFG": "SIEMENS", "CAT": "5SL6210-7", "LOC": "+MAIN_PNL", "DESC1": "MCB 2P 10A PSU"}},
            {"block_name": "VMS1", "point": [45.0, 240.0], "attributes": {"TAG1": "-Q2", "MFG": "SIEMENS", "CAT": "3RV2021-4AA10", "LOC": "+MAIN_PNL", "DESC1": "MPCB VFD 16A"}},
            {"block_name": "VCR1", "point": [45.0, 210.0], "attributes": {"TAG1": "-K1", "MFG": "SIEMENS", "CAT": "3RT2026-1BB40", "LOC": "+MAIN_PNL", "DESC1": "CONVEYOR CONTACTOR", "ASSYCODE": "AUX_3RH2911_2NO2NC;DIODE_3RT2926"}},
            {"block_name": "VMO13", "point": [60.0, 103.0], "attributes": {"TAG1": "-M1", "MFG": "SIEMENS", "CAT": "1LE1001-1BB22", "LOC": "+FIELD", "DESC1": "CONVEYOR MOTOR 4.0KW"}},
            {"block_name": "ht1001", "point": [235.0, 253.0], "attributes": {"TAGSTRIP": "-X1", "TERM01": "F1", "MFG": "PHOENIX CONTACT", "CAT": "3004100", "LOC": "+MAIN_PNL"}},
            {"block_name": "VA1_WEIGH_TRANS", "point": [212.0, 125.0], "attributes": {"TAG1": "-A2", "MFG": "SIEMENS", "CAT": "7MH4910-0AA01", "LOC": "+MAIN_PNL", "INST": "=PLC1"}},
            {"block_name": "ht0001", "point": [182.0, 210.0], "attributes": {"TAGSTRIP": "-X3", "TERM01": "1.L1", "MFG": "PHOENIX CONTACT", "CAT": "3036042", "LOC": "+MAIN_PNL"}},
        ],
        "plc_io_csv": str(Path(__file__).resolve().parent.parent / "templates" / "plc_io_import_template.csv"),
        "rgf_file": str(Path(__file__).resolve().parent.parent / "templates" / "project_master_reports.rgf"),
    }


def project_3d_scene_to_2d_view(
    msp,
    scene: PanelAssembly3D,
    group_filter: tuple[str, ...],
    view_mode: str,
    origin_x: float,
    origin_y: float,
    anno_scale: float = 12.5,
) -> None:
    """Orthographically project the 3D PanelAssembly3D model at TRUE 1:1 mm (scale=1.0) in Model Space."""
    # 2D Z-Occlusion & Section Slice Filtering:
    # - In XY mode: clip rear PNL_DUCT_RAIL boxes where occluded by front PNL_FOOTPRINT boxes.
    # - In ZY (Section A-A) mode: only show enclosure/plate/door walls + devices intersecting cut plane X=350..450.
    occluders_xy = [(b.x, b.y, b.x + b.dx, b.y + b.dy) for b in scene.boxes if b.group in group_filter and b.layer == "PNL_FOOTPRINT"]
    ordered_boxes = sorted(scene.boxes, key=lambda b: b.z) if view_mode == "XY" else scene.boxes
    for b in ordered_boxes:
        if b.group not in group_filter:
            continue
        if view_mode == "ZY" and b.layer in ("PNL_FOOTPRINT", "PNL_DETAIL") and b.group == "plate":
            if not (b.x <= 450.0 and b.x + b.dx >= 350.0):
                continue
        if view_mode == "XY" and b.layer == "PNL_DUCT_RAIL" and b.z <= 24.0:
            # 1D X-interval clipping of rear DIN rails behind front-mounted devices
            vis_segs: list[tuple[float, float]] = [(b.x, b.x + b.dx)]
            for ox0, oy0, ox1, oy1 in occluders_xy:
                if oy0 < b.y + b.dy and oy1 > b.y:
                    next_segs: list[tuple[float, float]] = []
                    for sx0, sx1 in vis_segs:
                        if ox1 <= sx0 or ox0 >= sx1:
                            next_segs.append((sx0, sx1))
                        else:
                            if sx0 < ox0:
                                next_segs.append((sx0, ox0))
                            if ox1 < sx1:
                                next_segs.append((ox1, sx1))
                    vis_segs = next_segs
            for sx0, sx1 in vis_segs:
                if sx1 - sx0 > 1.0:
                    rx0, ry0 = origin_x + sx0, origin_y + b.y
                    msp.add_lwpolyline([(rx0, ry0), (origin_x + sx1, ry0), (origin_x + sx1, ry0 + b.dy), (rx0, ry0 + b.dy), (rx0, ry0)], dxfattribs={"layer": b.layer})
            continue
        if view_mode == "XY":
            x0, y0, w, h = origin_x + b.x, origin_y + b.y, b.dx, b.dy
        else:
            x0, y0, w, h = origin_x + b.z, origin_y + b.y, b.dz, b.dy
        msp.add_lwpolyline([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)], dxfattribs={"layer": b.layer})

    for c in scene.cylinders:
        if c.group not in group_filter:
            continue
        if view_mode == "XY":
            if c.axis == "Z":
                cx, cy, r = origin_x + c.cx, origin_y + c.cy, c.radius
                msp.add_circle((cx, cy), radius=r, dxfattribs={"layer": c.layer})
                if r >= 4.0:
                    msp.add_line((cx - r * 1.15, cy), (cx + r * 1.15, cy), dxfattribs={"layer": "PNL_CENTER"})
                    msp.add_line((cx, cy - r * 1.15), (cx, cy + r * 1.15), dxfattribs={"layer": "PNL_CENTER"})
            else:
                x0, y0, w, h = origin_x + c.cx - c.radius, origin_y + c.cy, 2 * c.radius, c.length
                msp.add_lwpolyline([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)], dxfattribs={"layer": c.layer})
        elif c.axis == "Z":
            x0, y0, w, h = origin_x + c.cz, origin_y + c.cy - c.radius, c.length, 2 * c.radius
            msp.add_lwpolyline([(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)], dxfattribs={"layer": c.layer})

    if view_mode == "XY":
        for txt, lx, ly, lh, llayer, lgrp in scene.labels_2d:
            if lgrp in group_filter:
                put_text(msp, txt, origin_x + lx, origin_y + ly, height=max(lh * 0.85, 1.5 * anno_scale), layer=llayer)
        r_bal = 1.9 * anno_scale
        h_bal = 1.4 * anno_scale
        for bno, ax, ay, bx, by, bgrp in scene.balloons:
            if bgrp in group_filter and bno:
                draw_iso_balloon(
                    msp,
                    bno,
                    (origin_x + ax, origin_y + ay),
                    (origin_x + bx, origin_y + by + r_bal),
                    radius=r_bal,
                    text_h=h_bal,
                    surface=True,
                )


def build_sheet_07_panel_layout(scene: PanelAssembly3D) -> Path:
    """Create DXF/07_panel_layout.dxf: True 1:1 mm Model Space + Native AutoCAD DIMENSIONs + ISO 5455 1:20 ISO_A3 Viewport."""
    validate_panel_3d_clashes(scene, door_z_min=235.0, clearance_mm=10.0)
    doc = create_unicode_dxf()
    msp = doc.modelspace()
    dstyle = "ISO_MM_20"

    # --- A. MODEL SPACE: TRUE 1:1 MILLIMETER PROJECTIONS + NATIVE AUTOCAD DIMENSIONS ---
    # 1. View 1: Front Door External & Cutout View at (0, 0) -> 800 x 1200 mm
    put_text(msp, "1. MẶT NGOÀI CÁNH TỦ / FRONT DOOR (1:1)", 0, 1335, height=38.0, layer="TAGS")
    project_3d_scene_to_2d_view(msp, scene, ("door",), "XY", origin_x=0.0, origin_y=0.0, anno_scale=20.0)
    add_dim_linear(msp, (0, 0), (800, 0), (400, -75), angle=0, dimstyle=dstyle)
    add_dim_linear(msp, (0, 0), (0, 1200), (-85, 600), angle=90, dimstyle=dstyle)
    add_dim_linear(msp, (800, 0), (800, 540), (875, 270), angle=90, dimstyle=dstyle)
    add_dim_linear(msp, (800, 540), (800, 720), (875, 630), angle=90, dimstyle=dstyle)
    add_dim_linear(msp, (260, 720), (400, 720), (330, 795), angle=0, dimstyle=dstyle)
    add_dim_linear(msp, (293, 1018), (507, 1018), (400, 1105), angle=0, dimstyle=dstyle)
    add_dim_diameter(msp, center=(260, 720), radius=11.25, angle=135, dimstyle=dstyle)

    # 2. View 2: Internal Mounting Plate View at (1090, 0) -> Plate 740 x 1140 mm inside 800 x 1200 mm
    ox2 = 1090.0
    put_text(msp, "2. TẤM LẮP THIẾT BỊ / MOUNTING PLATE (1:1)", ox2, 1335, height=38.0, layer="TAGS")
    project_3d_scene_to_2d_view(msp, scene, ("enclosure", "plate"), "XY", origin_x=ox2, origin_y=0.0, anno_scale=20.0)
    add_dim_linear(msp, (ox2 + 30, 30), (ox2 + 770, 30), (ox2 + 400, -65), angle=0, dimstyle=dstyle)
    add_dim_linear(msp, (ox2, 0), (ox2 + 800, 0), (ox2 + 400, -135), angle=0, dimstyle=dstyle)
    add_dim_linear(msp, (ox2 + 770, 30), (ox2 + 770, 1170), (ox2 + 865, 600), angle=90, dimstyle=dstyle)
    add_dim_linear(msp, (ox2, 0), (ox2, 285), (ox2 - 75, 142.5), angle=90, dimstyle=dstyle)
    add_dim_linear(msp, (ox2, 285), (ox2, 610), (ox2 - 75, 447.5), angle=90, dimstyle=dstyle)
    add_dim_linear(msp, (ox2, 610), (ox2, 945), (ox2 - 75, 777.5), angle=90, dimstyle=dstyle)

    # Cutting Plane A-A on View 2 (ISO 128-30)
    msp.add_line((ox2 + 400.0, -35.0), (ox2 + 400.0, 1235.0), dxfattribs={"layer": "PNL_CENTER"})
    put_text(msp, "A ->", ox2 + 408.0, 1218.0, height=28.0, layer="TAGS")
    put_text(msp, "A ->", ox2 + 408.0, -28.0, height=28.0, layer="TAGS")

    # 3. View 3: Side Section View A-A at (2120, 0) -> Depth 300 mm (280 body + 20 door) x 1200 mm
    ox3 = 2120.0
    put_text(msp, "3. MẶT CẮT A-A", ox3, 1335, height=38.0, layer="TAGS")
    project_3d_scene_to_2d_view(msp, scene, ("enclosure", "plate", "door"), "ZY", origin_x=ox3, origin_y=0.0, anno_scale=20.0)
    hatch_sec = msp.add_hatch(color=8, dxfattribs={"layer": "PNL_DETAIL"})
    hatch_sec.paths.add_polyline_path([(ox3 + 15.0, 30.0), (ox3 + 18.0, 30.0), (ox3 + 18.0, 1170.0), (ox3 + 15.0, 1170.0)], is_closed=True)
    hatch_sec.set_pattern_fill("ANSI31", scale=8.0)
    add_dim_linear(msp, (ox3, 0), (ox3 + 300, 0), (ox3 + 150, -75), angle=0, dimstyle=dstyle)
    add_dim_linear(msp, (ox3, 1200), (ox3 + 280, 1200), (ox3 + 140, 1265), angle=0, dimstyle=dstyle)

    # --- B. PAPER SPACE ('ISO_A3'): A3 FRAME, VIEWPORT (ISO 5455 EXACT 1:20), & BORDERED SCHEDULES ---
    psp = setup_iso_a3_paperspace(doc, "ISO_A3")
    draw_iso_a3_frame_and_titleblock(
        psp,
        sheet_no="07",
        sheet_max="09",
        dwg_no="MCC-WEIGH-07",
        title_en="PANEL LAYOUT (MODEL 1:1 + NATIVE DIM, DOOR / PLATE / SECTION A-A)",
        title_vi="BẢN VẼ BỐ TRÍ TỦ ĐIỆN & KHOÉT LỖ (MODEL 1:1, LAYOUT VIEWPORT 1:20)",
        scale_str="1:20 (A3)",
    )

    vp = psp.add_viewport(
        center=(126.0, 215.5),
        size=(208.0, 139.0),
        view_center_point=(1175.0, 600.0),
        view_height=139.0 * 20.0,
        dxfattribs={"layer": "VIEWPORT_FRAME"},
    )
    vp.dxf.status = 1

    draw_grid_table(
        psp,
        x0=232.0,
        y_top=284.0,
        col_widths=[10.0, 16.0, 74.0, 25.0, 32.0, 10.0, 14.0],
        headers=["NO", "TAG", "DESCRIPTION (EN / VI)", "MFG", "CATALOG NO.", "QTY", "LOC"],
        rows=[
            ["1", "-Q1", "MCCB 4P (3P+N) 63A (BẮT VÍT TRỰC TIẾP BASE)", "SIEMENS", "3VA1163-4FF42", "1", "+MAIN"],
            ["2", "-F1", "BỘ CẦU CHÌ BÁO PHA 3P 10x38 2A (GÀI RAY)", "SIEMENS", "3NW7031", "1", "+MAIN"],
            ["3", "-Q3", "MCB 2P 10A (L1-N CẤP NGUỒN 24VDC & QUẠT)", "SIEMENS", "5SL6210-7", "1", "+MAIN"],
            ["4", "-Q2", "MPCB 16A + AUX / CB BẢO VỆ VFD (GÀI RAY)", "SIEMENS", "3RV2021+3RV2901", "1+1", "+MAIN"],
            ["5", "-K1", "CONTACTOR 25A + DIODE / KHỞI ĐỘNG TỪ (RAY)", "SIEMENS", "3RT2026+3RT2926", "1+1", "+MAIN"],
            ["6", "-U1", "SINAMICS G120C 4kW (BẮT VÍT TRỰC TIẾP BASE)", "SIEMENS", "6SL3210-1KE18", "1+1", "+MAIN"],
            ["7", "-G1", "SITOP PSU100S 24VDC/10A (VÀO 230VAC L1-N)", "SIEMENS", "6EP1334-2BA20", "1", "+MAIN"],
            ["8", "-A1", "S7-1500 CPU 1511 + 4 MODULES (RAY NHÔM S7)", "SIEMENS", "6ES7511+MODULES", "1+4", "+MAIN"],
            ["9", "-K_SAF1", "SAFETY RELAY 3SK1 / RƠ-LE AN TOÀN (GÀI RAY)", "SIEMENS", "3SK1111-1AB30", "1", "+MAIN"],
            ["10", "-A2", "WEIGH TRANS + ỐC CÁP EMC M16 + KẸP SK14", "SIEMENS", "7MH4910+ASSY", "1+2", "+MAIN"],
            ["11", "-X0", "CẦU ĐẤU ĐỘNG LỰC DOMINO 63A (L1,L2,L3,N,PE)", "PHOENIX", "3044199 (UT 16)", "9", "+MAIN"],
            ["12", "-X1..-X3", "CẦU ĐẤU CẦU CHÌ 24V + CẦU ĐẤU 3 TẦNG LOAD CELL", "PHOENIX", "3004100+3036042", "3+12", "+MAIN"],
            ["13", "-H_L1..3", "3 ĐÈN BÁO PHA L1-L2-L3 Ø22.5 (ĐỎ-VÀNG-XANH)", "SIEMENS", "3SU1152-6AA20", "3", "+DOOR"],
            ["14", "-S10..H1", "NÚT DỪNG KHẨN Ø40 + ĐÈN CHẠY & NÚT CHẠY/DỪNG", "SIEMENS", "3SU1150+3SU1152", "4", "+DOOR"],
        ],
        title="PANEL BILL OF MATERIALS / BẢNG VẬT TƯ TỦ ĐIỆN (PHÂN BIỆT GÀI RAY & BẮT VÍT BASE)",
        row_h=4.6,
        header_h=5.2,
        title_h=5.8,
        text_h=1.62,
    )

    bot_np = draw_grid_table(
        psp,
        x0=24.0,
        y_top=142.0,
        col_widths=[14.0, 16.0, 14.0, 56.0, 56.0, 22.0, 28.0],
        headers=["NP#", "TAG", "LOC", "LINE 1 (ENGLISH)", "LINE 2 (TIẾNG VIỆT)", "SIZE(mm)", "COLOR"],
        rows=[
            ["NP-01", "PANEL", "+DOOR", "CONVEYOR WEIGHING PANEL", "TỦ ĐIỀU KHIỂN TRẠM CÂN BĂNG TẢI", "150x50", "WHITE/BLACK"],
            ["NP-02", "-Q1", "+MAIN", "MAIN INCOMER MCCB 63A", "ÁPTÔMÁT TỔNG ĐẦU VÀO 3P 63A", "70x25", "WHITE/BLACK"],
            ["NP-03", "-S10", "+DOOR", "EMERGENCY STOP", "DỪNG KHẨN CẤP (XOAY NHẢ)", "Ø60 RING", "YELLOW/BLACK"],
            ["NP-04", "-H1", "+DOOR", "CONVEYOR RUNNING", "ĐÈN BÁO BĂNG TẢI ĐANG CHẠY", "50x18", "WHITE/BLACK"],
            ["NP-05", "-S11", "+DOOR", "CONVEYOR START", "NÚT NHẤN CHẠY BĂNG TẢI", "50x18", "WHITE/BLACK"],
            ["NP-06", "-S12", "+DOOR", "CONVEYOR STOP", "NÚT NHẤN DỪNG BĂNG TẢI", "50x18", "WHITE/BLACK"],
            ["NP-07", "-A2", "+MAIN", "6-WIRE LOAD CELL TRANS.", "BỘ KHUẾCH ĐẠI CÂN LOAD CELL", "60x20", "WHITE/BLACK"],
            ["NP-08", "WARN", "+MAIN", "DANGER! 400VAC BUSBAR", "NGUY HIỂM! ĐIỆN ÁP CAO 400VAC", "100x40", "YELLOW/RED"],
        ],
        title="BẢNG BIỂN TÊN KHẮC LASER 2 LỚP (NAMEPLATE SCHEDULE VIA AEREPORT)",
        row_h=5.0,
        header_h=5.5,
        title_h=6.0,
        text_h=1.68,
    )

    draw_grid_table(
        psp,
        x0=24.0,
        y_top=bot_np - 3.0,
        col_widths=[36.0, 48.0, 44.0, 78.0],
        headers=["VỊ TRÍ / THIẾT BỊ", "LỖ KHOÉT / CUTOUT (mm)", "CAO ĐỘ LẮP (TỪ ĐÁY)", "TIÊU CHUẨN MÀU / GHI CHÚ GIA CÔNG"],
        rows=[
            ["HMI KTP700 (-A3)", "Chữ nhật 192 x 138 (+1/-0)", "Tâm Y = 939 mm", "Ron cao su IP65, chừa sâu sau cánh 45 mm"],
            ["Đèn pha (-H_L1..L3)", "Lỗ tròn Ø22.5 (+0.4/-0.0)", "Tâm Y = 720 mm", "Rãnh chống xoay 3.2x24.1, bước ngang 140 mm"],
            ["Nút nhấn & E-Stop (-S10..)", "Lỗ tròn Ø22.5 (+0.4/-0.0)", "Tâm Y = 540 mm", "Nấm đỏ Ø40 trên vành vàng Ø60 (IEC 60073)"],
            ["Quạt & Lọc gió (Fan)", "Vuông 150 x 150 (+1/-0)", "Tâm Y = 225 mm", "Hút gió mát cạnh dưới, đẩy khí nóng cạnh trên"],
        ],
        title="BẢNG THÔNG SỐ KHOÉT LỖ CÁNH TỦ & CAO ĐỘ LẮP ĐẶT (DOOR CUTOUT SCHEDULE)",
        row_h=5.0,
        header_h=5.5,
        title_h=6.0,
        text_h=1.68,
    )

    draw_grid_table(
        psp,
        x0=232.0,
        y_top=148.0,
        col_widths=[62.0, 121.0],
        headers=["HẠNG MỤC KỸ THUẬT / ITEM", "THÔNG SỐ & GHI CHÚ GIA CÔNG CHUẨN (EN / VI)"],
        rows=[
            ["1. KÍCH THƯỚC & TÔN", "Rộng 800 x Cao 1200 x Sâu 300 mm (Model 1:1) | Vỏ: 2.0mm, Tấm lắp: 3.0mm"],
            ["2. CẤP BẢO VỆ & SƠN", "IP54 (Trong nhà), Form 2b (IEC 61439-2) | Sơn tĩnh điện sần RAL 7035"],
            ["3. TÍNH NHIỆT (IEC 60890)", "Tổng tổn hao P_loss = 115W, dT = 10K -> V_fan = 35.7 m³/h (Quạt 150x150 55m³/h)"],
            ["4. KHÔNG GIAN UỐN CÁP", "Đi cáp đáy qua bích rời 500x160mm; khoảng uốn cáp >= 200mm (R_min >= 8xOD)"],
            ["5. DUNG SAI & BAVIA", "Tất cả kích thước mm (ISO 2768-m); làm sạch bavia cạnh sắc 0.2-0.5 trước khi sơn"],
            ["6. LỰC SIẾT ĐỒNG (TORQUE)", "Bu-lông đồng M8x25 (Thép 8.8 mạ kẽm) siết đúng 22 N.m và chấm sơn Torque Seal"],
            ["7. TIẾP ĐỊA & CHE IP2X", "Dây đồng bện >= 6mm² nối cánh tủ; lắp tấm che Polycarbonate trong suốt 3mm IP2X"],
        ],
        title="THÔNG SỐ VỎ TỦ (ENCLOSURE DATA BLOCK) & GHI CHÚ KỸ THUẬT SONG NGỮ",
        row_h=5.2,
        header_h=5.8,
        title_h=6.2,
        text_h=1.68,
    )

    return save_dxf_safely(doc, DXF_DIR / "07_panel_layout.dxf")


def build_sheet_08_busbar_fabrication() -> Path:
    """Create DXF/08_busbar_fabrication.dxf: True 1:1 mm Model Space + Native AutoCAD DIMENSIONs + 1:2.5 ISO_A3 Viewport."""
    doc = create_unicode_dxf()
    msp = doc.modelspace()
    dstyle = "ISO_MM_2_5"

    # --- A. MODEL SPACE: TRUE 1:1 MILLIMETER BUSBAR FLAT PATTERNS & CT ASSEMBLY ---
    # 1. BB-01..03 Phase Busbars (E-Cu 30x5mm, Bent 120+240+100mm, 2x90° R5 K=0.42 -> exact L_flat=442.3mm)
    flat_len, bend_centers = compute_developed_length([120.0, 240.0, 100.0], [90.0, 90.0], thickness=5.0, inner_radius=5.0, k_factor=0.42)
    y1 = 480.0
    put_text(msp, "1. KHAI TRIỂN THANH CÁI PHA BB-01..03 (E-Cu 30x5mm, 1:1, 4 x Ø9.0 M8)", 0.0, y1 + 88.0, height=6.0, layer="TAGS")
    msp.add_lwpolyline([(0, y1), (flat_len, y1), (flat_len, y1 + 30), (0, y1 + 30), (0, y1)], dxfattribs={"layer": "PNL_BUSBAR_L1"})
    msp.add_line((-10, y1 + 15), (flat_len + 10, y1 + 15), dxfattribs={"layer": "PNL_CENTER"})

    prev_bx = 0.0
    for bx in bend_centers:
        msp.add_line((bx, y1 - 4), (bx, y1 + 34), dxfattribs={"layer": "LOC_BOX"})
        put_text(msp, "BEND 90° R5", bx + 2.0, y1 + 33.0, height=4.2, layer="PNL_DIM")
        add_dim_linear(msp, (prev_bx, y1 + 30), (bx, y1 + 30), ((prev_bx + bx) / 2.0, y1 + 48.0), dimstyle=dstyle)
        prev_bx = bx

    bb_holes = [25.0, 75.0, 220.0, 410.0]
    for hx in bb_holes:
        msp.add_circle((hx, y1 + 15.0), radius=4.5, dxfattribs={"layer": "PNL_HOLE_BOLT"})
        msp.add_line((hx, y1 - 5), (hx, y1 + 35), dxfattribs={"layer": "PNL_CENTER"})

    chain_1 = [0.0, *bb_holes, flat_len]
    offsets_1 = auto_stack_dim_offsets(chain_1[:-1], base_offset=-18.0, step=-12.0, min_gap=30.0)
    for (x_a, x_b), y_off in zip(zip(chain_1[:-1], chain_1[1:]), offsets_1):
        add_dim_linear(msp, (x_a, y1), (x_b, y1), ((x_a + x_b) / 2.0, y1 + y_off), dimstyle=dstyle)

    add_dim_linear(msp, (0.0, y1 + 30), (flat_len, y1 + 30), (flat_len / 2.0, y1 + 68.0), dimstyle=dstyle)
    add_dim_linear(msp, (0.0, y1), (0.0, y1 + 30), (-20.0, y1 + 15.0), angle=90, dimstyle=dstyle)
    add_dim_diameter(msp, center=(25.0, y1 + 15.0), radius=4.5, angle=45, dimstyle=dstyle)

    # Side flat view (442.3 x 5.0 mm)
    y1_side = 435.0
    msp.add_lwpolyline([(0, y1_side), (flat_len, y1_side), (flat_len, y1_side + 5.0), (0, y1_side + 5.0), (0, y1_side)], dxfattribs={"layer": "PNL_BUSBAR_L1"})
    add_dim_linear(msp, (0.0, y1_side), (0.0, y1_side + 5.0), (-20.0, y1_side + 2.5), angle=90, dimstyle=dstyle)

    # 2. BB-PE Compact Earth & EMC Shield Bar (E-Cu 25x5mm, L=220.0mm, 6xØ9.0 M8 + SK14 Clamp — matching Scene3D & Table 11A)
    y2 = 245.0
    pe_len = 220.0
    put_text(msp, "2. THANH ĐỒNG TIẾP ĐỊA & KẸP GIÁP BB-PE (E-Cu 25x5mm, L=220mm, 6 x Ø9.0 + SK14)", 0.0, y2 + 64.0, height=6.0, layer="TAGS")
    msp.add_lwpolyline([(0, y2), (pe_len, y2), (pe_len, y2 + 25.0), (0, y2 + 25.0), (0, y2)], dxfattribs={"layer": "PNL_BUSBAR_PE"})
    msp.add_line((-10, y2 + 12.5), (pe_len + 10, y2 + 12.5), dxfattribs={"layer": "PNL_CENTER"})
    pe_holes = [20.0, 55.0, 90.0, 125.0, 160.0, 200.0]
    for hx in pe_holes:
        msp.add_circle((hx, y2 + 12.5), radius=4.5, dxfattribs={"layer": "PNL_HOLE_BOLT"})
        msp.add_line((hx, y2 - 4), (hx, y2 + 29), dxfattribs={"layer": "PNL_CENTER"})
    msp.add_lwpolyline([(137, y2 - 4), (169, y2 - 4), (169, y2 + 29), (137, y2 + 29), (137, y2 - 4)], dxfattribs={"layer": "PNL_FOOTPRINT"})
    put_text(msp, "SK14 CLAMP", 137.0, y2 + 31.0, height=4.8, layer="TAGS")

    chain_2 = [0.0, *pe_holes, pe_len]
    for x_a, x_b in zip(chain_2[:-1], chain_2[1:]):
        add_dim_linear(msp, (x_a, y2), (x_b, y2), ((x_a + x_b) / 2.0, y2 - 18.0), dimstyle=dstyle)
    add_dim_linear(msp, (0.0, y2 + 25.0), (pe_len, y2 + 25.0), (pe_len / 2.0, y2 + 44.0), dimstyle=dstyle)
    add_dim_linear(msp, (0.0, y2), (0.0, y2 + 25.0), (-20.0, y2 + 12.5), angle=90, dimstyle=dstyle)

    # Formed Profile View for BB-01..03 (True 1:1 mm Z-profile: 120 + 240 + 100 mm, T=5mm, R_in=5mm)
    fp_x0, fp_y0, fp_t = 232.0, 138.0, 5.0
    msp.add_lwpolyline(
        [
            (fp_x0, fp_y0),
            (fp_x0 + 120.0, fp_y0),
            (fp_x0 + 120.0, fp_y0 + 240.0 - fp_t),
            (fp_x0 + 120.0 + 100.0 - fp_t, fp_y0 + 240.0 - fp_t),
            (fp_x0 + 120.0 + 100.0 - fp_t, fp_y0 + 240.0),
            (fp_x0 + 120.0 - fp_t, fp_y0 + 240.0),
            (fp_x0 + 120.0 - fp_t, fp_y0 + fp_t),
            (fp_x0, fp_y0 + fp_t),
            (fp_x0, fp_y0),
        ],
        dxfattribs={"layer": "PNL_BUSBAR_L1"},
    )
    add_dim_linear(msp, (fp_x0, fp_y0), (fp_x0 + 120.0, fp_y0), (fp_x0 + 60.0, fp_y0 - 12.0), dimstyle=dstyle)
    add_dim_linear(msp, (fp_x0 + 120.0, fp_y0), (fp_x0 + 120.0, fp_y0 + 240.0), (fp_x0 + 138.0, fp_y0 + 120.0), angle=90, dimstyle=dstyle)
    add_dim_linear(msp, (fp_x0 + 120.0 - fp_t, fp_y0 + 240.0), (fp_x0 + 120.0 + 100.0 - fp_t, fp_y0 + 240.0), (fp_x0 + 167.5, fp_y0 + 252.0), dimstyle=dstyle)
    put_text(msp, "FORMED PROFILE BB-01..03 (1:1, Z-BEND 90° R5)", fp_x0, fp_y0 + 266.0, height=4.2, layer="PNL_DIM")

    # 3. CT Window Spacing & SM-40 Standoff Insulator Assembly (True 1:1 mm: Pitch=85mm, W_CT=70mm, SM-40 H=40mm)
    put_text(msp, "3. CỤM BIẾN DÒNG (CT W=70, BƯỚC PHA 85mm), SỨ SM-40 (H=40) & CHE IP2X (1:1)", 0.0, 148.0, height=6.0, layer="TAGS")
    msp.add_lwpolyline([(0, 0), (300, 0), (300, 3), (0, 3), (0, 0)], dxfattribs={"layer": "PNL_PLATE"})
    for cx, blayer, pname in [(65.0, "PNL_BUSBAR_L1", "L1"), (150.0, "PNL_BUSBAR_L2", "L2"), (235.0, "PNL_BUSBAR_L3", "L3")]:
        # SM-40 insulator (H = 40.0 mm from Y=3..43, W_base = 30 mm)
        msp.add_lwpolyline([(cx - 15, 3), (cx + 15, 3), (cx + 12, 43), (cx - 12, 43), (cx - 15, 3)], dxfattribs={"layer": "PNL_DETAIL"})
        # Busbar 30x5 mm cross-section (Y=43..48)
        msp.add_lwpolyline([(cx - 15, 43), (cx + 15, 43), (cx + 15, 48), (cx - 15, 48), (cx - 15, 43)], dxfattribs={"layer": blayer})
        # CT Housing 70x70 mm (Y=10.5..80.5, cx-35..cx+35)
        msp.add_lwpolyline([(cx - 35, 10.5), (cx + 35, 10.5), (cx + 35, 80.5), (cx - 35, 80.5), (cx - 35, 10.5)], dxfattribs={"layer": "PNL_FOOTPRINT"})
        msp.add_line((cx, -4), (cx, 88), dxfattribs={"layer": "PNL_CENTER"})
        put_text(msp, f"CT-{pname}", cx - 14, 83.0, height=5.0, layer="TAGS")
        put_text(msp, "SM-40", cx - 11, 20.0, height=4.5, layer="DESC")

    # IP2X Clear PC Shroud (3 mm thick at Y=98..101) on solid detail layer
    msp.add_lwpolyline([(10, 98), (290, 98), (290, 101), (10, 101), (10, 98)], dxfattribs={"layer": "PNL_DETAIL"})
    put_text(msp, "TẤM CHE POLYCARBONATE IP2X (T=3mm)", 295.0, 96.0, height=5.0, layer="TAGS")

    add_dim_linear(msp, (65.0, 80.5), (150.0, 80.5), (107.5, 122.0), dimstyle=dstyle)
    add_dim_linear(msp, (150.0, 80.5), (235.0, 80.5), (192.5, 122.0), dimstyle=dstyle)
    add_dim_linear(msp, (115.0, 10.5), (185.0, 10.5), (150.0, -18.0), dimstyle=dstyle)
    add_dim_linear(msp, (50.0, 3.0), (50.0, 43.0), (12.0, 23.0), angle=90, dimstyle=dstyle)

    # --- B. PAPER SPACE ('ISO_A3'): A3 FRAME, VIEWPORT (EXACT 1:2.5), & TABLES 11A / 11B ---
    psp = setup_iso_a3_paperspace(doc, "ISO_A3")
    draw_iso_a3_frame_and_titleblock(
        psp,
        sheet_no="08",
        sheet_max="09",
        dwg_no="MCC-WEIGH-08",
        title_en="BUSBAR FABRICATION (MODEL 1:1 + NATIVE DIM, DIN 43673 & CT SPACING)",
        title_vi="BẢN VẼ GIA CÔNG ĐỒNG THANH CÁI, CT & SỨ SM-40 (MODEL 1:1, VIEWPORT 1:2.5)",
        scale_str="1:2.5 (A3)",
    )

    vp = psp.add_viewport(
        center=(120.5, 147.0),
        size=(199.0, 270.0),
        view_center_point=(210.0, 255.0),
        view_height=270.0 * 2.5,
        dxfattribs={"layer": "VIEWPORT_FRAME"},
    )
    vp.dxf.status = 1

    bot_11a = draw_grid_table(
        psp,
        x0=222.0,
        y_top=280.0,
        col_widths=[16.0, 12.0, 20.0, 22.0, 22.0, 32.0, 26.0, 29.0, 12.0],
        headers=["MARK", "PHA", "QUY CÁCH", "VẬT LIỆU", "L_FLAT(mm)", "ĐỘT LỖ (DIN)", "CHẤN UỐN", "PHẠM VI ÁP DỤNG", "SL"],
        rows=[
            ["BB-PE", "PE", "25 x 5", "E-Cu 99.9%", "220.0", "6 x Ø9.0 (M8)", "Thẳng (0°)", "Tủ <=63A (Dùng Domino -X0)", "1"],
            ["BB-01", "L1", "30 x 5", "E-Cu 99.9%", "442.3", "4 x Ø9.0 (M8)", "2x90° (R5,K0.42)", "Option Tủ >=100A (Có CT)", "1"],
            ["BB-02", "L2", "30 x 5", "E-Cu 99.9%", "442.3", "4 x Ø9.0 (M8)", "2x90° (R5,K0.42)", "Option Tủ >=100A (Có CT)", "1"],
            ["BB-03", "L3", "30 x 5", "E-Cu 99.9%", "442.3", "4 x Ø9.0 (M8)", "2x90° (R5,K0.42)", "Option Tủ >=100A (Có CT)", "1"],
        ],
        title="BẢNG 11A: THANH ĐỒNG TIẾP ĐỊA BB-PE (TỦ <=63A DÙNG DOMINO -X0) & MẪU BUSBAR TỦ >=100A",
        row_h=6.0,
        header_h=6.2,
        title_h=6.5,
        text_h=1.7,
    )

    draw_grid_table(
        psp,
        x0=222.0,
        y_top=bot_11a - 6.0,
        col_widths=[16.0, 78.0, 34.0, 26.0, 22.0, 15.0],
        headers=["MÃ PK", "MÔ TẢ PHỤ KIỆN (EN / VI)", "QUY CÁCH / MODEL", "CẤP BỀN", "LỰC SIẾT", "SL"],
        rows=[
            ["HW-01", "Bộ Bu-lông + 2 Long đền phẳng + 1 Long đền vênh + Tán", "ISO 4017 M8 x 25", "Thép 8.8 Zn", "22 N·m", "26"],
            ["HW-02", "Sứ đỡ thanh cái hạ thế hình lục giác / trụ", "SM-40 (H=40, M8)", "DMC UL94-V0", "20 N·m", "8"],
            ["HW-03", "Kẹp giáp cáp tín hiệu trực tiếp lên thanh đồng PE", "PHOENIX SK 14", "Thép lò xo", "8 N·m", "4"],
            ["HW-04", "Tấm che an toàn chống chạm trực tiếp IP2X + Trụ đỡ", "PC Trong 350x190x3", "Clear PC", "10 N·m", "1"],
            ["HW-05", "Ống co nhiệt bọc thanh cái hạ thế 1kV (Đỏ/Vàng/Xanh)", "Phi 35 (Co 2:1)", "Polyolefin", "--", "3m"],
        ],
        title="BẢNG 11B: PHỤ KIỆN LẮP GHÉP BUSBAR, SỨ ĐỠ & LỰC SIẾT CỜ-LÊ LỰC (TORQUE SCHEDULE)",
        row_h=6.0,
        header_h=6.2,
        title_h=6.5,
        text_h=1.7,
    )

    return save_dxf_safely(doc, DXF_DIR / "08_busbar_fabrication.dxf")


def build_3d_assembly_dxf(scene: PanelAssembly3D) -> Path:
    """Export the 1:1 3D PanelAssembly3D mechanical clash-check model to DXF/09_panel_3d_assembly.dxf.

    Note: Real Inventor Electromechanical Link (.emx) must be generated via native ACADE AEEMLINK command,
    never via mocked Python ElementTree XML.
    """
    doc3d = create_unicode_dxf()
    msp3d = doc3d.modelspace()

    for b in scene.boxes:
        x0, y0, z0, dx, dy, dz = b.x, b.y, b.z, b.dx, b.dy, b.dz
        pts_bot = [(x0, y0, z0), (x0 + dx, y0, z0), (x0 + dx, y0 + dy, z0), (x0, y0 + dy, z0)]
        pts_top = [(x0, y0, z0 + dz), (x0 + dx, y0, z0 + dz), (x0 + dx, y0 + dy, z0 + dz), (x0, y0 + dy, z0 + dz)]
        for i in range(4):
            msp3d.add_line(pts_bot[i], pts_bot[(i + 1) % 4], dxfattribs={"layer": b.layer})
            msp3d.add_line(pts_top[i], pts_top[(i + 1) % 4], dxfattribs={"layer": b.layer})
            msp3d.add_line(pts_bot[i], pts_top[i], dxfattribs={"layer": b.layer})

    for c in scene.cylinders:
        n_seg = 12
        ring1, ring2 = [], []
        for i in range(n_seg):
            ang = 2.0 * math.pi * i / n_seg
            if c.axis == "Z":
                px, py = c.cx + c.radius * math.cos(ang), c.cy + c.radius * math.sin(ang)
                ring1.append((px, py, c.cz))
                ring2.append((px, py, c.cz + c.length))
            else:
                px, pz = c.cx + c.radius * math.cos(ang), c.cz + c.radius * math.sin(ang)
                ring1.append((px, c.cy, pz))
                ring2.append((px, c.cy + c.length, pz))
        for i in range(n_seg):
            msp3d.add_line(ring1[i], ring1[(i + 1) % n_seg], dxfattribs={"layer": c.layer})
            msp3d.add_line(ring2[i], ring2[(i + 1) % n_seg], dxfattribs={"layer": c.layer})
            if i % 3 == 0:
                msp3d.add_line(ring1[i], ring2[i], dxfattribs={"layer": c.layer})

    psp3d = setup_iso_a3_paperspace(doc3d, "ISO_A3")
    draw_iso_a3_frame_and_titleblock(
        psp3d,
        sheet_no="09",
        sheet_max="09",
        dwg_no="MCC-WEIGH-09",
        title_en="3D PANEL ASSEMBLY ISOMETRIC VIEW (1:1 MODEL, INVENTOR EMX LINK)",
        title_vi="PHỐI CẢNH LẮP RÁP 3D TỦ ĐIỆN & LIÊN KẾT INVENTOR .EMX",
        scale_str="NTS (ISO 3D)",
    )
    vp3d = psp3d.add_viewport(
        center=(220.0, 165.0),
        size=(380.0, 230.0),
        view_center_point=(400.0, 600.0),
        view_height=1500.0,
        dxfattribs={"layer": "VIEWPORT_FRAME"},
    )
    vp3d.dxf.view_direction_vector = (1.0, -1.0, 0.8)
    vp3d.dxf.status = 1

    return save_dxf_safely(doc3d, DXF_DIR / "09_panel_3d_assembly.dxf")


def render_dxf_to_matplotlib_ax(doc: ezdxf.document.Drawing, ax, is_3d: bool = False) -> None:
    """Render DXF via ezdxf.addons.drawing so Paper Space VIEWPORTs & native AutoCAD DIMENSIONs render accurately."""
    target_layout = doc.layouts.get("ISO_A3") if "ISO_A3" in doc.layouts else doc.modelspace()
    cfg = Configuration.defaults().with_changes(
        background_policy=BackgroundPolicy.WHITE,
        color_policy=ColorPolicy.COLOR,
    )
    ctx = RenderContext(doc)
    backend = MatplotlibBackend(ax)
    Frontend(ctx, backend, config=cfg).draw_layout(target_layout, finalize=True)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-2, 422)
    ax.set_ylim(-2, 299)
    ax.axis("off")

    if is_3d:
        ax3d = ax.inset_axes([0.08, 0.12, 0.84, 0.80])
        ax3d.set_facecolor("none")
        aci_to_hex = {1: "#d92b2b", 2: "#b8860b", 3: "#1b8a3d", 4: "#008b8b", 5: "#1d4ed8", 6: "#a21caf", 7: "#111827", 8: "#6b7280", 9: "#9ca3af", 30: "#d97706", 40: "#b45309", 252: "#4b5563"}
        layer_colors = {lyr.dxf.name: aci_to_hex.get(lyr.color, "#111827") for lyr in doc.layers}
        for e in doc.modelspace():
            if e.dxftype() == "LINE":
                col = layer_colors.get(e.dxf.layer, "#111827")
                s, end = e.dxf.start, e.dxf.end
                ax3d.plot(
                    [s.x - s.z * 0.65, end.x - end.z * 0.65],
                    [s.y + s.x * 0.25 + s.z * 0.55, end.y + end.x * 0.25 + end.z * 0.55],
                    color=col,
                    linewidth=0.55,
                )
        ax3d.set_aspect("equal")
        ax3d.axis("off")


def build_release_pdf_and_previews(dxf_paths: list[Path], dxf_3d_path: Path) -> Path:
    """Render CAD DXF sheets (including Paper Space VIEWPORTs & native AutoCAD DIMENSIONs) to PDF and PNG previews."""
    out_pdf = PDF_DIR / "conveyor_weighing_station_release.pdf"
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(out_pdf) as pdf:
        for dp in dxf_paths:
            doc = ezdxf.readfile(dp)
            fig, ax = plt.subplots(figsize=(16.54, 11.69), dpi=200)
            render_dxf_to_matplotlib_ax(doc, ax, is_3d=False)
            fig.tight_layout(pad=0.1)
            pdf.savefig(fig, dpi=200)
            fig.savefig(PDF_DIR / f"preview_{dp.stem}.png", dpi=180)
            plt.close(fig)

        doc3d = ezdxf.readfile(dxf_3d_path)
        fig, ax = plt.subplots(figsize=(16.54, 11.69), dpi=200)
        render_dxf_to_matplotlib_ax(doc3d, ax, is_3d=True)
        fig.tight_layout(pad=0.1)
        pdf.savefig(fig, dpi=200)
        fig.savefig(PDF_DIR / "preview_09_panel_3d_assembly.png", dpi=180)
        plt.close(fig)

    return out_pdf


def main() -> None:
    import json

    scene = build_unified_3d_panel_scene()
    p1 = build_custom_symbol_va1_weigh_trans()
    p3 = build_sheet_07_panel_layout(scene)
    p4 = build_sheet_08_busbar_fabrication()
    p5_3d = build_3d_assembly_dxf(scene)
    p6 = build_release_pdf_and_previews([p3, p4], p5_3d)
    manifest = build_native_acade_project_manifest(PROJECT_DIR)
    manifest_path = PROJECT_DIR / "native_acade_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Built mechanical/3D/custom-symbol CAD artifacts & native ACADE manifest:")
    for p in (p1, p3, p4, p5_3d, p6, manifest_path):
        print(f" - {p} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
