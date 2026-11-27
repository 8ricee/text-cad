# Changelog — `autocad-electrical`

## v1.8.1 — 2026-11-27
- **Zero-Bug Runtime Patch (`autocad_mcp_server.py`)**: Fixed missing `import os`, fixed `ox -> x0` in `STAR_DELTA_3P` and `SAFETY_3SK1_2CH`, replaced coil `VCR1` misuse on 3-phase power feeders with 3-pole power contacts `VCR21` + mechanical `LINK` interlock, compiled dedicated `VK1_SAFE.dwg` (`3SK1111-1AB30`) + `VPB12/VPB22` dual-channel E-Stop, and added verified `3RV2021-4DA10` / `1LE1001-1CB23` catalog & footprint rows.
- **Multi-Sheet PLC Auto-Pagination & Database Seeding**: Returned `has_more_pages` / `total_pages` metadata from `acade_build_plc_from_csv`, auto-created `06b_plc_io_wiring.dwg` in `build_project_drawings.py` so `Slot 4 F-DI16` is never dropped, populated `RATING1..4` dynamically in `seed_acade_databases.py`, and inferred accurate `+DOOR` / `+MAIN_PNL` / `+FIELD` locations in `sync_tia_tags.py`.
- **Gatekeeper v3.2 (`acade_electrical_audit.py`) & MCP Schema Sync**: Replaced `GetSchema("Columns")` (`HYC00` ODBC crash) with `SELECT TOP 1 *` column inspection, enforced real `_PINLIST` contact-pair quota (`PINLIST_QUOTA_EXCEEDED`), added headless DWG `SIGARR` cross-sheet voltage-domain short detection, and synchronized all 16 `autocad-direct` MCP JSON schemas.

## v1.8.0 — 2026-11-27
- Added 10 Hard Guardrails to `SKILL.md`, unified `CTRL_0VDC_BUWH_0.75` and `PNL_FOOTPRINT`, separated IEC 60445 vs TCVN 3-phase color profiles, fixed `3RT2026-1BB40` `PINLIST` ordering, and introduced Fail-Closed panel footprint sync.

## v1.7.0 — 2026-11-27
- **100% Paper Space Layout (`ISO_A3`, `$TILEMODE=0`) across ALL drawings (`01..09`)**: Removed all borders and Title Blocks from `Model Space` in `TEMPLATE_IEC_A3.dwt` and `TEMPLATE_PANEL_LAYOUT_A3.dwt` (`MODEL_TB = 0`, `PAPER_TB = 1`, Display-Locked `1:1` and `1:10` `VIEWPORT`s, ISO 5456-2 Third-Angle Projection symbol, and all invisible system attributes strictly inside `[240..340, 8.0]`).
- **Multi-Pole Switching (`poles=2|3|4`) & Verified Industrial Circuit Macros (`acade_insert_verified_circuit`)**: Added linked multi-pole insertion (`VCB11Q13 + VCB21Q13`, `VFU1 + VFU2`, `VCR21`, `VDS11 + VDS21` with mechanical `LINK` line cutting all phase wires), Safe Zone guard (`[25..405, 12..276]`), 2-column A3 PLC sheet overflow guard (`my=256`), and pre-verified circuit macros (`BUS_3PH_N_PE`, `DOL_3P`, `VFD_3P`, `PSU_24VDC_PELV`).
- **Gatekeeper v3.0 (`Electrical Netlist DRC` + `Layout Gatekeeper`)**: Added graph-based netlist verification in `acade_electrical_audit.py` to block `modelspace_titleblock_violations`, `short_circuit_nets` (`PE` shorted to live phase or `AC_N` shorted to `DC_0V`), `unprotected_3phase_poles` (single-pole CB leaving `L2/L3` live), and `text_or_attr_overflows`.

## v1.6.0 — 2026-11-27
- Added Parent/Child & IEC 60617 family guards, 3 custom `.dwg` schematic blocks (`VG1_PSU_24V`, `VU1_VFD_3P`, `VA4_NET_BOX`), 24 verified footprints, auto wire-splitting, `WDDOT` deduplication, and horizontal closed-circuit PLC I/O rungs.

## v1.5.2 — 2026-11-26
- Native ACADE 2027 COM/AutoLISP engine (`c:wd_*`), Access `.mdb` ODBC seeding, and Gatekeeper v1.0.
