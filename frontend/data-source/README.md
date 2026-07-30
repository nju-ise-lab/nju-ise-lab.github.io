# 网站内容维护入口

本目录是日常内容维护的统一入口。结构化内容编辑 Excel，固定栏目正文编辑 Markdown，需要的图片放入 `fig/`。构建时会自动校验并转换数据。

```text
data-source/
├── members.xlsx
├── publications.xlsx
├── patents.xlsx
├── software-copyrights.xlsx
├── projects.xlsx
├── content/
│   ├── _index.md                 # 首页栏目、轮播图和新闻配图
│   ├── about/_index.md           # 关于我们
│   └── education/_index.md       # 教育教学
└── fig/
    ├── brand/                    # 网站标志
    ├── home/                     # 首页轮播图和新闻配图
    └── members/<teacher_id>/     # 教师头像
```

## members.xlsx

| 工作表 | 字段 |
| --- | --- |
| `教师` | `teacher_id, name, avatar, member_type, identity, homepage, bio` |
| `博士研究生` | `phd_id, name, member_type, identity, homepage` |
| `硕士研究生` | `master_id, name, member_type, identity, homepage` |
| `作者别名` | `alias, member_id` |

- 教师、博士和硕士分别使用 `teacher-001`、`phd-001`、`master-001` 格式的独立编号；已有编号不要重新分配。
- 行顺序就是成员页展示顺序。
- `member_type` 分别填写 `teacher`、`phd`、`master`。
- 教师头像必须放在 `fig/members/<teacher_id>/`，`avatar` 填写相对 `fig/` 的路径，例如 `members/teacher-001/avatar.jpg`。
- `homepage` 只允许完整的 `http://` 或 `https://` 链接，也可以留空。
- `作者别名` 用于把论文、专利和软件著作中的英文姓名精确链接到成员页。新增别名时填写作者原文和成员编号，不要使用模糊匹配。

## publications.xlsx

工作表 `学术论文`：

```text
year, id, title, link, status, author, cofauthor, corauthor, level, venue, note
```

- `author` 中多位作者使用英文分号 `;` 分隔。
- `cofauthor` 和 `corauthor` 填写作者姓名；多人仍用 `;` 分隔。
- `status` 可用：`published`、`accepted`、`pre-print`、`under review`、`submitted`、`in press`。`published` 不显示标签。
- `level` 可用 `CCF-A`、`CCF-B`、`CCF-C` 或留空。
- `link` 只使用 Google Scholar、arXiv、Semantic Scholar 或 OpenReview 论文链接。
- `note` 用于奖项、研究主题等补充标签，可留空。

## patents.xlsx

工作表 `专利`：

```text
patent_id, patent_name, inventors, public_number, application_number,
application_date, applicants
```

- 多位发明人或申请人使用英文分号 `;` 分隔。
- `application_date` 使用 `YYYY-MM-DD`。
- 专利条目不生成详情页。

## software-copyrights.xlsx

工作表 `软件著作`：

```text
software_id, software_name, registration_number, year, owners, note
```

- 从第二行开始新增记录。
- 多位著作权人使用英文分号 `;` 分隔。
- 软件著作条目不生成详情页。

## projects.xlsx

工作表 `项目`：

```text
project_id, project_name, project_code, project_period, project_summary,
featured, featured_order, homepage_label
```

- `featured` 填写 `TRUE` 时进入首页项目区。
- `featured_order` 是首页展示顺序，从 1 开始且不可重复。
- Excel 行顺序就是项目页顺序。
- 缺少项目号、时间或简介时，前端自动隐藏该项。

## Markdown 与图片

- 首页：`content/_index.md`。轮播图顺序、图片路径和首页栏目名称均在 front matter 中维护。
- 关于我们：`content/about/_index.md`。
- 教育教学：`content/education/_index.md`。
- 新闻仍在 `frontend/content/news/` 中按一篇一个 Markdown 维护。
- `fig/` 会映射到网站 `/images/data-source/`，Markdown 和 Excel 中不要填写本机绝对路径。

## 转换、预览与发布

在项目根目录执行：

```bash
# Excel → JSON，并更新成员页面
bash scripts/import_data.sh

# 本地预览（会自动先导入）
bash scripts/serve.sh

# 正式构建（会自动先导入）
bash scripts/build.sh
```

自动生成的文件包括：

```text
frontend/data/member-records.json
frontend/data/member-aliases.json
frontend/data/publication-records.json
frontend/data/patent-records.json
frontend/data/software-copyright-records.json
frontend/data/project-records.json
frontend/content/members/<成员编号>/index.md
```

不要手工修改这些生成文件；修改 Excel 后重新运行导入即可。推送 `main` 分支会触发 GitHub Pages 自动发布。
