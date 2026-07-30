from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import import_members


class ImportMembersTest(unittest.TestCase):
    def source_rows(self, *, duplicate_name: bool = False):
        return {
            "教师": [
                {
                    "teacher_id": "teacher-001",
                    "name": "张老师",
                    "avatar": "members/teacher-001/avatar.jpg",
                    "member_type": "teacher",
                    "identity": "教授",
                    "homepage": "https://example.com/",
                    "bio": "个人简介",
                    "_source_row": 2,
                }
            ],
            "博士研究生": [
                {
                    "phd_id": "phd-001",
                    "name": "张老师" if duplicate_name else "李同学",
                    "member_type": "phd",
                    "identity": "2024级博士研究生",
                    "homepage": "",
                    "_source_row": 2,
                }
            ],
            "硕士研究生": [
                {
                    "master_id": "master-001",
                    "name": "王同学",
                    "member_type": "master",
                    "identity": "2025级硕士研究生",
                    "homepage": "",
                    "_source_row": 2,
                }
            ],
        }

    def build_fixture(self, root: Path):
        content_dir = root / "content" / "members"
        figure_dir = root / "fig"
        (figure_dir / "members" / "teacher-001").mkdir(parents=True)
        (figure_dir / "members" / "teacher-001" / "avatar.jpg").write_bytes(b"avatar")
        return content_dir, figure_dir

    def test_build_outputs_generates_records_and_stable_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            content_dir, figure_dir = self.build_fixture(Path(temp))
            rows = self.source_rows()
            rows["作者别名"] = [
                {"alias": "Teacher Zhang", "member_id": "teacher-001", "_source_row": 2}
            ]
            with (
                mock.patch.object(import_members, "CONTENT_DIR", content_dir),
                mock.patch.object(import_members, "FIG_DIR", figure_dir),
                mock.patch.object(
                    import_members,
                    "read_table",
                    side_effect=lambda _path, sheet, **_: rows[sheet],
                ),
            ):
                payload, pages, aliases = import_members.build_outputs()

        self.assertEqual(len(payload["members"]), 3)
        teacher = payload["members"][0]
        self.assertEqual(teacher["url"], "/members/teacher-001/")
        self.assertEqual(
            teacher["avatar_url"],
            "/images/data-source/members/teacher-001/avatar.jpg",
        )
        self.assertEqual(teacher["bio"], "个人简介")
        self.assertEqual(aliases["张老师"], "/members/teacher-001/")
        self.assertEqual(aliases["Teacher Zhang"], "/members/teacher-001/")
        phd_page = pages[content_dir / "phd-001" / "index.md"]
        self.assertIn('identity: "2024级博士研究生"', phd_page)
        self.assertIn(
            'generated_from: "frontend/data-source/members.xlsx#博士研究生"',
            phd_page,
        )

    def test_build_outputs_rejects_duplicate_names(self):
        with tempfile.TemporaryDirectory() as temp:
            content_dir, figure_dir = self.build_fixture(Path(temp))
            rows = self.source_rows(duplicate_name=True)
            rows["作者别名"] = []
            with (
                mock.patch.object(import_members, "CONTENT_DIR", content_dir),
                mock.patch.object(import_members, "FIG_DIR", figure_dir),
                mock.patch.object(
                    import_members,
                    "read_table",
                    side_effect=lambda _path, sheet, **_: rows[sheet],
                ),
                self.assertRaises(import_members.MemberImportError),
            ):
                import_members.build_outputs()

    def test_load_source_rejects_wrong_member_type(self):
        with tempfile.TemporaryDirectory() as temp:
            content_dir, figure_dir = self.build_fixture(Path(temp))
            rows = self.source_rows()
            rows["作者别名"] = []
            rows["博士研究生"][0]["member_type"] = "master"
            with (
                mock.patch.object(import_members, "CONTENT_DIR", content_dir),
                mock.patch.object(import_members, "FIG_DIR", figure_dir),
                mock.patch.object(
                    import_members,
                    "read_table",
                    side_effect=lambda _path, sheet, **_: rows[sheet],
                ),
                self.assertRaises(import_members.MemberImportError),
            ):
                import_members.build_outputs()


if __name__ == "__main__":
    unittest.main()
