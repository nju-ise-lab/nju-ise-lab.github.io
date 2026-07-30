# ISE Lab Hugo Frontend

南京大学智能软件工程实验室网站的 Hugo 前端。

## 数据维护方式

成员、研究成果和项目统一维护在 `data-source/` 的五个 Excel 文件中：

- `members.xlsx`：教师、博士研究生、硕士研究生三个工作表。
- `publications.xlsx`：学术论文。
- `patents.xlsx`：专利。
- `software-copyrights.xlsx`：软件著作。
- `projects.xlsx`：科研项目及首页精选顺序。

这些 Excel 是正式维护源。`data/` 中的 `*-records.json` 均由脚本生成，不应手工编辑。构建数据流为：

```text
Excel
  → tools/import_*.py 校验并生成 JSON / 成员页
  → Hugo 读取 JSON
  → public/ 静态网站
```

新闻、关于我们和教育教学等正文仍在 `content/` 中用 Markdown 维护；轮播图配置保留在 `data/slides.json`。

## 本地预览

从项目根目录执行：

```bash
bash scripts/serve.sh
```

该命令会先更新全部 JSON，再启动 Hugo 开发服务器。仅需生成静态网站时执行：

```bash
bash scripts/build.sh
```

更完整的字段说明见：

- `data-source/README.md`
- `../docs/content-maintenance-guide.md`

## 主要目录

- `data-source/`：五个正式 Excel 数据源。
- `data/`：Hugo JSON 数据；生成文件与少量手工配置。
- `content/`：Markdown 页面和成员头像页面包。
- `themes/ise/`：模板、CSS 和 JavaScript。
- `static/`：轮播图、Logo、favicon 等静态资源。
