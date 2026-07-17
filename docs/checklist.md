# 上线检查清单

## 内容

- [ ] 新论文设置 `content_kind: "publication"`。
- [ ] 标题、作者、年份和发表信息正确。
- [ ] 新闻、成员、项目的 Markdown front matter 正确。
- [ ] 首页轮播和精选项目 JSON 格式正确。
- [ ] 页面图片使用页面包内相对路径，轮播图片使用 `static/images/slides/`。
- [ ] 不再修改迁移输出目录作为正式内容。

## 构建

```bash
cd ise-quick
bash scripts/build.sh
```

- [ ] Hugo 构建成功。
- [ ] 首页、新闻、论文、成员、项目、关于我们页面生成。
- [ ] 生成目录中存在 `index.html`。
- [ ] 页面没有旧的浏览量显示或 `/api/views` 请求。

## 部署

- [ ] GitHub 仓库 `Settings → Pages` 的来源设置为 `GitHub Actions`。
- [ ] GitHub Actions 的 build 和 deploy 两个 job 均成功。
- [ ] Nginx 的 `root` 指向最新的 `public/`。
- [ ] `sudo nginx -t` 通过。
- [ ] 首页和主要栏目返回 200。
- [ ] HTTPS 证书有效。
- [ ] 移动端页面布局正常。
- [ ] 轮播图、Logo、头像和正文图片正常。
