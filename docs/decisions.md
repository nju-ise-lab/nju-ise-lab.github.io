# ISE Quick Decisions

## Confirmed

- New project root: `ise-quick/`.
- Frontend path: `ise-quick/frontend/`.
- Migration path: `ise-quick/migration/`.
- Frontend framework: Hugo.
- Runtime architecture: Hugo static files served by Nginx.
- Hugo theme: custom-built, preserving the old site's layout and visual language.
- Main color: `#63065f`.
- Auxiliary blue: `#2e6590`.
- Desktop content width: 1200px.
- Homepage modules:
  - carousel
  - latest news: 5 items
  - academic activities: 3 items
  - research projects: 4 items
- Research project public URL: `/platform/`.
- Visible navigation has one `科研项目` entry; `平台产品` and old project outputs are merged under this page.
- `/projects/` remains as a compatibility page but renders the same merged research-project content and is not shown in navigation.
- Content update flow: edit Markdown/JSON, rebuild, deploy.
- Browser-visible footer copyright and ICP filing should be retained.
- Image strategy: localize content media, while preserving true external navigation links.
- Body conversion: convert legacy HTML to Markdown when safe; keep complex tables/images as HTML.
- View counter: removed; it is outside the core publishing requirement.
- Search: not needed for first release.
- CMS/admin: not needed for first release.
- Deployment target: self-owned server with Nginx static hosting.
- Legacy database direct export: paused.

## Member Display

Display order:

1. 教授
2. 副教授
3. 博士生 / 硕士生, grouped by research direction

Confirmed research direction groups:

- 智能化软件测试与质量保障: 虞圣呈, 伊高磊, 顾思琦, 钱瑞祥
- 智能驾驶与测试: 郭安
- 软件维护与程序自动化修复: 戎润祥, 乔力

The legacy export does not include a clean direction field, so migrated member Markdown includes a manually maintainable `research_direction` front matter field.

The separate legacy role sections `脱产博士后` and `专职科研岗位` are hidden on the member list. A person can still appear inside a confirmed direction group when explicitly mapped.

## Still Open

- Whether to add Nginx redirects for legacy detail URLs or only keep a legacy URL map.
- Final server path and deployment script details.
