from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import tempfile
import unittest

from tools import crawl_nju_ise_news


def item(iid: int, title: str, daytime: str, url: str) -> dict[str, object]:
    return {
        "iid": iid,
        "title": title,
        "daytime": daytime,
        "url": url,
        "summary": "新闻摘要",
    }


class CrawlNjuIseNewsTest(unittest.TestCase):
    def test_select_ise_news_normalizes_title_whitespace_and_date(self):
        records = crawl_nju_ise_news.select_ise_news(
            [
                item(10, "iSE 实验室新闻", "2025-01-01", "/xyxw/10.html"),
                item(11, "iSE实验室新闻", "2025-01-02", "/xyxw/11.html"),
                item(12, "iSE 实验室旧新闻", "2024-12-31", "/xyxw/12.html"),
                item(13, "其他实验室新闻", "2025-01-03", "/xyxw/13.html"),
            ],
            date(2025, 1, 1),
        )

        self.assertEqual([record["iid"] for record in records], [11, 10])

    def test_collect_list_items_fetches_pages_missing_from_index(self):
        index = (
            'var dataList=[{"infolist":[{"iid":1}]}];'
            ' var pagesData={}; var pageTotal=parseInt(2);'
        )
        records = crawl_nju_ise_news.collect_list_items(
            index,
            page_fetcher=lambda page: {"infolist": [{"iid": page}]},
        )

        self.assertEqual(records, [{"iid": 1}, {"iid": 2}])

    def test_crawl_writes_csv_preserves_editorial_fields_and_localizes_images(self):
        index = (
            'var dataList=[{"infolist":[{"iid":101,"title":"iSE实验室测试新闻",'
            '"daytime":"2025-02-03","url":"/xyxw/20250203/i101.html",'
            '"summary":"原站摘要"}]}]; var pagesData={}; var pageTotal=parseInt(1);'
        )
        detail = (
            '<div class="content"><p>正文</p><img src="/media/example.png"></div>'
            '<div id="upanddown"></div>'
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            csv_path = root / "news.csv"
            csv_path.write_text(
                "news_id,title,date,source_url,summary,content_html,cover_image,category,pinned\n"
                "nju-101,旧标题,2025-02-03,https://example.com,旧摘要,旧正文,,专题,TRUE\n",
                encoding="utf-8",
            )
            rows = crawl_nju_ise_news.crawl_news(
                since=date(2025, 1, 1),
                source_path=csv_path,
                fig_dir=root / "fig",
                index_fetcher=lambda _url: index,
                detail_fetcher=lambda _url: detail,
                image_fetcher=lambda _url: b"image-bytes",
            )

            self.assertEqual(rows[0]["category"], "专题")
            self.assertEqual(rows[0]["pinned"], "TRUE")
            self.assertEqual(rows[0]["cover_image"], "news/nju-101/image-001.png")
            self.assertIn("/images/data-source/news/nju-101/image-001.png", rows[0]["content_html"])
            self.assertEqual((root / "fig" / "news" / "nju-101" / "image-001.png").read_bytes(), b"image-bytes")
            with csv_path.open(encoding="utf-8", newline="") as handle:
                saved = list(csv.DictReader(handle))
            self.assertEqual(saved, rows)

    def test_extract_content_html_rejects_missing_content(self):
        with self.assertRaises(crawl_nju_ise_news.NewsCrawlError):
            crawl_nju_ise_news.extract_content_html("<html></html>")


if __name__ == "__main__":
    unittest.main()
