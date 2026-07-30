# Data Directory

`frontend/data/` 是 Hugo 运行时数据目录。

以下文件由 `frontend/data-source/*.xlsx` 自动生成，禁止手工编辑：

- `member-records.json`
- `publication-records.json`
- `patent-records.json`
- `software-copyright-records.json`
- `project-records.json`

以下文件仍手工维护：

- `slides.json`：首页轮播。
- `member-aliases.json`：英文作者名等精确写法到成员页的映射。
- `legacy-map.json`：历史迁移映射。
- `publications.json`：旧系统论文迁移记录，不参与当前页面维护。

执行 `bash scripts/import_data.sh` 可重新生成全部 `*-records.json`；`bash scripts/build.sh` 和 `bash scripts/serve.sh` 会自动先执行该步骤。
