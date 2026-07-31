import json
from pathlib import Path
import unittest

from tools.xlsx_reader import read_table


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "data-source"


class XlsxReaderTest(unittest.TestCase):
    def test_reads_all_maintenance_workbooks(self):
        teachers = read_table(
            SOURCE / "members.xlsx",
            "教师",
            expected_columns=(
                "teacher_id",
                "name",
                "avatar",
                "member_type",
                "identity",
                "homepage",
                "bio",
            ),
        )
        aliases = read_table(
            SOURCE / "members.xlsx",
            "作者别名",
            expected_columns=("alias", "member_id"),
        )
        publications = read_table(SOURCE / "publications.xlsx", "学术论文")
        patents = read_table(SOURCE / "patents.xlsx", "专利")
        software = read_table(SOURCE / "software-copyrights.xlsx", "软件著作")
        projects = read_table(SOURCE / "projects.xlsx", "项目")

        for label, records in (
            ("教师", teachers),
            ("作者别名", aliases),
            ("学术论文", publications),
            ("专利", patents),
            ("软件著作", software),
            ("项目", projects),
        ):
            self.assertGreater(len(records), 0, f"{label}维护表不应为空")

    def test_patent_generated_data_matches_maintenance_source(self):
        source_records = read_table(SOURCE / "patents.xlsx", "专利")
        generated_path = ROOT / "frontend" / "data" / "patent-records.json"
        generated_records = json.loads(generated_path.read_text(encoding="utf-8"))["patents"]

        self.assertEqual(
            [str(record["patent_id"]).strip() for record in source_records],
            [record["id"] for record in generated_records],
            "专利派生数据未与 patents.xlsx 同步，请运行 bash scripts/import_data.sh",
        )

    def test_boolean_and_numeric_cells_are_typed(self):
        projects = read_table(SOURCE / "projects.xlsx", "项目")
        featured = next(project for project in projects if project["featured"])
        self.assertIsInstance(featured["featured"], bool)
        self.assertIsInstance(featured["featured_order"], int)


if __name__ == "__main__":
    unittest.main()
