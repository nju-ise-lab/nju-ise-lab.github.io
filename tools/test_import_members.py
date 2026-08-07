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

    def test_build_outputs_keeps_placeholders_without_author_aliases(self):
        with tempfile.TemporaryDirectory() as temp:
            content_dir, figure_dir = self.build_fixture(Path(temp))
            rows = self.source_rows()
            rows["硕士研究生"] = [
                {
                    "master_id": "master-006",
                    "name": "xxx",
                    "member_type": "master",
                    "identity": "xxx级硕士研究生",
                    "homepage": "",
                    "_source_row": 6,
                },
                {
                    "master_id": "master-007",
                    "name": "xxx",
                    "member_type": "master",
                    "identity": "xxx级硕士研究生",
                    "homepage": "",
                    "_source_row": 7,
                },
            ]
            rows["作者别名"] = []
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

        self.assertEqual(len(payload["members"]), 4)
        self.assertIn(content_dir / "master-006" / "index.md", pages)
        self.assertIn(content_dir / "master-007" / "index.md", pages)
        self.assertNotIn("xxx", aliases)

    def test_teacher_placeholder_does_not_require_avatar(self):
        with tempfile.TemporaryDirectory() as temp:
            content_dir, figure_dir = self.build_fixture(Path(temp))
            rows = self.source_rows()
            rows["教师"].append(
                {
                    "teacher_id": "teacher-005",
                    "name": "xxx",
                    "avatar": "",
                    "member_type": "teacher",
                    "identity": "xxx",
                    "homepage": "",
                    "bio": "",
                    "_source_row": 3,
                }
            )
            rows["作者别名"] = []
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

        placeholder = next(
            member for member in payload["members"] if member["id"] == "teacher-005"
        )
        self.assertNotIn("avatar_url", placeholder)
        self.assertIn(content_dir / "teacher-005" / "index.md", pages)
        self.assertNotIn("xxx", aliases)

    def test_write_outputs_removes_only_stale_generated_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content_dir = root / "content" / "members"
            stale_page = content_dir / "teacher-001" / "index.md"
            manual_page = content_dir / "manual" / "index.md"
            current_page = content_dir / "phd-001" / "index.md"
            stale_page.parent.mkdir(parents=True)
            manual_page.parent.mkdir(parents=True)
            stale_page.write_text(
                'generated_from: "frontend/data-source/members.xlsx#教师"\n',
                encoding="utf-8",
            )
            manual_page.write_text("manually maintained\n", encoding="utf-8")

            with (
                mock.patch.object(import_members, "CONTENT_DIR", content_dir),
                mock.patch.object(import_members, "OUTPUT_PATH", root / "members.json"),
                mock.patch.object(import_members, "ALIASES_OUTPUT_PATH", root / "aliases.json"),
            ):
                import_members.write_outputs(
                    {"schema_version": 1, "members": []},
                    {
                        current_page: (
                            'generated_from: '
                            '"frontend/data-source/members.xlsx#博士研究生"\n'
                        )
                    },
                    {},
                )

            self.assertFalse(stale_page.exists())
            self.assertTrue(current_page.exists())
            self.assertTrue(manual_page.exists())


if __name__ == "__main__":
    unittest.main()
