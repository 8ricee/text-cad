"""Generate 1:1 2D Busbar Fabrication DXF following DIN 43673 hole standards & Sheet Metal Bend Allowance.

Supports both straight and bent copper busbars (calculating true developed flat length L_flat using K-factor
and bend radius R), enforces true 1:1 mm Model Space ($INSUNITS = 4), and places 100% native AutoCAD DIMENSION
entities (ISO_MM DimStyle with VN_ARIAL Unicode font, zero hand-drawn fake dims).

Usage:
    python generate_busbar_dxf.py --width 50 --thickness 10 --segments 200,300,150 --angles 90,90 --holes 50,150,580 --bolt M10 --out busbar_L1.dxf
"""

import argparse
import csv
import math
import os
from pathlib import Path

os.environ.setdefault("EZDXF_DISABLE_C_EXT", "1")
import ezdxf


BOLT_HOLE_DIAMETERS = {
    "M6": 6.8,
    "M8": 9.0,
    "M10": 11.0,
    "M12": 13.5,
    "M16": 17.5,
}


def setup_iso_dimstyle(doc: ezdxf.document.Drawing, name: str = "ISO_MM", dimscale: float = 1.0) -> str:
    """Configure an ISO metric AutoCAD DimStyle (true 1:1 measurement dimlfac=1.0, VN_ARIAL font, clean trailing zeros)."""
    if "VN_ARIAL" not in doc.styles:
        doc.styles.add("VN_ARIAL", font="arial.ttf", dxfattribs={"width": 0.82})
    ds = doc.dimstyles.get(name) if name in doc.dimstyles else doc.dimstyles.new(name)
    ds.dxf.dimtxsty = "VN_ARIAL"
    ds.dxf.dimtxt = 2.5
    ds.dxf.dimasz = 2.5
    ds.dxf.dimexo = 1.0
    ds.dxf.dimexe = 1.25
    ds.dxf.dimgap = 0.8
    ds.dxf.dimtad = 1
    ds.dxf.dimtih = 0
    ds.dxf.dimtoh = 0
    ds.dxf.dimdec = 1
    ds.dxf.dimzin = 8
    ds.dxf.dimdsep = ord(".")
    ds.dxf.dimlfac = 1.0
    ds.dxf.dimscale = dimscale
    ds.dxf.dimclrd = 3
    ds.dxf.dimclre = 3
    ds.dxf.dimclrt = 7
    return name


def compute_developed_length(
    segments: list[float],
    bend_angles_deg: list[float],
    thickness: float,
    inner_radius: float,
    k_factor: float = 0.42,
) -> tuple[float, list[float]]:
    """Compute true flat pattern length L_flat and bend centerlines using Sheet Metal Bend Allowance (DIN 6935)."""
    if not bend_angles_deg:
        return sum(segments), []
    if len(bend_angles_deg) != len(segments) - 1:
        raise ValueError("Number of bend angles must be len(segments) - 1.")

    flat_pos = 0.0
    bend_centers: list[float] = []
    for idx, angle_deg in enumerate(bend_angles_deg):
        angle_rad = abs(math.radians(angle_deg))
        ossb = (inner_radius + thickness) * math.tan(angle_rad / 2.0)
        ba = angle_rad * (inner_radius + k_factor * thickness)
        straight_leg = segments[idx] - ossb
        if idx > 0:
            prev_rad = abs(math.radians(bend_angles_deg[idx - 1]))
            prev_ossb = (inner_radius + thickness) * math.tan(prev_rad / 2.0)
            straight_leg -= prev_ossb
        if straight_leg < 0:
            raise ValueError(f"Segment {idx + 1} ({segments[idx]} mm) is shorter than bend setback.")
        flat_pos += straight_leg
        bend_centers.append(flat_pos + ba / 2.0)
        flat_pos += ba

    last_rad = abs(math.radians(bend_angles_deg[-1]))
    last_ossb = (inner_radius + thickness) * math.tan(last_rad / 2.0)
    last_leg = segments[-1] - last_ossb
    if last_leg < 0:
        raise ValueError(f"Last segment ({segments[-1]} mm) is shorter than bend setback.")
    flat_pos += last_leg
    return flat_pos, bend_centers


def build_busbar_dxf(
    width: float,
    thickness: float,
    length: float,
    hole_x_positions: list[float],
    bend_centers: list[float],
    bend_angles_deg: list[float],
    inner_radius: float,
    bolt: str,
    phase: str,
    mark: str,
    out_path: Path,
    k_factor: float = 0.42,
) -> None:
    """Create a 1:1 2D DXF flat pattern with DIN 43673 holes, bend lines, side view, and native AutoCAD DIMENSIONs."""
    if bolt not in BOLT_HOLE_DIAMETERS:
        raise ValueError(f"Unsupported bolt size '{bolt}'. Choose from {list(BOLT_HOLE_DIAMETERS)}")

    hole_dia = BOLT_HOLE_DIAMETERS[bolt]
    min_end_edge = 1.5 * hole_dia
    side_margin = (width - hole_dia) / 2.0
    if width < 1.5 * hole_dia or side_margin < 4.0:
        raise ValueError(
            f"Busbar width {width} mm is too narrow for {bolt} (hole Ø{hole_dia} mm, side margin {side_margin:.1f} mm < 4.0 mm)."
        )

    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    if "Standard" in doc.styles:
        doc.styles.get("Standard").dxf.font = "arial.ttf"
    dimstyle = setup_iso_dimstyle(doc, "ISO_MM", dimscale=1.0)
    doc.header["$DIMSTYLE"] = dimstyle
    msp = doc.modelspace()

    phase_color = {"L1": 1, "L2": 40, "L3": 5, "N": 4, "PE": 3}.get(phase.upper(), 7)
    bus_layer = f"PNL_BUSBAR_{phase.upper()}"
    doc.layers.add(bus_layer, color=phase_color)
    doc.layers.add("PNL_HOLE_BOLT", color=6)
    doc.layers.add("PNL_CENTER", color=1, linetype="CENTER" if "CENTER" in doc.linetypes else "CONTINUOUS")
    doc.layers.add("PNL_BEND_LINE", color=8, linetype="DASHED" if "DASHED" in doc.linetypes else "CONTINUOUS")
    doc.layers.add("PNL_DIM", color=3)

    # 1. Front flat pattern view (1:1 mm: Length x Width)
    msp.add_lwpolyline(
        [(0, 0), (length, 0), (length, width), (0, width), (0, 0)],
        dxfattribs={"layer": bus_layer},
    )

    # 2. Side flat view (1:1 mm: Length x Thickness) placed below hole-chain dimension
    side_y0 = -34.0 - thickness
    msp.add_lwpolyline(
        [(0, side_y0), (length, side_y0), (length, side_y0 + thickness), (0, side_y0 + thickness), (0, side_y0)],
        dxfattribs={"layer": bus_layer},
    )

    # Centerline along busbar length
    y_mid = width / 2.0
    msp.add_line((-8, y_mid), (length + 8, y_mid), dxfattribs={"layer": "PNL_CENTER"})

    # Bend centerlines & native bend-position dimensions
    prev_bx = 0.0
    for bx, ang in zip(bend_centers, bend_angles_deg):
        msp.add_line((bx, -3), (bx, width + 3), dxfattribs={"layer": "PNL_BEND_LINE"})
        msp.add_text(
            f"BEND {ang:.0f}° R{inner_radius:.0f}",
            height=2.5,
            dxfattribs={"layer": "PNL_DIM", "style": "VN_ARIAL"},
        ).set_placement((bx + 1.5, width + 3.5))
        msp.add_linear_dim(
            base=((prev_bx + bx) / 2.0, width + 11.0),
            p1=(prev_bx, width),
            p2=(bx, width),
            dimstyle=dimstyle,
            dxfattribs={"layer": "PNL_DIM"},
        ).render()
        prev_bx = bx

    # Bolt holes + crosshairs + native hole-chain & diameter dimensions
    radius = hole_dia / 2.0
    min_bend_dist = 1.5 * thickness + inner_radius + radius
    sorted_holes = sorted(hole_x_positions)
    for hx in sorted_holes:
        if hx < min_end_edge or hx > length - min_end_edge:
            raise ValueError(f"Hole at x={hx:.1f} mm violates minimum end distance ({min_end_edge:.1f} mm).")
        for bx in bend_centers:
            if abs(hx - bx) < min_bend_dist:
                raise ValueError(
                    f"Hole at x={hx:.1f} mm too close to bend center x={bx:.1f} mm "
                    f"(|dx|={abs(hx - bx):.2f} mm < min {min_bend_dist:.2f} mm = 1.5*T + R_in + D/2)."
                )
        msp.add_circle((hx, y_mid), radius=radius, dxfattribs={"layer": "PNL_HOLE_BOLT"})
        msp.add_line((hx, -4), (hx, width + 4), dxfattribs={"layer": "PNL_CENTER"})

    chain_pts = [0.0, *sorted_holes, length]
    for x1, x2 in zip(chain_pts[:-1], chain_pts[1:]):
        msp.add_linear_dim(
            base=((x1 + x2) / 2.0, -14.0),
            p1=(x1, 0.0),
            p2=(x2, 0.0),
            dimstyle=dimstyle,
            dxfattribs={"layer": "PNL_DIM"},
        ).render()

    if sorted_holes:
        msp.add_diameter_dim(
            center=(sorted_holes[0], y_mid),
            radius=radius,
            angle=45.0,
            dimstyle=dimstyle,
            dxfattribs={"layer": "PNL_DIM"},
        ).render()

    # Overall native dimensions (Length, Width, Thickness)
    top_dim_y = width + (21.0 if bend_centers else 13.0)
    msp.add_linear_dim(
        base=(length / 2.0, top_dim_y),
        p1=(0.0, width),
        p2=(length, width),
        dimstyle=dimstyle,
        dxfattribs={"layer": "PNL_DIM"},
    ).render()
    msp.add_linear_dim(
        base=(-16.0, width / 2.0),
        p1=(0.0, 0.0),
        p2=(0.0, width),
        angle=90.0,
        dimstyle=dimstyle,
        dxfattribs={"layer": "PNL_DIM"},
    ).render()
    msp.add_linear_dim(
        base=(-16.0, side_y0 + thickness / 2.0),
        p1=(0.0, side_y0),
        p2=(0.0, side_y0 + thickness),
        angle=90.0,
        dimstyle=dimstyle,
        dxfattribs={"layer": "PNL_DIM"},
    ).render()

    # 3. Formed Profile View (true thickness dual-offset + bend R_in + signed U/Z angles + outer leg dimensions)
    if bend_angles_deg:
        prof_x0, prof_y0 = length + 60.0, 0.0
        # Reconstruct outer segment lengths from flat_len & bend_centers (or exact outer legs)
        n_segs = len(bend_angles_deg) + 1
        ossbs = [(inner_radius + thickness) * math.tan(abs(math.radians(a)) / 2.0) for a in bend_angles_deg]
        bas = [abs(math.radians(a)) * (inner_radius + k_factor * thickness) for a in bend_angles_deg]
        outer_segs: list[float] = []
        for s_idx in range(n_segs):
            if s_idx == 0:
                straight = bend_centers[0] - bas[0] / 2.0
                outer_segs.append(straight + ossbs[0])
            elif s_idx == n_segs - 1:
                straight = length - (bend_centers[-1] + bas[-1] / 2.0)
                outer_segs.append(straight + ossbs[-1])
            else:
                straight = (bend_centers[s_idx] - bas[s_idx] / 2.0) - (bend_centers[s_idx - 1] + bas[s_idx - 1] / 2.0)
                outer_segs.append(straight + ossbs[s_idx - 1] + ossbs[s_idx])

        # Build centerline points using signed bend_angles_deg (+ = CCW/Up, - = CW/Down)
        half_t = thickness / 2.0
        cl_pts: list[tuple[float, float]] = [(prof_x0, prof_y0)]
        cur_x, cur_y, cur_ang = prof_x0, prof_y0, 0.0
        for s_idx, seg_l in enumerate(outer_segs):
            inset_start = half_t * math.tan(abs(math.radians(bend_angles_deg[s_idx - 1])) / 2.0) if s_idx > 0 else 0.0
            inset_end = half_t * math.tan(abs(math.radians(bend_angles_deg[s_idx])) / 2.0) if s_idx < len(bend_angles_deg) else 0.0
            eff_l = max(seg_l - inset_start - inset_end, thickness)
            cur_x += eff_l * math.cos(cur_ang)
            cur_y += eff_l * math.sin(cur_ang)
            cl_pts.append((cur_x, cur_y))
            if s_idx < len(bend_angles_deg):
                cur_ang += math.radians(bend_angles_deg[s_idx])

        # Offset centerline by +-thickness/2 with exact miter = half_t / cos(|turn|/2) for any bend angle
        top_pts: list[tuple[float, float]] = []
        bot_pts: list[tuple[float, float]] = []
        for i in range(len(cl_pts)):
            if i == 0:
                dx, dy = cl_pts[1][0] - cl_pts[0][0], cl_pts[1][1] - cl_pts[0][1]
                miter = half_t
            elif i == len(cl_pts) - 1:
                dx, dy = cl_pts[-1][0] - cl_pts[-2][0], cl_pts[-1][1] - cl_pts[-2][1]
                miter = half_t
            else:
                dx1, dy1 = cl_pts[i][0] - cl_pts[i - 1][0], cl_pts[i][1] - cl_pts[i - 1][1]
                dx2, dy2 = cl_pts[i + 1][0] - cl_pts[i][0], cl_pts[i + 1][1] - cl_pts[i][1]
                l1, l2 = math.hypot(dx1, dy1) or 1.0, math.hypot(dx2, dy2) or 1.0
                dx, dy = dx1 / l1 + dx2 / l2, dy1 / l1 + dy2 / l2
                turn_rad = abs(math.radians(bend_angles_deg[i - 1]))
                miter = half_t / max(math.cos(turn_rad / 2.0), 0.1)
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            top_pts.append((cl_pts[i][0] + nx * miter, cl_pts[i][1] + ny * miter))
            bot_pts.append((cl_pts[i][0] - nx * miter, cl_pts[i][1] - ny * miter))

        closed_prof = [*top_pts, *reversed(bot_pts), top_pts[0]]
        msp.add_lwpolyline(closed_prof, dxfattribs={"layer": bus_layer})
        msp.add_lwpolyline(cl_pts, dxfattribs={"layer": "PNL_CENTER"})
        for i in range(1, len(cl_pts) - 1):
            msp.add_circle(cl_pts[i], radius=inner_radius + half_t, dxfattribs={"layer": "PNL_CENTER"})

        # Dimension true outer-to-outer lengths for every segment (works for L, U, and Z profiles)
        for s_idx in range(n_segs):
            seg_ang_deg = math.degrees(math.atan2(cl_pts[s_idx + 1][1] - cl_pts[s_idx][1], cl_pts[s_idx + 1][0] - cl_pts[s_idx][0]))
            if s_idx == 0:
                pts_a = bot_pts[0] if bend_angles_deg[0] > 0 else top_pts[0]
                pts_b = bot_pts[1] if bend_angles_deg[0] > 0 else top_pts[1]
            elif s_idx == n_segs - 1:
                pts_a = bot_pts[-2] if bend_angles_deg[-1] > 0 else top_pts[-2]
                pts_b = bot_pts[-1] if bend_angles_deg[-1] > 0 else top_pts[-1]
            else:
                pts_a = bot_pts[s_idx] if bend_angles_deg[s_idx - 1] > 0 else top_pts[s_idx]
                pts_b = bot_pts[s_idx + 1] if bend_angles_deg[s_idx] > 0 else top_pts[s_idx + 1]
            mid_x = (pts_a[0] + pts_b[0]) / 2.0
            mid_y = (pts_a[1] + pts_b[1]) / 2.0
            perp_rad = math.radians(seg_ang_deg + 90.0)
            off = -16.0 if (s_idx == 0 and bend_angles_deg[0] > 0) else 16.0
            msp.add_linear_dim(
                base=(mid_x + off * math.cos(perp_rad), mid_y + off * math.sin(perp_rad)),
                p1=pts_a,
                p2=pts_b,
                angle=seg_ang_deg,
                dimstyle=dimstyle,
                dxfattribs={"layer": "PNL_DIM"},
            ).render()
        msp.add_text(
            f"FORMED PROFILE (R_in={inner_radius:.0f}mm, T={thickness:.0f}mm, ANGLES={bend_angles_deg})",
            height=3.0,
            dxfattribs={"layer": "PNL_DIM", "style": "VN_ARIAL"},
        ).set_placement((prof_x0, prof_y0 - 28.0))

    bend_info = f" | BENDS: {len(bend_angles_deg)}x (R={inner_radius:.0f})" if bend_angles_deg else ""
    msp.add_text(
        f"MARK: {mark} | BUSBAR {phase.upper()} E-Cu {width:.0f}x{thickness:.0f}mm (1:1) | HOLES: {len(sorted_holes)}x Ø{hole_dia} ({bolt}){bend_info}",
        height=3.5,
        dxfattribs={"layer": "PNL_DIM", "style": "VN_ARIAL"},
    ).set_placement((0.0, top_dim_y + 10.0))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 1:1 2D Busbar Fabrication DXF with Bend Allowance & Native AutoCAD Dimensions")
    parser.add_argument("--from-csv", type=Path, default=None, help="Batch-generate DXFs from a Busbar Cut List CSV")
    parser.add_argument("--out-dir", type=Path, default=Path("DXF"), help="Output directory when using --from-csv")
    parser.add_argument("--mark", type=str, default="BB-01", help="Busbar part mark matching Panel BOM")
    parser.add_argument("--width", type=float, default=50.0, help="Busbar width in mm (e.g. 50)")
    parser.add_argument("--thickness", type=float, default=10.0, help="Busbar thickness in mm (e.g. 10)")
    parser.add_argument("--length", type=float, default=0.0, help="Straight busbar length in mm (if no segments)")
    parser.add_argument("--segments", type=str, default="", help="Comma-separated outer leg lengths for bent busbar")
    parser.add_argument("--angles", type=str, default="", help="Comma-separated bend angles in deg (e.g. 90,90)")
    parser.add_argument("--radius", type=float, default=0.0, help="Inner bend radius in mm (defaults to thickness)")
    parser.add_argument("--k-factor", type=float, default=0.42, help="Sheet metal K-factor for E-Cu (default 0.42)")
    parser.add_argument("--holes", type=str, default="", help="Comma-separated hole X coordinates on flat pattern")
    parser.add_argument("--bolt", type=str, default="M10", help="Bolt size (M6, M8, M10, M12, M16)")
    parser.add_argument("--phase", type=str, default="L1", help="Phase name (L1, L2, L3, N, PE)")
    parser.add_argument("--out", type=Path, default=None, help="Output DXF path for single busbar")
    args = parser.parse_args()

    if args.from_csv:
        with args.from_csv.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                mark = row["MARK"].strip()
                phase = row["PHASE"].strip()
                width = float(row["WIDTH_MM"])
                thickness = float(row["THICKNESS_MM"])
                bolt = row.get("BOLT", "M10").strip()
                holes = [float(x.strip()) for x in row["HOLES_X_MM"].split(";") if x.strip()]
                segs_str = row.get("SEGMENTS_MM", "").strip()
                angs_str = row.get("ANGLES_DEG", "").strip()
                inner_r = float(row.get("RADIUS_MM") or thickness)
                if segs_str:
                    segs = [float(x) for x in segs_str.split(";") if x.strip()]
                    angs = [float(x) for x in angs_str.split(";") if x.strip()]
                    flat_len, bend_c = compute_developed_length(segs, angs, thickness, inner_r, args.k_factor)
                else:
                    flat_len, bend_c, angs = float(row["LENGTH_MM"]), [], []
                out_file = args.out_dir / f"{mark}_{phase}.dxf"
                build_busbar_dxf(width, thickness, flat_len, holes, bend_c, angs, inner_r, bolt, phase, mark, out_file, k_factor=args.k_factor)
                print(f"Generated {out_file} (L_flat={flat_len:.1f} mm)")
        return

    if not args.holes or not args.out:
        raise ValueError("Provide --holes and --out for single-bar mode, or --from-csv for batch mode.")

    inner_r = args.radius if args.radius > 0 else args.thickness
    if args.segments:
        segs = [float(x.strip()) for x in args.segments.split(",") if x.strip()]
        angs = [float(x.strip()) for x in args.angles.split(",") if x.strip()]
        flat_length, bend_centers = compute_developed_length(segs, angs, args.thickness, inner_r, args.k_factor)
    else:
        if args.length <= 0:
            raise ValueError("Provide either --length for straight bar or --segments and --angles for bent bar.")
        flat_length, bend_centers, angs = args.length, [], []

    holes = [float(x.strip()) for x in args.holes.split(",") if x.strip()]
    build_busbar_dxf(
        args.width,
        args.thickness,
        flat_length,
        holes,
        bend_centers,
        angs,
        inner_r,
        args.bolt,
        args.phase,
        args.mark,
        args.out,
        k_factor=args.k_factor,
    )
    print(f"Generated busbar DXF: {args.out} (Developed Length L_flat = {flat_length:.1f} mm)")


if __name__ == "__main__":
    main()
