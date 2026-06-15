# ISE Quick View Counter API

ISE Quick 的轻量浏览量 API。它只负责 `/api/views`，用 SQLite 保存每个站内 path 的 seed 和新增浏览量。

## 接口

### GET /api/views?path=/news/a/

查询页面浏览量。不存在的 path 不会创建记录，返回 0。

```json
{
  "path": "/news/a/",
  "seed": 0,
  "views": 0,
  "total": 0
}
```

### POST /api/views

请求体：

```json
{
  "path": "/news/a/"
}
```

对应 path 的 `views` 加 1，返回最新计数：

```json
{
  "path": "/news/a/",
  "seed": 0,
  "views": 1,
  "total": 1
}
```

`path` 必须是站内路径，例如 `/news/a/`。空 path、`https://...`、`//example.com/...` 等外链或协议相对 URL 会返回 `400`。

## 数据库

启动时会自动初始化表：

```sql
CREATE TABLE IF NOT EXISTS pages (
  path TEXT PRIMARY KEY,
  seed INTEGER NOT NULL DEFAULT 0,
  views INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
```

`seed` 用于未来导入旧站浏览量，`views` 是新 API 运行后的新增浏览量，接口返回的 `total = seed + views`。

## Seed 导入

启动时可以通过 `VIEW_COUNTER_SEED_FILE` 导入旧站浏览量 seed。文件使用 JSON 数组，不需要额外依赖：

```json
[
  {
    "path": "/news/a/",
    "seed": 42
  },
  {
    "path": "/news/b/",
    "seed": 108
  }
]
```

导入规则：

- `path` 使用和 API 相同的站内路径校验，例如 `/news/a/`
- `seed` 必须是非负整数
- 已存在的记录会更新 `seed`，但不会清零或覆盖已有 `views`
- 重复导入同一个 seed 文件是幂等的，`total` 仍然等于 `seed + views`
- 不设置 `VIEW_COUNTER_SEED_FILE` 时会跳过导入并正常启动

启动示例：

```bash
VIEW_COUNTER_DB=/var/lib/ise/views.db \
VIEW_COUNTER_SEED_FILE=/var/lib/ise/views-seed.json \
ADDR=127.0.0.1:8080 \
go run .
```

迁移方生成 seed JSON 时，只需要输出数组对象，字段为：

```json
{"path": "/news/a/", "seed": 42}
```

为兼容迁移中间产物，导入器也接受旧字段名 `views_seed`；如果 `seed` 缺省或为 `0`，会使用 `views_seed`。

建议迁移脚本对旧站 URL 做规范化，只保留站内 path，并把缺失或无法解析的浏览量处理为 `0` 或直接跳过该条。

## 运行

默认监听 `:8080`，默认数据库文件是当前目录的 `views.db`。

```bash
go mod download
go run .
```

生产环境建议显式指定监听地址和数据库路径：

```bash
VIEW_COUNTER_DB=/var/lib/ise/views.db ADDR=127.0.0.1:8080 go run .
```

也可以构建二进制：

```bash
go build -o view-counter .
VIEW_COUNTER_DB=/var/lib/ise/views.db ADDR=127.0.0.1:8080 ./view-counter
```

## 测试

```bash
go test ./...
```

测试覆盖：

- GET 不存在 path 返回 0
- POST 后 views 增加
- 空 path 拒绝
- 外链 path 拒绝
- seed + views 的 total 计算
- JSON seed 文件导入
- 重复导入保留已有 views
- 未设置 seed 文件路径时正常启动

## Nginx 反代示例

主站只需要把 `/api/views` 代理到后端：

```nginx
location = /api/views {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

如果后续增加更多 API，也可以改成 prefix location：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## SQLite 备份

服务运行中建议使用 SQLite 在线备份，避免直接复制时遇到未落盘的 WAL 或锁状态：

```bash
sqlite3 /var/lib/ise/views.db ".backup '/var/backups/ise/views-$(date +%F).db'"
```

如果确认服务已停止，也可以直接复制数据库文件：

```bash
cp /var/lib/ise/views.db /var/backups/ise/views.db
```
