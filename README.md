# 南京大学智能软件工程实验室网站

这是一个 Hugo 静态网站。成员、论文、专利、软件著作和项目以 Excel 为唯一维护源，导入脚本将其转换为 Hugo 使用的 JSON；首页、关于我们和教育教学正文集中用 Markdown 维护。

## 目录

```text
ise-quick/
├── frontend/
│   ├── data-source/       # 日常维护入口：Excel、Markdown、图片
│   ├── data/              # 自动生成的 JSON，请勿手工修改
│   ├── content/           # 新闻及脚本生成的成员页面
│   ├── static/            # 其他静态资源
│   ├── themes/ise/        # Hugo 模板与样式
│   └── hugo.yaml
├── scripts/               # 导入、构建、预览命令
└── tools/                 # Excel 校验与转换脚本
```

日常内容维护请先阅读 [`frontend/data-source/README.md`](frontend/data-source/README.md)。

## 本地预览

需要 Hugo 0.163.1 或兼容版本，以及 Python 3。

```bash
bash scripts/serve.sh
```

默认访问 `http://localhost:1313/`。脚本会先校验所有 Excel，再重新生成 JSON 和成员页面。

## 构建与校验

```bash
bash scripts/import_data.sh
bash scripts/build.sh
python3 -m unittest discover -s tools -p 'test_*.py'
```

构建结果位于 `frontend/public/`，该目录不提交到 Git。

## 发布

推送 `main` 分支后，`.github/workflows/pages.yml` 会自动构建并发布到 GitHub Pages。

## 数据规则

- 不要直接编辑 `frontend/data/*.json` 或带有 `generated_from` 的成员 Markdown。
- 不再保留旧站迁移脚本、旧 `/activities/`、`/platform/` 和成员 `member-xxx` 兼容路径。
- 历史内容可从 Git 提交记录恢复，不在当前工作目录保留重复副本。
