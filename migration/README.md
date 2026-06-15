# ISE Quick Migration

这是 ISE Quick Hugo 重构的数据迁移脚手架。当前阶段只实现可测试的纯函数：

- ASCII slug 生成与重复兜底。
- 旧时间字符串规范化为 Hugo 可解析的 `+08:00` ISO 时间。
- 新闻、科研项目、成员 front matter 数据组装。
- 媒体 URL 识别，区分需要本地化的图片和应保留的外部跳转链接。

## 测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests
```

脚本不会下载远程图片，也不会直连旧数据库。
