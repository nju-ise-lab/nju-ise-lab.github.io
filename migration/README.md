# ISE Quick Migration

这是 ISE Quick Hugo 重构的数据迁移脚手架。当前阶段只实现可测试的纯函数：

- ASCII slug 生成与重复兜底。
- 旧时间字符串规范化为 Hugo 可解析的 `+08:00` ISO 时间。
- 新闻、科研项目、成员 front matter 数据组装。
- 媒体 URL 识别，区分需要本地化的图片和应保留的外部跳转链接。
- 页面图片统一生成到 `image` 字段，成员头像统一生成到 `avatar` 字段。

## 测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests
```

生成站点后，可以用标准库脚本把旧站图片下载到 Hugo 页面包，并将正文中的图片 URL 改成相对路径：

```bash
cd ise-quick/migration
python scripts/migrate.py
python scripts/localize_media.py --site-dir output
```

脚本不会直连旧数据库；远程图片只在显式执行 `localize_media.py` 时下载。
