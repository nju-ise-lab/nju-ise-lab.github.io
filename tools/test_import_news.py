from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import import_news


class ImportNewsTest(unittest.TestCase):
    def row(self, **overrides: str) -> dict[str, str]:
        record = {
            "news_id": "nju-101",
            "title": "iSE 实验室新闻",
            "date": "2025-02-03",
            "source_url": "https://software.nju.edu.cn/xyxw/20250203/i101.html",
            "summary": "新闻摘要",
            "content_html": "<p>新闻正文</p>",
            "cover_image": "news/nju-101/image-001.png",
            "category": "学院新闻",
            "pinned": "FALSE",
        }
        record.update(overrides)
        return record

    def test_build_outputs_renders_static_cover_and_source_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fig_dir = root / "fig"
            image = fig_dir / "news" / "nju-101" / "image-001.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"image")
            content_dir = root / "content" / "news"
            with (
                mock.patch.object(import_news, "FIG_DIR", fig_dir),
                mock.patch.object(import_news, "CONTENT_DIR", content_dir),
            ):
                payload, pages = import_news.build_outputs([self.row(pinned="TRUE")])

        self.assertTrue(payload["news"][0]["pinned"])
        page = pages[content_dir / "nju-101" / "index.md"]
        self.assertIn('image: "/images/data-source/news/nju-101/image-001.png"', page)
        self.assertIn('generated_from: "frontend/data-source/news.csv"', page)
        self.assertIn("南京大学软件学院", page)

    def test_build_outputs_rejects_invalid_date_and_missing_cover(self):
        with tempfile.TemporaryDirectory() as temp:
            fig_dir = Path(temp) / "fig"
            with mock.patch.object(import_news, "FIG_DIR", fig_dir):
                with self.assertRaises(import_news.NewsImportError):
                    import_news.build_outputs([self.row(date="2025/02/03", cover_image="")])
                with self.assertRaises(import_news.NewsImportError):
                    import_news.build_outputs([self.row()])

    def test_write_outputs_removes_only_stale_generated_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content_dir = root / "content" / "news"
            stale = content_dir / "nju-100" / "index.md"
            manual = content_dir / "manual" / "index.md"
            current = content_dir / "nju-101" / "index.md"
            stale.parent.mkdir(parents=True)
            manual.parent.mkdir(parents=True)
            stale.write_text(import_news.GENERATED_PAGE_MARKER, encoding="utf-8")
            manual.write_text("manual news", encoding="utf-8")
            with (
                mock.patch.object(import_news, "CONTENT_DIR", content_dir),
                mock.patch.object(import_news, "OUTPUT_PATH", root / "news.json"),
            ):
                import_news.write_outputs(
                    {"schema_version": 1, "news": []},
                    {current: import_news.GENERATED_PAGE_MARKER + "\n"},
                )

            self.assertFalse(stale.exists())
            self.assertTrue(current.exists())
            self.assertTrue(manual.exists())


if __name__ == "__main__":
    unittest.main()
