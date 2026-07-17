from migration import core


def test_chinese_title_falls_back_to_stable_legacy_slug():
    slug = core.slugify_title("博士生张犬俊在安全漏洞修复方面取得新进展", prefix="news", legacy_id=64)

    assert slug == "news-64"


def test_mixed_title_keeps_ascii_tokens():
    slug = core.slugify_title("iSE实验室硕士生获 IEEE DSA 2023 最佳论文奖", prefix="news", legacy_id=61)

    assert slug == "ise-ieee-dsa-2023"


def test_slug_registry_handles_duplicate_and_empty_titles():
    registry = core.SlugRegistry(prefix="news")

    assert registry.generate("iSE News", legacy_id=1) == "ise-news"
    assert registry.generate("iSE News", legacy_id=2) == "ise-news-2"
    assert registry.generate("", legacy_id=3) == "news-3"


def test_normalize_datetime_outputs_hugo_timestamp():
    assert core.normalize_datetime(" 2023-12-11 14:43:55") == "2023-12-11T14:43:55+08:00"
    assert core.normalize_datetime("2023-12-11") == "2023-12-11T00:00:00+08:00"
    assert core.normalize_datetime("") is None


def test_news_front_matter_does_not_include_view_count_data():
    record = {
        "newsId": 64,
        "name": "博士生张犬俊在安全漏洞修复方面取得新进展",
        "category": "业界新闻",
        "creator": "iSE实验室",
        "createTime": " 2023-12-11 14:43:55",
        "views": 712,
    }

    front_matter = core.build_news_front_matter(record, slug="news-64")

    assert front_matter == {
        "title": "博士生张犬俊在安全漏洞修复方面取得新进展",
        "date": "2023-12-11T14:43:55+08:00",
        "category": "业界新闻",
        "creator": "iSE实验室",
        "legacy_id": 64,
        "draft": False,
        "url": "/news/news-64/",
    }


def test_platform_front_matter_uses_platform_url_base():
    record = {
        "id": 7,
        "title": "缺陷检测平台",
        "creator": "iSE实验室",
        "createTime": "2023-10-01 00:00:00",
        "views": 12,
    }

    front_matter = core.build_platform_front_matter(record, slug="platform-7")

    assert core.section_base_url("platform") == "/platform/"
    assert front_matter["url"] == "/platform/platform-7/"
    assert "views_seed" not in front_matter


def test_activity_front_matter_uses_activities_url_and_event_time():
    record = {
        "activitiesId": 4,
        "name": "学术讲座",
        "category": "讲座",
        "creator": "iSE实验室",
        "location": "软件学院",
        "time": "2023-11-01 15:00:00",
        "views": 33,
    }

    front_matter = core.build_activity_front_matter(record, slug="activities-4")

    assert core.section_base_url("activities") == "/activities/"
    assert front_matter["url"] == "/activities/activities-4/"
    assert front_matter["event_time"] == "2023-11-01T15:00:00+08:00"
    assert "views_seed" not in front_matter


def test_student_member_front_matter_adds_research_direction_mapping():
    record = {
        "id": 39,
        "name": "伊高磊",
        "role": "博士生",
        "email": "",
        "avatar": "http://118.178.18.181:9090/test01/avatar.jpg",
        "basicMessage": "24级博士生",
        "academy": "软件学院",
        "sort": 8,
    }

    front_matter = core.build_member_front_matter(record, slug="yi-gao-lei")

    assert front_matter["role"] == "博士生"
    assert front_matter["research_direction"] == "智能化软件测试与质量保障"
    assert front_matter["student_label"] == "24级博士生"
    assert front_matter["avatar"] == "avatar.jpg"
    assert "avatar_url" not in front_matter
    assert front_matter["legacy_id"] == 39


def test_mapped_postdoc_member_can_join_student_direction_group():
    record = {
        "id": 41,
        "name": "虞圣呈",
        "role": "脱产博士后",
        "basicMessage": "博士后",
        "sort": 10,
    }

    front_matter = core.build_member_front_matter(record, slug="member-41")

    assert front_matter["role"] == "脱产博士后"
    assert front_matter["research_direction"] == "智能化软件测试与质量保障"
    assert front_matter["student_label"] == ""


def test_teacher_member_front_matter_omits_research_direction_placeholder():
    record = {"id": 37, "name": "陈振宇", "role": "教授", "sort": 1}

    front_matter = core.build_member_front_matter(record, slug="member-37")

    assert front_matter["role"] == "教授"
    assert "research_direction" not in front_matter


def test_media_classification_downloads_image_fields_but_not_external_links():
    cover = core.classify_media_url(
        "http://118.178.18.181:9090/test01/45a91dc8-7a96-4765-8988-c9c0e0aa7e256.png",
        context="cover",
    )
    external_link = core.classify_media_url("https://example.com/report.png", context="link")
    legacy_api = core.classify_media_url("http://118.178.18.181/api/news/showNewsPages", context="link")

    assert cover.kind == "download_candidate"
    assert cover.should_localize is True
    assert external_link.kind == "external_link"
    assert external_link.should_localize is False
    assert legacy_api.kind == "legacy_api"
    assert legacy_api.should_localize is False


def test_extract_media_references_reads_img_src_only():
    html = """
    <p><a href="https://example.com/jump.png">external jump</a></p>
    <p><img src="https://software.nju.edu.cn/DFS/file/2023/image1.png"></p>
    """

    refs = core.extract_media_references(html)

    assert [ref.url for ref in refs] == ["https://software.nju.edu.cn/DFS/file/2023/image1.png"]
    assert refs[0].kind == "download_candidate"
