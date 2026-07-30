# Excel 数据源

本目录中的五个 Excel 文件是网站结构化数据的唯一正式维护源。

## members.xlsx

- `教师`：`teacher_id, name, avatar, member_type, identity, homepage, bio`
- `博士研究生`：`phd_id, name, member_type, identity, homepage`
- `硕士研究生`：`master_id, name, member_type, identity, homepage`

三类成员独立编号。行顺序即成员页展示顺序。教师头像文件仍放在 `content/members/<teacher_id>/`。

## publications.xlsx

工作表 `学术论文`：

`year, id, title, link, status, author, cofauthor, corauthor, level, venue, note`

多位作者使用英文分号 `;` 分隔。`status` 支持 `published`、`accepted`、`pre-print`、`under review`、`submitted`、`in press`；`published` 不显示标签。`level` 使用 `CCF-A`、`CCF-B`、`CCF-C` 或留空。

## patents.xlsx

工作表 `专利`：

`patent_id, patent_name, inventors, public_number, application_number, application_date, applicants`

发明人和申请人均使用英文分号 `;` 分隔。日期使用 `YYYY-MM-DD`。

## software-copyrights.xlsx

工作表 `软件著作`：

`software_id, software_name, registration_number, year, owners, note`

当前只有表头，可直接从第二行开始新增数据。多位著作权人使用英文分号 `;` 分隔。

## projects.xlsx

工作表 `项目`：

`project_id, project_name, project_code, project_period, project_summary, featured, featured_order, homepage_label`

- `featured` 为 `TRUE` 时进入首页项目区。
- `featured_order` 为首页顺序，从 1 开始且不可重复。
- Excel 行顺序即项目列表顺序。
- 缺少项目号、时间或简介时，对应字段自动隐藏。

## 生成与校验

```bash
bash scripts/import_data.sh
```

该命令校验字段、ID、链接和类型，并生成 Hugo 使用的 JSON。正常构建和预览无需单独执行，因为 `scripts/build.sh` 与 `scripts/serve.sh` 已自动调用。
