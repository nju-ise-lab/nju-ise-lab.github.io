from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from urllib.parse import urlparse

from . import core


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "output"
LOCAL_SLIDE_IMAGES = (
    "/images/legacy/home/01.jpg",
    "/images/legacy/home/02.jpg",
    "/images/legacy/home/03.jpg",
    "/images/legacy/home/04.png",
)
FEATURED_PROJECT_PRIORITIES = (
    ("国家重点研发计划", "National key R&D program"),
    ("国家自然科学基金项目（重点项目）", "National natural science foundation of China (Key Program)"),
    ("国家自然科学基金（重大项目）", "National natural science foundation of China (Major Program)"),
    ("国家重点基础研究发展计划", "973 Program"),
)
PROJECT_CHINESE_TITLE_MARKERS = (
    "国家重点研发计划",
    "国家自然科学基金项目",
    "国家自然科学基金",
    "国家重点基础研究发展计划",
    "教育部",
    "江苏省",
    "腾讯项目",
    "华为项目",
)


@dataclass(frozen=True)
class GeneratedFile:
    path: str
    content: str


@dataclass(frozen=True)
class GeneratedSite:
    files: tuple[GeneratedFile, ...]

    def file(self, path: str) -> GeneratedFile | None:
        for generated in self.files:
            if generated.path == path:
                return generated
        return None


@dataclass(frozen=True)
class GeneratedEntry:
    section: str
    legacy_id: int | str | None
    slug: str
    url: str
    file_path: str
    front_matter: dict
    body: str
    source: dict


def load_legacy_input(input_dir: Path) -> dict:
    legacy: dict[str, object] = {}
    for path in sorted(input_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            legacy[path.stem] = json.load(handle)
    return legacy


def generate_site(legacy: dict) -> GeneratedSite:
    entries: list[GeneratedEntry] = []
    media_manifest: list[dict] = []

    entries.extend(_article_entries("news", legacy, id_field="newsId"))
    entries.extend(_article_entries("activities", legacy, id_field="activitiesId"))
    entries.extend(_article_entries("platform", legacy, id_field="id", source_name="products"))
    entries.extend(_member_entries(legacy))

    files: list[GeneratedFile] = []
    files.extend(_section_index_files())
    files.extend(_page_files(legacy))
    for entry in entries:
        files.append(GeneratedFile(entry.file_path, _render_markdown(entry.front_matter, entry.body)))
        media_manifest.extend(_media_manifest_for_entry(entry))

    media_manifest.extend(_slide_media_manifest(legacy.get("slides") or []))

    files.extend(
        [
            GeneratedFile("data/featured-projects.json", _json(_featured_projects_data(entries))),
            GeneratedFile("data/projects.json", _json(_projects_data(legacy.get("projects") or []))),
            GeneratedFile("data/publications.json", _json(_publications_data(legacy.get("publications") or {}))),
            GeneratedFile("data/slides.json", _json(_slides_data(legacy.get("slides") or []))),
            GeneratedFile("data/legacy-map.json", _json(_legacy_map(entries))),
            GeneratedFile("data/media-manifest.json", _json(media_manifest)),
        ]
    )

    return GeneratedSite(tuple(files))


def _section_index_files() -> list[GeneratedFile]:
    sections = (
        ("news", "新闻资讯", "/news/"),
        ("activities", "学术活动", "/activities/"),
        ("platform", "科研项目", "/platform/"),
        ("members", "成员介绍", "/members/"),
    )
    return [
        GeneratedFile(
            f"content/{section}/_index.md",
            _render_markdown({"title": title, "url": url}, ""),
        )
        for section, title, url in sections
    ]


def _page_files(legacy: dict) -> list[GeneratedFile]:
    about = legacy.get("about") or {}
    about_body = about.get("about") if isinstance(about, dict) else ""
    recruit_items = _items(legacy.get("recruit_details")) or _items(legacy.get("recruit"))

    files = [
        GeneratedFile(
            "content/about/_index.md",
            _render_markdown({"title": "关于我们", "url": "/about/"}, about_body or "暂无关于我们内容。"),
        ),
        GeneratedFile(
            "content/projects/_index.md",
            _render_markdown({"title": "科研项目", "url": "/projects/"}, "科研项目列表由旧站项目数据自动生成。"),
        ),
    ]

    if recruit_items:
        body = "\n\n".join((item.get("context") or item.get("content") or item.get("name") or "").strip() for item in recruit_items)
    else:
        body = "暂无招聘信息。后续只需要编辑本文件即可更新诚聘英才页面。"

    files.append(
        GeneratedFile(
            "content/jobs/_index.md",
            _render_markdown({"title": "诚聘英才", "url": "/jobs/"}, body),
        )
    )
    return files


def write_site(site: GeneratedSite, output_dir: Path) -> dict:
    output_dir = output_dir.resolve()
    _validate_output_dir(output_dir)

    for generated in site.files:
        destination = (output_dir / generated.path).resolve()
        if not _is_relative_to(destination, output_dir):
            raise ValueError(f"Generated path escapes output directory: {generated.path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(generated.content, encoding="utf-8")

    return {"output_dir": str(output_dir), "files_written": len(site.files)}


def _article_entries(
    section: str,
    legacy: dict,
    *,
    id_field: str,
    source_name: str | None = None,
) -> list[GeneratedEntry]:
    source_name = source_name or section
    records = _merged_records(
        legacy.get(source_name),
        legacy.get(f"{source_name}_details"),
        id_field=id_field,
    )
    registry = core.SlugRegistry(prefix=section)
    entries: list[GeneratedEntry] = []

    for record in records:
        legacy_id = record.get(id_field)
        title = record.get("name") or record.get("title") or ""
        slug = registry.generate(title, legacy_id=legacy_id)
        front_matter = _front_matter(section, record, slug=slug)
        body = record.get("context") or record.get("content") or ""
        entries.append(
            GeneratedEntry(
                section=section,
                legacy_id=legacy_id,
                slug=slug,
                url=front_matter["url"],
                file_path=f"content/{section}/{slug}/index.md",
                front_matter=front_matter,
                body=body,
                source=record,
            )
        )

    return entries


def _member_entries(legacy: dict) -> list[GeneratedEntry]:
    records = legacy.get("members_details") or legacy.get("members") or []
    registry = core.SlugRegistry(prefix="member")
    entries: list[GeneratedEntry] = []

    for record in records:
        legacy_id = record.get("id")
        slug = registry.generate(record.get("name"), legacy_id=legacy_id)
        front_matter = core.build_member_front_matter(record, slug=slug)
        body = "\n\n".join(
            value
            for value in (
                record.get("basicMessage"),
                record.get("academicAchievement"),
                record.get("honor"),
                record.get("others"),
            )
            if value and value != "无"
        )
        entries.append(
            GeneratedEntry(
                section="members",
                legacy_id=legacy_id,
                slug=slug,
                url=front_matter["url"],
                file_path=f"content/members/{slug}/index.md",
                front_matter=front_matter,
                body=body,
                source=record,
            )
        )

    return entries


def _front_matter(section: str, record: dict, *, slug: str) -> dict:
    if section == "news":
        front_matter = core.build_news_front_matter(record, slug=slug)
    elif section == "activities":
        front_matter = core.build_activity_front_matter(record, slug=slug)
    elif section == "platform":
        front_matter = core.build_platform_front_matter(record, slug=slug)
    else:
        raise ValueError(f"Unsupported article section: {section}")

    cover = record.get("cover")
    if cover and not core.is_generic_project_image(cover) and "image" not in front_matter:
        front_matter["image"] = "cover" + _url_extension(cover, default=".png")
    return front_matter


def _merged_records(list_payload: object, detail_payload: object, *, id_field: str) -> list[dict]:
    list_items = _items(list_payload)
    detail_items = _items(detail_payload)
    if not list_items:
        return [dict(item) for item in detail_items]
    if not detail_items:
        return [dict(item) for item in list_items]

    detail_by_id = {item.get(id_field): item for item in detail_items}
    records: list[dict] = []
    seen: set[object] = set()
    for item in list_items:
        legacy_id = item.get(id_field)
        merged = dict(item)
        merged.update(detail_by_id.get(legacy_id, {}))
        records.append(merged)
        seen.add(legacy_id)

    for item in detail_items:
        if item.get(id_field) not in seen:
            records.append(dict(item))
    return records


def _items(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        items = payload.get("items")
        return items if isinstance(items, list) else []
    if isinstance(payload, list):
        return payload
    return []


def _legacy_map(entries: list[GeneratedEntry]) -> list[dict]:
    return [
        {
            "section": entry.section,
            "legacy_id": entry.legacy_id,
            "old": _legacy_query_url(entry.section, entry.legacy_id),
            "new": entry.url,
        }
        for entry in entries
        if _legacy_query_url(entry.section, entry.legacy_id)
    ]


def _legacy_query_url(section: str, legacy_id: int | str | None) -> str:
    if legacy_id in (None, ""):
        return ""
    if section == "news":
        return f"/news/detail?newsId={legacy_id}"
    if section == "activities":
        return f"/activity/detail?activitiesId={legacy_id}"
    if section == "platform":
        return f"/platform/detail?platformId={legacy_id}"
    if section == "members":
        return f"/member/detail?memberId={legacy_id}"
    return ""


def _projects_data(records: list[dict]) -> list[dict]:
    return [
        {
            "legacy_id": record.get("id"),
            "english": (record.get("english") or "").strip(),
            "chinese": (record.get("chinese") or "").strip(),
        }
        for record in records
    ]


def _featured_projects_data(entries: list[GeneratedEntry]) -> list[dict]:
    platform_entries = [entry for entry in entries if entry.section == "platform"]
    selected: list[GeneratedEntry] = []
    selected_ids: set[int | str | None] = set()

    for needles in FEATURED_PROJECT_PRIORITIES:
        for entry in platform_entries:
            if entry.legacy_id in selected_ids:
                continue
            title = entry.front_matter.get("title") or ""
            if any(needle in title for needle in needles):
                selected.append(entry)
                selected_ids.add(entry.legacy_id)

    for entry in platform_entries:
        if entry.legacy_id in selected_ids:
            continue
        selected.append(entry)
        selected_ids.add(entry.legacy_id)

    return [
        {
            "legacy_id": entry.legacy_id,
            "title": _compact_project_title(entry.front_matter.get("title") or ""),
            "url": entry.url,
        }
        for entry in selected[:4]
    ]


def _publications_data(payload: dict) -> list[dict]:
    publications: list[dict] = []
    for year in sorted(payload, reverse=True):
        group = payload.get(year) or {}
        for paper in group.get("papers") or []:
            publications.append(
                {
                    "legacy_id": paper.get("id"),
                    "year": paper.get("publishYear") or group.get("year") or year,
                    "content": paper.get("content") or "",
                    "create_time": core.normalize_datetime(paper.get("createTime")),
                }
            )
    return publications


def _slides_data(records: list[dict]) -> list[dict]:
    return [
        {
            "legacy_id": record.get("id"),
            "image": _local_slide_path(record, index),
            "fit": "contain",
            "url": "" if _is_image_url(record.get("url")) else record.get("url") or "",
            "create_time": core.normalize_datetime(record.get("createTime")),
        }
        for index, record in enumerate(records)
    ]


def _local_slide_path(record: dict, index: int) -> str:
    source = record.get("cover") or record.get("url")
    if _is_image_url(source):
        legacy_id = record.get("id") or index + 1
        return f"/images/slides/slide-{legacy_id}{_url_extension(source, default='.png')}"
    return source or LOCAL_SLIDE_IMAGES[index % len(LOCAL_SLIDE_IMAGES)]


def _is_image_url(url: str | None) -> bool:
    return bool(_url_extension(url, default=""))


def _compact_project_title(title: str) -> str:
    for marker in PROJECT_CHINESE_TITLE_MARKERS:
        marker_index = title.find(marker)
        if marker_index >= 0:
            return title[marker_index:].strip()
    return title.strip()


def _media_manifest_for_entry(entry: GeneratedEntry) -> list[dict]:
    manifest: list[dict] = []
    for source_field, output_field in (("cover", "image"), ("avatar", "avatar")):
        url = entry.source.get(source_field)
        if source_field == "cover" and core.is_generic_project_image(url):
            continue
        ref = core.classify_media_url(url, context=output_field)
        if ref.should_localize:
            basename = "cover" if output_field == "image" else output_field
            manifest.append(_media_manifest_item(entry, ref.url, output_field, basename))

    for index, ref in enumerate(core.extract_media_references(entry.body), start=1):
        if ref.should_localize:
            manifest.append(_media_manifest_item(entry, ref.url, "body", f"media-{index}"))

    return manifest


def _slide_media_manifest(records: list[dict]) -> list[dict]:
    manifest: list[dict] = []
    for record in records:
        legacy_id = record.get("id")
        for field in ("url", "cover"):
            ref = core.classify_media_url(record.get(field), context="image")
            if not ref.should_localize:
                continue
            manifest.append(
                {
                    "section": "slides",
                    "legacy_id": legacy_id,
                    "field": "image",
                    "source_url": ref.url,
                    "suggested_path": f"static/images/slides/slide-{legacy_id}{_url_extension(ref.url, default='.png')}",
                }
            )
    return manifest


def _media_manifest_item(entry: GeneratedEntry, url: str, field: str, basename: str) -> dict:
    return {
        "section": entry.section,
        "legacy_id": entry.legacy_id,
        "slug": entry.slug,
        "field": field,
        "source_url": url,
        "suggested_path": f"content/{entry.section}/{entry.slug}/{basename}{_url_extension(url, default='.png')}",
    }


def _render_markdown(front_matter: dict, body: str) -> str:
    return f"---\n{_yaml(front_matter)}---\n\n{body.strip()}\n"


def _yaml(values: dict) -> str:
    return "".join(f"{key}: {_yaml_scalar(value)}\n" for key, value in values.items())


def _yaml_scalar(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _url_extension(url: str | None, *, default: str) -> str:
    if not url:
        return default
    path = urlparse(url).path
    extension = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return extension if extension in core.IMAGE_EXTENSIONS else default


def _validate_output_dir(output_dir: Path) -> None:
    allowed_output = DEFAULT_OUTPUT_DIR.resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if _is_relative_to(output_dir, allowed_output) or _is_relative_to(output_dir, temp_root):
        return
    raise ValueError(f"Output directory must be under {allowed_output} or {temp_root}: {output_dir}")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
