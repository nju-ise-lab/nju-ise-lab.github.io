# Content Directory

`frontend/content/` 保存新闻、教育教学、关于我们等 Markdown 页面，以及成员头像所在的页面包。

成员、论文、专利、软件著作和项目不再以这里的 Markdown 作为日常结构化维护源，而统一维护在 `frontend/data-source/` 的 Excel 文件中。成员导入器会根据 `members.xlsx` 自动更新稳定成员页，同时保留页面包内的教师头像。

`content/platform/` 和 `content/activities/` 中的历史页面暂时保留用于旧链接兼容，但项目列表和论文列表已经改为读取 Excel 生成的 JSON。
