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
- `link` 优先填写 DOI 链接（`https://doi.org/...`）或期刊、会议出版社的论文详情页；预印本可填写 arXiv 或 OpenReview。暂未找到正式页面时可临时使用 Google Scholar，留空则前端不显示题目链接。
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

## 手动修改后如何更新网站

以下命令都需要在项目根目录 `ise-quick/` 下执行。

### 第一步：开始修改前同步 GitHub

```bash
git pull --ff-only origin main
```

这样可以避免在旧版本上继续修改。

### 第二步：修改维护源

- 成员、论文、专利、软件著作或项目：修改本目录中的对应 Excel。
- 首页、关于我们或教育教学：修改 `content/` 中对应的 Markdown。
- 首页或教师图片：把图片放入 `fig/`，同时更新 Excel 或 Markdown 中的相对路径。
- 新闻：修改 `frontend/content/news/` 中对应的 Markdown 页面。

不要直接修改 `frontend/data/*.json` 或 `frontend/content/members/<成员编号>/index.md`，这些文件会由脚本覆盖。

### 第三步：重新生成 JSON

如果修改了任何 Excel，执行：

```bash
bash scripts/import_data.sh
```

如果只修改了 Markdown 或图片，可以跳过这一步；后面的预览和构建命令也会自动执行一次数据导入。

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

### 第四步：本地预览

```bash
bash scripts/serve.sh
```

浏览器打开 `http://localhost:1313/`，检查首页、成员页、研究成果、项目和刚修改的页面。确认无误后，在终端按 `Control + C` 停止预览。

### 第五步：正式构建和测试

```bash
python3 -m unittest discover -s tools -p 'test_*.py'
bash scripts/build.sh
```

两条命令都成功完成后再提交。`frontend/public/` 是临时构建结果，已被 Git 忽略，不需要提交。

### 第六步：检查修改

```bash
git status
git diff --check
```

确认列表中只有本次准备发布的内容。Excel 更新后，同时出现生成的 JSON 和成员 Markdown 变化是正常的。

### 第七步：提交并推送 GitHub

```bash
git add -A
git commit -m "更新网站内容"
git push origin main
```

提交说明可以写得更具体，例如：

```bash
git commit -m "更新2026年论文和成员信息"
```

推送成功后，GitHub Actions 会自动构建并发布 GitHub Pages。通常等待几十秒后访问：

```text
https://nju-ise-lab.github.io/
```

可以在 GitHub 仓库的 `Actions` 页面查看部署是否成功。

## 常用命令速查

```bash
# 重新生成 Excel 对应的数据
bash scripts/import_data.sh

# 启动本地预览
bash scripts/serve.sh

# 运行测试并构建正式网站
python3 -m unittest discover -s tools -p 'test_*.py'
bash scripts/build.sh

# 提交并推送
git status
git add -A
git commit -m "更新网站内容"
git push origin main
```
