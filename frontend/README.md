# ISE Quick Frontend

这是 ISE Quick 的 Hugo 前端。当前已经使用旧系统迁移出的真实内容，后续日常维护主要修改 Markdown、JSON 和图片附件；本目录不包含后端、CMS 或搜索实现。

## 目录结构

- `hugo.yaml`：Hugo 站点配置、站点参数和主导航。
- `themes/ise/`：自建 Hugo 主题。
- `themes/ise/layouts/_default/baseof.html`：全站 HTML 基础模板。
- `themes/ise/layouts/partials/`：页头、页脚、面包屑、左侧栏等公共片段。
- `themes/ise/layouts/index.html`：首页模板，包含轮播、新闻 5 条、学术活动 3 条、科研项目 4 条。
- `themes/ise/layouts/news/`：新闻列表页和详情页模板。
- `themes/ise/layouts/activities/`：学术活动列表页和详情页模板。
- `themes/ise/layouts/platform/`：科研项目列表页和详情页模板，URL 为 `/platform/`。
- `themes/ise/layouts/members/`：成员介绍列表页和详情页模板。
- `themes/ise/assets/css/main.css`：旧站视觉骨架样式。
- `static/images/legacy/`：从旧站复制来的视觉资产。
- `content/`：新闻、学术活动、成员介绍、科研项目、关于我们、诚聘英才等 Markdown 内容。
- `data/`：首页轮播、首页精选科研项目、专利/产出、论文、浏览量初始值等 JSON 数据。

## 内容维护方式

新闻、学术活动、科研项目、成员介绍均使用 Hugo section 维护：

```text
content/news/my-news.md
content/activities/my-activity.md
content/platform/my-platform.md
content/members/member-name.md
```

推荐 front matter：

```yaml
---
title: "标题"
date: 2026-06-14
summary: "摘要，可选"
draft: false
---
```

首页会自动读取：

- `content/news/` 最新 5 条。
- `content/activities/` 最新 3 条。
- `data/featured-projects.json` 精选科研项目 4 条。

首页轮播读取 `data/slides.json`；论文截图、长图等内容会用完整展示方式避免被裁切。

成员介绍推荐使用：

```yaml
role: "professor" # professor / associate_professor / phd / master
role_title: "教授"
research_direction: "智能软件工程" # 博士生、硕士生可选；缺省显示“方向待补充”
weight: 10
```

当前 `content/` 和 `data/` 已经是迁移后的正式内容源。后续不要编辑 `migration/output/`，除非你明确要重新做迁移实验。

详情页包含轻量浏览量 partial：页面输出 `data-view-path`，前端脚本默认 `POST /api/views`，由 `ise-quick/backend` 记录并返回 `total`。如部署时 API 路径不同，可在 `hugo.yaml` 的 `params.viewAPI` 中覆盖。

更完整的日常维护说明见 `../docs/content-maintenance-guide.md`，里面按“页面模块 -> 模板组件 -> 数据文件 -> 更新方式”整理了所有主要页面。

## 旧视觉约定

已固化的旧站基础视觉：

- 主色：`#63065f`
- 辅助蓝：`#2e6590`
- 页面容器：`1200px`
- 顶部：logo、实验室中文名、英文名、紫色导航
- 页脚：黑色背景、友情链接、版权和备案号
- 内页：左侧栏背景图和高亮状态

## 静态资产

复制自旧项目，原文件未移动：

- `static/favicon.ico`
- `static/favicon/nju.ico`
- `static/images/legacy/logo/`
- `static/images/legacy/home/`
- `static/images/legacy/ui/leftbar_bg.jpg`

## 本地预览

本地预览可在本目录执行：

```bash
hugo server
```
