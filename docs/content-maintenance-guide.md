# ISE Quick 内容维护手册

这份文档给后期维护者使用，目标是：不理解 Hugo、Go、旧系统代码也能知道“我想改某个页面上的内容，应该改哪个文件”。

当前项目分为三块：

- `frontend/`：Hugo 静态站点，负责页面、布局、主题、Markdown 内容。
- `backend/`：轻量浏览量 API，负责记录和返回浏览量。
- `migration/`：旧系统数据迁移工具，负责把旧接口导出的数据转换成 Hugo 能读的 Markdown 和 JSON。

## 最重要的规则

后期日常更新，优先只改内容文件：

- 新闻、学术活动、成员、科研项目正文：改 `frontend/content/` 下的 Markdown。
- 首页轮播、首页精选科研项目、专利/产出列表：改 `frontend/data/` 下的数据文件。
- 浏览量：运行后由后端数据库记录，一般不要手动改 Markdown 里的浏览量。
- 页面布局、颜色、卡片样式：在 `frontend/themes/ise/`，除非要改设计，否则不要碰。

当前正式维护入口是：

- `frontend/content/`：迁移后的真实 Markdown 内容，也是后续新闻、活动、成员、科研项目等内容的维护入口。
- `frontend/data/`：迁移后的真实 JSON 数据，也是后续首页轮播、首页精选项目、专利/产出等数据的维护入口。

`migration/output/content/` 和 `migration/output/data/` 是旧系统迁移过程留下的输出记录，当前只作为备份和追溯来源。上线后不要随意重新跑迁移覆盖 `frontend/content/` 或 `frontend/data/`，否则可能覆盖你手动更新的内容。

## 页面与数据对应表

| 页面 / 模块 | 用户看到的内容 | 模板 / 组件 | 数据来源 | 日常怎么更新 |
| --- | --- | --- | --- | --- |
| 全站页头 | Logo、实验室中文名、英文名、导航菜单 | `frontend/themes/ise/layouts/partials/header.html` | `frontend/hugo.yaml` | 改 `params.labName`、`params.labNameEn`、`menus.main` |
| 全站页脚 | 版权、备案、友情链接区域 | `frontend/themes/ise/layouts/partials/footer.html` | `frontend/hugo.yaml`，部分模板固定文案 | 常规改 `params.footerCopyright`、`params.icpText`、`params.icpURL` |
| 首页轮播 | 首页最上方大图、左右箭头、小圆点、可选跳转 | `frontend/themes/ise/layouts/index.html`，`assets/js/carousel.js` | `frontend/data/slides.json` | 改 `data/slides.json`，图片放到 `static/` 或内容目录 |
| 首页新闻资讯 | 首页“新闻资讯”最新 5 条 | `index.html` 中的 news preview | `frontend/content/news/` | 新增或修改新闻 Markdown，按 `date` 自动排序 |
| 首页学术活动 | 首页“学术活动”最新 3 条 | `index.html` 中的 activity list | `frontend/content/activities/` | 新增或修改活动 Markdown，按 `date` 自动排序 |
| 首页科研项目 | 首页右下“科研项目”精选 4 条 | `index.html` 中的 platform list | `frontend/data/featured-projects.json` | 改精选项目 JSON，`url` 指向 `/platform/.../` |
| 新闻资讯列表页 | `/news/` 全部新闻列表 | `layouts/news/list.html`，`partials/section-list.html` | `frontend/content/news/` | 新增、删除、修改新闻 Markdown |
| 新闻资讯详情页 | `/news/<slug>/` 新闻正文、日期、浏览量 | `layouts/news/single.html` | 某篇新闻 Markdown + 浏览量 API | 改对应 Markdown；浏览量由后端记录 |
| 学术活动列表页 | `/activities/` 全部活动列表 | `layouts/activities/list.html`，`partials/section-list.html` | `frontend/content/activities/` | 新增、删除、修改活动 Markdown |
| 学术活动详情页 | `/activities/<slug>/` 活动正文、日期、浏览量 | `layouts/activities/single.html` | 某篇活动 Markdown + 浏览量 API | 改对应 Markdown；浏览量由后端记录 |
| 成员介绍列表页 | 教授、副教授、博士生/硕士生方向分组 | `layouts/members/list.html`，`member-card.html`，`student-member-card.html` | `frontend/content/members/` | 改成员 Markdown 的 `role`、`research_direction`、`weight` |
| 成员详情页 | 个人头像、职称、方向、简介正文 | `layouts/members/single.html` | 某个成员 Markdown | 改对应成员 Markdown |
| 科研项目页上半部分 | “项目与平台”列表 | `layouts/platform/list.html`，`partials/research-projects.html` | `frontend/content/platform/` | 新增或修改平台/项目 Markdown |
| 科研项目页下半部分 | “专利 / 产出”列表 | `partials/research-projects.html` | `frontend/data/projects.json` | 改 JSON 中的产出条目 |
| 关于我们 | `/about/` 页面正文 | 默认页面模板 | `frontend/content/about/_index.md` | 改该 Markdown |
| 诚聘英才 | `/jobs/` 页面正文 | 默认页面模板 | `frontend/content/jobs/_index.md` | 改该 Markdown |
| 浏览量 | 详情页“浏览量：xx” | `partials/view-counter.html`，`assets/js/view-counter.js` | Go 后端 + SQLite | 启动后端；不需要改前端内容 |

## 按页面从上到下对照维护

这一节按用户实际看到的页面顺序写。你可以打开网页，从上往下看，看到哪个区域就对照下面的“维护文件”和“可改内容”。

说明：

- “模板/组件”通常不要改，除非你要调整布局或样式。
- “维护文件”才是日常应该编辑的位置。
- 所有路径都以 `ise-quick/` 为项目根目录。

### 全站公共区域

这些区域会出现在大多数页面上。

| 从上到下 | 用户看到的区域 | 模板/组件 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 顶部 Logo 和实验室中英文名 | `frontend/themes/ise/layouts/partials/header.html` | `frontend/hugo.yaml`，`frontend/static/images/legacy/logo/ise_logo.png` | `params.labName`、`params.labNameEn`、Logo 图片 |
| 2 | 紫色主导航 | `partials/header.html` | `frontend/hugo.yaml` | `menus.main` 中的导航名称、URL、顺序 `weight` |
| 3 | 内页面包屑，例如 `首页 / 新闻资讯` | `frontend/themes/ise/layouts/partials/breadcrumb.html` | 通常不用手动改 | 由页面标题和层级自动生成 |
| 4 | 内页左侧紫色标题栏 | `frontend/themes/ise/layouts/partials/leftbar.html` | 各页面模板或 section `_index.md` | 通常不用改；如果标题不对，先看对应 `_index.md` 的 `title` |
| 5 | 页脚友情链接、版权、备案号 | `frontend/themes/ise/layouts/partials/footer.html` | `frontend/hugo.yaml`，必要时改 `footer.html` | `params.footerCopyright`、`params.icpText`、`params.icpURL`；友情链接目前写在模板里 |

如果只是日常更新内容，通常从第 3 步开始的公共结构都不需要改。

### 首页 `/`

首页模板：

```text
frontend/themes/ise/layouts/index.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | `home-hero` 首页轮播 | 大图、左右箭头、下方圆点、可选点击跳转 | `frontend/data/slides.json` | 轮播图顺序、图片、跳转 URL、显示方式 `fit`、可选标题/摘要 |
| 2 | `home-section` 新闻资讯 | 标题“新闻资讯”、左侧图片、右侧最新 5 条新闻 | `frontend/content/news/`；新闻图片在模板中固定为 `/images/legacy/home/news-1.jpg` | 新增/修改新闻 Markdown；更换首页新闻配图需要改模板或替换对应图片 |
| 3 | `home-grid` 左栏学术活动 | 最新 3 条活动，左侧日期块 | `frontend/content/activities/` | 新增/修改活动 Markdown，按日期影响首页显示 |
| 4 | `home-grid` 右栏科研项目 | 精选 4 条科研项目，带“国家重点研发计划/国家自然科学基金”等标签 | `frontend/data/featured-projects.json` | 首页精选项目标题和跳转地址 |
| 5 | 页脚 | 友情链接、版权、备案 | `frontend/hugo.yaml` | 页脚文字和备案链接 |

首页自动读取规则：

- 新闻：从 `content/news/` 取最新 5 条。
- 学术活动：从 `content/activities/` 取最新 3 条。
- 科研项目：从 `data/featured-projects.json` 取前 4 条。
- 轮播：按 `data/slides.json` 数组顺序展示。

### 新闻资讯列表页 `/news/`

模板：

```text
frontend/themes/ise/layouts/news/list.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 新闻资讯` | 自动生成 | 一般不改 |
| 2 | 左侧栏 | 紫色块“新闻资讯” | 模板固定传入“新闻资讯” | 一般不改 |
| 3 | 主标题 | 页面标题“新闻资讯” | `frontend/content/news/_index.md` | `title` |
| 4 | `section-list` 新闻列表 | 每条新闻的标题、日期、摘要 | `frontend/content/news/*/index.md` | `title`、`date`、`summary`、正文开头 |

新增新闻时，优先新建：

```text
frontend/content/news/英文短名/index.md
```

### 新闻详情页 `/news/<slug>/`

模板：

```text
frontend/themes/ise/layouts/news/single.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 新闻资讯 / 当前新闻标题` | 自动生成 | 由新闻 `title` 决定 |
| 2 | 左侧栏 | 紫色块“新闻资讯” | 模板固定 | 一般不改 |
| 3 | 详情标题 | 新闻标题 | 对应新闻 `index.md` | `title` |
| 4 | 日期 | `YYYY-MM-DD` | 对应新闻 `index.md` | `date` |
| 5 | 浏览量 | `浏览量：xx` | Go 后端 SQLite；前端 `params.viewAPI` | 不手动改，确保后端运行 |
| 6 | 正文区 `article__body` | 新闻正文、图片、表格、链接 | 对应新闻 `index.md` 和同目录图片 | Markdown 正文、图片、附件链接 |

### 学术活动列表页 `/activities/`

模板：

```text
frontend/themes/ise/layouts/activities/list.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 学术活动` | 自动生成 | 一般不改 |
| 2 | 左侧栏 | 紫色块“学术活动” | 模板固定传入“学术活动” | 一般不改 |
| 3 | 主标题 | 页面标题“学术活动” | `frontend/content/activities/_index.md` | `title` |
| 4 | `section-list` 活动列表 | 每条活动的标题、日期、摘要 | `frontend/content/activities/*/index.md` | `title`、`date`、`summary` |

### 学术活动详情页 `/activities/<slug>/`

模板：

```text
frontend/themes/ise/layouts/activities/single.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 学术活动 / 当前活动标题` | 自动生成 | 由活动 `title` 决定 |
| 2 | 左侧栏 | 紫色块“学术活动” | 模板固定 | 一般不改 |
| 3 | 详情标题 | 活动标题 | 对应活动 `index.md` | `title` |
| 4 | 日期 | 页面日期 | 对应活动 `index.md` | `date` |
| 5 | 浏览量 | `浏览量：xx` | Go 后端 SQLite | 不手动改 |
| 6 | 正文区 | 活动正文、报告人、地点、图片等 | 对应活动 `index.md` | Markdown 正文；`event_time`、`location`、`speaker` 可写在 front matter 或正文 |

### 成员介绍列表页 `/members/`

模板：

```text
frontend/themes/ise/layouts/members/list.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 成员介绍` | 自动生成 | 一般不改 |
| 2 | 左侧栏 | 紫色块“成员介绍” | 模板固定传入“成员介绍” | 一般不改 |
| 3 | 主标题和说明 | `成员介绍` 及可选介绍文字 | `frontend/content/members/_index.md` | `title` 和正文说明 |
| 4 | 教授区 | 教授头像卡片、姓名、职称、方向、摘要 | `frontend/content/members/*/index.md` | `role: "professor"`、`role_title`、`avatar`、`research_direction`、`weight`、正文摘要 |
| 5 | 副教授区 | 副教授头像卡片、姓名、职称、方向、摘要 | `frontend/content/members/*/index.md` | `role: "associate_professor"` 及同上字段 |
| 6 | 博士生/硕士生方向一 | 智能化软件测试与质量保障分组头像网格 | 成员 Markdown | `role`、`student_label`、`avatar`、`research_direction: "智能化软件测试与质量保障"`、`weight` |
| 7 | 博士生/硕士生方向二 | 智能驾驶与测试分组头像网格 | 成员 Markdown | `research_direction: "智能驾驶与测试"` |
| 8 | 博士生/硕士生方向三 | 软件维护与程序自动化修复分组头像网格 | 成员 Markdown | `research_direction: "软件维护与程序自动化修复"` |
| 9 | 方向待补充 | 没有方向的博士/硕士 | 成员 Markdown | 给成员补上准确 `research_direction` 即可移入对应方向 |

成员排序：

- `weight` 越小越靠前。
- 学生必须同时满足 `role` 是 `phd`/`master` 类值，并且 `research_direction` 和方向名称完全一致，才会进入对应方向。

如果要新增第四个方向，需要改模板中的 `$studentDirections`，位置：

```text
frontend/themes/ise/layouts/members/list.html
```

### 成员详情页 `/members/<slug>/`

模板：

```text
frontend/themes/ise/layouts/members/single.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 成员介绍 / 成员姓名` | 自动生成 | 由成员 `title` 决定 |
| 2 | 左侧栏 | 紫色块“成员介绍” | 模板固定 | 一般不改 |
| 3 | 成员姓名 | 详情页标题 | 对应成员 `index.md` | `title` |
| 4 | 身份/职称 | 例如“教授”“24级博士生” | 对应成员 `index.md` | `role_title`，学生卡片另用 `student_label` |
| 5 | 浏览量 | `浏览量：xx` | Go 后端 SQLite | 不手动改 |
| 6 | 正文区 | 个人简介、研究方向、论文主页等 | 对应成员 `index.md` | Markdown 正文和图片/链接 |

### 科研项目列表页 `/platform/`

模板：

```text
frontend/themes/ise/layouts/platform/list.html
frontend/themes/ise/layouts/partials/research-projects.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 科研项目` | 自动生成 | 一般不改 |
| 2 | 左侧栏 | 紫色块“科研项目” | 模板固定传入“科研项目” | 一般不改 |
| 3 | 主标题 | `科研项目` | `frontend/content/platform/_index.md` | `title` |
| 4 | `项目与平台` | 项目/平台列表，显示标题、日期、摘要 | `frontend/content/platform/*/index.md` | 每个项目的 `title`、`date`、`summary`、正文 |
| 5 | `专利 / 产出` | 专利或成果列表 | `frontend/data/projects.json` | `english` 主标题、`chinese` 作者/编号/说明 |

如果某个项目要出现在首页“科研项目”模块，还要同步维护：

```text
frontend/data/featured-projects.json
```

### 科研项目详情页 `/platform/<slug>/`

模板：

```text
frontend/themes/ise/layouts/platform/single.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 科研项目 / 项目标题` | 自动生成 | 由项目 `title` 决定 |
| 2 | 左侧栏 | 紫色块“科研项目” | 模板固定 | 一般不改 |
| 3 | 项目标题 | 详情页标题 | 对应项目 `index.md` | `title` |
| 4 | 日期 | 项目日期 | 对应项目 `index.md` | `date` |
| 5 | 浏览量 | `浏览量：xx` | Go 后端 SQLite | 不手动改 |
| 6 | 正文区 | 项目介绍、周期、合作单位、图片等 | 对应项目 `index.md` | Markdown 正文 |

### 关于我们 `/about/`

模板：

```text
frontend/themes/ise/layouts/_default/list.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 关于我们` | 自动生成 | 一般不改 |
| 2 | 左侧栏 | 紫色块“关于我们” | 默认模板读取页面标题 | `frontend/content/about/_index.md` 的 `title` |
| 3 | 主标题 | `关于我们` | `frontend/content/about/_index.md` | `title` |
| 4 | 正文区 | 实验室介绍文字 | `frontend/content/about/_index.md` | Markdown 或保留 HTML 的正文 |

### 诚聘英才 `/jobs/`

模板：

```text
frontend/themes/ise/layouts/_default/list.html
```

从上到下：

| 顺序 | 页面容器/模块 | 用户看到什么 | 维护文件 | 可改内容 |
| --- | --- | --- | --- | --- |
| 1 | 面包屑 | `首页 / 诚聘英才` | 自动生成 | 一般不改 |
| 2 | 左侧栏 | 紫色块“诚聘英才” | 默认模板读取页面标题 | `frontend/content/jobs/_index.md` 的 `title` |
| 3 | 主标题 | `诚聘英才` | `frontend/content/jobs/_index.md` | `title` |
| 4 | 正文区 | 招聘说明、岗位、联系方式 | `frontend/content/jobs/_index.md` | Markdown 正文 |

### 兼容页 `/projects/`

`/projects/` 不在主导航显示，主要用于兼容旧结构。它渲染的内容和 `/platform/` 相同，也就是“项目与平台 + 专利 / 产出”。日常维护仍然改：

```text
frontend/content/platform/
frontend/data/projects.json
```

## 推荐的内容目录形态

Hugo 支持两种写法：

```text
content/news/example.md
content/news/example/index.md
```

如果这篇内容有图片，推荐使用第二种“页面文件夹”：

```text
content/news/2026-award/
  index.md
  cover.jpg
  group-photo.png
```

这样正文里可以直接写：

```md
![会议现场](group-photo.png)
```

图片和文章放在同一个文件夹里，后期复制、删除、迁移都更清楚。

## Markdown 基本格式

每篇内容顶部都有一段 `---` 包起来的元数据，叫 front matter。下面是最常用字段：

```yaml
---
title: "标题"
date: 2026-06-14
summary: "列表页和首页可显示的摘要，可选"
draft: false
views_seed: 0
---
```

字段说明：

- `title`：页面标题，也是列表里的标题。
- `date`：排序用日期，格式建议固定为 `YYYY-MM-DD`。
- `summary`：摘要；不填时 Hugo 会从正文截取。
- `draft`：是否草稿。`true` 表示默认不发布。
- `views_seed`：旧站迁移时的初始浏览量；新文章通常填 `0` 或不填。

正文写在 front matter 下面，普通 Markdown 即可：

```md
这里是正文。

## 小标题

- 列表项一
- 列表项二

[外部链接](https://example.com)
```

复杂表格、旧站迁移过来的复杂图片排版，可以继续保留 HTML。当前 Hugo 配置允许 Markdown 中出现 HTML。

## 首页维护

首页模板是：

```text
frontend/themes/ise/layouts/index.html
```

日常不要直接改模板，除非要改布局。首页内容来自下面这些地方。

### 首页轮播

维护文件：

```text
frontend/data/slides.json
```

JSON 示例：

```json
[
  {
    "image": "/images/legacy/home/01.jpg",
    "alt": "实验室活动",
    "url": "/news/example/",
    "fit": "cover",
    "title": "",
    "summary": ""
  },
  {
    "image": "/images/uploads/paper-demo.png",
    "alt": "论文成果",
    "url": "",
    "fit": "contain"
  }
]
```

字段说明：

- `image`：图片路径。以 `/` 开头表示从网站根目录找，例如 `/images/uploads/a.jpg`。
- `alt`：图片替代文字，建议填写。
- `url`：点击轮播后跳转的地址；不需要跳转就留空。
- `fit`：图片显示方式。普通照片用 `cover` 或不填；论文截图、长图用 `contain`，避免被裁切。
- `title`、`summary`：轮播图上的文字说明。当前你要求删除默认“南京大学智能软件工程实验室”，所以这两个为空时不会显示文字层。

图片建议放在：

```text
frontend/static/images/uploads/
```

访问路径写成：

```text
/images/uploads/文件名.jpg
```

### 首页新闻资讯

首页自动读取最新 5 条新闻：

```text
frontend/content/news/
```

排序依据是 Markdown 里的 `date`，日期越新越靠前。

### 首页学术活动

首页自动读取最新 3 条学术活动：

```text
frontend/content/activities/
```

同样按 `date` 倒序排列。

### 首页科研项目

首页展示 4 条精选科研项目，维护文件：

```text
frontend/data/featured-projects.json
```

示例：

```json
[
  {
    "title": "国家重点研发计划：面向信息产品与技术服务的集成化众包测试服务平台研发与应用",
    "url": "/platform/national-key-r-d-program-of-china-r-d-and-application-of-integrated-crowdsourcing-test-service-platform-for-information-products-and-technology-services-2018yfb1403400-2019-2021-2018yfb1403400-2019-2021/"
  }
]
```

`title` 里包含“国家重点研发计划”或“国家自然科学基金”时，首页会自动显示对应标签。`url` 应该指向某个 `content/platform/` 生成出来的详情页。

## 新闻资讯

列表页地址：

```text
/news/
```

内容目录：

```text
frontend/content/news/
```

新增一篇新闻，推荐这样建：

```text
frontend/content/news/2026-lab-award/index.md
frontend/content/news/2026-lab-award/photo.jpg
```

`index.md` 示例：

```md
---
title: "实验室论文获得最佳论文奖"
date: 2026-06-14
summary: "实验室在某某会议上获得最佳论文奖。"
draft: false
views_seed: 0
---

近日，南京大学智能软件工程实验室在某某会议上取得新进展。

![现场照片](photo.jpg)
```

注意事项：

- 文件夹名建议用英文、小写、短横线，例如 `2026-lab-award`。
- `date` 会影响首页和列表页排序。
- 删除新闻时，删除对应文件或文件夹即可。
- 暂时隐藏新闻时，把 `draft` 改成 `true`。

## 学术活动

列表页地址：

```text
/activities/
```

内容目录：

```text
frontend/content/activities/
```

新增一个活动：

```text
frontend/content/activities/2026-guest-talk/index.md
```

示例：

```md
---
title: "学术报告：智能软件测试的新趋势"
date: 2026-06-14
summary: "本次报告介绍智能软件测试方向的最新研究进展。"
event_time: "2026-06-18 14:00"
location: "南京大学软件学院"
speaker: "张三 教授"
draft: false
views_seed: 0
---

报告内容简介写在这里。
```

当前列表页主要显示 `title`、`date`、`summary`。`event_time`、`location`、`speaker` 可以先写在 front matter 或正文中，后续如果你希望页面固定展示这些字段，再调整详情页模板即可。

## 成员介绍

列表页地址：

```text
/members/
```

内容目录：

```text
frontend/content/members/
```

列表页现在分为：

- 教授
- 副教授
- 博士生 / 硕士生，按研究方向分组

学生方向目前固定为：

- 智能化软件测试与质量保障
- 智能驾驶与测试
- 软件维护与程序自动化修复

新增一个成员，推荐：

```text
frontend/content/members/yu-shengcheng/index.md
frontend/content/members/yu-shengcheng/avatar.jpg
```

教师示例：

```md
---
title: "教师姓名"
date: 2026-06-14
role: "professor"
role_title: "教授"
avatar: "avatar.jpg"
research_direction: "智能软件工程"
weight: 10
email: "name@example.com"
draft: false
---

这里写个人简介、研究方向、论文主页等。
```

学生示例：

```md
---
title: "学生姓名"
date: 2026-06-14
role: "phd"
role_title: "博士生"
student_label: "24级博士生"
avatar: "avatar.jpg"
research_direction: "智能化软件测试与质量保障"
weight: 20
draft: false
---

这里写个人简介。
```

字段说明：

- `role`：控制分组。可用值建议为 `professor`、`associate_professor`、`phd`、`master`。
- `role_title`：页面上显示的职称或身份，例如 `教授`、`副教授`、`博士生`。
- `student_label`：学生卡片下方的小字，例如 `24级博士生`、`23级硕士生`。
- `avatar`：本地头像路径。页面文件夹写法下，直接写 `avatar.jpg`。
- `avatar_url`：远程头像地址。如果本地化了图片，优先用 `avatar`。
- `research_direction`：学生按这个字段分组。必须和上面三个方向名称完全一致，才会进入对应方向。
- `weight`：排序权重，数字越小越靠前。

如果新增第四个研究方向，只改 Markdown 还不够，需要修改：

```text
frontend/themes/ise/layouts/members/list.html
```

在 `$studentDirections` 中加入新方向。这个属于轻量模板改动。

## 科研项目

页面地址：

```text
/platform/
```

这个页面合并了两类内容：

- 上半部分“项目与平台”：来自 `frontend/content/platform/`。
- 下半部分“专利 / 产出”：来自 `frontend/data/projects.json`。

### 添加项目与平台

内容目录：

```text
frontend/content/platform/
```

新增项目：

```text
frontend/content/platform/2026-key-project/index.md
```

示例：

```md
---
title: "国家重点研发计划：智能软件质量保障关键技术研究"
date: 2026-06-14
summary: "项目围绕智能软件质量保障开展关键技术研究。"
creator: "南京大学智能软件工程实验室"
draft: false
views_seed: 0
---

这里写项目介绍、研究内容、合作单位、项目周期等。
```

这个条目会出现在 `/platform/` 的“项目与平台”列表里。详情页地址由文件夹名决定，例如：

```text
/platform/2026-key-project/
```

如果想让它出现在首页“科研项目”精选里，还需要同步改：

```text
frontend/data/featured-projects.json
```

### 添加专利 / 产出

维护文件：

```text
frontend/data/projects.json
```

当前字段沿用了旧系统命名，语义略别扭：

- `english`：页面上加粗显示的主标题，当前可放专利或产出名称。
- `chinese`：标题下面的小字，当前可放作者、编号、说明。

示例：

```json
[
  {
    "english": "一种基于语法规则的深度神经网络自动生成方法（202111471925.0）",
    "chinese": "南京大学智能软件工程实验室"
  }
]
```

JSON 注意事项：

- 字符串必须用英文双引号。
- 每个对象之间用英文逗号分隔。
- 最后一项后面不要多写逗号。

## 关于我们

页面地址：

```text
/about/
```

维护文件：

```text
frontend/content/about/_index.md
```

示例：

```md
---
title: "关于我们"
date: 2026-06-14
draft: false
---

这里写实验室介绍、研究方向、师资队伍、平台基础等。
```

## 诚聘英才

页面地址：

```text
/jobs/
```

维护文件：

```text
frontend/content/jobs/_index.md
```

示例：

```md
---
title: "诚聘英才"
date: 2026-06-14
draft: false
---

这里写招聘方向、岗位要求、联系方式等。
```

## 浏览量

浏览量由两部分组成：

- 前端：`frontend/themes/ise/layouts/partials/view-counter.html` 和 `assets/js/view-counter.js`。
- 后端：`backend/` 下的 Go 服务，使用 SQLite 保存浏览量。

详情页会自动向接口请求：

```text
POST /api/views
```

部署时，前端接口地址在这里配置：

```yaml
params:
  viewAPI: "/api/views"
```

文件位置：

```text
frontend/hugo.yaml
```

本地启动后端示例：

```bash
cd ise-quick/backend
VIEW_COUNTER_DB=./views.db \
VIEW_COUNTER_SEED_FILE=../frontend/data/views-seed.json \
ADDR=127.0.0.1:18080 \
go run .
```

说明：

- `VIEW_COUNTER_DB`：SQLite 数据库文件位置。
- `VIEW_COUNTER_SEED_FILE`：旧站浏览量初始值，只在初始化时有用。
- `ADDR`：后端监听地址。

新文章不需要手动分配浏览量。页面第一次被访问时，后端会开始记录。

## 图片和附件怎么放

推荐规则：

- 和某篇文章强相关的图片，放在文章自己的文件夹里。
- 全站通用图片，放在 `frontend/static/images/uploads/`。
- PDF、PPT、附件可以放在 `frontend/static/files/`，正文里用链接引用。

文章图片示例：

```text
frontend/content/news/2026-award/
  index.md
  photo.jpg
```

正文引用：

```md
![获奖现场](photo.jpg)
```

全站图片示例：

```text
frontend/static/images/uploads/banner-2026.jpg
```

数据文件或 Markdown 中引用：

```text
/images/uploads/banner-2026.jpg
```

附件示例：

```text
frontend/static/files/recruitment.pdf
```

正文引用：

```md
[下载招聘 PDF](/files/recruitment.pdf)
```

真正的外部跳转链接，例如学校官网、论文 DOI、GitHub 项目地址，不需要本地化，保留原 URL 即可。

## 常见更新任务

### 发布一篇新闻

1. 在 `frontend/content/news/` 下新建一个英文文件夹。
2. 在文件夹里创建 `index.md`。
3. 写好 `title`、`date`、`summary`、正文。
4. 图片放在同一文件夹，正文用相对路径引用。
5. 本地运行 Hugo 检查页面。

### 发布一个学术活动

1. 在 `frontend/content/activities/` 下新建文件夹。
2. 创建 `index.md`。
3. 填写 `title`、`date`、`summary`、`event_time`、`location`。
4. 正文写报告介绍、嘉宾介绍、参会方式。

### 修改首页轮播

1. 把图片放到 `frontend/static/images/uploads/`。
2. 修改 `frontend/data/slides.json`。
3. 普通照片使用 `fit: "cover"` 或不填。
4. 论文截图、长图使用 `fit: "contain"`。
5. 如果不想显示文字，把 `title` 和 `summary` 留空。

### 新增成员

1. 在 `frontend/content/members/` 下新建成员文件夹。
2. 放入 `index.md` 和头像图片。
3. 教师设置 `role: "professor"` 或 `role: "associate_professor"`。
4. 学生设置 `role: "phd"` 或 `role: "master"`。
5. 学生填写准确的 `research_direction`。
6. 用 `weight` 调整排序。

### 新增科研项目

1. 在 `frontend/content/platform/` 下新建项目文件夹。
2. 创建 `index.md`，填写项目标题、日期、摘要、正文。
3. 如果要在首页展示，同步修改 `frontend/data/featured-projects.json`。

### 新增专利或产出

1. 打开 `frontend/data/projects.json`。
2. 在数组中新增一项。
3. `english` 写产出标题，`chinese` 写作者、编号或说明。
4. 保存后运行 Hugo 检查 JSON 是否有效。

### 临时隐藏某篇内容

把 Markdown 顶部改成：

```yaml
draft: true
```

默认构建不会发布草稿。

## 本地预览和检查

真实内容已经在 `frontend/content/` 和 `frontend/data/` 中，日常预览最简单：

```bash
cd ise-quick/frontend
hugo server
```

然后浏览器打开 Hugo 输出的本地地址，通常是：

```text
http://localhost:1313/
```

正式构建前建议运行：

```bash
cd ise-quick/frontend
hugo --panicOnWarning
```

如果你只改了 Markdown 或 JSON，一般只需要跑 Hugo 构建检查。若改了后端浏览量逻辑，再运行：

```bash
cd ise-quick/backend
go test ./...
```

若改了迁移脚本，再运行：

```bash
cd ise-quick/migration
../../.venv/bin/python -m pytest tests
```

## 迁移输出的定位

当前前端已经使用迁移后的真实数据：

```text
ise-quick/frontend/content/
ise-quick/frontend/data/
```

迁移输出仍保留在：

```text
ise-quick/migration/output/content/
ise-quick/migration/output/data/
```

它们的作用是备份、追溯和必要时重新生成，不是日常维护入口。

- 日常只维护 `frontend/content/` 和 `frontend/data/`。
- `migration/output/` 只作为迁移记录，不再作为手动编辑入口。
- 如果重新跑迁移，先备份 `frontend/content/` 和 `frontend/data/`，避免覆盖人工修改。

## 哪些文件通常不要改

除非你明确要改页面设计或功能，否则不要频繁修改：

- `frontend/themes/ise/layouts/`：页面模板。
- `frontend/themes/ise/assets/css/main.css`：主题样式。
- `frontend/themes/ise/assets/js/`：轮播、浏览量脚本。
- `backend/`：浏览量 API。
- `migration/`：旧数据迁移逻辑。

日常维护的理想状态是：只改 Markdown、JSON 和图片附件。

## 出问题时先看这里

轮播图不显示：

- 检查 `data/slides.json` 里 `image` 路径是否正确。
- 如果图片在 `static/images/uploads/a.jpg`，路径应写 `/images/uploads/a.jpg`。
- 检查 JSON 逗号和双引号是否正确。

新闻或活动没有出现在首页：

- 检查 Markdown 是否在正确目录。
- 检查 `draft` 是否为 `true`。
- 检查 `date` 是否太旧。首页只显示最新几条。

学生没有进入指定方向：

- 检查 `role` 是否是 `phd` 或 `master`。
- 检查 `research_direction` 是否和模板里的方向名称完全一致。

科研项目详情能打开，但首页没有：

- `/platform/` 页面来自 `content/platform/`。
- 首页精选来自 `data/featured-projects.json`。
- 两者需要分别维护。

浏览量一直是 `--`：

- 检查后端是否启动。
- 检查 `frontend/hugo.yaml` 里的 `params.viewAPI` 是否能访问。
- 检查部署环境是否把 `/api/views` 转发到 Go 后端。

Hugo 构建失败：

- 优先检查最近改过的 JSON 是否有多余逗号。
- 检查 Markdown front matter 的 `---` 是否成对。
- 检查日期格式是否是 `YYYY-MM-DD`。
