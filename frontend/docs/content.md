# Content Directory

Hugo Markdown content lives here. This directory currently contains migrated legacy content and is the day-to-day maintenance source.

Sections:

- `news/`
- `activities/`（历史论文页面，保留兼容；新论文从 CSV 导入）
- `platform/`
- `projects/`（项目入口；内容仍兼容 `platform/`）
- `patents/`
- `research-results/`（学术论文与专利的统一成果入口）
- `education/`
- `members/`
- `about/`
- `jobs/`

Edit these files directly for normal content updates. Do not edit `migration/output/content/` unless you are intentionally rerunning or debugging migration.

Publication source data is maintained separately in `frontend/publication-source/publications.csv`; run `python3 tools/import_publications.py` to regenerate Hugo data after edits.
