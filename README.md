# text-cad

Unified repository for **AutoCAD Electrical (ACADE)**, **Autodesk Inventor**, **Parametric CAD / 2D DXF**, **DFM / DfAM**, **G-code / 3D Printing**, and **Robot Description (URDF / SRDF / SDF)** engineering skills and direct COM MCP servers.

## Repository Structure

- `skills/` — 15 CAD, Inventor, Manufacturing, and Robotics engineering skills:
  - `autocad-electrical/` — Native ACADE 2027 standards, `TEMPLATE_IEC_A3.dwt`, `TEMPLATE_PROJECT.wdp`, `.rgf`, ODBC `.mdb` seeder, Scratch DB Gatekeeper, and TIA Portal sync.
  - `autodesk-inventor-engineering/` — Inventor Professional COM API & iLogic workflow (Master Skeleton, Sheet Metal, Weldment, Flat Pattern DXF).
  - `cad-project-naming/` — Strict ASCII semantic naming and folder standards for AutoCAD & Inventor.
  - `cad/`, `dxf/`, `engineering-drawing/`, `step-parts/` — Parametric CAD, 2D DXF generation, ISO engineering drawings, and standard parts lookup.
  - `dfm/`, `dfam-check/`, `sendcutsend/`, `gcode/`, `bambu-labs/` — Design for Manufacturing / Additive Manufacturing, slicing, and 3D printing.
  - `urdf/`, `srdf/`, `sdf/` — Robot & simulation model authoring and validation.
- `mcp_servers/` — Direct Windows COM MCP servers:
  - `autocad_mcp_server.py` (`autocad-direct` v2.0.0 — AutoCAD + native ACADE `c:wd_*` API)
  - `inventor_mcp_server.py` (`inventor-direct` — Autodesk Inventor COM automation)
- `docs/work-status.md` — Cross-session Git and scope continuity record.
