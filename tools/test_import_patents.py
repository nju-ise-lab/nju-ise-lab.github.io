from __future__ import annotations

from pathlib import Path
import unittest
from unittest import mock

from tools import import_patents
from tools.xlsx_reader import XlsxReadError


class ImportPatentsTest(unittest.TestCase):
    def test_read_source_rows_accepts_labeled_columns(self):
        labeled_row = {
            "patent_id": "patent-001",
            "patent_name": "测试专利",
            "inventors": "张三",
            "public_number（公开号）": "CN123A",
            "application_number（申请号）": "CN123",
            "application_date（申请日）": "2026-01-02",
            "applicants": "南京大学",
            "_source_row": 2,
        }
        with mock.patch.object(
            import_patents,
            "read_table",
            side_effect=[XlsxReadError("标准表头不匹配"), [labeled_row]],
        ):
            rows = import_patents.read_source_rows(Path("patents.xlsx"))

        self.assertEqual(rows[0]["public_number"], "CN123A")
        self.assertEqual(rows[0]["application_number"], "CN123")
        self.assertEqual(rows[0]["application_date"], "2026-01-02")
        self.assertEqual(rows[0]["_source_row"], 2)


if __name__ == "__main__":
    unittest.main()
