# 内容维护指南

网站是 Hugo 静态网站，日常更新不需要启动后端服务。

## 维护原则

- 正式内容修改 `frontend/content/`。
- 首页和列表数据修改 `frontend/data/`。
- 新闻、项目、论文和成员图片放在对应 `index.md` 的同目录页面包；首页轮播放到 `frontend/static/images/slides/`。
- `migration/output/` 和 `migration_exports/` 只作为迁移记录。
- 修改内容后必须重新构建并上传 `public/`。

## 内容对应关系

| 内容 | 文件 |
| --- | --- |
| 新闻 | `frontend/content/news/<slug>/index.md` |
| 学术论文 | `frontend/content/activities/<slug>/index.md` |
| 成员 | `frontend/content/members/<slug>/index.md` |
| 科研项目 | `frontend/content/platform/<slug>/index.md` |
| 关于我们 | `frontend/content/about/_index.md` |
| 招聘 | `frontend/content/jobs/_index.md` |
| 首页轮播 | `frontend/data/slides.json` |
| 首页精选项目 | `frontend/data/featured-projects.json` |
| 专利/科研产出 | `frontend/data/projects.json` |
| 站点名称和导航 | `frontend/hugo.yaml` |

## 新闻

目录：

```text
frontend/content/news/my-news/index.md
```

示例：

```yaml
---
title: "新闻标题"
date: 2026-07-18
summary: "列表摘要"
draft: false
---

新闻正文。
```

首页会自动显示按日期倒序排列的最新 5 条新闻。

## 学术论文

论文放在：

```text
frontend/content/activities/my-paper/index.md
```

示例：

```yaml
---
content_kind: "publication"
title: "论文标题"
publication_year: "2026"
venue: "会议或期刊"
image: "paper-preview.png" # 可选；与 index.md 同目录
authors:
  - name: "作者姓名"
    member_url: "/members/member-38/"
raw_citation: "完整引用"
draft: false
---
```

论文正文图片也放在本目录，并使用相对路径，例如 `![实验结果](figure-1.png)`。作者图片不在论文中重复保存，只通过 `member_url` 关联成员页面。

设置 `content_kind: "publication"` 后，论文会进入论文列表和首页论文区域。

## 成员

示例：

```yaml
---
title: "姓名"
role: "博士生"
role_title: "博士生"
avatar: "avatar.jpg" # 与 index.md 同目录
research_direction: "智能驾驶与测试"
student_label: "博士生"
weight: 10
draft: false
---
```

教师和学生会根据 `role`、`research_direction` 和 `weight` 分组、排序。

## 科研项目

项目正文放在：

```text
frontend/content/platform/
```

只有存在真实项目图片时才添加 `image` 字段；没有图片的项目不要使用实验室 Logo 或通用占位图。迁移器会自动忽略旧站的 `*ise.jpg` 通用单位图。

首页精选项目修改：

```text
frontend/data/featured-projects.json
```

专利和科研产出修改：

```text
frontend/data/projects.json
```

## 首页轮播

```json
[
  {
    "image": "/images/lab/slides/banner-01.png",
    "fit": "contain",
    "url": "",
    "title": "可选标题",
    "summary": "可选摘要"
  }
]
```

## 图片

页面图片使用相对文件名，实际文件和页面的 `index.md` 放在一起；Hugo 会将它们发布到对应页面目录。轮播 JSON 使用 `/images/slides/...`，文件位于 `frontend/static/images/slides/`。不要在正式网站依赖旧站 HTTP 图片地址。

## 本地预览和发布

```bash
cd frontend
hugo server
```

构建：

```bash
cd frontend
hugo --panicOnWarning --minify \
  --destination /private/tmp/ise-quick-public \
  --cleanDestinationDir
```

上传：

```bash
rsync -az --delete \
  /private/tmp/ise-quick-public/ \
  user@your-server:/var/www/ise-quick/public/
```

## 发布前检查

- 页面标题和日期正确。
- 论文设置了 `content_kind: "publication"`。
- 图片路径可以访问。
- `draft: false`。
- Hugo 构建没有报错。
- 首页、新闻、论文、成员和科研项目页面都能打开。
