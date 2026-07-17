import json

from migration import generate


def legacy_fixture():
    return {
        "news": {
            "items": [
                {
                    "newsId": 64,
                    "name": "博士生张犬俊在安全漏洞修复方面取得新进展",
                    "category": "业界新闻",
                    "createTime": "2023-12-11 14:43:55",
                    "cover": "http://118.178.18.181:9090/test01/news.png",
                }
            ]
        },
        "news_details": [
            {
                "newsId": 64,
                "name": "博士生张犬俊在安全漏洞修复方面取得新进展",
                "category": "业界新闻",
                "creator": "iSE实验室",
                "createTime": "2023-12-11 14:43:55",
                "context": '<p>正文<img src="https://software.nju.edu.cn/DFS/file/image1.png"></p>',
                "views": 712,
            }
        ],
        "activities_details": [
            {
                "activitiesId": 28,
                "name": "学术讲座",
                "category": "讲座",
                "creator": "iSE实验室",
                "location": "软件学院",
                "context": "<p>活动正文</p>",
                "views": 33,
                "time": "2023-12-05 20:02:02",
            }
        ],
        "products_details": [
            {
                "id": 17,
                "title": "National key R&D program of China: Demo 国家重点研发计划：示例重点课题，2019-2021",
                "views": 81,
                "content": "<p>国家重点研发计划正文</p>",
                "createTime": "2023-12-12 15:17:06",
                "creator": "iSE实验室",
            },
            {
                "id": 16,
                "title": "Duo Platform",
                "views": 70,
                "content": "<p>平台正文</p>",
                "cover": "http://118.178.18.181:9090/test01/product.png",
                "createTime": "2023-12-11 15:17:06",
                "creator": "iSE实验室",
            }
        ],
        "members_details": [
            {
                "id": 38,
                "name": "虞圣呈",
                "role": "脱产博士后",
                "avatar": "http://118.178.18.181:9090/test01/yushengcheng.jpg",
                "basicMessage": "脱产博士后",
                "sort": 7,
            },
            {
                "id": 39,
                "name": "伊高磊",
                "role": "博士生",
                "avatar": "http://118.178.18.181:9090/test01/avatar.jpg",
                "basicMessage": "24级博士生",
                "sort": 8,
            },
            {
                "id": 45,
                "name": "乔力",
                "role": "硕士生",
                "avatar": "http://118.178.18.181:9090/test01/master.png",
                "sort": 9,
            },
        ],
        "projects": [{"id": 20, "english": "Project EN", "chinese": "项目中文"}],
        "publications": {
            "2022": {
                "year": "2022",
                "papers": [{"id": 40, "content": "Paper", "publishYear": "2022"}],
            }
        },
        "slides": [
            {
                "id": 14,
                "url": "http://118.178.18.181:9090/test01/slide.png",
                "cover": "http://118.178.18.181:9090/test01/slide.png",
                "createTime": "2023-12-11 14:59:08",
            }
        ],
        "about": {"about": "<p>实验室介绍</p>"},
        "recruit": {"items": []},
        "recruit_details": [],
    }


def test_generates_news_page_bundle_path():
    site = generate.generate_site(legacy_fixture())

    bundle = site.file("content/news/news-64/index.md")

    assert bundle is not None
    assert "title: \"博士生张犬俊在安全漏洞修复方面取得新进展\"" in bundle.content
    assert "url: \"/news/news-64/\"" in bundle.content


def test_generates_chinese_section_index_pages():
    site = generate.generate_site(legacy_fixture())

    assert 'title: "新闻资讯"' in site.file("content/news/_index.md").content
    assert 'title: "学术活动"' in site.file("content/activities/_index.md").content
    assert 'title: "科研项目"' in site.file("content/platform/_index.md").content
    assert 'title: "科研项目"' in site.file("content/projects/_index.md").content
    assert 'title: "成员介绍"' in site.file("content/members/_index.md").content


def test_generates_about_jobs_and_projects_pages():
    site = generate.generate_site(legacy_fixture())

    assert "<p>实验室介绍</p>" in site.file("content/about/_index.md").content
    assert "暂无招聘信息" in site.file("content/jobs/_index.md").content
    assert "科研项目列表" in site.file("content/projects/_index.md").content


def test_generates_activities_and_platform_paths():
    site = generate.generate_site(legacy_fixture())

    activity = site.file("content/activities/activities-28/index.md")
    platform = site.file("content/platform/duo-platform/index.md")

    assert activity is not None
    assert "url: \"/activities/activities-28/\"" in activity.content
    assert platform is not None
    assert "url: \"/platform/duo-platform/\"" in platform.content


def test_student_members_include_research_direction_mapping():
    site = generate.generate_site(legacy_fixture())

    postdoc = site.file("content/members/member-38/index.md")
    phd = site.file("content/members/member-39/index.md")
    master = site.file("content/members/member-45/index.md")

    assert postdoc is not None
    assert 'research_direction: "智能化软件测试与质量保障"' in postdoc.content
    assert 'student_label: ""' in postdoc.content
    assert phd is not None
    assert 'research_direction: "智能化软件测试与质量保障"' in phd.content
    assert 'student_label: "24级博士生"' in phd.content
    assert 'avatar: "avatar.jpg"' in phd.content
    assert "avatar_url:" not in phd.content
    assert master is not None
    assert 'research_direction: "软件维护与程序自动化修复"' in master.content


def test_legacy_map_contains_old_query_url_to_new_url():
    site = generate.generate_site(legacy_fixture())

    legacy_map = json.loads(site.file("data/legacy-map.json").content)

    assert {
        "section": "news",
        "legacy_id": 64,
        "old": "/news/detail?newsId=64",
        "new": "/news/news-64/",
    } in legacy_map
    assert {
        "section": "platform",
        "legacy_id": 16,
        "old": "/platform/detail?platformId=16",
        "new": "/platform/duo-platform/",
    } in legacy_map
    assert {
        "section": "members",
        "legacy_id": 39,
        "old": "/member/detail?memberId=39",
        "new": "/members/member-39/",
    } in legacy_map


def test_generates_minimal_data_outputs_and_writes_files(tmp_path):
    site = generate.generate_site(legacy_fixture())

    assert site.file("data/featured-projects.json") is not None
    assert site.file("data/projects.json") is not None
    assert site.file("data/publications.json") is not None
    assert site.file("data/slides.json") is not None
    assert site.file("data/media-manifest.json") is not None

    manifest = generate.write_site(site, tmp_path)

    assert (tmp_path / "content/news/news-64/index.md").exists()
    assert manifest["files_written"] == len(site.files)


def test_slide_image_url_is_not_used_as_click_target():
    site = generate.generate_site(legacy_fixture())

    slides = json.loads(site.file("data/slides.json").content)

    assert slides[0]["image"] == "/images/slides/slide-14.png"
    assert "image_url" not in slides[0]
    assert slides[0]["fit"] == "contain"
    assert slides[0]["url"] == ""


def test_featured_projects_prioritizes_national_key_research_projects():
    site = generate.generate_site(legacy_fixture())

    projects = json.loads(site.file("data/featured-projects.json").content)

    assert projects[0]["title"] == "国家重点研发计划：示例重点课题，2019-2021"
    assert projects[0]["url"].startswith("/platform/national-key-r-d-program-of-china")
