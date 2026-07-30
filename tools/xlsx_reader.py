from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
import re
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"x": MAIN_NS, "r": REL_NS, "pr": PACKAGE_REL_NS}
BUILTIN_DATE_FORMATS = set(range(14, 23)) | set(range(45, 48))


class XlsxReadError(ValueError):
    pass


@dataclass(frozen=True)
class SheetReference:
    name: str
    path: str


def column_index(reference: str) -> int:
    match = re.match(r"([A-Za-z]+)", reference)
    if not match:
        raise XlsxReadError(f"无法识别单元格地址：{reference}")
    value = 0
    for character in match.group(1).upper():
        value = value * 26 + ord(character) - ord("A") + 1
    return value - 1


def normalize_archive_path(target: str) -> str:
    normalized = target.lstrip("/")
    if normalized.startswith("xl/"):
        return normalized
    return str(PurePosixPath("xl") / normalized)


def text_content(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext())


class XlsxWorkbook:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        if not self.path.is_file():
            raise XlsxReadError(f"缺少 Excel 文件：{self.path}")
        try:
            self.archive = ZipFile(self.path)
        except BadZipFile as exc:
            raise XlsxReadError(f"不是有效的 XLSX 文件：{self.path}") from exc
        self.shared_strings = self._load_shared_strings()
        self.date_styles = self._load_date_styles()
        self.sheets = self._load_sheet_references()

    def close(self) -> None:
        self.archive.close()

    def __enter__(self) -> "XlsxWorkbook":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _read_xml(self, name: str) -> ET.Element:
        try:
            return ET.fromstring(self.archive.read(name))
        except KeyError as exc:
            raise XlsxReadError(f"{self.path} 缺少 XLSX 组件：{name}") from exc
        except ET.ParseError as exc:
            raise XlsxReadError(f"{self.path} 的 XLSX 组件损坏：{name}") from exc

    def _load_shared_strings(self) -> list[str]:
        try:
            root = self._read_xml("xl/sharedStrings.xml")
        except XlsxReadError:
            return []
        return [text_content(item) for item in root.findall("x:si", NS)]

    def _load_date_styles(self) -> set[int]:
        try:
            root = self._read_xml("xl/styles.xml")
        except XlsxReadError:
            return set()
        custom_formats = {
            int(item.attrib["numFmtId"]): item.attrib.get("formatCode", "")
            for item in root.findall("x:numFmts/x:numFmt", NS)
            if item.attrib.get("numFmtId", "").isdigit()
        }
        date_styles: set[int] = set()
        cell_xfs = root.find("x:cellXfs", NS)
        if cell_xfs is None:
            return date_styles
        for style_index, style in enumerate(cell_xfs.findall("x:xf", NS)):
            num_fmt_id = int(style.attrib.get("numFmtId", "0"))
            code = custom_formats.get(num_fmt_id, "")
            cleaned = re.sub(r'"[^"]*"', "", code.lower())
            cleaned = re.sub(r"\\.", "", cleaned)
            cleaned = re.sub(r"\[[^]]+\]", "", cleaned)
            if num_fmt_id in BUILTIN_DATE_FORMATS or (
                "y" in cleaned and ("m" in cleaned or "d" in cleaned)
            ):
                date_styles.add(style_index)
        return date_styles

    def _load_sheet_references(self) -> dict[str, SheetReference]:
        workbook = self._read_xml("xl/workbook.xml")
        relationships = self._read_xml("xl/_rels/workbook.xml.rels")
        targets = {
            item.attrib.get("Id", ""): normalize_archive_path(item.attrib.get("Target", ""))
            for item in relationships.findall("pr:Relationship", NS)
        }
        sheets: dict[str, SheetReference] = {}
        for sheet in workbook.findall("x:sheets/x:sheet", NS):
            name = sheet.attrib.get("name", "")
            relationship_id = sheet.attrib.get(f"{{{REL_NS}}}id", "")
            target = targets.get(relationship_id)
            if name and target:
                sheets[name] = SheetReference(name=name, path=target)
        return sheets

    def _cell_value(self, cell: ET.Element) -> Any:
        cell_type = cell.attrib.get("t", "")
        raw = text_content(cell.find("x:v", NS))
        if cell_type == "inlineStr":
            return text_content(cell.find("x:is", NS))
        if cell_type in {"str", "e"}:
            return raw
        if cell_type == "s":
            if not raw:
                return ""
            index = int(raw)
            try:
                return self.shared_strings[index]
            except IndexError as exc:
                raise XlsxReadError(
                    f"{self.path} 的共享字符串索引越界：{index}"
                ) from exc
        if cell_type == "b":
            return raw == "1"
        if not raw:
            return ""

        try:
            number = float(raw)
        except ValueError:
            return raw

        style = int(cell.attrib.get("s", "0"))
        if style in self.date_styles:
            moment = datetime(1899, 12, 30) + timedelta(days=number)
            if moment.time() == datetime.min.time():
                return moment.strftime("%Y-%m-%d")
            return moment.isoformat(timespec="seconds")
        return int(number) if number.is_integer() else number

    def rows(self, sheet_name: str) -> list[list[Any]]:
        sheet = self.sheets.get(sheet_name)
        if sheet is None:
            available = "、".join(self.sheets) or "无"
            raise XlsxReadError(
                f"{self.path} 缺少工作表“{sheet_name}”；现有工作表：{available}"
            )
        root = self._read_xml(sheet.path)
        rows: list[list[Any]] = []
        for row in root.findall("x:sheetData/x:row", NS):
            values: dict[int, Any] = {}
            for cell in row.findall("x:c", NS):
                reference = cell.attrib.get("r", "")
                values[column_index(reference)] = self._cell_value(cell)
            if not values:
                rows.append([])
                continue
            width = max(values) + 1
            rows.append([values.get(index, "") for index in range(width)])
        while rows and not any(value not in {"", None} for value in rows[-1]):
            rows.pop()
        return rows

    def table(
        self,
        sheet_name: str,
        *,
        expected_columns: tuple[str, ...] | list[str] | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.rows(sheet_name)
        if not rows:
            raise XlsxReadError(f"{self.path} 的工作表“{sheet_name}”为空。")
        headers = [str(value).strip() for value in rows[0]]
        if not headers or any(not header for header in headers):
            raise XlsxReadError(
                f"{self.path} 的工作表“{sheet_name}”第一行必须是非空字段名。"
            )
        if len(set(headers)) != len(headers):
            raise XlsxReadError(
                f"{self.path} 的工作表“{sheet_name}”存在重复字段名。"
            )
        if expected_columns is not None and tuple(headers) != tuple(expected_columns):
            raise XlsxReadError(
                f"{self.path} 的工作表“{sheet_name}”字段应依次为 "
                f"{', '.join(expected_columns)}；当前为 {', '.join(headers)}。"
            )

        records: list[dict[str, Any]] = []
        for source_row, values in enumerate(rows[1:], start=2):
            padded = values + [""] * (len(headers) - len(values))
            if any(value not in {"", None} for value in padded[: len(headers)]):
                record = dict(zip(headers, padded[: len(headers)]))
                record["_source_row"] = source_row
                records.append(record)
        return records


def read_table(
    path: Path | str,
    sheet_name: str,
    *,
    expected_columns: tuple[str, ...] | list[str] | None = None,
) -> list[dict[str, Any]]:
    with XlsxWorkbook(path) as workbook:
        return workbook.table(sheet_name, expected_columns=expected_columns)
