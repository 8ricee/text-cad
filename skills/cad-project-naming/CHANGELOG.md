# Changelog

## [v1.3.0] - 2026-11-26
### Changed
- Upgraded Section 2 (`Mandatory Execution Gate`) into a **Dual Gate** requiring both Administrative inputs (project code, storage path, standard, format) and minimal Technical inputs (voltage/earthing, $I_{cu}$, IP/material, cable entry for panels; load, thickness, $R_{\text{in}}$, mounting holes for sheet metal/mechanical) before generating drawings.
- Synchronized Section 4 file naming: removed `_R00` suffix from active working `.dwg`/`.dxf`/`.ipt`/`.iam`/`.idw` files (revisions managed via Git and Title Block `REV` attribute; `_R[XX]` reserved for static exports in `03_Issued_PDF/` and `05_Exports/`), and allowed `[SheetNo]_[ProjectCode]-[Discipline]-[DocType]-[Description].dwg` for AutoCAD Electrical `.wdp` sheets.

## [v1.2.0] - 2026-11-26
### Changed
- Enforced strict world-class ISO 128 / ASME Y14.100 separation in `SKILL.md` (Section 6): ALL geometry (including enlarged detail views `Detail A..D` and 3D views) MUST be drawn at `1:1 mm` in Model Space and displayed on Paper Space `Layout` exclusively via calibrated `VIEWPORT`s (never drawn directly in Paper Space).

## [v1.1.1] - 2026-11-25
### Changed
- Explicitly prohibited drawing sheet borders (`BORDER`) or Title Blocks inside **Model Space** on any AutoCAD drawing (mechanical, panel layout, busbar, or schematic); 100% of frames, title blocks, and schedules must reside on **Paper Space (`Layout`)**.

## [v1.1.0] - 2026-11-25
### Changed
- Enforced strict AutoCAD geometric & dimensioning constraints in `SKILL.md` (Section 6) and `README.md`: mandatory `1:1 mm` Model Space (`$INSUNITS = 4`), Paper Space `Layout` with scaled `VIEWPORT`s, and 100% native AutoCAD `DIMENSION` entities (`dimlfac = 1.0`, prohibiting hand-drawn `LINE` + `TEXT` fake dimensions).

## [v1.0.0] - 2026-11-25
### Added
- Initial release of `cad-project-naming` skill (`SKILL.md`) covering AutoCAD and Autodesk Inventor folder structure, file naming conventions, mandatory 3-step execution gate, and confirmation output template.
