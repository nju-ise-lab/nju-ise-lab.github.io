from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import import_members


class ImportMembersTest(unittest.TestCase):
    def write_sources(self, root: Path, *, duplicate_name: bool = False) -> tuple[Path, Path]:
        source_dir = root / "member-source"
        content_dir = root / "content" / "members"
        source_dir.mkdir(parents=True)
        (content_dir / "member-1").mkdir(parents=True)
        (content_dir / "member-1" / "avatar.jpg").write_bytes(b"avatar")

        source_dir.joinpath("teachers.csv").write_text(
            "id,name,avatar,member_type,identity,homepage,bio\n"
            "member-1,张老师,avatar.jpg,teacher,教授,https://example.com/,个人简介\n",
            encoding="utf-8",
        )
        source_dir.joinpath("phd.csv").write_text(
            "id,name,member_type,identity,homepage\n"
            f"member-2,{'张老师' if duplicate_name else '李同学'},phd,2024级博士研究生,\n",
            encoding="utf-8",
        )
        source_dir.joinpath("masters.csv").write_text(
            "id,name,member_type,identity,homepage\n"
            "member-3,王同学,master,2025级硕士研究生,\n",
            encoding="utf-8",
        )
        return source_dir, content_dir

    def test_build_outputs_generates_records_and_stable_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            source_dir, content_dir = self.write_sources(Path(temp))
            with (
                mock.patch.object(import_members, "SOURCE_DIR", source_dir),
                mock.patch.object(import_members, "CONTENT_DIR", content_dir),
            ):
                payload, pages = import_members.build_outputs()

        self.assertEqual(len(payload["members"]), 3)
        teacher = payload["members"][0]
        self.assertEqual(teacher["url"], "/members/member-1/")
        self.assertEqual(teacher["avatar_url"], "/members/member-1/avatar.jpg")
        self.assertEqual(teacher["bio"], "个人简介")
        phd_page = pages[content_dir / "member-2" / "index.md"]
        self.assertIn('identity: "2024级博士研究生"', phd_page)
        self.assertIn('generated_from: "frontend/member-source/phd.csv"', phd_page)

    def test_build_outputs_rejects_duplicate_names(self):
        with tempfile.TemporaryDirectory() as temp:
            source_dir, content_dir = self.write_sources(Path(temp), duplicate_name=True)
            with (
                mock.patch.object(import_members, "SOURCE_DIR", source_dir),
                mock.patch.object(import_members, "CONTENT_DIR", content_dir),
                self.assertRaises(import_members.MemberImportError),
            ):
                import_members.build_outputs()

    def test_load_source_rejects_wrong_member_type(self):
        with tempfile.TemporaryDirectory() as temp:
            source_dir, content_dir = self.write_sources(Path(temp))
            phd_path = source_dir / "phd.csv"
            phd_path.write_text(
                "id,name,member_type,identity,homepage\n"
                "member-2,李同学,master,2024级博士研究生,\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(import_members, "SOURCE_DIR", source_dir),
                mock.patch.object(import_members, "CONTENT_DIR", content_dir),
                self.assertRaises(import_members.MemberImportError),
            ):
                import_members.build_outputs()


if __name__ == "__main__":
    unittest.main()
