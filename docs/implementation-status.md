# Implementation Status

Last updated: 2026-06-14

## Current Scope

The new rebuild lives under `ise-quick/`:

- `frontend/`: Hugo static site with a custom ISE theme.
- `backend/`: Go + SQLite view counter API.
- `migration/`: Python legacy JSON to Hugo content/data pipeline.

The legacy projects have been removed from this workspace. New work should stay under `ise-quick/`.

## Completed

- Created the `ise-quick/` project structure.
- Preserved the old visual baseline in the Hugo theme:
  - main purple `#63065f`
  - auxiliary blue `#2e6590`
  - 1200px content width
  - header, nav, footer, breadcrumb, and leftbar layout direction
- Copied reusable legacy assets into `frontend/static/images/legacy/`.
- Implemented homepage sections:
  - carousel with visible dots and previous/next controls
  - latest news, 5 items
  - academic activities, 3 items
  - featured research projects, 4 items
- Implemented section templates for:
  - news
  - activities
  - platform / research projects
  - members
- Implemented member grouping:
  - 教授
  - 副教授
  - 博士生 by `research_direction`
  - 硕士生 by `research_direction`
- Implemented the migration MVP:
  - section index pages for Chinese section titles
  - content page bundles for news, activities, platform, and members
  - `data/projects.json`
  - `data/featured-projects.json`
  - `data/publications.json`
  - `data/slides.json`
  - `data/views-seed.json`
  - `data/legacy-map.json`
  - `data/media-manifest.json`
- Regenerated migration output from `migration_exports/legacy_api`.
- Implemented the view counter API:
  - `GET /api/views?path=/...`
  - `POST /api/views`
  - SQLite initialization
  - seed import from JSON
  - repeated import preserves accumulated `views`
- Connected frontend detail pages to the backend view counter through configurable `params.viewAPI`.
- Added `tools/dev_static_proxy.py` for local static preview plus `/api/views` proxying.
- Replaced blurry section heading images with text plus inline SVG icons.
- Added auto-rotating carousel behavior with dot and previous/next controls.
- Changed carousel data back to legacy slide images while using `object-fit: contain` for paper/screenshot-style slides.
- Removed the default carousel text overlay; slide captions only render when explicitly configured.
- Merged visible `平台产品` and `科研项目` presentation under one `科研项目` navigation entry at `/platform/`.
- Rendered `/platform/` as a combined page: project/platform records first, patent/output records below.
- Removed single-item leftbar menus so section pages no longer show the same label twice inside the leftbar.
- Completed the first lightweight visual enhancement pass:
  - softer section/list hierarchy
  - homepage project badges
  - refined news/activity hover states
  - more readable article body, image, and table styling
  - subtle research-project and member-card hover feedback
- Added deterministic member direction mapping for:
  - 智能化软件测试与质量保障
  - 智能驾驶与测试
  - 软件维护与程序自动化修复
- Removed separate `脱产博士后` and `专职科研岗位` sections from the member list.
- Added homepage featured project data that prioritizes 国家重点研发计划 and 国家自然科学基金重点/重大项目.
- Generated non-empty about, jobs, and projects pages from legacy data or editable placeholders.

## Verified

Backend tests:

```bash
cd ise-quick/backend
GOMODCACHE=/private/tmp/isequick-gomod GOCACHE=/private/tmp/isequick-gocache /opt/homebrew/bin/go test ./...
```

Result:

```text
ok ise-quick/backend
```

Python migration tests:

```bash
cd ise-quick/migration
../../.venv/bin/python -m pytest tests
```

Result:

```text
22 passed
```

Python syntax check:

```bash
cd ise-quick/migration
PYTHONPYCACHEPREFIX=/private/tmp/isequick-pyc ../../.venv/bin/python -m compileall .
```

Migration generation:

```bash
cd ise-quick/migration
../../.venv/bin/python scripts/migrate.py --write
```

Result:

```text
generated_files: 80
files_written: 80
```

Frontend build from current migrated `frontend/content` and `frontend/data`:

```bash
cd ise-quick/frontend
/opt/homebrew/bin/hugo --panicOnWarning --destination /private/tmp/isequick-hugo-public --cleanDestinationDir
```

Result:

```text
Pages: 83
```

Local integration check:

```bash
VIEW_COUNTER_DB=/private/tmp/isequick-live-views.db \
VIEW_COUNTER_SEED_FILE=../frontend/data/views-seed.json \
ADDR=127.0.0.1:18080 \
/opt/homebrew/bin/go run .

/usr/bin/python3 ise-quick/tools/dev_static_proxy.py \
  --root /private/tmp/<generated-public> \
  --backend http://127.0.0.1:18080 \
  --host 127.0.0.1 \
  --port 1313
```

Verified:

- Homepage renders 8 legacy slide images, 5 news items, 3 activities, and 4 featured research projects.
- Carousel controls were verified with the real `carousel.js` module in a DOM stub: initial slide 0, next to slide 1, previous back to slide 0.
- Homepage section headings render as text plus SVG icons, with no heading image assets.
- About and jobs pages return 200 and show content.
- The former dataset block now renders as `科研项目`.
- Slide image URLs are legacy image assets, displayed with contain fit, and are no longer clickable anchors.
- `/news/news-64/` posts to `/api/views`.
- API returned `seed: 712`, `views: 1`, `total: 713`.
- Members page title is `成员介绍`, hides separate `脱产博士后` and `专职科研岗位` sections, and uses compact avatar grids for configured student direction groups.
- Homepage featured projects include 国家重点研发计划 and 国家自然科学基金重点项目 titles.
- The main nav has one visible `科研项目` entry and no separate `项目成果` / `研究成果` dropdown.
- `/platform/` renders `项目与平台` first and `专利 / 产出` below, including patent/output records such as `一种基于语法规则的深度神经网络自动生成方法（202111471925.0）`.
- `/news/` no longer renders the lower duplicate one-item leftbar menu.

## Not Yet Verified

- Browser screenshot verification. The in-app browser was unavailable and system Chrome headless launch was blocked locally; HTML, Hugo build, backend tests, migration tests, and carousel JS behavior were verified.
- Production Nginx reverse proxy configuration.

## Known Gaps

- Unmapped doctoral/master students still render under `方向待补充`; the seven confirmed names are mapped to the three requested directions.
- Media files are not downloaded/localized yet; `media-manifest.json` records download candidates.
- Legacy redirects are not implemented; only `legacy-map.json` is generated.

## Next Recommended Step

Run a local preview with the backend API and Hugo server, then prepare production deployment with `docs/cloud-deployment-guide.md`.
