# 网站内容维护指南

网站采用 Hugo 构建。成员、研究成果和项目统一使用 Excel 维护，再自动转换为 JSON 供 Hugo 渲染。

## 数据流

```text
frontend/data-source/*.xlsx
        ↓ 字段与数据校验
tools/import_*.py
        ↓
frontend/data/*-records.json
        ↓
Hugo 模板
        ↓
frontend/public/
```

日常不要直接修改 `*-records.json`。

## 五个 Excel 维护源

| 内容 | Excel | 工作表 |
| --- | --- | --- |
| 成员 | `frontend/data-source/members.xlsx` | `教师`、`博士研究生`、`硕士研究生` |
| 学术论文 | `frontend/data-source/publications.xlsx` | `学术论文` |
| 专利 | `frontend/data-source/patents.xlsx` | `专利` |
| 软件著作 | `frontend/data-source/software-copyrights.xlsx` | `软件著作` |
| 项目 | `frontend/data-source/projects.xlsx` | `项目` |

字段顺序不可随意更改。可以新增、删除或调整数据行；空字段在页面自动隐藏。

## 成员

教师字段：

```text
teacher_id, name, avatar, member_type, identity, homepage, bio
```

博士字段：

```text
phd_id, name, member_type, identity, homepage
```

硕士字段：

```text
master_id, name, member_type, identity, homepage
```

- 教师、博士、硕士分别使用 `teacher-001`、`phd-001`、`master-001` 这样的独立 ID。
- `member_type` 分别固定为 `teacher`、`phd`、`master`。
- 教师头像文件放在 `frontend/content/members/<teacher_id>/`，Excel 的 `avatar` 填文件名。
- 行顺序控制成员列表顺序。
- 导入器生成 `member-records.json` 和稳定成员页；旧成员 URL 继续通过 alias 兼容。

## 学术论文

字段：

```text
year, id, title, link, status, author, cofauthor, corauthor, level, venue, note
```

- `id` 唯一。
- 多位作者使用英文分号 `;` 分隔。
- `cofauthor` 和 `corauthor` 中的人名必须出现在 `author`。
- `status` 支持 `published`、`accepted`、`pre-print`、`under review`、`submitted`、`in press`。
- `level` 使用 `CCF-A`、`CCF-B`、`CCF-C` 或留空。
- `link` 保存论文来源链接。页面标题仅链接到 Google Scholar、arXiv、OpenReview、Semantic Scholar；其他来源自动转换为 Google Scholar 题名检索。
- 作者与成员页只按精确姓名映射，不做模糊匹配；英文别名维护在 `frontend/data/member-aliases.json`。

## 专利

字段：

```text
patent_id, patent_name, inventors, public_number, application_number, application_date, applicants
```

- `patent_id` 唯一。
- 多位发明人或申请人使用英文分号 `;` 分隔。
- `application_date` 使用 `YYYY-MM-DD`。
- 专利卡片本身不进入详情页；能精确匹配成员的人名自动链接成员页。

## 软件著作

字段：

```text
software_id, software_name, registration_number, year, owners, note
```

当前工作表为空，可直接从第二行新增。多位著作权人使用英文分号 `;` 分隔。

## 项目

字段：

```text
project_id, project_name, project_code, project_period, project_summary, featured, featured_order, homepage_label
```

- 项目列表顺序由 Excel 行顺序决定。
- `featured=TRUE` 的项目进入首页。
- 首页项目按 `featured_order` 从小到大排列；值必须为正整数且不可重复。
- `homepage_label` 是首页项目左侧类别标签。
- 项目号、项目时间和简介为空时自动隐藏。
- `/projects/` 为正式入口，`/platform/` 保留兼容。

## 新闻与轮播

- 新闻：`frontend/content/news/<slug>/index.md`
- 首页轮播配置：`frontend/data/slides.json`
- 轮播图片：`frontend/static/images/slides/`

新闻设置 `pinned: true` 后会在首页和新闻列表置顶。

## 预览与构建

本地预览：

```bash
bash scripts/serve.sh
```

正式构建：

```bash
bash scripts/build.sh
```

两个命令都会先执行全部 Excel → JSON 导入器。只检查生成数据是否同步时：

```bash
python3 tools/import_members.py --check
python3 tools/import_publications.py --check
python3 tools/import_patents.py --check
python3 tools/import_software_copyrights.py --check
python3 tools/import_projects.py --check
```
