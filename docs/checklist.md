# Manual Integration Checklist

Use this checklist when validating the migrated Hugo rebuild.

## Paths

- [x] Research project public URL is `/platform/`.
- [x] Academic activity public URL is `/activities/`.
- [x] New frontend/migration code uses `/activities/`; old `/activity/` only appears in `legacy-map.json` as a source URL.
- [x] No new code uses `/platforms/`.

## Homepage

- [x] Latest news: 5 items.
- [x] Academic activities: 3 items.
- [x] Featured research projects: 4 items from `/platform/`.
- [x] Featured research projects prioritize 国家重点研发计划 and 国家自然科学基金重点/重大项目.
- [x] Carousel falls back gracefully when slide data is missing.
- [x] Carousel uses legacy slide image data.
- [x] Carousel uses contain fit for paper/screenshot-style slide images.
- [x] Carousel does not render the default site-title overlay.
- [x] Carousel auto-rotates and exposes dot plus previous/next controls.
- [x] Validate with `hugo` build.

## Members

- [x] Display order: 教授, 副教授, 博士生 / 硕士生.
- [x] 博士生 / 硕士生 are grouped by `research_direction`.
- [x] Empty direction displays as `方向待补充`.
- [x] Student groups render as compact avatar grids similar to the provided reference.
- [x] Separate `脱产博士后` and `专职科研岗位` sections are hidden.
- [x] Confirmed direction mapping:
  - 智能化软件测试与质量保障: 虞圣呈, 伊高磊, 顾思琦, 钱瑞祥
  - 智能驾驶与测试: 郭安
  - 软件维护与程序自动化修复: 戎润祥, 乔力
- [ ] Fill remaining unmapped student research directions after manual review.

## Migration

- [x] `legacy_id` is preserved.
- [x] `views` is migrated as both `seed` and `views_seed`.
- [x] `legacy-map` is generated.
- [x] Media URL manifest separates download candidates from external links.
- [x] Python migration tests pass.
- [x] Generated content/data can build with Hugo from a temporary source.
- [x] Generated section index pages keep Chinese section titles.
- [x] Generated about, jobs, and projects pages are not empty.
- [x] Slide image URLs are not treated as clickable external links.
- [x] `data/featured-projects.json` is generated for homepage featured research projects.
- [ ] Media files are not downloaded yet; only manifest is generated.

## Research Projects

- [x] Visible navigation has one `科研项目` entry.
- [x] `平台产品` wording is removed from visible content/navigation.
- [x] `/platform/` renders project/platform records first.
- [x] `/platform/` renders patent/output records below, including records from `data/projects.json`.
- [x] Single-item leftbar menus are hidden to avoid duplicate section titles.

## Backend

- [x] `GET /api/views?path=/...` handler is implemented.
- [x] `POST /api/views` increment handler is implemented.
- [x] Seed import does not reset accumulated views.
- [x] Seed import accepts `seed` and legacy `views_seed`.
- [x] Run `go test ./...`.

## Frontend Runtime

- [x] Detail pages output `data-view-path`.
- [x] Frontend JS posts to configurable `params.viewAPI`, default `/api/views`.
- [x] Validate Hugo-generated HTML build.
- [x] Validate local `/api/views` integration through the dev static proxy.
- [x] Validate carousel JavaScript behavior with a DOM stub.
- [ ] Validate browser screenshots.
