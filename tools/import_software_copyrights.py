from __future__ import annotations

import argparse
from pathlib import Path
import re
from typing import Any

try:
    from tools.data_import_common import clean_text, load_member_links, people, write_json
    from tools.xlsx_reader import XlsxReadError, read_table
except ModuleNotFoundError:
    from data_import_common import clean_text, load_member_links, people, write_json
    from xlsx_reader import XlsxReadError, read_table


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SOURCE_PATH = FRONTEND / "data-source" / "software-copyrights.xlsx"
OUTPUT_PATH = FRONTEND / "data" / "software-copyright-records.json"
MEMBER_RECORDS_PATH = FRONTEND / "data" / "member-records.json"
ALIASES_PATH = FRONTEND / "data" / "member-aliases.json"
SHEET_NAME = "软件著作"
COLUMNS = (
    "software_id",
    "software_name",
    "registration_number",
    "year",
    "owners",
    "note",
)


class SoftwareCopyrightImportError(ValueError):
    pass


def import_software_copyrights(
    source_path: Path = SOURCE_PATH,
    member_records_path: Path = MEMBER_RECORDS_PATH,
    aliases_path: Path = ALIASES_PATH,
) -> dict[str, Any]:
    try:
        rows = read_table(source_path, SHEET_NAME, expected_columns=COLUMNS)
    except XlsxReadError as exc:
        raise SoftwareCopyrightImportError(str(exc)) from exc

    member_links = load_member_links(member_records_path, aliases_path)
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source_order, row in enumerate(rows, start=1):
        row_number = int(row.get("_source_row", source_order + 1))
        software_id = clean_text(row.get("software_id"))
        software_name = clean_text(row.get("software_name"))
        if not software_id or not software_name:
            raise SoftwareCopyrightImportError(
                f"第 {row_number} 行必须包含 software_id 和 software_name。"
            )
        if software_id in seen_ids:
            raise SoftwareCopyrightImportError(
                f"第 {row_number} 行的 software_id `{software_id}` 重复。"
            )
        seen_ids.add(software_id)

        year = clean_text(row.get("year"))
        if year and not re.fullmatch(r"\d{4}", year):
            raise SoftwareCopyrightImportError(
                f"第 {row_number} 行的 year 应为四位年份或留空。"
            )
        records.append(
            {
                "id": software_id,
                "software_name": software_name,
                "registration_number": clean_text(row.get("registration_number")),
                "year": int(year) if year else "",
                "owners": people(row.get("owners"), member_links),
                "note": clean_text(row.get("note")),
                "source_order": source_order,
            }
        )
    records.sort(
        key=lambda record: (
            -(record["year"] if isinstance(record["year"], int) else 0),
            record["source_order"],
        )
    )
    return {"schema_version": 1, "software_copyrights": records}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert the software-copyright Excel workbook into Hugo JSON data."
    )
    parser.add_argument("--xlsx", type=Path, default=SOURCE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--members", type=Path, default=MEMBER_RECORDS_PATH)
    parser.add_argument("--aliases", type=Path, default=ALIASES_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = import_software_copyrights(args.xlsx, args.members, args.aliases)
    changed = write_json(payload, args.output, check=args.check)
    print(
        f"{'Updated' if changed else 'Verified'} {args.output} with "
        f"{len(payload['software_copyrights'])} software copyrights."
    )


if __name__ == "__main__":
    try:
        main()
    except (SoftwareCopyrightImportError, ValueError) as error:
        raise SystemExit(f"Software-copyright import failed: {error}")
