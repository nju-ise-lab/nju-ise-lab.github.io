# ISE Quick 项目介绍与架构设计

本文档用于解释 ISE Quick 是什么、为什么这样设计、各目录负责什么，以及请求、内容、浏览量和迁移数据如何流动。

日常内容更新请优先看：

```text
docs/content-maintenance-guide.md
```

云服务器部署请看：

```text
docs/cloud-deployment-guide.md
```

## 项目定位

ISE Quick 是南京大学智能软件工程实验室主页的轻量化重构版本。它的目标不是做一个复杂后台系统，而是把旧站中“可公开展示、后期需要低成本维护”的内容沉淀为静态站点。

核心目标：

- 保留旧站的主要布局、主题色和视觉框架。
- 后期内容更新尽量通过 Markdown、JSON、图片文件完成。
- 去掉复杂数据库依赖，降低维护成本。
- 仅保留一个轻量后端，用于浏览量统计。
- 支持部署到自有云服务器。

明确不做：

- 不做完整 CMS 后台。
- 不做复杂搜索。
- 不做复杂访问去重。
- 不继续维护旧前后端项目。

## 技术栈

| 层 | 技术 | 作用 |
| --- | --- | --- |
| 前端站点 | Hugo | 生成静态 HTML、CSS、JS |
| 前端主题 | 自建 Hugo theme `ise` | 保留旧站布局、颜色、组件 |
| 内容源 | Markdown / JSON | 新闻、活动、成员、项目、轮播等内容 |
| 浏览量 API | Go | 提供 `/api/views` |
| 浏览量存储 | SQLite | 保存页面初始浏览量和新增浏览量 |
| 迁移工具 | Python | 将旧系统导出数据转换为 Hugo 内容 |
| 推荐 Web 服务 | Nginx | 托管静态站点并反向代理 API |

## 顶层目录

```text
ise-quick/
  frontend/   Hugo 静态站点
  backend/    Go + SQLite 浏览量 API
  migration/  旧数据迁移管道
  tools/      本地开发辅助工具
  docs/       架构、维护、部署、决策文档
```

当前正式站点内容已经放在：

```text
ise-quick/frontend/content/
ise-quick/frontend/data/
```

`migration/output/` 只是迁移输出记录和备份，不是日常维护入口。

## 运行时架构

生产环境建议采用下面的结构：

```text
Browser
  |
  | HTTPS
  v
Nginx
  |
  |-- 静态页面、CSS、JS、图片
  |     root: /var/www/ise-quick/public
  |
  |-- /api/views
        |
        v
      Go view-counter
        |
        v
      SQLite views.db
```

说明：

- Hugo 生成出来的是静态文件，由 Nginx 直接返回。
- 只有浏览量请求走 Go 后端。
- Go 后端只监听 `127.0.0.1:8080`，不直接暴露公网。
- SQLite 数据文件放在服务器持久化目录中，例如 `/var/lib/ise-quick/views.db`。

## 构建与发布流

```text
编辑 Markdown / JSON / 图片
  |
  v
Hugo 构建
  |
  v
生成 public 静态目录
  |
  v
上传或部署到 Nginx root
  |
  v
浏览器访问页面
```

浏览量单独流动：

```text
详情页加载
  |
  v
view-counter.js 请求 /api/views
  |
  v
Nginx 反代到 Go 后端
  |
  v
SQLite 更新并返回 total
```

## Frontend 架构

前端目录：

```text
frontend/
  hugo.yaml
  content/
  data/
  static/
  themes/ise/
```

### `hugo.yaml`

站点级配置，包含：

- `baseURL`
- 站点标题
- 实验室中文名、英文名
- 页脚版权和备案号
- 主导航
- 浏览量 API 地址 `params.viewAPI`

主导航目前为：

- 首页
- 新闻资讯
- 学术活动
- 成员介绍
- 科研项目
- 关于我们
- 诚聘英才

### `content/`

页面型内容，主要是 Markdown：

```text
content/news/         新闻资讯
content/activities/   学术活动
content/members/      成员介绍
content/platform/     科研项目中的“项目与平台”
content/about/        关于我们
content/jobs/         诚聘英才
content/projects/     兼容页，不在主导航展示
```

这些内容会生成真实页面。新增、删除、修改这些内容，通常只需要改 Markdown。

### `data/`

非页面型数据，主要是 JSON：

```text
data/slides.json             首页轮播
data/featured-projects.json  首页精选科研项目
data/projects.json           科研项目页“专利 / 产出”
data/publications.json       迁移出的论文数据，预留使用
data/views-seed.json         浏览量初始值
data/legacy-map.json         旧系统 ID/URL 映射
data/media-manifest.json     迁移时发现的媒体引用
```

这些数据不会每条都生成单独页面，而是被模板读取后渲染到页面中。

### `themes/ise/`

自建 Hugo 主题，负责页面结构和视觉：

```text
themes/ise/layouts/       Hugo 模板
themes/ise/layouts/partials/ 公共组件
themes/ise/assets/css/    样式
themes/ise/assets/js/     轮播和浏览量脚本
```

一般维护内容时不要改主题。只有要调整布局、颜色、卡片样式、页面结构时才改这里。

## 主要页面与组件

| 页面 | URL | 模板 | 内容来源 |
| --- | --- | --- | --- |
| 首页 | `/` | `layouts/index.html` | `data/slides.json`、`content/news/`、`content/activities/`、`data/featured-projects.json` |
| 新闻资讯 | `/news/` | `layouts/news/list.html` | `content/news/` |
| 新闻详情 | `/news/<slug>/` | `layouts/news/single.html` | 单篇新闻 Markdown |
| 学术活动 | `/activities/` | `layouts/activities/list.html` | `content/activities/` |
| 活动详情 | `/activities/<slug>/` | `layouts/activities/single.html` | 单篇活动 Markdown |
| 成员介绍 | `/members/` | `layouts/members/list.html` | `content/members/` |
| 成员详情 | `/members/<slug>/` | `layouts/members/single.html` | 单个成员 Markdown |
| 科研项目 | `/platform/` | `layouts/platform/list.html` | `content/platform/`、`data/projects.json` |
| 关于我们 | `/about/` | 默认单页模板 | `content/about/_index.md` |
| 诚聘英才 | `/jobs/` | 默认单页模板 | `content/jobs/_index.md` |

更细的“页面模块 -> 数据文件”映射见 `docs/content-maintenance-guide.md`。

## Backend 架构

后端目录：

```text
backend/
  main.go
  server.go
  server_test.go
  go.mod
```

后端只负责浏览量，不参与页面内容管理。

### API

查询浏览量：

```text
GET /api/views?path=/news/example/
```

增加浏览量：

```text
POST /api/views
Content-Type: application/json

{"path":"/news/example/"}
```

返回结构：

```json
{
  "path": "/news/example/",
  "seed": 100,
  "views": 5,
  "total": 105
}
```

字段说明：

- `seed`：旧站迁移过来的初始浏览量。
- `views`：新站上线后的新增浏览量。
- `total`：页面显示的总浏览量，等于 `seed + views`。

### 环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `VIEW_COUNTER_DB` | `views.db` | SQLite 数据库路径 |
| `VIEW_COUNTER_SEED_FILE` | 空 | 初始浏览量 seed JSON |
| `ADDR` | `:8080` | 后端监听地址 |

生产环境建议：

```text
VIEW_COUNTER_DB=/var/lib/ise-quick/views.db
VIEW_COUNTER_SEED_FILE=/opt/ise-quick/frontend/data/views-seed.json
ADDR=127.0.0.1:8080
```

## Migration 架构

迁移目录：

```text
migration/
  migration/core.py
  migration/generate.py
  scripts/migrate.py
  tests/
  output/
```

迁移工具的作用：

- 读取旧系统导出的 JSON。
- 转换为 Hugo Markdown 内容。
- 生成首页轮播、精选项目、专利/产出、浏览量 seed 等 JSON。
- 保留旧数据映射和媒体引用清单。

当前迁移结果已经复制到：

```text
frontend/content/
frontend/data/
```

因此日常维护不需要运行迁移工具。只有当你想重新从旧系统导入数据，才需要关注 `migration/`。

## 数据源策略

当前有三类数据：

| 数据类型 | 正式维护位置 | 说明 |
| --- | --- | --- |
| 页面内容 | `frontend/content/` | Markdown，可直接编辑 |
| 页面辅助数据 | `frontend/data/` | JSON，可直接编辑 |
| 迁移记录 | `migration/output/` | 备份和追溯，不作为日常入口 |

后续维护时，应避免同时编辑 `frontend/` 和 `migration/output/` 中的同一份内容。正式站点只读取 `frontend/`。

## 设计取舍

### 为什么使用 Hugo

- 部署简单，生成静态文件即可。
- 不需要数据库承载主要内容。
- Markdown 适合低频内容维护。
- 页面速度快，安全面小。
- 适合实验室主页这类展示型网站。

### 为什么还保留 Go 后端

纯静态站无法自己保存浏览量。浏览量又是用户明确希望保留的功能，所以保留一个很小的 API：

- 功能边界清楚。
- 不涉及内容管理。
- 只依赖 SQLite。
- 可以独立重启、备份和迁移。

### 为什么不做 CMS

CMS 会带来登录、权限、数据库、后台安全、备份恢复等维护成本。当前维护目标是“没有很多时间也能更新”，所以选择 Markdown 文件加静态构建。

## 安全与运维边界

建议生产环境：

- Nginx 暴露公网的 80/443。
- Go 后端只监听 `127.0.0.1`。
- SQLite 文件放到 `/var/lib/ise-quick/` 并定期备份。
- 服务器上不要暴露 `migration_exports/`、旧项目源码或临时导出文件。
- 内容更新前先本地构建，构建通过再上传。

## 当前已知限制

- 浏览量是简单计数，不做复杂去重。
- 媒体本地化仍需要后续逐步整理，`data/media-manifest.json` 记录了迁移时发现的媒体引用。
- 旧系统详情页 URL 没有做完整重定向，目前只保留了 `legacy-map.json`。
- `data/publications.json` 已迁移，但当前没有单独论文展示页。

## 推荐后续演进

优先级从高到低：

1. 正式部署前检查所有页面内容是否完整。
2. 整理本地化图片和附件，减少外链失效风险。
3. 建立固定部署流程，例如本地构建后 `rsync` 到服务器。
4. 为浏览量 SQLite 增加定期备份。
5. 如确实需要，再考虑论文页、搜索或轻量后台。
