# ISE Quick 项目架构

ISE Quick 是南京大学智能软件工程实验室官网的 Hugo 静态重构版本。

## 设计目标

- 保留现有实验室网站的视觉风格。
- 论文、新闻、成员和项目通过 Markdown/JSON 快速更新。
- 构建结果是纯静态文件，便于部署和备份。
- 不引入 CMS、搜索、动态后端或数据库。

## 运行时架构

```text
浏览器
  ↓ HTTPS
Nginx
  ↓
Hugo 生成的 public/
```

网站运行时不需要 Go、SQLite 或 systemd 服务。

## 目录职责

```text
frontend/
  hugo.yaml       网站配置
  content/        页面内容
  data/           首页和列表数据
  static/         图片、Logo、favicon
  themes/ise/     模板、CSS、JS

migration/
  旧系统 JSON 到 Hugo 内容的转换工具

docs/
  架构、维护、部署和验收说明
```

## 页面和数据流

| 页面 | 地址 | 数据源 |
| --- | --- | --- |
| 首页 | `/` | `data/slides.json`、新闻、论文、精选项目 |
| 新闻 | `/news/` | `content/news/` |
| 学术论文 | `/activities/` | `content/activities/` |
| 成员 | `/members/` | `content/members/` |
| 科研项目 | `/platform/` | `content/platform/`、`data/projects.json` |
| 关于我们 | `/about/` | `content/about/_index.md` |
| 招聘 | `/jobs/` | `content/jobs/_index.md` |

## 构建和发布

```text
修改 Markdown / JSON / 图片
        ↓
hugo server 本地预览
        ↓
hugo --minify 构建
        ↓
rsync 上传 public/
        ↓
Nginx 托管
```

## 主题

`themes/ise/` 保留网站的主要视觉：

- 紫色主色和蓝色辅助色。
- 1200px 页面容器。
- 页头、导航、面包屑、页脚。
- 首页轮播和滚动进入动画。
- 新闻、论文、成员、项目卡片。
- 移动端响应式布局。

日常更新内容不需要修改主题。只有页面结构或视觉需要改变时才修改模板和 CSS。

