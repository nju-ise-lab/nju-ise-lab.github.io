from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools import import_publications


class ImportPublicationsTest(unittest.TestCase):
    def write_aliases(self, directory: Path) -> Path:
        aliases_path = directory / "aliases.json"
        aliases_path.write_text(
            json.dumps({"Zhenyu Chen": "/members/teacher-001/"}),
            encoding="utf-8",
        )
        return aliases_path

    def row(self, **overrides):
        record = {
            "year": 2026,
            "id": "paper-1",
            "title": "Paper title",
            "link": "",
            "status": "published",
            "author": "Zhenyu Chen",
            "cofauthor": "",
            "corauthor": "",
            "level": "",
            "venue": "ASE",
            "note": "",
            "_source_row": 2,
        }
        record.update(overrides)
        return record

    def test_import_enriches_exact_member_alias_and_author_marks(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases_path = self.write_aliases(Path(temp))
            catalog, unmatched = import_publications.import_rows(
                [
                    self.row(
                        link="https://doi.org/example",
                        status="acctpted",
                        author="Jane Doe;Zhenyu Chen",
                        corauthor="Zhenyu Chen",
                        level="A",
                        note="Industry Track",
                    )
                ],
                aliases_path,
            )

        record = catalog["publications"][0]
        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["status_label"], "Accepted")
        self.assertEqual(record["ccf_level"], "CCF-A")
        self.assertEqual(record["publication_type"], "conference")
        self.assertEqual(record["publication_type_label"], "会议论文")
        self.assertEqual(record["venue_short"], "ASE")
        self.assertEqual(record["source_url"], "https://doi.org/example")
        self.assertTrue(record["url"].startswith("https://scholar.google.com/scholar?"))
        self.assertEqual(record["authors"][1]["member_url"], "/members/teacher-001/")
        self.assertTrue(record["authors"][1]["corresponding"])
        self.assertEqual(unmatched, {"Jane Doe"})

    def test_import_rejects_marked_author_not_in_author_list(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases_path = self.write_aliases(Path(temp))
            with self.assertRaises(import_publications.PublicationImportError):
                import_publications.import_rows(
                    [self.row(author="Jane Doe", cofauthor="Zhenyu Chen")],
                    aliases_path,
                )

    def test_import_infers_conservative_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases_path = self.write_aliases(Path(temp))
            catalog, _ = import_publications.import_rows(
                [
                    self.row(
                        id="paper-1",
                        title="Regular paper",
                        venue="IEEE Transactions on Software Engineering",
                    ),
                    self.row(
                        id="paper-2",
                        title="Demo paper",
                        venue="International Conference on Software Engineering",
                        _source_row=3,
                    ),
                ],
                aliases_path,
            )

        self.assertEqual(catalog["publications"][0]["ccf_level"], "CCF-A")
        self.assertEqual(catalog["publications"][0]["publication_type_label"], "期刊论文")
        self.assertEqual(catalog["publications"][0]["venue_short"], "TSE")
        self.assertEqual(catalog["publications"][0]["status_label"], "")
        self.assertEqual(catalog["publications"][1]["ccf_level"], "")

    def test_import_infers_compact_topics(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases_path = self.write_aliases(Path(temp))
            catalog, _ = import_publications.import_rows(
                [
                    self.row(
                        title="Deep Learning Framework Testing via Model Mutation",
                        status="accepted",
                        level="A",
                        venue="IEEE Transactions on Software Engineering",
                    )
                ],
                aliases_path,
            )

        record = catalog["publications"][0]
        self.assertEqual(record["venue_short"], "TSE")
        self.assertEqual(record["topics"], ["Deep Learning Testing", "Model Mutation"])

    def test_title_link_preserves_academic_discovery_urls(self):
        arxiv_url = "https://arxiv.org/abs/2604.17016"
        self.assertEqual(import_publications.title_link(arxiv_url, "Paper title"), arxiv_url)
        self.assertTrue(
            import_publications.title_link(
                "https://example.com/paper", "Paper title"
            ).startswith("https://scholar.google.com/scholar?")
        )


if __name__ == "__main__":
    unittest.main()
