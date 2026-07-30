import unittest

from tools import research_content


class ResearchContentTest(unittest.TestCase):
    def test_publication_record_extracts_title_authors_and_member_links(self):
        members = {
            "Zhenyu Chen": "/members/teacher-001/",
            "Chunrong Fang": "/members/teacher-004/",
        }
        record = {
            "legacy_id": 40,
            "year": "2022",
            "content": (
                "Weisong Sun, Chunrong Fang, Yuchen Chen, Zhenyu Chen. "
                "Code Search based on Context-aware Code Translation [C]//"
                "2022 IEEE/ACM International Conference on Software Engineering."
            ),
        }

        publication = research_content.publication_from_record(record, members)

        self.assertEqual(publication["content_kind"], "publication")
        self.assertNotIn("kind", publication)
        self.assertEqual(publication["title"], "Code Search based on Context-aware Code Translation")
        self.assertEqual(publication["publication_year"], "2022")
        self.assertEqual(publication["url"], "/activities/publication-40/")
        self.assertEqual(publication["authors"][0], {"name": "Weisong Sun"})
        self.assertEqual(
            publication["authors"][1],
            {"name": "Chunrong Fang", "member_url": "/members/teacher-004/"},
        )
        self.assertEqual(
            publication["authors"][3],
            {"name": "Zhenyu Chen", "member_url": "/members/teacher-001/"},
        )

    def test_patent_record_keeps_title_and_links_known_chinese_authors(self):
        members = {
            "陈振宇": "/members/teacher-001/",
            "房春荣": "/members/teacher-004/",
        }
        record = {
            "legacy_id": 20,
            "english": "一种基于语法规则的深度神经网络自动生成方法（202111471925.0）",
            "chinese": "房春荣、何云、陈振宇",
        }

        patent = research_content.patent_from_record(record, members)

        self.assertEqual(patent["title"], "一种基于语法规则的深度神经网络自动生成方法（202111471925.0）")
        self.assertEqual(patent["raw_authors"], "房春荣、何云、陈振宇")
        self.assertEqual(
            patent["authors"],
            [
                {"name": "房春荣", "member_url": "/members/teacher-004/"},
                {"name": "何云"},
                {"name": "陈振宇", "member_url": "/members/teacher-001/"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
