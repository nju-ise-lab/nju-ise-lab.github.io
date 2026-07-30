# 内容维护指南

网站是 Hugo 静态网站，日常更新不需要启动后端服务。

## 维护原则

- 正式内容修改 `frontend/content/`；论文源数据维护在 `frontend/publication-source/`，成员源数据维护在 `frontend/member-source/`。
- 首页和列表数据修改 `frontend/data/`，其中 `publication-records.json` 和 `member-records.json` 均由 CSV 自动生成，不手动编辑。
- 新闻、项目和成员图片放在对应 `index.md` 的同目录页面包；首页轮播放到 `frontend/static/images/slides/`。
- `migration/output/` 和 `migration_exports/` 只作为迁移记录。
- 修改内容后必须重新构建并上传 `public/`。

## 内容对应关系

| 内容 | 文件 |
| --- | --- |
| 新闻 | `frontend/content/news/<slug>/index.md` |
| 学术论文源数据 | `frontend/publication-source/publications.csv` |
| 论文生成数据 | `frontend/data/publication-records.json`（执行脚本生成，不手动编辑） |
| 论文作者—成员链接 | `frontend/data/member-aliases.json`（精确姓名映射） |
| 教师维护源 | `frontend/member-source/teachers.csv` |
| 博士维护源 | `frontend/member-source/phd.csv` |
| 硕士维护源 | `frontend/member-source/masters.csv` |
| 成员生成数据 | `frontend/data/member-records.json`（执行脚本生成，不手动编辑） |
| 成员个人页 | `frontend/content/members/<id>/index.md`（执行脚本生成；同目录保留教师头像） |
| 研究成果入口 | `frontend/content/research-results/_index.md`；论文和专利仍分别维护 |
| 科研项目 | `frontend/content/platform/<slug>/index.md`（兼容入口 `/platform/`；新入口 `/projects/`） |
| 关于我们 | `frontend/content/about/_index.md` |
| 招聘 | `frontend/content/jobs/_index.md` |
| 首页轮播 | `frontend/data/slides.json` |
| 首页精选项目 | `frontend/data/featured-projects.json` |
| 专利 | `frontend/data/projects.json` |
| 站点名称和导航 | `frontend/hugo.yaml` |

## 新闻

目录：

```text
frontend/content/news/my-news/index.md
```

示例：

```yaml
---
title: "新闻标题"
date: 2026-07-18
summary: "列表摘要"
pinned: true # 可选；置顶显示在首页和新闻列表前面
draft: false
---

新闻正文。
```

首页会自动显示置顶优先、再按日期倒序排列的最新 5 条新闻；需要置顶时设置 `pinned: true`。

## 学术论文

论文以 CSV 作为唯一维护源：

```text
frontend/publication-source/publications.csv
```

CSV 必须保留以下列名。多位作者使用英文分号 `;` 分隔；`cofauthor` 和 `corauthor` 中的姓名必须同时出现在 `author` 列中。

```csv
year,id,title,link,status,author,cofauthor,corauthor,level,venue,note
2026,ase-2026,论文标题,https://doi.org/...,accepted,张三;李四,张三,李四,CCF-A,ASE,Industry Track
```

字段说明：

| 字段 | 用途 |
| --- | --- |
| `year`、`id`、`title` | 必填；年份、唯一编号和论文标题 |
| `link` | 论文来源链接。标题只跳转至 Google Scholar、arXiv、OpenReview 或 Semantic Scholar；其他链接（如 DOI、出版社页面）会自动改为 Google Scholar 的题名检索链接。 |
| `status` | `published`、`accepted`（也兼容 `acctpted`）、`pre-print`、`submitted`、`under-review`、`in-press`；`published` 不显示标签，其余特殊状态按需显示 |
| `author` | 必填；按作者顺序填写，使用 `;` 分隔 |
| `cofauthor`、`corauthor` | 共同一作与通讯作者，页面分别显示 `#` 与 `*` |
| `level` | `CCF-A`、`CCF-B`、`CCF-C` 或留空；请优先手动填写。旧数据中少量可明确识别的期刊/会议会自动补充，手动值优先。 |
| `venue`、`note` | 期刊/会议名与补充说明；为空时自动隐藏。页面会从 `venue` 生成 TSE、ICSE、ASE 等简称，并按标题关键词生成最多三个 Topic 标签。 |

作者链接只来自 `frontend/data/member-aliases.json` 的精确映射，避免因同名或写法猜测而误链。例如：

```json
{
  "Zhenyu Chen": "/members/teacher-001/",
  "陈振宇": "/members/teacher-001/"
}
```

更新 CSV 后，在项目根目录执行：

```bash
bash scripts/build.sh
```

构建脚本会先生成页面所需的 `publication-records.json`，再按 Manuscript、年份、特殊状态、作者标记、CCF 等级、期刊/会议、Topic 和备注展示到“研究成果”的学术论文区及首页论文区。也可单独执行 `python3 tools/import_publications.py` 更新数据，或使用 `python3 tools/import_publications.py --check` 检查生成文件是否已同步。

## 软件著作

软件著作维护文件：

```text
frontend/data/software-copyrights.json
```

示例：

```json
[
  {
    "software_name": "软件名称",
    "registration_number": "登记号",
    "year": "2026",
    "owners": [
      {
        "name": "陈振宇",
        "member_url": "/members/teacher-001/"
      }
    ]
  }
]
```

## 成员

成员以三个 CSV 作为唯一维护源：

```text
frontend/member-source/teachers.csv
frontend/member-source/phd.csv
frontend/member-source/masters.csv
```

教师字段：

```csv
teacher_id,name,avatar,member_type,identity,homepage,bio
teacher-001,陈振宇,avatar.jpg,teacher,教授,https://...,个人简介
```

博士字段：

```csv
phd_id,name,member_type,identity,homepage
phd-003,郭安,phd,2020级博士研究生,
```

硕士字段：

```csv
master_id,name,member_type,identity,homepage
master-001,乔力,master,硕士研究生,
```

字段说明：

| 字段 | 用途 |
| --- | --- |
| `teacher_id`、`phd_id`、`master_id` | 必填且不可随意修改；三类成员分别独立编号，如 `teacher-001`、`phd-001`、`master-001` |
| `name` | 成员姓名 |
| `avatar` | 仅教师 CSV 使用；填写教师页面包中的头像文件名 |
| `member_type` | 教师、博士、硕士分别固定为 `teacher`、`phd`、`master` |
| `identity` | 教师填写职称；学生填写“2024级博士研究生”或“硕士研究生”等 |
| `homepage` | 可选的个人主页链接 |
| `bio` | 仅教师 CSV 使用；个人简介 |

新增成员时，在对应 CSV 内查看该类型的最大编号并顺延即可，不需要与另外两类成员共同排号。CSV 中的行顺序就是页面展示顺序。修改后在项目根目录执行：

```bash
bash scripts/build.sh
```

构建脚本会自动校验字段、重复 ID/姓名、成员类型、主页链接和教师头像，并生成 `member-records.json` 以及稳定的教师、博士和硕士成员页。也可单独执行 `python3 tools/import_members.py` 更新数据，或使用 `python3 tools/import_members.py --check` 检查生成文件是否已同步。教师和博士可以进入个人页，硕士只在成员列表展示；非教师不显示头像。已有过往成员页面仅用于保留历史论文作者链接，不出现在成员列表，也不进入三个日常维护 CSV。

论文和专利只依据明确的 `member_url` 关联，不按姓名模糊匹配。英文作者名仍在 `frontend/data/member-aliases.json` 中维护。

## 科研项目

项目正文放在：

```text
frontend/content/platform/
```

只有存在真实项目图片时才添加 `image` 字段；没有图片的项目不要使用实验室 Logo 或通用占位图。迁移器会自动忽略旧站的 `*ise.jpg` 通用单位图。

项目列表字段：

```yaml
project_name: "项目名称"
project_code: "项目号" # 缺失时隐藏
project_period: "2018—2021" # 缺失时隐藏
project_summary: "项目简介" # 卡片中的简短说明
```

项目列表不进入详情页，也不显示迁移生成日期。

首页精选项目修改：

```text
frontend/data/featured-projects.json
```

专利和科研产出修改：

```text
frontend/data/projects.json
```

每条专利使用 `patent_name` 和 `inventors` 字段；申请信息可使用 `public_number`、`application_number`、`application_date` 和 `applicants`。专利本身不可点击，明确关联的专利人可以链接到成员页；缺少发明人时申请人会单独标注，不会被当作发明人。

## 首页轮播

```json
[
  {
    "image": "/images/lab/slides/banner-01.png",
    "fit": "contain",
    "url": "",
    "title": "可选标题",
    "summary": "可选摘要"
  }
]
```

## 图片

页面图片使用相对文件名，实际文件和页面的 `index.md` 放在一起；Hugo 会将它们发布到对应页面目录。轮播 JSON 使用 `/images/slides/...`，文件位于 `frontend/static/images/slides/`。不要在正式网站依赖旧站 HTTP 图片地址。

## 本地预览和发布

```bash
cd frontend
hugo server
```

构建：

```bash
cd frontend
hugo --panicOnWarning --minify \
  --destination /private/tmp/ise-quick-public \
  --cleanDestinationDir
```

上传：

```bash
rsync -az --delete \
  /private/tmp/ise-quick-public/ \
  user@your-server:/var/www/ise-quick/public/
```

## 发布前检查

- 页面标题和日期正确。
- 论文设置了 `content_kind: "publication"`。
- 图片路径可以访问。
- `draft: false`。
- Hugo 构建没有报错。
- 首页、新闻、论文、成员和科研项目页面都能打开。
- 成员页只有教师显示照片；专利和项目不应出现详情跳转或中英文重复字段。
