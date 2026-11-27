# Changelog

## v1.7.0 — 2026-11-27
- **100% Paper Space Layout (`ISO_A3`, `$TILEMODE=0`) across ALL drawings (`01..09`)**: Removed all borders and Title Blocks from `Model Space` in `TEMPLATE_IEC_A3.dwt` and `TEMPLATE_PANEL_LAYOUT_A3.dwt` (`MODEL_TB = 0`, `PAPER_TB = 1`, Display-Locked `1:1` and `1:10` `VIEWPORT`s, ISO 5456-2 projection symbol).
- **Multi-Pole Switching (`poles=2|3|4`) & Verified Industrial Circuit Macros (`acade_insert_verified_circuit`)**: Added linked multi-pole insertion (`VCB11Q13 + VCB21Q13`, `VFU1 + VFU2`, `VCR21`, `VDS11 + VDS21` with mechanical `LINK` line cutting all phase wires), Safe Zone guard (`[25..405, 12..276]`), 2-column A3 PLC sheet overflow guard (`my=256`), and pre-verified circuit macros (`BUS_3PH_N_PE`, `DOL_3P`, `VFD_3P`, `PSU_24VDC_PELV`).
- **Gatekeeper v3.0 (`Electrical Netlist DRC` + `Layout Gatekeeper`)**: Added graph-based netlist verification in `acade_electrical_audit.py` to block `modelspace_titleblock_violations`, `short_circuit_nets` (`PE` shorted to live phase or `AC_N` shorted to `DC_0V`), `unprotected_3phase_poles` (single-pole CB leaving `L2/L3` live), and `text_or_attr_overflows`.

## v1.6.0 — 2026-11-27
- Patched `skills/autocad-electrical` and `mcp_servers/autocad_mcp_server.py` with Parent/Child & IEC 60617 family guards, 3 custom `.dwg` schematic blocks (`VG1_PSU_24V`, `VU1_VFD_3P`, `VA4_NET_BOX`), 24 verified footprints, auto wire-splitting, `WDDOT` deduplication, and horizontal closed-circuit PLC I/O rungs.

## v1.0.0 — 2026-11-26
- Initialized unified `text-cad` repository combining 15 CAD / Inventor / Manufacturing / Robotics skills and 2 direct COM MCP servers (`autocad_mcp_server.py`, `inventor_mcp_server.py`).
