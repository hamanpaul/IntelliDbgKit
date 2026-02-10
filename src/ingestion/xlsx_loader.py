from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
from zipfile import ZipFile


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass(slots=True)
class SheetRef:
    name: str
    xml_path: str


def _compact_spaces(text: str) -> str:
    return " ".join(text.replace("\n", " ").split()).strip()


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        return 0
    value = 0
    for character in match.group(1):
        value = value * 26 + (ord(character) - 64)
    return value - 1


def _shared_strings(zip_file: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("main:si", NS):
        text = "".join((node.text or "") for node in item.findall(".//main:t", NS))
        values.append(text)
    return values


def _sheet_refs(zip_file: ZipFile) -> list[SheetRef]:
    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rels = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("pkgrel:Relationship", NS)
    }
    refs: list[SheetRef] = []
    for sheet in workbook.findall("main:sheets/main:sheet", NS):
        rid = sheet.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id",
            "",
        )
        target = rel_map.get(rid, "")
        if not target:
            continue
        refs.append(SheetRef(name=sheet.attrib.get("name", ""), xml_path=f"xl/{target}"))
    return refs


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    value_elem = cell.find("main:v", NS)
    inline_elem = cell.find("main:is/main:t", NS)
    if cell_type == "s" and value_elem is not None and value_elem.text is not None:
        return shared[int(value_elem.text)]
    if cell_type == "inlineStr" and inline_elem is not None:
        return inline_elem.text or ""
    if value_elem is not None and value_elem.text is not None:
        return value_elem.text
    return ""


def _row_values(row_elem: ET.Element, shared: list[str]) -> dict[int, str]:
    values: dict[int, str] = {}
    for cell in row_elem.findall("main:c", NS):
        cell_ref = cell.attrib.get("r", "A1")
        column = _column_index(cell_ref)
        values[column] = _compact_spaces(_cell_text(cell, shared))
    return values


def _canonical_header(header: str) -> str | None:
    normalized = _compact_spaces(header).lower()
    if not normalized:
        return None
    if normalized in {"object", "datamodel"}:
        return "object_path"
    if normalized in {"parameter name", "parameter"}:
        return "parameter_name"
    if "hlapi" in normalized:
        return "hlapi_command"
    if normalized == "llapi":
        return "llapi_support"
    if "test steps" in normalized:
        return "test_steps"
    if "command output" in normalized:
        return "command_output"
    if "test result" in normalized:
        return "result_status"
    if "comment" in normalized:
        return "comment"
    if "implemented by" in normalized:
        return "implemented_by"
    if "description" in normalized:
        return "description"
    return None


def _priority(header: str) -> int:
    normalized = _compact_spaces(header).lower()
    if "bcm v4.0.3" in normalized:
        return 0
    if "4.0.1" in normalized:
        return 1
    return 2


def _select_header_columns(header_row: dict[int, str]) -> dict[str, int]:
    candidate_map: dict[str, list[tuple[int, int]]] = {}
    for column, title in header_row.items():
        canonical = _canonical_header(title)
        if canonical is None:
            continue
        candidate_map.setdefault(canonical, []).append((_priority(title), column))
    selected: dict[str, int] = {}
    for canonical, candidates in candidate_map.items():
        candidates.sort(key=lambda item: (item[0], item[1]))
        selected[canonical] = candidates[0][1]
    return selected


def _normalize_result(value: str) -> str:
    text = _compact_spaces(value).lower()
    if not text:
        return "unknown"
    if "not support" in text:
        return "not-supported"
    if text in {"n/a", "na", "skip"} or "skip" in text:
        return "skip"
    if "pass" in text:
        return "pass"
    if "fail" in text:
        return "fail"
    return "unknown"


def _required_payload_has_data(record: dict[str, Any]) -> bool:
    keys = (
        "object_path",
        "parameter_name",
        "hlapi_command",
        "llapi_support",
        "test_steps",
        "command_output",
        "comment",
    )
    return any(record.get(key, "") for key in keys)


def load_hlapi_testcases(
    source_file: str | Path,
    start_sheet: str = "QoS_LLAPI",
) -> list[dict[str, Any]]:
    source_path = Path(source_file)
    cases: list[dict[str, Any]] = []
    with ZipFile(source_path) as zip_file:
        shared = _shared_strings(zip_file)
        sheets = _sheet_refs(zip_file)
        start_index = 0
        for index, ref in enumerate(sheets):
            if ref.name == start_sheet:
                start_index = index
                break
        target_sheets = sheets[start_index:]

        for ref in target_sheets:
            sheet_root = ET.fromstring(zip_file.read(ref.xml_path))
            rows = sheet_root.findall("main:sheetData/main:row", NS)
            if not rows:
                continue

            header_row = _row_values(rows[0], shared)
            column_map = _select_header_columns(header_row)
            if not column_map:
                continue

            for row_elem in rows[1:]:
                row_number = int(row_elem.attrib.get("r", "0"))
                row_map = _row_values(row_elem, shared)
                row_data: dict[str, Any] = {
                    "case_id": f"{ref.name}-r{row_number}",
                    "source_file": str(source_path),
                    "source_sheet": ref.name,
                    "source_row": row_number,
                }
                for field in (
                    "object_path",
                    "parameter_name",
                    "hlapi_command",
                    "llapi_support",
                    "test_steps",
                    "command_output",
                    "comment",
                    "implemented_by",
                    "description",
                ):
                    column = column_map.get(field)
                    row_data[field] = row_map.get(column, "") if column is not None else ""

                result_column = column_map.get("result_status")
                result_raw = row_map.get(result_column, "") if result_column is not None else ""
                row_data["result_status"] = _normalize_result(result_raw)
                row_data["tags"] = ["llapi", ref.name]

                if not _required_payload_has_data(row_data):
                    continue
                cases.append(row_data)
    return cases
