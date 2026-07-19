from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re


CSV_COLUMNS = [
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
]


def scalar(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return json.loads(value)
    return value


def parse_front_matter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, raw, _ = text.split("---", 2)
    result: dict[str, object] = {}
    current_list: list[dict[str, str]] | None = None
    current_item: dict[str, str] | None = None
    for line in raw.splitlines():
        if re.match(r"^[a-z_]+:", line):
            key, value = line.split(":", 1)
            if value.strip():
                result[key] = scalar(value)
                current_list = None
                current_item = None
            else:
                current_list = []
                result[key] = current_list
                current_item = None
        elif line.startswith("  - ") and current_list is not None:
            key, value = line.strip()[2:].split(":", 1)
            current_item = {key: scalar(value)}
            current_list.append(current_item)
        elif line.startswith("    ") and current_item is not None and ":" in line:
            key, value = line.strip().split(":", 1)
            current_item[key] = scalar(value)
    return result


def export_csv(activities_dir: Path, output_path: Path, *, force: bool) -> int:
    if output_path.exists() and not force:
        raise FileExistsError(f"{output_path} 已存在；如需重新导出，请使用 --force。")
    publications: list[dict[str, object]] = []
    for path in activities_dir.glob("*/index.md"):
        front_matter = parse_front_matter(path)
        if front_matter.get("content_kind") != "publication":
            continue
        publications.append(front_matter)
    publications.sort(key=lambda item: (-int(str(item.get("publication_year") or 0)), str(item.get("legacy_id") or "")))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in publications:
            authors = item.get("authors") or []
            writer.writerow(
                {
                    "year": item.get("publication_year", ""),
                    "id": f"publication-{item.get('legacy_id')}",
                    "title": item.get("title", ""),
                    "link": "",
                    "status": "published",
                    "author": ";".join(author.get("name", "") for author in authors),
                    "cofauthor": "",
                    "corauthor": "",
                    "level": "",
                    "venue": item.get("venue", ""),
                    "note": "",
                }
            )
    return len(publications)


def main() -> None:
    parser = argparse.ArgumentParser(description="One-time export of legacy Hugo publication pages to the CSV maintenance format.")
    parser.add_argument("--activities", type=Path, default=Path("frontend/content/activities"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("frontend/publication-source/publications.csv"),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    count = export_csv(args.activities, args.output, force=args.force)
    print(f"Exported {count} publications to {args.output}.")


if __name__ == "__main__":
    main()
