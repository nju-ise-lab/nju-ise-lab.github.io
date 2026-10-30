from __future__ import annotations

from copy import copy, deepcopy
from datetime import date
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError

from tools import import_publications, sync_publications as sync
from tools.xlsx_reader import read_table


TODAY = date(2026, 10, 30)


class PublicationSyncTest(unittest.TestCase):
    def config(self):
        return sync.load_config(sync.CONFIG)

    def paper(self, **overrides):
        paper = {
            "source": "https://dblp.org/rec/journals/tse/Example26",
            "title": "Testing the New Framework.", "year": 2026,
            "venue": "IEEE Trans. Software Eng.", "dois": ["10.1109/example.2026"],
            "types": ["Article"], "count": 2,
            "authors": ["Jane Doe", "Zhenyu Chen"],
            "author_pids": ["https://dblp.org/pid/86/541-1"], "complete_authors": True,
        }
        paper.update(overrides)
        return paper

    def metadata(self, **overrides):
        metadata = {
            "DOI": "10.1109/example.2026", "title": ["Testing the New Framework"],
            "type": "journal-article", "container-title": ["IEEE Transactions on Software Engineering"],
            "published": {"date-parts": [[2026, 3]]},
            "author": [{"given": "Jane", "family": "Doe"}, {"given": "Zhenyu", "family": "Chen"}],
        }
        metadata.update(overrides)
        return metadata

    def client(self):
        return mock.Mock(crossref=mock.Mock(return_value=self.metadata()))

    def row(self, **overrides):
        row = {column: "" for column in import_publications.REQUIRED_COLUMNS}
        row.update(year=2026, id="manual-001", title="An Existing Paper", author="Zhenyu Chen", status="accepted", note="Manual award", corauthor="Zhenyu Chen")
        row.update(overrides)
        return row

    def bindings(self):
        items = []
        for ordinal, name in ((2, "Zhenyu Chen 0001"), (1, "Jane Doe")):
            values = {"paper": self.paper()["source"], "title": self.paper()["title"],
                      "year": "2026", "type": sync.DBLP_SCHEMA + "Article",
                      "count": "2", "doi": "https://doi.org/10.1109/example.2026",
                      "ordinal": str(ordinal), "author": name, "authorPid": "https://dblp.org/pid/86/541-1"}
            items.append({key: {"value": value} for key, value in values.items()})
        return {"results": {"bindings": items}}

    def test_normalization_preserves_name_and_doi_identity(self):
        self.assertEqual(sync.doi_key("HTTPS://DOI.ORG/10.1109/EXAMPLE.2026"), "10.1109/example.2026")
        self.assertEqual(sync.doi_key("doi:10.1109/Example.2026"), "10.1109/example.2026")
        self.assertEqual(sync.doi_key("https://example.org/10.1109/wrong"), "")
        self.assertEqual(sync.title_key("Ａ Paper: TEST!"), sync.title_key("A paper test"))
        self.assertEqual(sync.author_name("Zhenyu Chen 0001"), "Zhenyu Chen")

    def test_discovery_deduplicates_bindings_and_orders_authors(self):
        payload = self.bindings()
        payload["results"]["bindings"] += deepcopy(payload["results"]["bindings"])
        papers = sync.parse_discovery(payload)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["authors"], ["Jane Doe", "Zhenyu Chen"])
        self.assertTrue(papers[0]["complete_authors"])

    def test_discovery_marks_missing_author_positions_incomplete(self):
        payload = self.bindings()
        payload["results"]["bindings"].pop()
        self.assertFalse(sync.parse_discovery(payload)[0]["complete_authors"])

    def test_discovery_rejects_empty_blocked_and_truncated_responses(self):
        for payload in ({}, {"results": {"bindings": []}}, {"results": {"bindings": [{}] * 20001}}):
            with self.subTest(payload_size=len(str(payload))), self.assertRaises(sync.SyncError):
                sync.parse_discovery(payload)

    def test_prepared_row_matches_existing_schema_without_inventing_marks(self):
        row, reason = sync.prepare_row(self.paper(), self.metadata(), TODAY)
        self.assertFalse(reason)
        self.assertEqual(tuple(row), import_publications.REQUIRED_COLUMNS)
        self.assertEqual(row["status"], "published")
        self.assertEqual(row["level"], "CCF-A")
        self.assertEqual(row["author"], "Jane Doe;Zhenyu Chen")
        self.assertEqual(row["cofauthor"], "")
        self.assertEqual(row["corauthor"], "")
        catalog, _ = import_publications.import_rows([row], sync.ALIASES)
        self.assertEqual(catalog["publications"][0]["authors"][1]["member_url"], "/members/teacher-001/")
        self.assertEqual(sync.prepare_row(self.paper(), self.metadata(), TODAY)[0]["id"], row["id"])

    def test_metadata_conflicts_and_future_dates_need_review(self):
        variants = [None, self.metadata(DOI="10.1109/wrong"), self.metadata(title=["Wrong Paper"]),
                    self.metadata(type="posted-content"), self.metadata(author=[{"family": "Doe"}]),
                    self.metadata(author=list(reversed(self.metadata()["author"]))),
                    self.metadata(published={"date-parts": [[2027, 1]]}),
                    self.metadata(published={"date-parts": [[2026, 99]]}),
                    self.metadata(published={"date-parts": [[2022]]}),
                    self.metadata(**{"container-title": []})]
        for metadata in variants:
            with self.subTest(metadata=metadata):
                row, reason = sync.prepare_row(self.paper(), metadata, TODAY)
                self.assertIsNone(row)
                self.assertTrue(reason)

    def test_two_profiles_and_reruns_do_not_duplicate_a_paper(self):
        paper = self.paper(author_pids=["https://dblp.org/pid/86/541-1", "https://dblp.org/pid/124/0310"])
        client = self.client()
        report = sync.make_proposal([paper, paper], [], self.config(), client, TODAY)
        self.assertEqual(len(report["added"]), 1)
        client.crossref.assert_called_once()
        second = sync.make_proposal([paper], [report["added"][0]["row"]], self.config(), client, TODAY)
        self.assertFalse(second["added"])
        self.assertEqual(len(second["duplicates"]), 1)

    def test_doi_duplicates_preserve_manual_metadata(self):
        existing = [self.row(link="https://doi.org/10.1109/EXAMPLE.2026")]
        original = deepcopy(existing)
        client = self.client()
        report = sync.make_proposal([self.paper()], existing, self.config(), client, TODAY)
        self.assertEqual(existing, original)
        self.assertEqual(len(report["duplicates"]), 1)
        client.crossref.assert_not_called()

    def test_same_title_with_different_doi_and_similar_titles_need_review(self):
        for title in (self.paper()["title"], "Testing the New Frameworks with Reliable Oracles"):
            paper = self.paper(title=title)
            existing_title = title if title == self.paper()["title"] else "Testing the New Framework with Reliable Oracles"
            existing = [self.row(title=existing_title, link="https://doi.org/10.1109/other")]
            report = sync.make_proposal([paper], existing, self.config(), self.client(), TODAY)
            self.assertFalse(report["added"])
            self.assertEqual(len(report["pending"]), 1)

    def test_preprints_and_missing_dois_are_not_marked_published(self):
        for overrides in ({"types": ["Informal"]}, {"dois": []}, {"dois": ["10.48550/arxiv.2601.12345"]}):
            report = sync.make_proposal([self.paper(**overrides)], [], self.config(), self.client(), TODAY)
            self.assertFalse(report["added"])
            self.assertEqual(len(report["pending"]), 1)

    def test_batch_limit_and_ignore_list(self):
        config = self.config()
        config["max_new_records"] = 1
        ignored = self.paper(source="https://dblp.org/rec/ignored")
        config["ignored_dblp_records"] = [ignored["source"]]
        deferred = self.paper(source="https://dblp.org/rec/new", title="Another New Publication", dois=["10.1109/another"])
        report = sync.make_proposal([ignored, self.paper(), deferred], [], config, self.client(), TODAY)
        self.assertEqual([len(report[key]) for key in ("added", "ignored", "deferred")], [1, 1, 1])

    def test_wrong_author_pid_fails_closed(self):
        with self.assertRaises(sync.SyncError):
            sync.make_proposal([self.paper(author_pids=["https://dblp.org/pid/other"])], [], self.config(), self.client(), TODAY)

    def test_crossref_404_pending_but_rate_limits_fail_the_run(self):
        client = sync.ApiClient()
        for status in (404, 403, 429, 500):
            error = HTTPError("https://api.crossref.org/works/test", status, "failure", {}, None)
            with mock.patch.object(client, "get_json", side_effect=error):
                if status == 404:
                    self.assertIsNone(client.crossref("10.1109/test"))
                else:
                    with self.assertRaises(sync.SyncError):
                        client.crossref("10.1109/test")

    def test_dry_run_does_not_write_workbook(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "publications.xlsx"
            shutil.copyfile(sync.SOURCE, path)
            before = path.read_bytes()
            argv = ["sync_publications", "--dry-run", "--xlsx", str(path), "--report-dir", directory]
            with mock.patch("sys.argv", argv), mock.patch.object(sync, "discover", return_value=[self.paper()]), mock.patch.object(sync.ApiClient, "crossref", return_value=self.metadata()):
                self.assertEqual(sync.main(), 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(json.loads((Path(directory) / "report.json").read_text())["added"]), 1)

    def test_api_failure_does_not_apply_a_partial_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "publications.xlsx"
            shutil.copyfile(sync.SOURCE, path)
            before = path.read_bytes()
            second = self.paper(source="https://dblp.org/rec/second", title="Another Completely New Paper", dois=["10.1109/second"])
            argv = ["sync_publications", "--xlsx", str(path), "--report-dir", directory]
            with mock.patch("sys.argv", argv), mock.patch.object(sync, "discover", return_value=[self.paper(), second]), mock.patch.object(sync.ApiClient, "crossref", side_effect=[self.metadata(), sync.SyncError("HTTP 429")]):
                self.assertEqual(sync.main(), 1)
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((Path(directory) / "report.json").exists())


@unittest.skipUnless(importlib.util.find_spec("openpyxl"), "Optional synchronization dependency is not installed")
class PublicationWorkbookTest(unittest.TestCase):
    paper = PublicationSyncTest.paper
    metadata = PublicationSyncTest.metadata

    def test_append_preserves_values_formats_table_and_validations(self):
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "publications.xlsx"
            shutil.copyfile(sync.SOURCE, path)
            existing = read_table(path, "学术论文", expected_columns=import_publications.REQUIRED_COLUMNS)
            row, _ = sync.prepare_row(self.paper(), self.metadata(), TODAY)
            before = load_workbook(path)
            original = before["学术论文"]
            formats = [[(cell.value, cell.number_format, copy(cell.font), copy(cell.fill), copy(cell.alignment)) for cell in line] for line in original]
            table_names = list(original.tables)
            validations = [str(item.sqref) for item in original.data_validations.dataValidation]
            sync.append_workbook(path, [row], existing)
            after = load_workbook(path)
            sheet = after["学术论文"]
            self.assertEqual(after.sheetnames, before.sheetnames)
            for row_index, line in enumerate(formats, start=1):
                for column, expected in enumerate(line, start=1):
                    cell = sheet.cell(row_index, column)
                    self.assertEqual((cell.value, cell.number_format, copy(cell.font), copy(cell.fill), copy(cell.alignment)), expected)
            self.assertEqual(list(sheet.tables), table_names)
            self.assertEqual(sheet.tables[table_names[0]].ref, f"A1:K{len(existing) + 2}")
            self.assertEqual([str(item.sqref) for item in sheet.data_validations.dataValidation], validations)
            self.assertEqual(sheet.freeze_panes, original.freeze_panes)
            values = read_table(path, "学术论文")
            self.assertEqual({k: v for k, v in values[-1].items() if k != "_source_row"}, row)
            before.close()
            after.close()

    def test_concurrent_edit_and_failed_save_preserve_original_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "publications.xlsx"
            shutil.copyfile(sync.SOURCE, path)
            original = path.read_bytes()
            existing = read_table(path, "学术论文")
            row, _ = sync.prepare_row(self.paper(), self.metadata(), TODAY)
            with self.assertRaises(sync.SyncError):
                sync.append_workbook(path, [row], [])
            self.assertEqual(path.read_bytes(), original)
            with mock.patch("openpyxl.workbook.workbook.Workbook.save", side_effect=OSError("disk full")), self.assertRaises(OSError):
                sync.append_workbook(path, [row], existing)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(len(list(Path(directory).glob("*.xlsx"))), 1)

    def test_no_additions_leave_workbook_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "publications.xlsx"
            shutil.copyfile(sync.SOURCE, path)
            original = path.read_bytes()
            sync.append_workbook(path, [], [])
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
