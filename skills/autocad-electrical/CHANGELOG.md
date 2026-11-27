# Changelog — `autocad-electrical`

## v1.6.0 — 2026-11-27
- Replaced Child contact `VMS2NA13F` with Parent MPCB/CB symbols (`VCB11Q13` / `VMS1NA21F`) and enforced hard Parent/Child (`TAG1` vs `TAG2`) and IEC 60617 family guards (`U`/`G`/`A` forbidden on `VCR1`/`HCR1`) in `autocad_mcp_server.py`.
- Compiled 3 dedicated schematic `.dwg` blocks (`VG1_PSU_24V`, `VU1_VFD_3P`, `VA4_NET_BOX`) into `Libs\iec-60617\` and expanded `verified_footprints_catalog.csv` (24 footprints) & `catalog_master_seed.csv` (23 catalogs) for S7-1500 I/O, SCALANCE switch, EOL resistor, and pilot devices.
- Added `templates/TEMPLATE_PANEL_LAYOUT_A3.dwt` (`$TILEMODE=0`, Paper Space `ISO_A3` 1:10 `VIEWPORT`) and embedded `WD_TB` inside `TITLE_BLOCK_A3_BILINGUAL` across both `.dwt` templates, with deterministic `WD_M.SHEET` and Title Block attribute stamping across all sheets.
- Upgraded `acade_insert_schematic_symbol` (auto wire-break across opposite pins), `acade_draw_smart_wires_and_arrows` (`WDDOT` deduplication), `acade_build_plc_from_csv` (`V*->H*` horizontal rung mapping + intermediate `ht0001` + closed-circuit `+24VDC`/`0VDC` rails), `acade_sync_panel_footprints` (`PNL_FOOTPRINT` layer + fallback footprint generator), and `acade_electrical_audit.py` (Gatekeeper v2.0 headless `.dwg` + `.mdb` inspection).

## v1.5.2 — 2026-11-26
- Native ACADE 2027 COM/AutoLISP engine (`c:wd_*`), Access `.mdb` ODBC seeding, and Gatekeeper v1.0.
