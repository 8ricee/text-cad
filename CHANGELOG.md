# Changelog

## v1.6.0 — 2026-11-27
- Patched `skills/autocad-electrical` and `mcp_servers/autocad_mcp_server.py` to eliminate all 6 root-cause schematic, PLC I/O, Title Block, and Panel Layout defects:
  - Enforced IEC 60617 Parent/Child (`TAG1` vs `TAG2`) and family (`U`/`G`/`A` vs `VCR1`/`HCR1`) guards + auto wire-splitting across component pins and `WDDOT` deduplication.
  - Added dedicated schematic symbols (`VG1_PSU_24V`, `VU1_VFD_3P`, `VA4_NET_BOX`) and expanded S7-1500 I/O, PROFINET switch, EOL resistor, and pilot footprints (24 total).
  - Created `TEMPLATE_PANEL_LAYOUT_A3.dwt` (`TILEMODE=0` Paper Space `ISO_A3` 1:10 `VIEWPORT`), embedded `WD_TB` in `TITLE_BLOCK_A3_BILINGUAL`, and enforced deterministic `WD_M.SHEET` + Title Block attribute sync across all `.wdp` sheets.
  - Upgraded `acade_build_plc_from_csv` (`V*->H*` horizontal rung mapping + `ht0001` terminals + closed-circuit `+24VDC`/`0VDC` rails) and `acade_electrical_audit.py` (Gatekeeper v2.0 `.mdb` + headless `.dwg` verification).

## v1.0.0 — 2026-11-26
- Initialized unified `text-cad` repository combining 15 CAD / Inventor / Manufacturing / Robotics skills and 2 direct COM MCP servers (`autocad_mcp_server.py`, `inventor_mcp_server.py`).
- Included native AutoCAD Electrical 2027 workflow (`TEMPLATE_IEC_A3.dwt`, `TEMPLATE_PROJECT.wdp`, `project_master_reports.rgf`, `seed_acade_databases.py`, `acade_electrical_audit.py`).
