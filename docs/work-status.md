# Work Status — `text-cad`

- **Active Branch & Base Tag**: `feat/dotnet-named-pipe-addins` (branched from `main` `v1.8.1`, preparing `v2.0.0`)
- **Working Directory & Remote**: `F:\Projects\CAD\text-cad` → `https://github.com/8ricee/text-cad.git` (`origin`)
- **Active Scope**: `addins/autocad/Agy.AutoCadBridge/*`, `addins/inventor/Agy.InventorBridge/*`, `mcp_servers/*`, `skills/autocad-electrical/SKILL.md`, `skills/autodesk-inventor-engineering/*`, `README.md`, `CHANGELOG.md`, `docs/work-status.md`
- **Protected Scope**: Other 13 CAD/DFM/Robotics skills under `skills/*` and ACADE templates/catalogs
- **Last Change**: Built and deployed `.NET 10` in-process Add-ins (`Agy.AutoCadBridge.dll` & `Agy.InventorBridge.dll`) and upgraded `autocad-direct` (`v3.0.0`) and `inventor-direct` (`v2.0.0`) to pure Named Pipe JSON-RPC with atomic `Transaction` rollback and zero PowerShell COM dependencies.
- **Next Step**: Verify end-to-end Named Pipe + `Transaction` commit/rollback tests on live AutoCAD 2027 & Inventor 2027, commit atomically, merge to `main`, and push to `origin`.
