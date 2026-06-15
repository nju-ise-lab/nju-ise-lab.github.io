from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


MEMBER_ALIASES_BY_TITLE = {
    "陈振宇": ("Zhenyu Chen", "Chen Zhenyu", "CHEN Zhen-Yu"),
    "房春荣": ("Chunrong Fang", "Fang Chunrong", "FANG Chun-Rong"),
    "刘嘉": ("Jia Liu", "Liu Jia"),
    "何铁科": ("Tieke He", "He Tieke"),
    "赵志宏": ("Zhihong Zhao", "Zhao Zhihong", "ZHAO Zhi-Hong"),
    "王兴亚": ("Xingya Wang", "Wang Xingya"),
    "冯洋": ("Yang Feng", "Feng Yang"),
    "赵源": ("Yuan Zhao", "Zhao Yuan"),
    "孙伟松": ("Weisong Sun", "Sun Weisong"),
    "虞圣呈": ("Shengcheng Yu", "Yu Shengcheng"),
    "郭安": ("An Guo", "Guo An"),
    "钱瑞祥": ("Ruixiang Qian", "Qian Ruixiang"),
    "乔力": ("Li Qiao", "Qiao Li"),
    "戎润祥": ("Runxiang Rong", "Rong Runxiang"),
    "顾思琦": ("Siqi Gu", "Gu Siqi"),
    "伊高磊": ("Gaolei Yi", "Yi Gaolei"),
}


def load_member_links(frontend_dir: Path) -> dict[str, str]:
    links: dict[str, str] = {}
    for path in sorted((frontend_dir / "content" / "members").glob("*/index.md")):
        front_matter = parse_front_matter(path.read_text(encoding="utf-8"))
        title = front_matter.get("title")
        url = front_matter.get("url")
        if not title or not url:
            continue
        for alias in (title, *MEMBER_ALIASES_BY_TITLE.get(title, ())):
            links[normalize_name(alias)] = url
            links[alias] = url
    return links


def parse_front_matter(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        return {}
    try:
        _, raw_front_matter, _ = content.split("---", 2)
    except ValueError:
        return {}

    values: dict[str, str] = {}
    for line in raw_front_matter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                values[key.strip()] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        values[key.strip()] = value
    return values


def publication_from_record(record: dict[str, Any], member_links: dict[str, str]) -> dict[str, Any]:
    legacy_id = record.get("legacy_id") or record.get("id")
    raw_citation = (record.get("content") or "").strip()
    author_text, citation_tail = split_first_sentence(raw_citation)
    title, venue = split_title_and_venue(citation_tail)
    if not title:
        title = raw_citation or f"Publication {legacy_id}"

    return {
        "content_kind": "publication",
        "title": title,
        "publication_year": str(record.get("year") or record.get("publishYear") or ""),
        "venue": venue,
        "authors": authors_from_text(author_text, member_links),
        "raw_citation": raw_citation,
        "legacy_id": legacy_id,
        "url": f"/activities/publication-{legacy_id}/",
        "draft": False,
    }


def patent_from_record(record: dict[str, Any], member_links: dict[str, str]) -> dict[str, Any]:
    title = (record.get("title") or record.get("english") or record.get("chinese") or "").strip()
    raw_authors = (record.get("raw_authors") or record.get("chinese") or "").strip()
    authors = [] if raw_authors == title and not has_author_delimiter(raw_authors) else authors_from_text(raw_authors, member_links)

    enriched = dict(record)
    enriched.update(
        {
            "legacy_id": record.get("legacy_id") or record.get("id"),
            "title": title,
            "raw_authors": raw_authors,
            "authors": authors,
        }
    )
    return enriched


def split_first_sentence(text: str) -> tuple[str, str]:
    if "." not in text:
        return "", text.strip()
    author_text, rest = text.split(".", 1)
    return author_text.strip(), rest.strip()


def split_title_and_venue(text: str) -> tuple[str, str]:
    text = text.strip()
    if not text:
        return "", ""

    marker_match = re.search(r"\s+\[[JC]\]", text)
    if marker_match:
        title = text[: marker_match.start()].strip()
        venue = text[marker_match.start() :].strip(" .")
        return title, venue

    if ". " in text:
        title, venue = text.split(". ", 1)
        return title.strip(), venue.strip(" .")

    return text.strip(" ."), ""


def authors_from_text(text: str, member_links: dict[str, str]) -> list[dict[str, str]]:
    authors = []
    for name in split_author_names(text):
        item = {"name": name}
        member_url = member_links.get(name) or member_links.get(normalize_name(name))
        if member_url:
            item["member_url"] = member_url
        authors.append(item)
    return authors


def split_author_names(text: str) -> list[str]:
    text = text.strip().strip(".")
    if not text:
        return []

    normalized = re.sub(r"\s+and\s+", ", ", text, flags=re.IGNORECASE)
    delimiter = r"[、，,;；]"
    return [clean_author_name(part) for part in re.split(delimiter, normalized) if clean_author_name(part)]


def clean_author_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip(" .")


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", name.lower())


def has_author_delimiter(text: str) -> bool:
    return any(delimiter in text for delimiter in ("、", "，", ",", ";", "；"))


def markdown_for_publication(publication: dict[str, Any]) -> str:
    return f"---\n{to_yaml(publication)}---\n\n{publication['raw_citation']}\n"


def to_yaml(values: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in values.items():
        append_yaml_value(lines, key, value, indent=0)
    return "".join(lines)


def append_yaml_value(lines: list[str], key: str, value: Any, *, indent: int) -> None:
    prefix = " " * indent
    if isinstance(value, list):
        lines.append(f"{prefix}{key}:\n")
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}  -")
                if not item:
                    lines.append(" {}\n")
                    continue
                first = True
                for child_key, child_value in item.items():
                    if first:
                        lines.append(f" {child_key}: {yaml_scalar(child_value)}\n")
                        first = False
                    else:
                        lines.append(f"{prefix}    {child_key}: {yaml_scalar(child_value)}\n")
            else:
                lines.append(f"{prefix}  - {yaml_scalar(item)}\n")
        return
    if isinstance(value, dict):
        lines.append(f"{prefix}{key}:\n")
        for child_key, child_value in value.items():
            append_yaml_value(lines, child_key, child_value, indent=indent + 2)
        return
    lines.append(f"{prefix}{key}: {yaml_scalar(value)}\n")


def yaml_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def sync_frontend(frontend_dir: Path) -> dict[str, int]:
    member_links = load_member_links(frontend_dir)
    publications_path = frontend_dir / "data" / "publications.json"
    projects_path = frontend_dir / "data" / "projects.json"

    publication_records = json.loads(publications_path.read_text(encoding="utf-8"))
    publications = [publication_from_record(record, member_links) for record in publication_records]
    for publication in publications:
        destination = frontend_dir / "content" / "activities" / f"publication-{publication['legacy_id']}" / "index.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(markdown_for_publication(publication), encoding="utf-8")

    patent_records = json.loads(projects_path.read_text(encoding="utf-8"))
    patents = [patent_from_record(record, member_links) for record in patent_records]
    projects_path.write_text(json.dumps(patents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {"publications": len(publications), "patents": len(patents)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate research publication pages and structured patent data.")
    parser.add_argument("--frontend", type=Path, default=Path("frontend"))
    args = parser.parse_args()
    result = sync_frontend(args.frontend)
    print(f"Generated {result['publications']} publication pages and enriched {result['patents']} patents.")


if __name__ == "__main__":
    main()
