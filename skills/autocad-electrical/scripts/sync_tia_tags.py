"""Bidirectional Converter between AutoCAD Electrical (CSV / AEEXPORT) and Siemens TIA Portal (PLC Tags CSV & AutomationML .aml).

Supported modes:
1. --mode acade-to-tia : Convert ACADE PLC I/O CSV (or AEEXPORT CSV) -> TIA Portal PLC Tags CSV
   - Filters out secondary channels of 1oo2 Fail-Safe DI pairs (:CH2 / 1oo2 DUAL CH8).
   - Infers Data Type ('Bool' for %I/%Q, 'Int' for %IW/%QW, 'DInt' for %ID/%QD).
   - Generates symbolic tag names from TAG + DESC1 and preserves Vietnamese Unicode comments from DESC2.
2. --mode tia-to-acade : Convert TIA Portal exported PLC Tags CSV -> ACADE Spreadsheet to PLC I/O CSV
   - Assigns standard S7-1500 Slot >= 2 and maps standard Wire Type Layers (SIG_PLC_BU_0.5, CTRL_24VDC_DBU_0.75, SAFE_24VDC_YE_0.75).
3. --mode export-aml   : Export hardware rack/slot & I/O tag mapping to AutomationML (.aml) XML for TIA Selection Tool / TIA Portal Openness.

Usage:
    python sync_tia_tags.py --mode acade-to-tia --in ../templates/plc_io_import_template.csv --out tia_plc_tags.csv
    python sync_tia_tags.py --mode tia-to-acade --in tia_plc_tags.csv --out acade_plc_import.csv
    python sync_tia_tags.py --mode export-aml --in ../templates/plc_io_import_template.csv --out plc_hardware.aml
"""

import argparse
import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def infer_tia_data_type(address: str) -> str:
    """Infer Siemens TIA Portal data type from IEC address (%I0.0 -> Bool, %IW64 -> Int, %ID100 -> DInt)."""
    addr = address.strip().upper()
    if addr.startswith(("%IW", "%QW", "%MW", "IW", "QW", "MW")):
        return "Int"
    if addr.startswith(("%ID", "%QD", "%MD", "ID", "QD", "MD")):
        return "DInt"
    return "Bool"


def make_symbolic_name(address: str, desc1: str, tag: str) -> str:
    """Build a clean PascalCase / IEC symbolic tag name from address prefix and English description."""
    addr = address.strip().upper().lstrip("%")
    prefix = addr[:2] if len(addr) >= 2 and addr[1] in ("W", "D", "B") else addr[:1]
    clean_words = re.findall(r"[A-Za-z0-9]+", desc1)
    pascal = "".join(w.capitalize() for w in clean_words[:5])
    clean_tag = re.sub(r"[^A-Za-z0-9]", "", tag.split(":")[0])
    return f"{prefix}_{clean_tag}_{pascal}" if clean_tag else f"{prefix}_{pascal}"


def is_secondary_1oo2_channel(row: dict[str, str]) -> bool:
    """Return True if this row is the secondary channel of a 1oo2 Fail-Safe pair that TIA handles internally."""
    tag = (row.get("TAG") or row.get("DEV_TAG") or "").upper()
    desc3 = (row.get("DESC3") or "").upper()
    return tag.endswith(":CH2") or ("1OO2" in desc3 and "CH8" in desc3)


def convert_acade_to_tia(in_csv: Path, out_csv: Path) -> int:
    """Convert ACADE PLC I/O CSV (or AEEXPORT Component CSV) to TIA Portal PLC Tag Table import CSV."""
    with in_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    tia_rows: list[dict[str, str]] = []
    for row in rows:
        if is_secondary_1oo2_channel(row):
            continue
        addr = (row.get("ADDRESS") or row.get("ADDR") or "").strip()
        if not addr:
            continue
        desc1 = (row.get("DESC1") or "").strip()
        desc2 = (row.get("DESC2") or "").strip()
        tag = (row.get("TAG") or row.get("DEV_TAG") or "").strip()
        wtype = (row.get("WIRETYPE") or "").upper()
        dtype = infer_tia_data_type(addr)
        sym_name = make_symbolic_name(addr, desc1, tag)
        table_path = "Safety_IO_Tags" if "SAFE" in wtype else "Standard_IO_Tags"

        tia_rows.append(
            {
                "Name": sym_name,
                "Path": table_path,
                "Data Type": dtype,
                "Logical Address": addr if addr.startswith("%") else f"%{addr}",
                "Comment": f"{desc1} / {desc2} ({tag})" if desc2 else f"{desc1} ({tag})",
                "Hmi Visible": "True",
                "Hmi Accessible": "True",
                "Hmi Writeable": "False" if addr.lstrip("%").upper().startswith("I") else "True",
            }
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Name",
        "Path",
        "Data Type",
        "Logical Address",
        "Comment",
        "Hmi Visible",
        "Hmi Accessible",
        "Hmi Writeable",
    ]
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tia_rows)

    return len(tia_rows)


def convert_tia_to_acade(in_csv: Path, out_csv: Path) -> int:
    """Convert TIA Portal PLC Tags CSV -> ACADE Spreadsheet to PLC I/O CSV format (matches default_plc_io.wdi)."""
    with in_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    acade_rows: list[dict[str, str]] = []
    for idx, row in enumerate(rows):
        addr = (row.get("Logical Address") or "").strip()
        if not addr:
            continue
        path_name = (row.get("Path") or "").upper()
        comment = (row.get("Comment") or "").strip()
        # Split bilingual comment "EN / VI (-TAG)"
        tag_match = re.search(r"\(([-+A-Za-z0-9_:]+)\)\s*$", comment)
        tag = tag_match.group(1) if tag_match else f"-DEV{idx + 1}"
        clean_comment = re.sub(r"\s*\(([-+A-Za-z0-9_:]+)\)\s*$", "", comment)
        parts = [p.strip() for p in clean_comment.split("/", 1)]
        desc1 = parts[0] if parts else row.get("Name", "")
        desc2 = parts[1] if len(parts) > 1 else ""

        upper_addr = addr.lstrip("%").upper()
        tag_alpha = tag.upper().lstrip("-=+0123456789")
        # Column BLOCK (BLK_NAME = B in default_plc_io.wdi) must be a real peripheral symbol in Libs\iec-60617
        if "SAFETY" in path_name:
            code, block, slot, wtype, loc_def = "6ES7526-1BH00-0AB0", "VSW12", "4", "SAFE_24VDC_YE_0.75", "+DOOR"
        elif upper_addr.startswith("IW"):
            code, block, slot, wtype, loc_def = "6ES7531-7KF00-0AB0", "", "5", "SIG_PLC_BU_0.5", "+FIELD"
        elif upper_addr.startswith("Q"):
            if tag_alpha.startswith("H"):
                code, block, slot, wtype, loc_def = "6ES7522-1BH01-0AB0", "VLT1A", "3", "CTRL_24VDC_DBU_0.75", "+DOOR"
            elif tag_alpha.startswith("Y"):
                code, block, slot, wtype, loc_def = "6ES7522-1BH01-0AB0", "VSV1", "3", "CTRL_24VDC_DBU_0.75", "+FIELD"
            else:
                code, block, slot, wtype, loc_def = "6ES7522-1BH01-0AB0", "VCR1", "3", "CTRL_24VDC_DBU_0.75", "+MAIN_PNL"
        else:
            if tag_alpha.startswith("K"):
                code, block, slot, wtype, loc_def = "6ES7521-1BH00-0AB0", "VCR1", "2", "SIG_PLC_BU_0.5", "+MAIN_PNL"
            elif tag_alpha.startswith("SQ") or tag_alpha.startswith("B"):
                code, block, slot, wtype, loc_def = "6ES7521-1BH00-0AB0", "VPX1", "2", "SIG_PLC_BU_0.5", "+FIELD"
            else:
                code, block, slot, wtype, loc_def = "6ES7521-1BH00-0AB0", "VPB11", "2", "SIG_PLC_BU_0.5", "+DOOR"

        acade_rows.append(
            {
                "CODE": code,
                "BLOCK": block,
                "RACK": "0",
                "SLOT": slot,
                "ADDRESS": addr if addr.startswith("%") else f"%{addr}",
                "TAG": tag,
                "DESC1": desc1,
                "DESC2": desc2,
                "DESC3": f"CH{idx}",
                "TERMDESC": upper_addr,
                "WIRETYPE": wtype,
                "LOC": loc_def,
                "INST": "=PLC1",
            }
        )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "CODE",
        "BLOCK",
        "RACK",
        "SLOT",
        "ADDRESS",
        "TAG",
        "DESC1",
        "DESC2",
        "DESC3",
        "TERMDESC",
        "WIRETYPE",
        "LOC",
        "INST",
    ]
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(acade_rows)

    return len(acade_rows)


def export_automation_ml(in_csv: Path, out_aml: Path) -> int:
    """Export ACADE PLC Rack/Slot/Channel CSV to an AutomationML (.aml) CAEX file for TIA Portal Openness."""
    with in_csv.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    root = ET.Element("CAEXFile", FileName=out_aml.name, SchemaVersion="2.15")
    inst_hierarchy = ET.SubElement(root, "InstanceHierarchy", Name="TIA_ACADE_HardwareSync")
    rack_elem = ET.SubElement(inst_hierarchy, "InternalElement", Name="Rack_0_S71500")

    slots: dict[str, ET.Element] = {}
    count = 0
    for row in rows:
        slot_no = (row.get("SLOT") or "2").strip()
        code = (row.get("CODE") or "").strip()
        slot_key = f"Slot_{slot_no}_{code}"
        if slot_key not in slots:
            slots[slot_key] = ET.SubElement(
                rack_elem,
                "InternalElement",
                Name=slot_key,
                OrderNumber=code,
                SlotNumber=slot_no,
            )
        ch_elem = ET.SubElement(
            slots[slot_key],
            "InternalElement",
            Name=(row.get("TERMDESC") or f"CH_{count}").strip(),
            Address=(row.get("ADDRESS") or "").strip(),
            ComponentTag=(row.get("TAG") or "").strip(),
        )
        desc1 = (row.get("DESC1") or "").strip()
        desc2 = (row.get("DESC2") or "").strip()
        ET.SubElement(ch_elem, "Attribute", Name="Comment").text = f"{desc1} / {desc2}"
        count += 1

    out_aml.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(out_aml, encoding="utf-8", xml_declaration=True)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Bidirectional ACADE <-> Siemens TIA Portal / AutomationML Sync")
    parser.add_argument(
        "--mode",
        choices=["acade-to-tia", "tia-to-acade", "export-aml"],
        default="acade-to-tia",
        help="Conversion direction or AutomationML export",
    )
    parser.add_argument("--in", dest="in_path", type=Path, required=True, help="Input file path")
    parser.add_argument("--out", dest="out_path", type=Path, required=True, help="Output file path")
    args = parser.parse_args()

    if args.mode == "acade-to-tia":
        n = convert_acade_to_tia(args.in_path, args.out_path)
        print(f"Converted {n} ACADE rows -> TIA Portal PLC Tags at: {args.out_path}")
    elif args.mode == "tia-to-acade":
        n = convert_tia_to_acade(args.in_path, args.out_path)
        print(f"Converted {n} TIA Portal tags -> ACADE PLC I/O CSV at: {args.out_path}")
    else:
        n = export_automation_ml(args.in_path, args.out_path)
        print(f"Exported {n} PLC channels -> AutomationML (.aml) at: {args.out_path}")


if __name__ == "__main__":
    main()
