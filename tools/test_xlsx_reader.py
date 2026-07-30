from pathlib import Path
import unittest

from tools.xlsx_reader import read_table


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "data-source"


class XlsxReaderTest(unittest.TestCase):
    def test_reads_all_maintenance_workbooks(self):
        self.assertEqual(
            len(
                read_table(
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
            ),
            7,
        )
        self.assertEqual(
            len(read_table(SOURCE / "publications.xlsx", "学术论文")),
            132,
        )
        self.assertEqual(len(read_table(SOURCE / "patents.xlsx", "专利")), 125)
        self.assertEqual(
            len(read_table(SOURCE / "software-copyrights.xlsx", "软件著作")),
            0,
        )
        self.assertEqual(len(read_table(SOURCE / "projects.xlsx", "项目")), 36)

    def test_boolean_and_numeric_cells_are_typed(self):
        projects = read_table(SOURCE / "projects.xlsx", "项目")
        featured = next(project for project in projects if project["featured"])
        self.assertIsInstance(featured["featured"], bool)
        self.assertIsInstance(featured["featured_order"], int)


if __name__ == "__main__":
    unittest.main()
