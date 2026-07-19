from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
from typing import Any
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


DBLP_PERSON_XMLS = (
    "https://dblp.org/pid/86/541-1.xml",  # Zhenyu Chen
    "https://dblp.org/pid/124/0310.xml",  # Chunrong Fang
    "https://dblp.org/pid/07/6095-3.xml",  # Yang Feng
)
USER_AGENT = "NJU-ISE-Lab-Publication-Refresh/1.0"
CSV_FIELDS = ["year", "id", "title", "link", "status", "author", "cofauthor", "corauthor", "level", "venue", "note"]
MIN_CONFIDENCE = 0.92


@dataclass
class Candidate:
    score: float
    title: str
    authors: list[str]
    year: str
    venue: str
    doi: str
    link: str
    record_type: str


def text_of(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext()).strip()


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def clean_title(value: str) -> str:
    value = re.sub(r"\s+(ICSE|ISSTA|ASE|FSE|QRS|SANER)\s*20\d{2}(?:\s+(?:demo|short paper))?$", "", value, flags=re.I)
    value = re.sub(r"\s+Journal of Software,?\s*20\d{2}$", "", value, flags=re.I)
    return value.strip()


def normalized_venue(value: str) -> str:
    names = {
        "ISSTA": "ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)",
        "ICSE": "IEEE/ACM International Conference on Software Engineering (ICSE)",
        "ICSE-Companion": "IEEE/ACM International Conference on Software Engineering: Companion Proceedings (ICSE-Companion)",
        "ASE": "IEEE/ACM International Conference on Automated Software Engineering (ASE)",
        "FSE": "ACM International Conference on the Foundations of Software Engineering (FSE)",
        "TSE": "IEEE Transactions on Software Engineering",
        "JSS": "Journal of Systems and Software",
        "EMSE": "Empirical Software Engineering",
        "SANER": "IEEE International Conference on Software Analysis, Evolution and Reengineering (SANER)",
        "Int. J. Softw. Eng. Knowl. Eng.": "International Journal of Software Engineering and Knowledge Engineering",
        "J. Softw. Evol. Process.": "Journal of Software: Evolution and Process",
        "IEEE Trans. Reliab.": "IEEE Transactions on Reliability",
        "IEEE Trans. Software Eng.": "IEEE Transactions on Software Engineering",
        "J. Syst. Softw.": "Journal of Systems and Software",
        "Empir. Softw. Eng.": "Empirical Software Engineering",
        "Frontiers Comput. Sci.": "Frontiers of Computer Science",
        "Sci. China Inf. Sci.": "Science China Information Sciences",
        "ACM Trans. Internet Techn.": "ACM Transactions on Internet Technology",
        "AITest": "IEEE International Conference on Artificial Intelligence Testing (AITest)",
        "QRS": "IEEE International Conference on Software Quality, Reliability and Security (QRS)",
    }
    return names.get(value, value)


def fetch_dblp_catalog() -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for source in DBLP_PERSON_XMLS:
        request = Request(source, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=60) as response:
            root = ET.fromstring(response.read())
        for wrapper in root.findall("r"):
            if not len(wrapper):
                continue
            record = wrapper[0]
            title = text_of(record.find("title")).rstrip(".")
            year = text_of(record.find("year"))
            if not title or not year:
                continue
            authors = [re.sub(r"\s+\d{4}$", "", text_of(author)).strip() for author in record.findall("author")]
            venue = text_of(record.find("journal")) or text_of(record.find("booktitle"))
            ees = [text_of(ee) for ee in record.findall("ee")]
            doi = next((entry.removeprefix("https://doi.org/") for entry in ees if "doi.org/" in entry), "")
            link = next((entry for entry in ees if entry.startswith(("http://", "https://"))), "")
            catalog.append(
                {
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "venue": normalized_venue(venue),
                    "doi": doi,
                    "link": link,
                    "record_type": record.tag,
                }
            )
    return catalog


def author_similarity(existing: str, candidate_authors: list[str]) -> float:
    existing_first = existing.split(";")[0].strip()
    if not existing_first or not candidate_authors:
        return 0.5
    left = compact(existing_first)
    right = compact(candidate_authors[0])
    if left == right:
        return 1.0
    if left in right or right in left:
        return 0.85
    return SequenceMatcher(None, left, right).ratio()


def venue_key(value: str) -> str:
    searchable = value.lower()
    markers = {
        "icse": "ICSE",
        "issta": "ISSTA",
        "ase": "ASE",
        "fse": "FSE",
        "saner": "SANER",
        "qrs": "QRS",
        "journal of systems and software": "JSS",
        "journal of software: evolution and process": "JSEP",
        "empirical software engineering": "EMSE",
        "transactions on software engineering": "TSE",
    }
    for marker, key in markers.items():
        if marker in searchable:
            return key
    return ""


def candidate_for(row: dict[str, str], catalog: list[dict[str, Any]]) -> Candidate | None:
    expected_year = row["year"].strip()
    best: Candidate | None = None
    for record in catalog:
        if expected_year.isdigit() and record["year"].isdigit() and abs(int(expected_year) - int(record["year"])) > 1:
            continue
        title_score = max(
            SequenceMatcher(None, compact(row["title"]), compact(record["title"])).ratio(),
            SequenceMatcher(None, compact(clean_title(row["title"])), compact(record["title"])).ratio(),
        )
        year_score = 1.0 if record["year"] == expected_year else 0.65
        expected_venue = venue_key(row["venue"])
        candidate_venue = venue_key(record["venue"])
        venue_score = 0.5
        if expected_venue:
            venue_score = 1.0 if expected_venue == candidate_venue else 0.0
        score = 0.74 * title_score + 0.12 * year_score + 0.08 * author_similarity(row["author"], record["authors"]) + 0.06 * venue_score
        candidate = Candidate(score=score, **record)
        if best is None or candidate.score > best.score:
            best = candidate
    return best


def enrich(rows: list[dict[str, str]], catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for row in rows:
        candidate = candidate_for(row, catalog)
        result: dict[str, Any] = {"id": row["id"], "title": row["title"], "status": "unmatched"}
        if candidate:
            result["candidate"] = asdict(candidate)
            result["status"] = "matched" if candidate.score >= MIN_CONFIDENCE else "review"
        results.append(result)
    return results


def apply_matches(rows: list[dict[str, str]], report: list[dict[str, Any]]) -> int:
    by_id = {item["id"]: item["candidate"] for item in report if item["status"] == "matched"}
    applied = 0
    for row in rows:
        candidate = by_id.get(row["id"])
        if not candidate:
            continue
        for key in ("title", "year", "venue", "link"):
            if candidate.get(key):
                row[key] = candidate[key]
        if candidate["authors"]:
            row["author"] = ";".join(candidate["authors"])
        applied += 1
    return applied


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify laboratory publication CSV rows against the DBLP author catalog.")
    parser.add_argument("--csv", type=Path, default=Path("frontend/publication-source/publications.csv"))
    parser.add_argument("--report", type=Path, default=Path("/tmp/ise-publication-enrichment.json"))
    parser.add_argument("--from-report", type=Path, help="Reuse an existing verification report without another DBLP request.")
    parser.add_argument("--apply", action="store_true", help="Apply only high-confidence matches to the CSV.")
    args = parser.parse_args()

    with args.csv.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    if args.from_report:
        report = json.loads(args.from_report.read_text(encoding="utf-8"))
        print(f"Reused verification report: {args.from_report}")
    else:
        catalog = fetch_dblp_catalog()
        report = enrich(rows, catalog)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Loaded {len(catalog)} DBLP publications.")

    counts: dict[str, int] = {}
    for item in report:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print("Metadata verification:", ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print(f"Review report: {args.report}")

    if args.apply:
        backup = args.csv.with_suffix(args.csv.suffix + ".before-dblp")
        backup.write_text(args.csv.read_text(encoding="utf-8"), encoding="utf-8")
        applied = apply_matches(rows, report)
        write_csv(args.csv, rows)
        print(f"Applied {applied} high-confidence matches. Backup: {backup}")


if __name__ == "__main__":
    main()
