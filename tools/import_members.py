from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

try:
    from tools.xlsx_reader import XlsxReadError, read_table
except ModuleNotFoundError:
    from xlsx_reader import XlsxReadError, read_table


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SOURCE_PATH = FRONTEND / "data-source" / "members.xlsx"
OUTPUT_PATH = FRONTEND / "data" / "member-records.json"
ALIASES_OUTPUT_PATH = FRONTEND / "data" / "member-aliases.json"
CONTENT_DIR = FRONTEND / "content" / "members"
FIG_DIR = FRONTEND / "data-source" / "fig"
GENERATED_PAGE_MARKER = 'generated_from: "frontend/data-source/members.xlsx#'

SOURCE_DEFINITIONS = (
    (
        "教师",
        "teacher",
        "teacher_id",
        ("teacher_id", "name", "avatar", "member_type", "identity", "homepage", "bio"),
    ),
    (
        "博士研究生",
        "phd",
        "phd_id",
        ("phd_id", "name", "member_type", "identity", "homepage"),
    ),
    (
        "硕士研究生",
        "master",
        "master_id",
        ("master_id", "name", "member_type", "identity", "homepage"),
    ),
)

class MemberImportError(ValueError):
    pass


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def is_placeholder_name(value: str) -> bool:
    return clean_text(value).casefold() == "xxx"


def validate_homepage(value: str, filename: str, row_number: int) -> str:
    homepage = clean_text(value)
    if not homepage:
        return ""

    parsed = urlparse(homepage)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise MemberImportError(
            f"{filename} 第 {row_number} 行的 homepage 必须是 http(s) 链接或留空。"
        )
    return homepage


def load_source(
    sheet_name: str,
    expected_type: str,
    id_column: str,
    required_columns: tuple[str, ...],
) -> list[dict[str, Any]]:
    try:
        rows = read_table(
            SOURCE_PATH,
            sheet_name,
            expected_columns=required_columns,
        )
    except XlsxReadError as exc:
        raise MemberImportError(str(exc)) from exc

    records: list[dict[str, Any]] = []
    for source_order, row in enumerate(rows, start=1):
        row_number = int(row.get("_source_row", source_order + 1))
        member_id = clean_text(row.get(id_column))
        name = clean_text(row.get("name"))
        member_type = clean_text(row.get("member_type")).lower()
        identity = clean_text(row.get("identity"))

        if not re.fullmatch(rf"{re.escape(expected_type)}-\d{{3,}}", member_id):
            raise MemberImportError(
                f"{sheet_name} 第 {row_number} 行的 {id_column} `{member_id}` "
                f"应使用 {expected_type}-001 这样的独立编号格式。"
            )
        if not name:
            raise MemberImportError(f"{sheet_name} 第 {row_number} 行缺少 name。")
        if member_type != expected_type:
            raise MemberImportError(
                f"{sheet_name} 第 {row_number} 行的 member_type "
                f"应为 `{expected_type}`。"
            )
        if not identity:
            raise MemberImportError(f"{sheet_name} 第 {row_number} 行缺少 identity。")

        homepage = validate_homepage(row.get("homepage", ""), sheet_name, row_number)
        avatar = clean_text(row.get("avatar"))
        bio = clean_text(row.get("bio"))

        if expected_type == "teacher" and not is_placeholder_name(name):
            if not avatar:
                raise MemberImportError(
                    f"{sheet_name} 第 {row_number} 行的教师缺少 avatar。"
                )
            avatar_relative = Path(avatar)
            if avatar_relative.is_absolute() or ".." in avatar_relative.parts:
                raise MemberImportError(
                    f"{sheet_name} 第 {row_number} 行的 avatar 必须是 fig 下的相对路径。"
                )
            avatar_path = FIG_DIR / avatar_relative
            if not avatar_path.is_file():
                raise MemberImportError(
                    f"{sheet_name} 第 {row_number} 行的头像不存在：{avatar_path}"
                )

        record: dict[str, Any] = {
            "id": member_id,
            "name": name,
            "member_type": member_type,
            "identity": identity,
            "homepage": homepage,
            "url": f"/members/{member_id}/",
            "source_order": source_order,
        }
        if avatar:
            record["avatar"] = avatar
            record["avatar_url"] = f"/images/data-source/{avatar}"
        if bio:
            record["bio"] = bio
        records.append(record)

    return records


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_member_page(record: dict[str, Any], source_sheet: str) -> str:
    lines = [
        "---",
        f"title: {yaml_string(record['name'])}",
        f"url: {yaml_string(record['url'])}",
        f"member_id: {yaml_string(record['id'])}",
        f"member_type: {yaml_string(record['member_type'])}",
        f"identity: {yaml_string(record['identity'])}",
        f"display_order: {record['source_order']}",
    ]
    if record.get("homepage"):
        lines.append(f"homepage: {yaml_string(record['homepage'])}")
    if record.get("avatar_url"):
        lines.append(f"avatar_url: {yaml_string(record['avatar_url'])}")
    lines.extend(
        [
            f"generated_from: {yaml_string(f'frontend/data-source/members.xlsx#{source_sheet}')}",
            "---",
            "",
        ]
    )
    if record.get("bio"):
        lines.extend([record["bio"], ""])
    return "\n".join(lines)


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def build_aliases(records: list[dict[str, Any]]) -> dict[str, str]:
    member_urls = {record["id"]: record["url"] for record in records}
    aliases: dict[str, str] = {}
    normalized_aliases: dict[str, str] = {}

    def add_alias(alias: str, member_id: str, source: str) -> None:
        cleaned = clean_text(alias)
        normalized = normalize_name(cleaned)
        if not cleaned or not normalized:
            raise MemberImportError(f"{source} 的 alias 不能为空。")
        member_url = member_urls.get(member_id)
        if not member_url:
            raise MemberImportError(f"{source} 引用了不存在的 member_id：{member_id}")
        existing = normalized_aliases.get(normalized)
        if existing and existing != member_url:
            raise MemberImportError(f"{source} 的 alias `{cleaned}` 与其他成员冲突。")
        normalized_aliases[normalized] = member_url
        aliases[cleaned] = member_url

    for record in records:
        if not is_placeholder_name(record["name"]):
            add_alias(record["name"], record["id"], f"成员 {record['id']}")

    try:
        rows = read_table(
            SOURCE_PATH,
            "作者别名",
            expected_columns=("alias", "member_id"),
        )
    except XlsxReadError as exc:
        raise MemberImportError(str(exc)) from exc

    for source_order, row in enumerate(rows, start=1):
        row_number = int(row.get("_source_row", source_order + 1))
        add_alias(
            clean_text(row.get("alias")),
            clean_text(row.get("member_id")),
            f"作者别名 第 {row_number} 行",
        )
    return aliases


def build_outputs() -> tuple[dict[str, Any], dict[Path, str], dict[str, str]]:
    all_records: list[dict[str, Any]] = []
    pages: dict[Path, str] = {}
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for sheet_name, member_type, id_column, columns in SOURCE_DEFINITIONS:
        records = load_source(sheet_name, member_type, id_column, columns)
        for record in records:
            if record["id"] in seen_ids:
                raise MemberImportError(f"成员 id 重复：{record['id']}")
            if record["name"] in seen_names and not is_placeholder_name(record["name"]):
                raise MemberImportError(f"成员姓名重复：{record['name']}")
            seen_ids.add(record["id"])
            seen_names.add(record["name"])
            all_records.append(record)
            pages[CONTENT_DIR / record["id"] / "index.md"] = render_member_page(
                record, sheet_name
            )

    payload = {
        "schema_version": 1,
        "members": all_records,
    }
    return payload, pages, build_aliases(all_records)


def expected_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def find_generated_pages() -> set[Path]:
    if not CONTENT_DIR.exists():
        return set()

    return {
        path
        for path in CONTENT_DIR.glob("*/index.md")
        if GENERATED_PAGE_MARKER in path.read_text(encoding="utf-8")
    }


def check_outputs(
    payload: dict[str, Any],
    pages: dict[Path, str],
    aliases: dict[str, str],
) -> bool:
    mismatches: list[str] = []
    expected_data = expected_json(payload)
    if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != expected_data:
        mismatches.append(str(OUTPUT_PATH))
    expected_aliases = expected_json(aliases)
    if (
        not ALIASES_OUTPUT_PATH.exists()
        or ALIASES_OUTPUT_PATH.read_text(encoding="utf-8") != expected_aliases
    ):
        mismatches.append(str(ALIASES_OUTPUT_PATH))

    for path, expected in pages.items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(str(path))

    for path in sorted(find_generated_pages() - set(pages)):
        mismatches.append(str(path))

    if mismatches:
        print("以下生成文件未同步：")
        for path in mismatches:
            print(f"- {path}")
        return False

    print(f"Verified member data with {len(payload['members'])} active members.")
    return True


def write_outputs(
    payload: dict[str, Any],
    pages: dict[Path, str],
    aliases: dict[str, str],
) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected_json(payload), encoding="utf-8")
    ALIASES_OUTPUT_PATH.write_text(expected_json(aliases), encoding="utf-8")
    for path, content in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    stale_pages = find_generated_pages() - set(pages)
    for path in stale_pages:
        path.unlink()
        if not any(path.parent.iterdir()):
            path.parent.rmdir()
    print(f"Updated {OUTPUT_PATH} with {len(payload['members'])} active members.")
    print(f"Updated {ALIASES_OUTPUT_PATH} with {len(aliases)} exact author aliases.")
    print(f"Updated {len(pages)} stable member pages.")
    if stale_pages:
        print(f"Removed {len(stale_pages)} obsolete generated member pages.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the member Excel workbook and generate Hugo member data/pages."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated member data/pages without writing files.",
    )
    args = parser.parse_args()

    try:
        payload, pages, aliases = build_outputs()
        if args.check:
            return 0 if check_outputs(payload, pages, aliases) else 1
        write_outputs(payload, pages, aliases)
        return 0
    except MemberImportError as exc:
        print(f"Member import failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
