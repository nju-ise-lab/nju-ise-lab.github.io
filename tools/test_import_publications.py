from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools import import_publications


class ImportPublicationsTest(unittest.TestCase):
    def write_fixture(self, directory: Path, csv_text: str) -> tuple[Path, Path]:
        csv_path = directory / "publications.csv"
        aliases_path = directory / "aliases.json"
        csv_path.write_text(csv_text, encoding="utf-8")
        aliases_path.write_text(json.dumps({"Zhenyu Chen": "/members/member-37/"}), encoding="utf-8")
        return csv_path, aliases_path

    def test_import_enriches_exact_member_alias_and_author_marks(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_path, aliases_path = self.write_fixture(
                Path(temp),
                "year,id,title,link,status,author,cofauthor,corauthor,level,venue,note\n"
                "2026,paper-1,Paper title,https://doi.org/example,acctpted,Jane Doe;Zhenyu Chen,,Zhenyu Chen,A,ASE,Industry Track\n",
            )
            catalog, unmatched = import_publications.import_csv(csv_path, aliases_path)

        record = catalog["publications"][0]
        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["status_label"], "Accepted")
        self.assertEqual(record["ccf_level"], "CCF-A")
        self.assertEqual(record["publication_type"], "conference")
        self.assertEqual(record["publication_type_label"], "会议论文")
        self.assertEqual(record["source_url"], "https://doi.org/example")
        self.assertTrue(record["url"].startswith("https://scholar.google.com/scholar?"))
        self.assertEqual(record["authors"][1]["member_url"], "/members/member-37/")
        self.assertTrue(record["authors"][1]["corresponding"])
        self.assertEqual(unmatched, {"Jane Doe"})

    def test_import_rejects_marked_author_not_in_author_list(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_path, aliases_path = self.write_fixture(
                Path(temp),
                "year,id,title,link,status,author,cofauthor,corauthor,level,venue,note\n"
                "2026,paper-1,Paper title,,published,Jane Doe,Zhenyu Chen,,,ASE,\n",
            )
            with self.assertRaises(import_publications.PublicationImportError):
                import_publications.import_csv(csv_path, aliases_path)

    def test_import_inferrs_conservative_legacy_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            csv_path, aliases_path = self.write_fixture(
                Path(temp),
                "year,id,title,link,status,author,cofauthor,corauthor,level,venue,note\n"
                "2026,paper-1,Regular paper,,published,Zhenyu Chen,,,,IEEE Transactions on Software Engineering,\n"
                "2026,paper-2,Demo paper,,published,Zhenyu Chen,,,,International Conference on Software Engineering,\n",
            )
            catalog, _ = import_publications.import_csv(csv_path, aliases_path)

        self.assertEqual(catalog["publications"][0]["ccf_level"], "CCF-A")
        self.assertEqual(catalog["publications"][0]["publication_type_label"], "期刊论文")
        self.assertEqual(catalog["publications"][1]["ccf_level"], "")

    def test_title_link_preserves_academic_discovery_urls(self):
        arxiv_url = "https://arxiv.org/abs/2604.17016"
        self.assertEqual(import_publications.title_link(arxiv_url, "Paper title"), arxiv_url)
        self.assertTrue(
            import_publications.title_link("https://example.com/paper", "Paper title").startswith(
                "https://scholar.google.com/scholar?"
            )
        )


if __name__ == "__main__":
    unittest.main()
