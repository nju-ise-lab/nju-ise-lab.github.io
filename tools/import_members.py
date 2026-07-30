from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SOURCE_DIR = FRONTEND / "member-source"
OUTPUT_PATH = FRONTEND / "data" / "member-records.json"
CONTENT_DIR = FRONTEND / "content" / "members"

SOURCE_DEFINITIONS = (
    (
        "teachers.csv",
        "teacher",
        "teacher_id",
        ("teacher_id", "name", "avatar", "member_type", "identity", "homepage", "bio"),
    ),
    (
        "phd.csv",
        "phd",
        "phd_id",
        ("phd_id", "name", "member_type", "identity", "homepage"),
    ),
    (
        "masters.csv",
        "master",
        "master_id",
        ("master_id", "name", "member_type", "identity", "homepage"),
    ),
)

LEGACY_MEMBER_URLS = {
    "teacher-001": "/members/member-37/",
    "teacher-002": "/members/member-42/",
    "teacher-003": "/members/member-55/",
    "teacher-004": "/members/member-38/",
    "teacher-005": "/members/member-44/",
    "teacher-006": "/members/member-52/",
    "teacher-007": "/members/member-53/",
    "phd-001": "/members/member-39/",
    "phd-002": "/members/member-46/",
    "phd-003": "/members/member-47/",
    "phd-004": "/members/member-48/",
    "phd-005": "/members/member-49/",
    "master-001": "/members/member-45/",
    "master-002": "/members/member-56/",
    "master-003": "/members/member-57/",
    "master-004": "/members/member-58/",
}


class MemberImportError(ValueError):
    pass


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


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
    filename: str,
    expected_type: str,
    id_column: str,
    required_columns: tuple[str, ...],
) -> list[dict[str, Any]]:
    path = SOURCE_DIR / filename
    if not path.exists():
        raise MemberImportError(f"缺少成员维护文件：{path}")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        if columns != required_columns:
            raise MemberImportError(
                f"{filename} 字段应依次为 {', '.join(required_columns)}；"
                f"当前为 {', '.join(columns) or '空'}。"
            )

        records: list[dict[str, Any]] = []
        for source_order, row in enumerate(reader, start=1):
            row_number = source_order + 1
            member_id = clean_text(row.get(id_column))
            name = clean_text(row.get("name"))
            member_type = clean_text(row.get("member_type")).lower()
            identity = clean_text(row.get("identity"))

            if not re.fullmatch(rf"{re.escape(expected_type)}-\d{{3,}}", member_id):
                raise MemberImportError(
                    f"{filename} 第 {row_number} 行的 {id_column} `{member_id}` "
                    f"应使用 {expected_type}-001 这样的独立编号格式。"
                )
            if not name:
                raise MemberImportError(f"{filename} 第 {row_number} 行缺少 name。")
            if member_type != expected_type:
                raise MemberImportError(
                    f"{filename} 第 {row_number} 行的 member_type "
                    f"应为 `{expected_type}`。"
                )
            if not identity:
                raise MemberImportError(f"{filename} 第 {row_number} 行缺少 identity。")

            homepage = validate_homepage(row.get("homepage", ""), filename, row_number)
            avatar = clean_text(row.get("avatar"))
            bio = clean_text(row.get("bio"))

            if expected_type == "teacher":
                if not avatar:
                    raise MemberImportError(
                        f"{filename} 第 {row_number} 行的教师缺少 avatar。"
                    )
                avatar_path = CONTENT_DIR / member_id / avatar
                if not avatar_path.is_file():
                    raise MemberImportError(
                        f"{filename} 第 {row_number} 行的头像不存在：{avatar_path}"
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
                record["avatar_url"] = f"/members/{member_id}/{avatar}"
            if bio:
                record["bio"] = bio
            records.append(record)

    return records


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_member_page(record: dict[str, Any], source_filename: str) -> str:
    lines = [
        "---",
        f"title: {yaml_string(record['name'])}",
        f"url: {yaml_string(record['url'])}",
        f"member_id: {yaml_string(record['id'])}",
            f"member_type: {yaml_string(record['member_type'])}",
            f"identity: {yaml_string(record['identity'])}",
            f"display_order: {record['source_order']}",
    ]
    legacy_url = LEGACY_MEMBER_URLS.get(record["id"])
    if legacy_url:
        lines.extend(["aliases:", f"  - {yaml_string(legacy_url)}"])
    if record.get("homepage"):
        lines.append(f"homepage: {yaml_string(record['homepage'])}")
    if record.get("avatar"):
        lines.append(f"avatar: {yaml_string(record['avatar'])}")
    lines.extend(
        [
            f"generated_from: {yaml_string(f'frontend/member-source/{source_filename}')}",
            "---",
            "",
        ]
    )
    if record.get("bio"):
        lines.extend([record["bio"], ""])
    return "\n".join(lines)


def build_outputs() -> tuple[dict[str, Any], dict[Path, str]]:
    all_records: list[dict[str, Any]] = []
    pages: dict[Path, str] = {}
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for filename, member_type, id_column, columns in SOURCE_DEFINITIONS:
        records = load_source(filename, member_type, id_column, columns)
        for record in records:
            if record["id"] in seen_ids:
                raise MemberImportError(f"成员 id 重复：{record['id']}")
            if record["name"] in seen_names:
                raise MemberImportError(f"成员姓名重复：{record['name']}")
            seen_ids.add(record["id"])
            seen_names.add(record["name"])
            all_records.append(record)
            pages[CONTENT_DIR / record["id"] / "index.md"] = render_member_page(
                record, filename
            )

    payload = {
        "schema_version": 1,
        "members": all_records,
    }
    return payload, pages


def expected_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def check_outputs(payload: dict[str, Any], pages: dict[Path, str]) -> bool:
    mismatches: list[str] = []
    expected_data = expected_json(payload)
    if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != expected_data:
        mismatches.append(str(OUTPUT_PATH))

    for path, expected in pages.items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(str(path))

    if mismatches:
        print("以下生成文件未同步：")
        for path in mismatches:
            print(f"- {path}")
        return False

    print(f"Verified member data with {len(payload['members'])} active members.")
    return True


def write_outputs(payload: dict[str, Any], pages: dict[Path, str]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected_json(payload), encoding="utf-8")
    for path, content in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"Updated {OUTPUT_PATH} with {len(payload['members'])} active members.")
    print(f"Updated {len(pages)} stable member pages.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate member CSV files and generate Hugo member data/pages."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated member data/pages without writing files.",
    )
    args = parser.parse_args()

    try:
        payload, pages = build_outputs()
        if args.check:
            return 0 if check_outputs(payload, pages) else 1
        write_outputs(payload, pages)
        return 0
    except MemberImportError as exc:
        print(f"Member import failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
