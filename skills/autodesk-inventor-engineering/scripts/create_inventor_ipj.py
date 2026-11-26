"""Generate a portable, workstation-independent Autodesk Inventor Project (.ipj) XML file.

Configures Workspace='.' and ContentCenter='.\\03_Purchased_Standard\\ContentCenter\\' so Pack-and-Go across
different engineering workstations results in 0 Broken Links.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def create_portable_ipj(project_dir: Path, project_code: str, project_name: str) -> Path:
    project_dir.mkdir(parents=True, exist_ok=True)
    for sub in (
        "01_Assemblies",
        "02_Parts",
        "03_Purchased_Standard/ContentCenter",
        "04_Drawings",
        "05_Exports",
        "06_BOM_Docs",
    ):
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    ipj_path = project_dir / f"{project_code}_{project_name}.ipj"
    # Autodesk Inventor native <Project> XML schema (preserves standard Metric Templates while keeping Workspace & ContentCenter portable)
    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<Project Version="1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.autodesk.com/Inventor/DesignProject/DesignProject.xsd">
  <Type>SingleUser</Type>
  <Name>{project_code}_{project_name}</Name>
  <UsingUniqueFileNames>true</UsingUniqueFileNames>
  <OldVersionsToKeep>3</OldVersionsToKeep>
  <Locations>
    <LocationType id="Workspace">
      <Path Name="Workspace">.</Path>
    </LocationType>
    <LocationType id="Workgroup">
      <Path Name="Assemblies">.\\01_Assemblies\\</Path>
      <Path Name="Parts">.\\02_Parts\\</Path>
      <Path Name="Purchased">.\\03_Purchased_Standard\\</Path>
      <Path Name="Drawings">.\\04_Drawings\\</Path>
    </LocationType>
  </Locations>
  <FolderOptions>
    <ContentCenterFiles>.\\03_Purchased_Standard\\ContentCenter\\</ContentCenterFiles>
  </FolderOptions>
</Project>
"""
    ipj_path.write_text(xml_content, encoding="utf-8")
    return ipj_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create portable Inventor .ipj project structure")
    parser.add_argument("--dir", type=Path, required=True, help="Root project directory")
    parser.add_argument("--code", type=str, required=True, help="ProjectCode (e.g. NHC)")
    parser.add_argument("--name", type=str, required=True, help="PascalCase ProjectName (e.g. Cabinet)")
    args = parser.parse_args()
    out = create_portable_ipj(args.dir, args.code, args.name)
    print(f"Created portable Inventor project: {out}")


if __name__ == "__main__":
    main()
