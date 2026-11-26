# Autodesk Inventor Engineering Skill

Industrial Autodesk Inventor (`.ipj`, `.ipt`, `.iam`, `.idw`, Sheet Metal & Weldments) workflow, DFM rules, iLogic automation templates, and direct COM MCP integration (`inventor-direct`).

## Contents

- `SKILL.md`: Mandatory workflow, Dual Gate checks, Sheet Metal / Weldment DFM rules, and MCP tool protocol.
- `scripts/create_inventor_ipj.py`: Generates a clean XML `.ipj` project file with standard Content Center and local library paths.
- `templates/export_sheet_metal_and_idw.iLogicVb`: iLogic rule template to unfold Sheet Metal flat patterns to 1:1 DXF and export IDW/DWG sheets to PDF.

## Requirements

- Autodesk Inventor installed on Windows (for `inventor-direct` COM MCP server).
- Python 3.13+ (standard library only for `create_inventor_ipj.py` and `inventor_mcp_server.py`).
