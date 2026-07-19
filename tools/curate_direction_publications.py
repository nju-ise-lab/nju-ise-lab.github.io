from __future__ import annotations

import argparse
import csv
from difflib import SequenceMatcher
from hashlib import sha1
from pathlib import Path
import re
from typing import Any

try:
    from tools.enrich_publications import compact, fetch_dblp_catalog
    from tools.import_publications import import_csv
except ModuleNotFoundError:  # Support `python3 tools/curate_direction_publications.py`.
    from enrich_publications import compact, fetch_dblp_catalog
    from import_publications import import_csv


CSV_FIELDS = ["year", "id", "title", "link", "status", "author", "cofauthor", "corauthor", "level", "venue", "note"]
DIRECTIONS = {
    "代码自动理解",
    "代码自动修复",
    "单元测试生成",
    "GUI测试生成",
    "智能系统测试理论与方法",
    "深度学习框架测试",
    "自动驾驶与智能网联测试",
    "众包与群体智能测试",
}
CCF_LEVELS = {
    "ICSE": "CCF-A",
    "TSE": "CCF-A",
    "TOSEM": "CCF-A",
    "ASE": "CCF-A",
    "FSE": "CCF-A",
    "ISSTA": "CCF-A",
    "TDSC": "CCF-A",
    "CSUR": "CCF-A",
    "CVPR": "CCF-A",
    "JSS": "CCF-B",
    "EMSE": "CCF-B",
}
VENUE_NAMES = {
    "ICSE": "IEEE/ACM International Conference on Software Engineering (ICSE)",
    "TSE": "IEEE Transactions on Software Engineering",
    "TOSEM": "ACM Transactions on Software Engineering and Methodology",
    "ASE": "IEEE/ACM International Conference on Automated Software Engineering (ASE)",
    "FSE": "ACM International Conference on the Foundations of Software Engineering (FSE)",
    "ISSTA": "ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)",
    "TDSC": "IEEE Transactions on Dependable and Secure Computing",
    "CSUR": "ACM Computing Surveys",
    "CVPR": "IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)",
    "JSS": "Journal of Systems and Software",
    "EMSE": "Empirical Software Engineering",
}
VENUE_PATTERN = "|".join(sorted((*CCF_LEVELS, "arXiv", "软件学报", "Springer", "QRS", "TRel"), key=len, reverse=True))
LISTING_PATTERN = re.compile(rf"^(?P<title>.+?)(?:\.\s*|\s+)(?P<venue>{VENUE_PATTERN})\s*(?P<year>20\d{{2}})?\s*$", re.I)

# ACTesting was not yet available in the three DBLP author catalogs during
# the refresh, but its publication metadata is explicitly available from ACM.
MANUAL_METADATA = {
    "ACTesting: Automated Cross-modal Testing Method of Text-to-Image Software": {
        "title": "ACTesting: Automated Cross-modal Testing Method of Text-to-Image Software",
        "authors": ["Siqi Gu", "Chunrong Fang", "Quanjun Zhang", "Zhenyu Chen"],
        "year": "2025",
        "link": "https://doi.org/10.1145/3768581",
        "record_type": "article",
    }
}


class CurationError(ValueError):
    pass


def parse_listing(path: Path) -> list[dict[str, str]]:
    direction = ""
    records: list[dict[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line in DIRECTIONS:
            direction = line
            continue
        if not direction:
            continue
        match = LISTING_PATTERN.match(line)
        if not match:
            raise CurationError(f"无法解析研究方向清单中的论文行：{line}")
        item = {key: (value or "").strip() for key, value in match.groupdict().items()}
        item["direction"] = direction
        records.append(item)
    return records


def best_dblp_candidate(title: str, catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
    key = compact(title)
    matches = ((SequenceMatcher(None, key, compact(item["title"])).ratio(), item) for item in catalog)
    score, candidate = max(matches, key=lambda item: item[0])
    return candidate if score >= 0.93 else None


def paper_id(title: str) -> str:
    return f"curated-{sha1(title.encode('utf-8')).hexdigest()[:12]}"


def build_row(spec: dict[str, str], catalog: list[dict[str, Any]]) -> dict[str, str]:
    if spec["venue"] not in CCF_LEVELS:
        raise CurationError(f"{spec['title']} 没有明确 CCF 分类，不能加入。")
    candidate = MANUAL_METADATA.get(spec["title"]) or best_dblp_candidate(spec["title"], catalog)
    if not candidate:
        raise CurationError(f"未能在 DBLP 或人工核验数据中找到：{spec['title']}")

    is_manuscript = candidate.get("venue") == "CoRR"
    return {
        "year": spec["year"] if is_manuscript else str(candidate["year"]),
        "id": paper_id(spec["title"]),
        "title": candidate["title"],
        "link": candidate["link"],
        "status": "accepted" if is_manuscript else "published",
        "author": ";".join(candidate["authors"]),
        "cofauthor": "",
        "corauthor": "",
        "level": CCF_LEVELS[spec["venue"]],
        "venue": VENUE_NAMES[spec["venue"]],
        "note": "",
    }


def title_key(value: str) -> str:
    return compact(value)


def curate(source_path: Path, csv_path: Path, aliases_path: Path) -> tuple[list[dict[str, str]], dict[str, int]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        existing_rows = list(csv.DictReader(handle))

    current_catalog, _ = import_csv(csv_path, aliases_path)
    existing_ccf = {record["id"]: record["ccf_level"] for record in current_catalog["publications"]}
    retained = [row.copy() for row in existing_rows if existing_ccf.get(row["id"])]
    for row in retained:
        row["level"] = existing_ccf[row["id"]]

    specs = parse_listing(source_path)
    catalog = fetch_dblp_catalog()
    existing_titles = {title_key(row["title"]): row for row in retained}
    added = 0
    skipped = 0
    for spec in specs:
        if spec["venue"] not in CCF_LEVELS:
            skipped += 1
            continue
        row = build_row(spec, catalog)
        key = title_key(row["title"])
        if key in existing_titles:
            # Preserve the stable legacy id while replacing incomplete metadata.
            row["id"] = existing_titles[key]["id"]
            retained = [row if item["id"] == row["id"] else item for item in retained]
        else:
            retained.append(row)
            existing_titles[key] = row
            added += 1

    retained.sort(key=lambda row: (-int(row["year"]), row["title"].lower()))
    stats = {"existing": len(existing_rows), "retained": len(retained), "added": added, "skipped_unclassified": skipped}
    return retained, stats


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep CCF-classified publications and import the research-direction listing.")
    parser.add_argument("--source", type=Path, required=True, help="Plain-text research-direction listing supplied by the laboratory.")
    parser.add_argument("--csv", type=Path, default=Path("frontend/publication-source/publications.csv"))
    parser.add_argument("--aliases", type=Path, default=Path("frontend/data/member-aliases.json"))
    parser.add_argument("--apply", action="store_true", help="Write the curated result to the CSV after validation.")
    args = parser.parse_args()

    rows, stats = curate(args.source, args.csv, args.aliases)
    print(
        "Curation: "
        + ", ".join(f"{key}={value}" for key, value in stats.items())
        + ("; writing changes." if args.apply else "; dry run only.")
    )
    if args.apply:
        backup = args.csv.with_suffix(args.csv.suffix + ".before-direction-curation")
        backup.write_text(args.csv.read_text(encoding="utf-8"), encoding="utf-8")
        write_csv(args.csv, rows)
        print(f"Backup: {backup}")


if __name__ == "__main__":
    try:
        main()
    except CurationError as error:
        raise SystemExit(f"Publication curation failed: {error}")
