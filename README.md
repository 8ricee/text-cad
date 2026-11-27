# text-cad

Unified repository for **AutoCAD Electrical (ACADE)**, **Autodesk Inventor**, **Parametric CAD / 2D DXF**, **DFM / DfAM**, **G-code / 3D Printing**, and **Robot Description (URDF / SRDF / SDF)** engineering skills and in-process `.NET 10` Named Pipe MCP servers.

## Repository Structure

- `skills/` — 15 CAD, Inventor, Manufacturing, and Robotics engineering skills:
  - `autocad-electrical/` — Native ACADE 2027 standards, `TEMPLATE_IEC_A3.dwt`, `TEMPLATE_PROJECT.wdp`, `.rgf`, ODBC `.mdb` seeder, Scratch DB Gatekeeper, and TIA Portal sync.
  - `autodesk-inventor-engineering/` — Inventor Professional 2027 `.NET 10` API & iLogic workflow (Master Skeleton, Sheet Metal, Weldment, Flat Pattern DXF).
  - `cad-project-naming/` — Strict ASCII semantic naming and folder standards for AutoCAD & Inventor.
  - `cad/`, `dxf/`, `engineering-drawing/`, `step-parts/` — Parametric CAD, 2D DXF generation, ISO engineering drawings, and standard parts lookup.
  - `dfm/`, `dfam-check/`, `sendcutsend/`, `gcode/`, `bambu-labs/` — Design for Manufacturing / Additive Manufacturing, slicing, and 3D printing.
  - `urdf/`, `srdf/`, `sdf/` — Robot & simulation model authoring and validation.
- `addins/` — In-process `.NET 10` (`net10.0-windows`) CAD Add-ins with Named Pipe JSON-RPC & atomic `Transaction` rollback:
  - `autocad/Agy.AutoCadBridge/` — AutoCAD / ACADE 2027 `IExtensionApplication` (`\\.\pipe\agy-autocad-direct`).
  - `inventor/Agy.InventorBridge/` — Inventor 2027 `ApplicationAddInServer` (`\\.\pipe\agy-inventor-direct`).
- `mcp_servers/` — Zero-dependency Stdio → Named Pipe MCP servers:
  - `pipe_client.py` — Win32 `kernel32` Named Pipe JSON-RPC client.
  - `autocad_mcp_server.py` (`autocad-direct` v3.0.0 — AutoCAD `.NET` Transactions + ACADE `c:wd_*` API + `odbc32.dll` `.mdb` queries).
  - `inventor_mcp_server.py` (`inventor-direct` v2.0.0 — Inventor `.NET` Transactions + in-process iLogic execution).
- `docs/work-status.md` — Cross-session Git and scope continuity record.
