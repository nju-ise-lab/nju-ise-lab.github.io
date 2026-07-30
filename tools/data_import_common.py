from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def split_names(value: Any) -> list[str]:
    return [
        clean_text(name)
        for name in re.split(r"[;；]", clean_text(value))
        if clean_text(name)
    ]


def load_member_links(
    member_records_path: Path,
    aliases_path: Path,
) -> dict[str, str]:
    links: dict[str, str] = {}
    if member_records_path.is_file():
        catalog = json.loads(member_records_path.read_text(encoding="utf-8"))
        for member in catalog.get("members", []):
            name = clean_text(member.get("name"))
            url = clean_text(member.get("url"))
            if name and url:
                links[normalize_name(name)] = url
    if aliases_path.is_file():
        aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
        for name, url in aliases.items():
            if clean_text(name) and clean_text(url):
                links[normalize_name(clean_text(name))] = clean_text(url)
    return links


def people(value: Any, member_links: dict[str, str]) -> list[dict[str, str]]:
    records = []
    for name in split_names(value):
        item = {"name": name}
        member_url = member_links.get(normalize_name(name))
        if member_url:
            item["member_url"] = member_url
        records.append(item)
    return records


def parse_boolean(value: Any, *, label: str, row_number: int) -> bool:
    if isinstance(value, bool):
        return value
    normalized = clean_text(value).lower()
    if normalized in {"1", "true", "yes", "y", "是"}:
        return True
    if normalized in {"0", "false", "no", "n", "否", ""}:
        return False
    raise ValueError(f"第 {row_number} 行的 {label} 应为 TRUE/FALSE。")


def write_json(payload: Any, path: Path, *, check: bool) -> bool:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if check:
        if existing != rendered:
            raise ValueError(f"{path} 未同步，请运行导入脚本。")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return existing != rendered
