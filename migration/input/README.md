# Migration Input

旧站公开 API 已导出到仓库根目录：

```text
migration_exports/legacy_api/
```

本迁移脚手架暂不移动或复制这些原始 JSON 文件，后续脚本应以只读方式引用该目录中的
`*.json` 作为输入，并把生成结果写入 Hugo 的 `content/` 与 `data/` 目录。
