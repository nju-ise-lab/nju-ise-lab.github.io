from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
import re
import unicodedata
from urllib.parse import urlparse


CHINA_TZ = timezone(timedelta(hours=8))
IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".jfif",
    ".png",
    ".svg",
    ".webp",
}
MEDIA_CONTEXTS = {"avatar", "cover", "image", "img", "media"}
SECTION_BASE_URLS = {
    "news": "/news/",
    "activities": "/activities/",
    "platform": "/platform/",
    "members": "/members/",
}
LEGACY_ID_FIELDS = ("newsId", "activitiesId", "id")
STUDENT_ROLES = {"博士生", "硕士生"}
STUDENT_LABEL_PATTERN = re.compile(r"(\d{2}级[博硕]士生)")
STUDENT_DIRECTIONS = {
    "虞圣呈": "智能化软件测试与质量保障",
    "伊高磊": "智能化软件测试与质量保障",
    "顾思琦": "智能化软件测试与质量保障",
    "钱瑞祥": "智能化软件测试与质量保障",
    "郭安": "智能驾驶与测试",
    "戎润祥": "软件维护与程序自动化修复",
    "乔力": "软件维护与程序自动化修复",
}


@dataclass(frozen=True)
class MediaReference:
    url: str
    kind: str
    should_localize: bool
    context: str = "image"


def slugify_title(title: str | None, *, prefix: str = "item", legacy_id: int | str | None = None) -> str:
    """Create a deterministic ASCII slug without requiring pinyin dependencies."""
    text = unicodedata.normalize("NFKC", title or "").lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    slug = "-".join(tokens)
    if slug:
        return slug
    if legacy_id not in (None, ""):
        return f"{prefix}-{legacy_id}"
    return prefix


class SlugRegistry:
    def __init__(self, *, prefix: str = "item") -> None:
        self.prefix = prefix
        self._seen: dict[str, int] = {}

    def generate(self, title: str | None, *, legacy_id: int | str | None = None) -> str:
        base = slugify_title(title, prefix=self.prefix, legacy_id=legacy_id)
        count = self._seen.get(base, 0) + 1
        self._seen[base] = count
        if count == 1:
            return base
        return f"{base}-{count}"


def normalize_datetime(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=CHINA_TZ).isoformat()
        except ValueError:
            continue

    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=CHINA_TZ)
    return parsed.isoformat()


def section_base_url(section: str) -> str:
    try:
        return SECTION_BASE_URLS[section]
    except KeyError as exc:
        raise ValueError(f"Unknown section: {section}") from exc


def content_url(section: str, slug: str) -> str:
    return f"{section_base_url(section)}{slug}/"


def build_news_front_matter(record: dict, *, slug: str) -> dict:
    return {
        "title": record.get("name") or "",
        "date": normalize_datetime(record.get("createTime")),
        "category": record.get("category") or "",
        "creator": record.get("creator") or "",
        "legacy_id": _legacy_id(record),
        "draft": False,
        "url": content_url("news", slug),
    }


def build_activity_front_matter(record: dict, *, slug: str) -> dict:
    return {
        "title": record.get("name") or "",
        "date": normalize_datetime(record.get("time") or record.get("createTime")),
        "event_time": normalize_datetime(record.get("time")),
        "category": record.get("category") or "",
        "creator": record.get("creator") or "",
        "location": record.get("location") or "",
        "legacy_id": _legacy_id(record),
        "draft": False,
        "url": content_url("activities", slug),
    }


def build_platform_front_matter(record: dict, *, slug: str) -> dict:
    front_matter = {
        "title": record.get("title") or record.get("name") or "",
        "date": normalize_datetime(record.get("createTime")),
        "creator": record.get("creator") or "",
        "legacy_id": _legacy_id(record),
        "draft": False,
        "url": content_url("platform", slug),
    }
    if record.get("cover") and not is_generic_project_image(record["cover"]):
        front_matter["image"] = "cover" + _url_extension(record["cover"], default=".png")
    return front_matter


def build_member_front_matter(record: dict, *, slug: str) -> dict:
    name = record.get("name") or ""
    role = record.get("role") or ""
    front_matter = {
        "title": name,
        "role": role,
        "email": record.get("email") or "",
        "avatar": "avatar" + _url_extension(record.get("avatar"), default=".jpg") if record.get("avatar") else "",
        "academy": record.get("academy") or "",
        "sort": _int_or_zero(record.get("sort")),
        "legacy_id": _legacy_id(record),
        "url": content_url("members", slug),
    }
    research_direction = STUDENT_DIRECTIONS.get(name)
    if role in STUDENT_ROLES or research_direction:
        front_matter["research_direction"] = research_direction or ""
        front_matter["student_label"] = _student_label(record, role if role in STUDENT_ROLES else "")
    return front_matter


def classify_media_url(url: str | None, *, context: str = "link") -> MediaReference:
    text = (url or "").strip()
    if not text:
        return MediaReference(url="", kind="empty", should_localize=False, context=context)

    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https", ""}:
        return MediaReference(url=text, kind="unsupported", should_localize=False, context=context)

    if _is_legacy_api(parsed):
        return MediaReference(url=text, kind="legacy_api", should_localize=False, context=context)

    is_media_context = context in MEDIA_CONTEXTS
    if parsed.scheme in {"http", "https"} and is_media_context and _has_image_extension(parsed.path):
        return MediaReference(url=text, kind="download_candidate", should_localize=True, context=context)

    if parsed.scheme in {"http", "https"}:
        return MediaReference(url=text, kind="external_link", should_localize=False, context=context)

    return MediaReference(url=text, kind="relative", should_localize=False, context=context)


def is_generic_project_image(url: str | None) -> bool:
    """Identify the legacy ISE unit logo used as a project placeholder."""
    path = urlparse((url or "").strip()).path
    return path.rsplit("/", 1)[-1].lower().endswith("ise.jpg")


def extract_media_references(html: str | None) -> list[MediaReference]:
    parser = _ImageSourceParser()
    parser.feed(html or "")
    return [classify_media_url(url, context="image") for url in parser.urls]


class _ImageSourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attr_map = {name.lower(): value for name, value in attrs if value is not None}
        src = attr_map.get("src")
        if src:
            self.urls.append(src)


def _legacy_id(record: dict) -> int | str | None:
    for field in LEGACY_ID_FIELDS:
        if field in record:
            return record[field]
    return None


def _int_or_zero(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _student_label(record: dict, fallback: str) -> str:
    text = "\n".join(
        str(record.get(field) or "")
        for field in ("basicMessage", "honor", "academicAchievement", "others")
    )
    match = STUDENT_LABEL_PATTERN.search(text)
    if match:
        return match.group(1)
    return fallback


def _url_extension(url: str | None, *, default: str) -> str:
    if not url:
        return default
    suffix = "." + urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
    return suffix if suffix in IMAGE_EXTENSIONS else default


def _has_image_extension(path: str) -> bool:
    extension = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return extension in IMAGE_EXTENSIONS


def _is_legacy_api(parsed) -> bool:
    return parsed.hostname == "118.178.18.181" and (
        parsed.path.rstrip("/") == "/api" or parsed.path.startswith("/api/")
    )
