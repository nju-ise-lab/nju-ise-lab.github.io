# 内容维护指南

网站是 Hugo 静态网站，日常更新不需要启动后端服务。

## 维护原则

- 正式内容修改 `frontend/content/`；论文源数据维护在 `frontend/publication-source/`。
- 首页和列表数据修改 `frontend/data/`，其中 `publication-records.json` 由论文 CSV 自动生成，不手动编辑。
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
| 成员 | `frontend/content/members/<slug>/index.md` |
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
| `status` | `published`、`accepted`（也兼容 `acctpted`）、`pre-print`、`submitted`、`under-review`、`in-press` |
| `author` | 必填；按作者顺序填写，使用 `;` 分隔 |
| `cofauthor`、`corauthor` | 共同一作与通讯作者，页面分别显示 `#` 与 `*` |
| `level` | `CCF-A`、`CCF-B`、`CCF-C` 或留空；请优先手动填写。旧数据中少量可明确识别的期刊/会议会自动补充，手动值优先。 |
| `venue`、`note` | 期刊/会议名与补充说明；为空时自动隐藏 |

作者链接只来自 `frontend/data/member-aliases.json` 的精确映射，避免因同名或写法猜测而误链。例如：

```json
{
  "Zhenyu Chen": "/members/member-37/",
  "陈振宇": "/members/member-37/"
}
```

更新 CSV 后，在项目根目录执行：

```bash
python3 tools/import_publications.py
bash scripts/build.sh
```

脚本会生成页面所需的 `publication-records.json`，并按 Manuscript、年份、状态、作者标记、CCF 等级、期刊/会议和备注展示到“研究成果”的学术论文区及首页论文区。可使用 `python3 tools/import_publications.py --check` 检查生成文件是否已同步。

## 成员

示例：

```yaml
---
title: "姓名"
member_type: "phd" # teacher | phd | master | alumni
role_title: "博士生" # 教师可填写职称
grade: "2021级" # 缺失时不显示
research_direction: "智能驾驶与测试" # 博士生按此字段分组
homepage: "https://..." # 可选；个人页显示
destination: "华为" # 过往成员可选
display_order: 10
avatar: "avatar.jpg" # 数据保留；只有教师列表和个人页渲染
draft: false
---
```

成员类型映射为：教授/副教授使用 `teacher`，博士生使用 `phd`，硕士生使用 `master`，现有博士后归入 `alumni`。教师和博士生可以进入个人页；论文和专利只依据明确的 `member_url` 关联，不按姓名模糊匹配。

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

每条专利使用 `patent_name` 和 `inventors` 字段；专利本身不可点击，明确关联的专利人可以链接到成员页。

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
