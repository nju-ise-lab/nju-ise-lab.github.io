from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from tools.data_import_common import clean_text, parse_boolean, write_json
    from tools.xlsx_reader import XlsxReadError, read_table
except ModuleNotFoundError:
    from data_import_common import clean_text, parse_boolean, write_json
    from xlsx_reader import XlsxReadError, read_table


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SOURCE_PATH = FRONTEND / "data-source" / "projects.xlsx"
OUTPUT_PATH = FRONTEND / "data" / "project-records.json"
SHEET_NAME = "项目"
COLUMNS = (
    "project_id",
    "project_name",
    "project_code",
    "project_period",
    "project_summary",
    "featured",
    "featured_order",
    "homepage_label",
)


class ProjectImportError(ValueError):
    pass


def parse_featured_order(value: Any, *, featured: bool, row_number: int) -> int | None:
    raw = clean_text(value)
    if not raw:
        return None
    try:
        order = int(float(raw))
    except ValueError as exc:
        raise ProjectImportError(
            f"第 {row_number} 行的 featured_order 应为正整数或留空。"
        ) from exc
    if order < 1:
        raise ProjectImportError(
            f"第 {row_number} 行的 featured_order 应为正整数或留空。"
        )
    if not featured:
        raise ProjectImportError(
            f"第 {row_number} 行填写了 featured_order，但 featured 不是 TRUE。"
        )
    return order


def import_projects(source_path: Path = SOURCE_PATH) -> dict[str, Any]:
    try:
        rows = read_table(source_path, SHEET_NAME, expected_columns=COLUMNS)
    except XlsxReadError as exc:
        raise ProjectImportError(str(exc)) from exc

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_featured_orders: set[int] = set()
    for source_order, row in enumerate(rows, start=1):
        row_number = int(row.get("_source_row", source_order + 1))
        project_id = clean_text(row.get("project_id"))
        project_name = clean_text(row.get("project_name"))
        if not project_id or not project_name:
            raise ProjectImportError(
                f"第 {row_number} 行必须包含 project_id 和 project_name。"
            )
        if project_id in seen_ids:
            raise ProjectImportError(
                f"第 {row_number} 行的 project_id `{project_id}` 重复。"
            )
        seen_ids.add(project_id)
        try:
            featured = parse_boolean(
                row.get("featured"), label="featured", row_number=row_number
            )
        except ValueError as exc:
            raise ProjectImportError(str(exc)) from exc
        featured_order = parse_featured_order(
            row.get("featured_order"), featured=featured, row_number=row_number
        )
        if featured_order is not None:
            if featured_order in seen_featured_orders:
                raise ProjectImportError(
                    f"第 {row_number} 行的 featured_order `{featured_order}` 重复。"
                )
            seen_featured_orders.add(featured_order)

        records.append(
            {
                "id": project_id,
                "project_name": project_name,
                "project_code": clean_text(row.get("project_code")),
                "project_period": clean_text(row.get("project_period")),
                "project_summary": clean_text(row.get("project_summary")),
                "featured": featured,
                "featured_order": featured_order,
                "homepage_label": clean_text(row.get("homepage_label")),
                "source_order": source_order,
            }
        )
    return {"schema_version": 1, "projects": records}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert the project Excel workbook into Hugo JSON data."
    )
    parser.add_argument("--xlsx", type=Path, default=SOURCE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    payload = import_projects(args.xlsx)
    changed = write_json(payload, args.output, check=args.check)
    print(
        f"{'Updated' if changed else 'Verified'} {args.output} "
        f"with {len(payload['projects'])} projects."
    )


if __name__ == "__main__":
    try:
        main()
    except (ProjectImportError, ValueError) as error:
        raise SystemExit(f"Project import failed: {error}")
