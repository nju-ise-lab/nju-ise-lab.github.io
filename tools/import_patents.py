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
SOURCE_PATH = FRONTEND / "data-source" / "patents.xlsx"
OUTPUT_PATH = FRONTEND / "data" / "patent-records.json"
MEMBER_RECORDS_PATH = FRONTEND / "data" / "member-records.json"
ALIASES_PATH = FRONTEND / "data" / "member-aliases.json"
SHEET_NAME = "专利"
COLUMNS = (
    "patent_id",
    "patent_name",
    "inventors",
    "public_number",
    "application_number",
    "application_date",
    "applicants",
)


class PatentImportError(ValueError):
    pass


def import_patents(
    source_path: Path = SOURCE_PATH,
    member_records_path: Path = MEMBER_RECORDS_PATH,
    aliases_path: Path = ALIASES_PATH,
) -> dict[str, Any]:
    try:
        rows = read_table(source_path, SHEET_NAME, expected_columns=COLUMNS)
    except XlsxReadError as exc:
        raise PatentImportError(str(exc)) from exc

    member_links = load_member_links(member_records_path, aliases_path)
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source_order, row in enumerate(rows, start=1):
        row_number = int(row.get("_source_row", source_order + 1))
        patent_id = clean_text(row.get("patent_id"))
        patent_name = clean_text(row.get("patent_name"))
        if not patent_id or not patent_name:
            raise PatentImportError(
                f"第 {row_number} 行必须包含 patent_id 和 patent_name。"
            )
        if patent_id in seen_ids:
            raise PatentImportError(f"第 {row_number} 行的 patent_id `{patent_id}` 重复。")
        seen_ids.add(patent_id)

        application_date = clean_text(row.get("application_date"))
        if application_date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", application_date):
            raise PatentImportError(
                f"第 {row_number} 行的 application_date 应为 YYYY-MM-DD 或留空。"
            )
        inventors = people(row.get("inventors"), member_links)
        applicants = people(row.get("applicants"), member_links)

        records.append(
            {
                "id": patent_id,
                "patent_name": patent_name,
                "inventors": inventors,
                "public_number": clean_text(row.get("public_number")),
                "application_number": clean_text(row.get("application_number")),
                "application_date": application_date,
                "applicants": applicants,
                "source_order": source_order,
            }
        )
    return {"schema_version": 1, "patents": records}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert the patent Excel workbook into Hugo JSON data."
    )
    parser.add_argument("--xlsx", type=Path, default=SOURCE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--members", type=Path, default=MEMBER_RECORDS_PATH)
    parser.add_argument("--aliases", type=Path, default=ALIASES_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = import_patents(args.xlsx, args.members, args.aliases)
    changed = write_json(payload, args.output, check=args.check)
    print(
        f"{'Updated' if changed else 'Verified'} {args.output} "
        f"with {len(payload['patents'])} patents."
    )


if __name__ == "__main__":
    try:
        main()
    except (PatentImportError, ValueError) as error:
        raise SystemExit(f"Patent import failed: {error}")
