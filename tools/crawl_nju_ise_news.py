from __future__ import annotations

import argparse
import base64
import csv
from datetime import date
import html
import json
from pathlib import Path
import re
import shutil
from typing import Any, Callable
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SOURCE_PATH = FRONTEND / "data-source" / "news.csv"
FIG_DIR = FRONTEND / "data-source" / "fig"
INDEX_URL = "https://software.nju.edu.cn/xyxw/index.html"
API_URL = "https://software.nju.edu.cn/njdx/openapi/t/info/list.do"
SITE_URL = "https://software.nju.edu.cn/"
CHANNEL_ID = "6437"
PAGE_SIZE = 15
ADDITIONAL_NEWS_IIDS = frozenset({"402149"})
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
USER_AGENT = "nju-ise-lab-news-importer/1.0 (+https://nju-ise-lab.github.io/)"
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}


class NewsCrawlError(ValueError):
    pass


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", errors="replace")


def api_value(value: str | int) -> str:
    return base64.b64encode(str(value).encode("utf-8")).decode("ascii")


def fetch_page(page_number: int) -> dict[str, Any]:
    body = urlencode(
        {
            "channelid": api_value(CHANNEL_ID),
            "pageno": api_value(page_number),
            "pagesize": api_value(PAGE_SIZE),
        }
    ).encode("ascii")
    request = Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    with urlopen(request, timeout=30) as response:
        try:
            payload = json.loads(response.read().decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise NewsCrawlError(f"学院新闻第 {page_number} 页返回了无效 JSON。") from exc
    if not isinstance(payload, dict):
        raise NewsCrawlError(f"学院新闻第 {page_number} 页返回格式不正确。")
    return payload


def parse_index_pages(document: str) -> tuple[list[dict[str, Any]], int]:
    match = re.search(
        r"\bdataList\s*=\s*(\[.*?\])\s*;\s*var\s+pagesData\b",
        document,
        flags=re.DOTALL,
    )
    if not match:
        raise NewsCrawlError("无法从学院新闻列表页读取预加载新闻数据。")
    try:
        pages = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise NewsCrawlError("学院新闻列表页中的预加载新闻数据不是有效 JSON。") from exc
    if not isinstance(pages, list):
        raise NewsCrawlError("学院新闻列表页中的预加载新闻数据格式不正确。")

    page_total_match = re.search(r"\bpageTotal\s*=\s*parseInt\((\d+)\)", document)
    if not page_total_match:
        raise NewsCrawlError("无法从学院新闻列表页读取总页数。")
    return pages, int(page_total_match.group(1))


def collect_list_items(
    index_document: str,
    page_fetcher: Callable[[int], dict[str, Any]] = fetch_page,
) -> list[dict[str, Any]]:
    pages, page_total = parse_index_pages(index_document)
    if page_total < len(pages):
        raise NewsCrawlError("学院新闻列表页的分页数据不一致。")

    for page_number in range(len(pages) + 1, page_total + 1):
        pages.append(page_fetcher(page_number))

    items: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            raise NewsCrawlError("学院新闻列表页包含无效分页记录。")
        info_list = page.get("infolist", [])
        if not isinstance(info_list, list):
            raise NewsCrawlError("学院新闻列表页包含无效新闻列表。")
        items.extend(item for item in info_list if isinstance(item, dict))
    return items


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def select_ise_news(items: list[dict[str, Any]], since: date) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for item in items:
        raw_date = clean_text(item.get("daytime"))
        raw_title = clean_text(item.get("title"))
        iid = clean_text(item.get("iid"))
        source_url = clean_text(item.get("url"))
        try:
            published = date.fromisoformat(raw_date)
        except ValueError:
            continue
        title_matches = "ise实验室" in normalize_title(raw_title)
        if published < since or (not title_matches and iid not in ADDITIONAL_NEWS_IIDS):
            continue
        if not iid or not source_url:
            raise NewsCrawlError(f"新闻《{raw_title}》缺少 IID 或详情页链接。")
        selected[iid] = item

    return sorted(
        selected.values(),
        key=lambda item: (clean_text(item.get("daytime")), int(item.get("iid", 0))),
        reverse=True,
    )


def extract_content_html(document: str) -> str:
    match = re.search(
        r'<div\s+class=["\']content["\']\s*>(.*?)</div>\s*<div\s+id=["\']upanddown["\']',
        document,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        raise NewsCrawlError("无法从新闻详情页提取正文。")
    content = match.group(1).strip()
    if not content:
        raise NewsCrawlError("新闻详情页正文为空。")
    return content


def image_extension(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in IMAGE_EXTENSIONS else ".bin"


def rewrite_images(
    content_html: str,
    detail_url: str,
    news_id: str,
    fig_dir: Path,
    image_fetcher: Callable[[str], bytes] = fetch_bytes,
) -> tuple[str, str]:
    image_counter = 0
    cover_image = ""

    def replace_image(match: re.Match[str]) -> str:
        nonlocal image_counter, cover_image
        original = html.unescape(match.group("src").strip())
        if original.startswith("data:"):
            return match.group(0)
        absolute_url = urljoin(detail_url, original)
        parsed = urlparse(absolute_url)
        if parsed.scheme not in {"http", "https"}:
            raise NewsCrawlError(f"新闻《{news_id}》包含不支持的图片链接：{original}")

        image_counter += 1
        relative_path = Path("news") / news_id / f"image-{image_counter:03d}{image_extension(absolute_url)}"
        output_path = fig_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_fetcher(absolute_url))
        if not cover_image:
            cover_image = relative_path.as_posix()

        prefix = match.group("prefix")
        quote = match.group("quote")
        return f'{prefix}{quote}/images/data-source/{relative_path.as_posix()}{quote}'

    pattern = re.compile(
        r'(?P<prefix>\bsrc\s*=\s*)(?P<quote>["\'])(?P<src>.*?)(?P=quote)',
        flags=re.IGNORECASE,
    )
    return pattern.sub(replace_image, content_html), cover_image


def read_editorial_fields(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return {}
        return {
            clean_text(row.get("news_id")): {
                "category": clean_text(row.get("category")) or "学院新闻",
                "pinned": clean_text(row.get("pinned")) or "FALSE",
            }
            for row in reader
            if clean_text(row.get("news_id"))
        }


def render_csv(rows: list[dict[str, str]]) -> str:
    from io import StringIO

    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def crawl_news(
    *,
    since: date,
    source_path: Path = SOURCE_PATH,
    fig_dir: Path = FIG_DIR,
    index_fetcher: Callable[[str], str] = fetch_text,
    page_fetcher: Callable[[int], dict[str, Any]] = fetch_page,
    detail_fetcher: Callable[[str], str] = fetch_text,
    image_fetcher: Callable[[str], bytes] = fetch_bytes,
) -> list[dict[str, str]]:
    editorial = read_editorial_fields(source_path)
    items = select_ise_news(
        collect_list_items(index_fetcher(INDEX_URL), page_fetcher), since
    )
    rows: list[dict[str, str]] = []
    staged_root = fig_dir / ".news-crawl-staging"
    if staged_root.exists():
        shutil.rmtree(staged_root)
    try:
        for item in items:
            iid = clean_text(item.get("iid"))
            news_id = f"nju-{iid}"
            source_url = urljoin(SITE_URL, clean_text(item.get("url")))
            content_html = extract_content_html(detail_fetcher(source_url))
            rewritten_content, cover_image = rewrite_images(
                content_html,
                source_url,
                news_id,
                staged_root,
                image_fetcher,
            )
            controls = editorial.get(news_id, {})
            rows.append(
                {
                    "news_id": news_id,
                    "title": clean_text(item.get("title")),
                    "date": clean_text(item.get("daytime")),
                    "source_url": source_url,
                    "summary": clean_text(re.sub(r"<[^>]+>", "", str(item.get("summary", "")))),
                    "content_html": rewritten_content,
                    "cover_image": cover_image,
                    "category": controls.get("category", "学院新闻"),
                    "pinned": controls.get("pinned", "FALSE"),
                }
            )

        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(render_csv(rows), encoding="utf-8")
        target_root = fig_dir / "news"
        if target_root.exists():
            shutil.rmtree(target_root)
        staged_news = staged_root / "news"
        if staged_news.exists():
            shutil.move(str(staged_news), str(target_root))
        return rows
    finally:
        if staged_root.exists():
            shutil.rmtree(staged_root)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Crawl Nanjing University Software School iSE laboratory news into CSV."
    )
    parser.add_argument("--since", default="2025-01-01", help="Include news on or after YYYY-MM-DD.")
    parser.add_argument("--output", type=Path, default=SOURCE_PATH)
    parser.add_argument("--fig-dir", type=Path, default=FIG_DIR)
    args = parser.parse_args()

    try:
        since = date.fromisoformat(args.since)
    except ValueError:
        parser.error("--since 必须使用 YYYY-MM-DD 格式。")

    try:
        rows = crawl_news(since=since, source_path=args.output, fig_dir=args.fig_dir)
    except (NewsCrawlError, OSError) as exc:
        print(f"News crawl failed: {exc}")
        return 1

    print(f"Updated {args.output} with {len(rows)} iSE news items since {since}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
