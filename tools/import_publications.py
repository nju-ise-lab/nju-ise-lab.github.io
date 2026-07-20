from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote_plus, urlparse


REQUIRED_COLUMNS = {
    "year",
    "id",
    "title",
    "link",
    "status",
    "author",
    "cofauthor",
    "corauthor",
    "level",
    "venue",
    "note",
}

STATUS_ALIASES = {
    "published": ("published", "Published"),
    "accepted": ("accepted", "Accepted"),
    "acctpted": ("accepted", "Accepted"),
    "preprint": ("preprint", "Preprint"),
    "pre-print": ("preprint", "Preprint"),
    "under review": ("under_review", "Under Review"),
    "under-review": ("under_review", "Under Review"),
    "submitted": ("submitted", "Submitted"),
    "in press": ("in_press", "In Press"),
    "in-press": ("in_press", "In Press"),
}
MANUSCRIPT_STATUSES = {"preprint", "under_review", "submitted"}

# Only venues that can be identified unambiguously from the legacy export are
# inferred. The explicit CSV `level` value always takes precedence.
CCF_LEVEL_HINTS = (
    ("CCF-A", ("transactions on software engineering", "acm transactions on software engineering and methodology", "international conference on software engineering", "international symposium on software testing and analysis", "international conference on automated software engineering", "foundations of software engineering")),
    ("CCF-B", ("empirical software engineering", "journal of systems and software", "journal of software: evolution and process", "software analysis, evolution,and reengineering", "software analysis, evolution, and reengineering")),
    ("CCF-C", ("international journal of software engineering and knowledge engineering", "software quality journal")),
)
NON_REGULAR_PAPER_HINTS = ("companion", "demo", "short paper", "technical brief", "industry showcase", "workshop")
SCHOLARLY_TITLE_LINK_HOSTS = (
    "arxiv.org",
    "scholar.google.com",
    "semanticscholar.org",
    "openreview.net",
)


class PublicationImportError(ValueError):
    pass


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def split_names(value: str | None) -> list[str]:
    return [clean_text(name) for name in re.split(r"[;；]", value or "") if clean_text(name)]


def load_aliases(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise PublicationImportError(f"{path} 必须是作者姓名到成员链接的 JSON 对象。")

    aliases: dict[str, str] = {}
    for name, member_url in raw.items():
        if not isinstance(name, str) or not isinstance(member_url, str) or not member_url.startswith("/members/"):
            raise PublicationImportError(f"成员别名 `{name}` 的链接必须以 /members/ 开头。")
        aliases[normalize_name(name)] = member_url
    return aliases


def normalize_status(value: str, row_number: int) -> tuple[str, str]:
    raw = clean_text(value).lower()
    if raw not in STATUS_ALIASES:
        supported = ", ".join(sorted(STATUS_ALIASES))
        raise PublicationImportError(f"第 {row_number} 行的 status `{value}` 无法识别；可使用：{supported}。")
    return STATUS_ALIASES[raw]


def normalize_level(value: str, row_number: int) -> str:
    raw = clean_text(value).upper().replace("_", "-").replace(" ", "")
    if not raw:
        return ""
    if raw in {"A", "B", "C"}:
        return f"CCF-{raw}"
    if raw in {"CCF-A", "CCF-B", "CCF-C"}:
        return raw
    raise PublicationImportError(f"第 {row_number} 行的 level `{value}` 应为 CCF-A、CCF-B、CCF-C 或留空。")


def infer_ccf_level(venue: str, title: str) -> str:
    searchable = f"{venue} {title}".lower()
    if any(hint in searchable for hint in NON_REGULAR_PAPER_HINTS):
        return ""
    for level, hints in CCF_LEVEL_HINTS:
        if any(hint in searchable for hint in hints):
            return level
    return ""


def infer_publication_type(venue: str, status: str) -> tuple[str, str]:
    searchable = venue.lower()
    if status == "preprint" or "arxiv" in searchable:
        return "preprint", "预印本"
    if any(hint in searchable for hint in ("[j]", "journal", "transactions", "empirical software engineering")):
        return "journal", "期刊论文"
    if any(hint in searchable for hint in ("[c]", "conference", "proceedings", "symposium")) or re.search(r"\b(icse|issta|ase|fse|saner)\b", searchable):
        return "conference", "会议论文"
    return "", ""


def normalize_year(value: str, row_number: int) -> int:
    raw = clean_text(value)
    if not re.fullmatch(r"\d{4}", raw):
        raise PublicationImportError(f"第 {row_number} 行的 year `{value}` 必须是四位年份。")
    year = int(raw)
    if year < 1900 or year > 2200:
        raise PublicationImportError(f"第 {row_number} 行的 year `{value}` 不在允许范围内。")
    return year


def validate_url(value: str, row_number: int) -> str:
    url = clean_text(value)
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PublicationImportError(f"第 {row_number} 行的 link 必须是 http(s) 链接或留空。")
    return url


def title_link(source_url: str, title: str) -> str:
    """Return a research-discovery URL suitable for a public paper title.

    DOI and publisher pages remain in the source data for maintenance, but the
    visible paper title should only point to scholarly discovery services. For
    all other URL types, use a Google Scholar title search instead.
    """
    hostname = (urlparse(source_url).hostname or "").lower()
    if any(hostname == host or hostname.endswith(f".{host}") for host in SCHOLARLY_TITLE_LINK_HOSTS):
        return source_url
    return f"https://scholar.google.com/scholar?hl=en&q={quote_plus(title)}"


def build_authors(row: dict[str, str], aliases: dict[str, str], row_number: int, unmatched: set[str]) -> list[dict[str, Any]]:
    author_names = split_names(row.get("author"))
    if not author_names:
        raise PublicationImportError(f"第 {row_number} 行缺少 author。作者请使用分号分隔。")

    normalized_authors = [normalize_name(name) for name in author_names]
    if len(set(normalized_authors)) != len(normalized_authors):
        raise PublicationImportError(f"第 {row_number} 行的 author 包含重复姓名。")

    co_first = set(split_names(row.get("cofauthor")))
    corresponding = set(split_names(row.get("corauthor")))
    author_lookup = {normalize_name(name): name for name in author_names}

    for label, marked_names in (("cofauthor", co_first), ("corauthor", corresponding)):
        unknown = [name for name in marked_names if normalize_name(name) not in author_lookup]
        if unknown:
            raise PublicationImportError(f"第 {row_number} 行的 {label} 包含未出现在 author 中的姓名：{', '.join(unknown)}。")

    authors: list[dict[str, Any]] = []
    for name in author_names:
        key = normalize_name(name)
        author: dict[str, Any] = {
            "name": name,
            "co_first": key in {normalize_name(item) for item in co_first},
            "corresponding": key in {normalize_name(item) for item in corresponding},
        }
        member_url = aliases.get(key)
        if member_url:
            author["member_url"] = member_url
        else:
            unmatched.add(name)
        authors.append(author)
    return authors


def import_csv(csv_path: Path, aliases_path: Path) -> tuple[dict[str, Any], set[str]]:
    aliases = load_aliases(aliases_path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise PublicationImportError(f"CSV 缺少字段：{', '.join(sorted(missing))}。")

        records: list[dict[str, Any]] = []
        ids: set[str] = set()
        unmatched: set[str] = set()
        for source_order, row in enumerate(reader, start=1):
            row_number = source_order + 1
            paper_id = clean_text(row.get("id"))
            title = clean_text(row.get("title"))
            if not paper_id or not title:
                raise PublicationImportError(f"第 {row_number} 行必须包含 id 和 title。")
            if paper_id in ids:
                raise PublicationImportError(f"第 {row_number} 行的 id `{paper_id}` 重复。")
            ids.add(paper_id)

            status, status_label = normalize_status(row.get("status", ""), row_number)
            venue = clean_text(row.get("venue"))
            publication_type, publication_type_label = infer_publication_type(venue, status)
            ccf_level = normalize_level(row.get("level", ""), row_number) or infer_ccf_level(venue, title)
            source_url = validate_url(row.get("link", ""), row_number)
            record = {
                "id": paper_id,
                "year": normalize_year(row.get("year", ""), row_number),
                "title": title,
                "url": title_link(source_url, title),
                "source_url": source_url,
                "status": status,
                "status_label": status_label,
                "category": "manuscript" if status in MANUSCRIPT_STATUSES else "publication",
                "authors": build_authors(row, aliases, row_number, unmatched),
                "ccf_level": ccf_level,
                "publication_type": publication_type,
                "publication_type_label": publication_type_label,
                "venue": venue,
                "note": clean_text(row.get("note")),
                "source_order": source_order,
            }
            records.append(record)

    records.sort(key=lambda record: (-record["year"], record["source_order"]))
    return {"schema_version": 1, "publications": records}, unmatched


def write_catalog(catalog: dict[str, Any], output_path: Path, *, check: bool) -> bool:
    rendered = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    existing = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    if check:
        if existing != rendered:
            raise PublicationImportError(f"{output_path} 未同步，请运行导入脚本。")
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return existing != rendered


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert the laboratory publication CSV into Hugo JSON data.")
    parser.add_argument(
        "--csv", type=Path, default=Path("frontend/publication-source/publications.csv")
    )
    parser.add_argument("--aliases", type=Path, default=Path("frontend/data/member-aliases.json"))
    parser.add_argument("--output", type=Path, default=Path("frontend/data/publication-records.json"))
    parser.add_argument("--check", action="store_true", help="Fail when the generated JSON is not current.")
    parser.add_argument("--show-unlinked", action="store_true", help="Print every author that has no exact member alias.")
    args = parser.parse_args()

    catalog, unmatched = import_csv(args.csv, args.aliases)
    changed = write_catalog(catalog, args.output, check=args.check)
    verb = "Updated" if changed else "Verified"
    print(f"{verb} {args.output} with {len(catalog['publications'])} publications.")
    if unmatched:
        print(f"{len(unmatched)} authors have no exact member alias.")
        if args.show_unlinked:
            print("Unlinked authors (add exact aliases when they are lab members): " + ", ".join(sorted(unmatched)))


if __name__ == "__main__":
    try:
        main()
    except PublicationImportError as error:
        raise SystemExit(f"Publication import failed: {error}")
