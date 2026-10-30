from __future__ import annotations

import argparse
from collections import defaultdict
from copy import copy
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

try:
    from tools import import_publications as publications
    from tools.xlsx_reader import read_table
except ModuleNotFoundError:
    import import_publications as publications
    from xlsx_reader import read_table


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend/data-source/publications.xlsx"
CONFIG = ROOT / "tools/publication-sync.json"
ALIASES = ROOT / "frontend/data/member-aliases.json"
DBLP_API = "https://sparql.dblp.org/sparql"
CROSSREF_API = "https://api.crossref.org/works/"
DBLP_SCHEMA = "https://dblp.org/rdf/schema#"
USER_AGENT = "nju-ise-lab-publication-sync/1.0 (+https://nju-ise-lab.github.io/)"


class SyncError(ValueError):
    pass


def title_key(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in text if character.isalnum())


def doi_key(value: str) -> str:
    text = unquote(value.strip()).lower()
    if text.startswith(("http://", "https://")):
        parsed = urlparse(text)
        if parsed.hostname not in {"doi.org", "dx.doi.org"}:
            return ""
        text = parsed.path.lstrip("/")
    text = re.sub(r"^doi:\s*", "", text)
    return text if re.fullmatch(r"10\.\d{4,9}/\S+", text) else ""


def author_name(value: str) -> str:
    # DBLP's four-digit homonym suffix is an identifier, not part of the name.
    return publications.clean_text(re.sub(r" \d{4}$", "", value))


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1 or not config.get("authors"):
        raise SyncError("Invalid publication sync configuration.")
    for key in ("lookback_years", "max_new_records"):
        if type(config.get(key)) is not int or not 1 <= config[key] <= 100:
            raise SyncError(f"{key} must be an integer from 1 to 100.")
    if not isinstance(config.get("request_interval_seconds"), (int, float)) or config["request_interval_seconds"] < 1:
        raise SyncError("request_interval_seconds must be at least 1.")
    seen = set()
    for author in config["authors"]:
        if not re.fullmatch(r"[0-9]+/[0-9]+(?:-[0-9]+)?", author.get("dblp_pid", "")):
            raise SyncError("Every author needs a stable DBLP PID.")
        if not author.get("name") or not re.fullmatch(r"teacher-\d{3,}", author.get("member_id", "")):
            raise SyncError("Every author needs a name and teacher member ID.")
        if author["dblp_pid"] in seen:
            raise SyncError("Duplicate configured DBLP PID.")
        seen.add(author["dblp_pid"])
    ignored = config.get("ignored_dblp_records", [])
    if not isinstance(ignored, list) or any(not isinstance(item, str) for item in ignored):
        raise SyncError("ignored_dblp_records must be a list of DBLP record URLs.")
    return config


class ApiClient:
    def __init__(self, interval: float = 1, mailto: str = ""):
        self.interval = interval
        self.mailto = mailto
        self.last_request = 0.0

    def get_json(self, url: str) -> dict[str, Any]:
        time.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        agent = USER_AGENT + (f" (mailto:{self.mailto})" if self.mailto else "")
        request = Request(url, headers={"User-Agent": agent, "Accept": "application/sparql-results+json, application/json"})
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.load(response)
        except HTTPError:
            raise
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SyncError(f"API request failed ({urlparse(url).hostname}): {exc}") from exc
        if not isinstance(payload, dict):
            raise SyncError("API returned a non-object response.")
        return payload

    def crossref(self, doi: str) -> dict[str, Any] | None:
        url = CROSSREF_API + quote(doi, safe="")
        if self.mailto:
            url += "?" + urlencode({"mailto": self.mailto})
        try:
            payload = self.get_json(url)
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise SyncError(f"Crossref HTTP {exc.code}; no workbook changes were made.") from exc
        message = payload.get("message")
        if payload.get("status") != "ok" or not isinstance(message, dict):
            raise SyncError("Invalid Crossref response.")
        return message


def discovery_query(authors: list[dict[str, str]], since_year: int, current_year: int) -> str:
    people = " ".join(f"<https://dblp.org/pid/{author['dblp_pid']}>" for author in authors)
    return f"""PREFIX dblp: <{DBLP_SCHEMA}>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?paper ?title ?year ?venue ?doi ?type ?count ?ordinal ?author ?authorPid
WHERE {{
  VALUES ?tracked {{ {people} }}
  VALUES ?type {{ dblp:Article dblp:Inproceedings dblp:Informal }}
  ?paper dblp:authoredBy ?tracked; a ?type;
         dblp:title ?title; dblp:yearOfPublication ?year .
  FILTER(?year >= "{since_year}"^^xsd:gYear && ?year <= "{current_year}"^^xsd:gYear)
  FILTER NOT EXISTS {{ ?paper a dblp:Withdrawn }}
  OPTIONAL {{ ?paper dblp:publishedIn ?venue }}
  OPTIONAL {{ ?paper dblp:doi ?doi }}
  OPTIONAL {{ ?paper dblp:numberOfCreators ?count }}
  OPTIONAL {{
    ?paper dblp:hasSignature ?signature .
    ?signature a dblp:AuthorSignature;
               dblp:signatureOrdinal ?ordinal;
               dblp:signatureDblpName ?author;
               dblp:signatureCreator ?authorPid .
  }}
}}
ORDER BY DESC(?year) ?paper ?ordinal
LIMIT 20001"""


def parse_discovery(payload: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = payload.get("results", {}).get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise SyncError("DBLP returned no records or an invalid response; refusing an empty refresh.")
    if len(bindings) >= 20001:
        raise SyncError("DBLP response reached the safety limit; narrow the year range.")
    grouped: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        item = {key: value.get("value", "") for key, value in binding.items()}
        if not item.get("paper", "").startswith("https://dblp.org/rec/") or not item.get("title") or not re.fullmatch(r"\d{4}", item.get("year", "")):
            raise SyncError("DBLP returned an invalid publication.")
        paper = grouped.setdefault(item["paper"], {
            "source": item["paper"], "title": item["title"], "year": int(item["year"]),
            "venue": item.get("venue", ""), "dois": set(), "types": set(),
            "authors_by_order": {}, "author_pids": set(), "count": int(item.get("count") or 0),
        })
        if paper["title"] != item["title"] or paper["year"] != int(item["year"]):
            raise SyncError("Conflicting DBLP title/year values.")
        paper["types"].add(item.get("type", "").removeprefix(DBLP_SCHEMA))
        if item.get("doi") and doi_key(item["doi"]):
            paper["dois"].add(doi_key(item["doi"]))
        if item.get("author"):
            ordinal = int(item["ordinal"])
            name = author_name(item["author"])
            existing = paper["authors_by_order"].get(ordinal)
            if existing is not None and existing != name:
                raise SyncError("Conflicting DBLP author positions.")
            paper["authors_by_order"][ordinal] = name
            paper["author_pids"].add(item.get("authorPid", ""))
    papers = []
    for paper in grouped.values():
        orders = sorted(paper.pop("authors_by_order").items())
        paper["authors"] = [name for _, name in orders]
        paper["complete_authors"] = (
            paper["count"] > 0 and len(orders) == paper["count"]
            and [order for order, _ in orders] == list(range(1, paper["count"] + 1))
        )
        paper["dois"] = sorted(paper["dois"])
        paper["types"] = sorted(paper["types"])
        paper["author_pids"] = sorted(paper["author_pids"])
        papers.append(paper)
    return sorted(papers, key=lambda paper: (-paper["year"], title_key(paper["title"]), paper["source"]))


def discover(client: ApiClient, config: dict[str, Any], since_year: int, today: date) -> list[dict[str, Any]]:
    query = discovery_query(config["authors"], since_year, today.year)
    try:
        return parse_discovery(client.get_json(DBLP_API + "?" + urlencode({"query": query})))
    except HTTPError as exc:
        raise SyncError(f"DBLP HTTP {exc.code}; no workbook changes were made.") from exc


def regular_dois(paper: dict[str, Any]) -> list[str]:
    return [doi for doi in paper["dois"] if not doi.startswith("10.48550/arxiv.")]


def prepare_row(paper: dict[str, Any], metadata: dict[str, Any] | None, today: date) -> tuple[dict[str, Any] | None, str]:
    if not metadata:
        return None, "Crossref has no metadata for this DOI."
    dois = regular_dois(paper)
    if len(dois) != 1 or doi_key(metadata.get("DOI", "")) != dois[0]:
        return None, "Crossref DOI does not match the discovered DOI."
    titles = metadata.get("title", [])
    if not titles or title_key(titles[0]) != title_key(paper["title"]):
        return None, "DBLP and Crossref titles differ; check versions manually."
    if metadata.get("type") not in {"journal-article", "proceedings-article"}:
        return None, "No verified journal/conference publication status."
    if not paper["complete_authors"]:
        return None, "DBLP does not provide a complete ordered author list."
    authors = metadata.get("author", [])
    names = [publications.clean_text(f"{author.get('given', '')} {author.get('family', '')}") for author in authors]
    if len(names) != len(paper["authors"]) or any(not author.get("family") for author in authors):
        return None, "Crossref author list is incomplete."
    if [title_key(name) for name in names] != [title_key(name) for name in paper["authors"]]:
        return None, "DBLP and Crossref author names/order differ."
    parts = metadata.get("published", {}).get("date-parts", [])
    if not parts or not parts[0] or not isinstance(parts[0][0], int):
        return None, "Missing publication date."
    published = parts[0]
    try:
        publication_date = date(*((published + [1, 1])[:3]))
    except (TypeError, ValueError):
        return None, "Invalid publication date."
    if publication_date > today:
        return None, "Future publication date; wait or confirm manually."
    if abs(published[0] - paper["year"]) > 1:
        return None, "DBLP and Crossref publication years conflict."
    venues = metadata.get("container-title", [])
    if not venues or not publications.clean_text(venues[0]):
        return None, "Missing publication venue."
    row = {column: "" for column in publications.REQUIRED_COLUMNS}
    row.update({
        "year": paper["year"],
        "id": "dblp-" + hashlib.sha256(paper["source"].encode()).hexdigest()[:16],
        "title": publications.clean_text(titles[0]),
        "link": "https://doi.org/" + dois[0],
        "status": "published",
        "author": ";".join(paper["authors"]),
        "venue": publications.clean_text(venues[0]),
    })
    row["level"] = publications.infer_ccf_level(row["venue"], row["title"])
    return row, ""


def make_proposal(papers: list[dict[str, Any]], existing: list[dict[str, Any]], config: dict[str, Any], client: ApiClient, today: date) -> dict[str, Any]:
    known_dois = {doi_key(str(row.get("link", ""))) for row in existing} - {""}
    known_titles: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in existing:
        known_titles[title_key(str(row["title"]))].append(row)
    known_ids = {row["id"] for row in existing}
    report: dict[str, Any] = {"schema_version": 1, "added": [], "pending": [], "duplicates": [], "ignored": [], "deferred": []}
    tracked = {f"https://dblp.org/pid/{author['dblp_pid']}" for author in config["authors"]}
    observed = set()
    for paper in papers:
        source = paper["source"]
        if source in observed:
            continue
        observed.add(source)
        entry = {"title": paper["title"], "source": source, "year": paper["year"]}
        if source in config.get("ignored_dblp_records", []):
            report["ignored"].append(entry)
            continue
        if not tracked.intersection(paper["author_pids"]):
            raise SyncError("Discovered record cannot be linked to a configured DBLP author.")
        doi_matches = set(paper["dois"]) & known_dois
        exact = known_titles.get(title_key(paper["title"]), [])
        if doi_matches:
            report["duplicates"].append(entry)
            continue
        if exact:
            existing_dois = {doi_key(str(row.get("link", ""))) for row in exact} - {""}
            if not existing_dois or not paper["dois"]:
                report["duplicates"].append(entry)
            else:
                report["pending"].append({**entry, "reason": "Same title with a different DOI; possible preprint/final version."})
            continue
        similar = next((key for key in known_titles if len(key) >= 30 and SequenceMatcher(None, key, title_key(paper["title"])).ratio() >= 0.92), None)
        if similar:
            report["pending"].append({**entry, "reason": "Similar title already exists; check versions manually."})
            continue
        if "Informal" in paper["types"] or len(regular_dois(paper)) != 1:
            report["pending"].append({**entry, "reason": "Preprint, missing DOI, or multiple publication DOIs."})
            continue
        if len(report["added"]) >= config["max_new_records"]:
            report["deferred"].append(entry)
            continue
        row, reason = prepare_row(paper, client.crossref(regular_dois(paper)[0]), today)
        if row is None:
            report["pending"].append({**entry, "reason": reason})
            continue
        if row["id"] in known_ids:
            raise SyncError("Generated publication ID collision.")
        report["added"].append({**entry, "row": row})
        known_ids.add(row["id"])
        known_dois.add(doi_key(row["link"]))
        known_titles[title_key(row["title"])].append(row)
    return report


def append_workbook(path: Path, rows: list[dict[str, Any]], expected_rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    # The scheduled runner cannot use conversation-only artifact tooling.
    # openpyxl preserves the existing maintenance table, styles and validation.
    try:
        from openpyxl import load_workbook
        from openpyxl.utils.cell import range_boundaries
    except ImportError as exc:
        raise SyncError("Install tools/requirements-sync.txt before applying updates.") from exc
    current = read_table(path, "学术论文", expected_columns=publications.REQUIRED_COLUMNS)
    if current != expected_rows:
        raise SyncError("Workbook changed during discovery; rerun instead of overwriting edits.")
    original_bytes = path.read_bytes()
    workbook = load_workbook(path)
    sheet = workbook["学术论文"]
    last_row = max((cell.row for line in sheet.iter_rows(max_col=len(publications.REQUIRED_COLUMNS)) for cell in line if cell.value is not None), default=1)
    final_row = last_row + len(rows)
    for offset, row in enumerate(rows, start=1):
        destination = last_row + offset
        for column, field in enumerate(publications.REQUIRED_COLUMNS, start=1):
            template = sheet.cell(last_row, column)
            cell = sheet.cell(destination, column)
            cell._style = copy(template._style)
            cell.value = row[field]
            if isinstance(cell.value, str):
                cell.data_type = "s"
        sheet.row_dimensions[destination].height = sheet.row_dimensions[last_row].height
    for table in sheet.tables.values():
        _, start, end_column, end = range_boundaries(table.ref)
        if start == 1 and end == last_row and end_column == len(publications.REQUIRED_COLUMNS):
            table.ref = f"A1:K{final_row}"
            if table.autoFilter:
                table.autoFilter.ref = table.ref
    if sheet.auto_filter.ref:
        sheet.auto_filter.ref = f"A1:K{final_row}"
    for validation in sheet.data_validations.dataValidation:
        for cell_range in list(validation.sqref.ranges):
            if cell_range.max_row == last_row:
                validation.sqref.remove(cell_range)
                cell_range.max_row = final_row
                validation.sqref.add(cell_range)
    descriptor, temporary_name = tempfile.mkstemp(suffix=".xlsx", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        workbook.save(temporary)
        actual = read_table(temporary, "学术论文", expected_columns=publications.REQUIRED_COLUMNS)
        values = lambda records: [{key: value for key, value in row.items() if key != "_source_row"} for row in records]
        if values(actual) != values(current + rows):
            raise SyncError("Saved workbook failed the value-preservation check.")
        if path.read_bytes() != original_bytes:
            raise SyncError("Workbook changed before save; no changes applied.")
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        workbook.close()
        temporary.unlink(missing_ok=True)


def report_markdown(report: dict[str, Any]) -> str:
    def literal(value: str) -> str:
        return value.replace("`", "'").replace("<", "&lt;").replace("\n", " ")
    lines = ["# Publication Sync", "", f"Checked publication years {report['since_year']}–{report['current_year']}.", "",
             "Existing records and author annotations are unchanged. Proposed rows leave co-first/corresponding authors blank.", ""]
    for key, title in (("added", "Proposed Additions"), ("pending", "Needs Review"), ("deferred", "Deferred To Next Batch")):
        lines.extend([f"## {title} ({len(report[key])})", ""])
        for item in report[key]:
            lines.append(f"- {item['year']}: {literal(item['title'])} ([DBLP]({item['source']}))")
            if "reason" in item:
                lines.append(f"  Reason: {literal(item['reason'])}")
            if "row" in item:
                row = item["row"]
                lines.append(f"  {literal(row['venue'])}; [DOI]({row['link']}); {literal(row['author'])}")
        if not report[key]:
            lines.append("None.")
        lines.append("")
    lines.append(f"Skipped {len(report['duplicates'])} duplicates and {len(report['ignored'])} explicitly ignored records.")
    lines.extend(["", "Merge this PR to publish via the existing Pages workflow. No direct main-branch push or deployment is performed by synchronization.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover DBLP/Crossref publications and propose append-only maintenance updates.")
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--xlsx", type=Path, default=SOURCE)
    parser.add_argument("--aliases", type=Path, default=ALIASES)
    parser.add_argument("--report-dir", type=Path, default=ROOT / "outputs/publication-sync")
    parser.add_argument("--since-year", type=int)
    parser.add_argument("--max-new", type=int)
    parser.add_argument("--dry-run", action="store_true", help="Write reports without changing the maintenance workbook.")
    args = parser.parse_args()
    try:
        today = datetime.now(timezone(timedelta(hours=8))).date()
        config = load_config(args.config)
        since = args.since_year if args.since_year is not None else today.year - config["lookback_years"] + 1
        if not 1900 <= since <= today.year:
            raise SyncError("--since-year must be between 1900 and the current year.")
        if args.max_new is not None:
            if not 1 <= args.max_new <= 100:
                raise SyncError("--max-new must be between 1 and 100.")
            config["max_new_records"] = args.max_new
        existing = read_table(args.xlsx, "学术论文", expected_columns=publications.REQUIRED_COLUMNS)
        publications.import_rows(existing, args.aliases)
        aliases = publications.load_aliases(args.aliases)
        for author in config["authors"]:
            if aliases.get(publications.normalize_name(author["name"])) != f"/members/{author['member_id']}/":
                raise SyncError("Configured author does not match the project's member aliases.")
        client = ApiClient(config["request_interval_seconds"], os.environ.get("CROSSREF_MAILTO", ""))
        papers = discover(client, config, since, today)
        report = make_proposal(papers, existing, config, client, today)
        report.update({"since_year": since, "current_year": today.year, "dry_run": args.dry_run})
        rows = [item["row"] for item in report["added"]]
        publications.import_rows(existing + rows, args.aliases)
        if not args.dry_run:
            append_workbook(args.xlsx, rows, existing)
        args.report_dir.mkdir(parents=True, exist_ok=True)
        (args.report_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.report_dir / "report.md").write_text(report_markdown(report), encoding="utf-8")
        print(f"{'Proposed' if args.dry_run else 'Added'} {len(rows)} papers; {len(report['pending'])} need review; {len(report['duplicates'])} duplicates; {len(report['deferred'])} deferred.")
        print(f"Report: {args.report_dir / 'report.md'}")
        return 0
    except (SyncError, ValueError, OSError) as exc:
        print(f"Publication sync failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
