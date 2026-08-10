from __future__ import annotations

import argparse
import csv
from datetime import date
import html
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

try:
    from tools.data_import_common import clean_text, parse_boolean, write_json
except ModuleNotFoundError:
    from data_import_common import clean_text, parse_boolean, write_json


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SOURCE_PATH = FRONTEND / "data-source" / "news.csv"
OUTPUT_PATH = FRONTEND / "data" / "news-records.json"
CONTENT_DIR = FRONTEND / "content" / "news"
FIG_DIR = FRONTEND / "data-source" / "fig"
REQUIRED_COLUMNS = (
    "news_id",
    "title",
    "date",
    "source_url",
    "summary",
    "content_html",
    "cover_image",
    "category",
    "pinned",
)
GENERATED_PAGE_MARKER = 'generated_from: "frontend/data-source/news.csv"'


class NewsImportError(ValueError):
    pass


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise NewsImportError(f"缺少新闻 CSV 文件：{path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise NewsImportError(
                f"{path} 字段应依次为 {', '.join(REQUIRED_COLUMNS)}。"
            )
        return [dict(row) for row in reader]


def validate_source_url(value: str, row_number: int) -> str:
    source_url = clean_text(value)
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise NewsImportError(f"第 {row_number} 行的 source_url 必须是完整的 http(s) 链接。")
    return source_url


def validate_cover_image(value: str, row_number: int) -> tuple[str, str]:
    cover_image = clean_text(value)
    if not cover_image:
        return "", ""
    relative = Path(cover_image)
    if relative.is_absolute() or ".." in relative.parts:
        raise NewsImportError(f"第 {row_number} 行的 cover_image 必须是 fig 下的相对路径。")
    path = FIG_DIR / relative
    if not path.is_file():
        raise NewsImportError(f"第 {row_number} 行的封面图片不存在：{path}")
    return relative.as_posix(), f"/images/data-source/{relative.as_posix()}"


def build_outputs(
    rows: list[dict[str, str]] | None = None,
) -> tuple[dict[str, Any], dict[Path, str]]:
    records: list[dict[str, Any]] = []
    pages: dict[Path, str] = {}
    seen_ids: set[str] = set()
    for source_order, row in enumerate(rows if rows is not None else read_rows(SOURCE_PATH), start=1):
        row_number = source_order + 1
        news_id = clean_text(row.get("news_id"))
        title = clean_text(row.get("title"))
        raw_date = clean_text(row.get("date"))
        summary = clean_text(row.get("summary"))
        content_html = str(row.get("content_html") or "").strip()
        category = clean_text(row.get("category"))

        if not re.fullmatch(r"nju-\d+", news_id):
            raise NewsImportError(f"第 {row_number} 行的 news_id 应使用 nju-123456 格式。")
        if news_id in seen_ids:
            raise NewsImportError(f"第 {row_number} 行的 news_id `{news_id}` 重复。")
        if not title or not category or not content_html:
            raise NewsImportError(f"第 {row_number} 行缺少 title、content_html 或 category。")
        try:
            published = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise NewsImportError(f"第 {row_number} 行的 date 必须为 YYYY-MM-DD。") from exc

        source_url = validate_source_url(row.get("source_url", ""), row_number)
        cover_image, cover_image_url = validate_cover_image(row.get("cover_image", ""), row_number)
        try:
            pinned = parse_boolean(row.get("pinned", ""), label="pinned", row_number=row_number)
        except ValueError as exc:
            raise NewsImportError(str(exc)) from exc

        seen_ids.add(news_id)
        record: dict[str, Any] = {
            "id": news_id,
            "title": title,
            "date": published.isoformat(),
            "source_url": source_url,
            "summary": summary,
            "content_html": content_html,
            "cover_image": cover_image,
            "category": category,
            "pinned": pinned,
            "source_order": source_order,
        }
        if cover_image_url:
            record["cover_image_url"] = cover_image_url
        records.append(record)
        pages[CONTENT_DIR / news_id / "index.md"] = render_page(record)

    records.sort(key=lambda record: (record["date"], -record["source_order"]), reverse=True)
    return {"schema_version": 1, "news": records}, pages


def render_page(record: dict[str, Any]) -> str:
    timestamp = f"{record['date']}T00:00:00+08:00"
    page_url = f"/news/{record['id']}/"
    source_link = html.escape(record["source_url"], quote=True)
    lines = [
        "---",
        f"title: {yaml_string(record['title'])}",
        f"date: {yaml_string(timestamp)}",
        f"category: {yaml_string(record['category'])}",
        f"pinned: {'true' if record['pinned'] else 'false'}",
        "draft: false",
        f"url: {yaml_string(page_url)}",
        f"source_url: {yaml_string(record['source_url'])}",
    ]
    if record.get("cover_image_url"):
        lines.append(f"image: {yaml_string(record['cover_image_url'])}")
    lines.extend(
        [
            'generated_from: "frontend/data-source/news.csv"',
            "---",
            "",
            record["content_html"],
            "",
            f'<p class="article__source">来源：<a href="{source_link}" target="_blank" rel="noreferrer">南京大学软件学院</a></p>',
            "",
        ]
    )
    return "\n".join(lines)


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


def check_outputs(payload: dict[str, Any], pages: dict[Path, str]) -> bool:
    mismatches: list[Path] = []
    if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != expected_json(payload):
        mismatches.append(OUTPUT_PATH)
    for path, expected in pages.items():
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(path)
    mismatches.extend(sorted(find_generated_pages() - set(pages)))
    if mismatches:
        print("以下新闻生成文件未同步：")
        for path in mismatches:
            print(f"- {path}")
        return False
    print(f"Verified {len(payload['news'])} generated news items.")
    return True


def write_outputs(payload: dict[str, Any], pages: dict[Path, str]) -> None:
    write_json(payload, OUTPUT_PATH, check=False)
    for path, content in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    stale_pages = find_generated_pages() - set(pages)
    for path in stale_pages:
        path.unlink()
        if not any(path.parent.iterdir()):
            path.parent.rmdir()
    print(f"Updated {OUTPUT_PATH} with {len(payload['news'])} news items.")
    print(f"Updated {len(pages)} generated news pages.")
    if stale_pages:
        print(f"Removed {len(stale_pages)} obsolete generated news pages.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the iSE news CSV and generate Hugo news data/pages."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, pages = build_outputs()
        if args.check:
            return 0 if check_outputs(payload, pages) else 1
        write_outputs(payload, pages)
        return 0
    except NewsImportError as exc:
        print(f"News import failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
