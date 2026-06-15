# ISE Quick 云服务器部署文档

本文档说明如何把 ISE Quick 部署到自有云服务器。推荐结构是：

- Nginx 托管 Hugo 生成的静态文件。
- Go 后端只提供 `/api/views` 浏览量接口。
- SQLite 保存浏览量。

以下命令以 Ubuntu / Debian 系服务器为例。其他 Linux 发行版思路相同，包管理命令可能不同。

## 部署目标

最终服务器上建议形成：

```text
/opt/ise-quick/                 项目源码或发布包
/opt/ise-quick/bin/view-counter 浏览量后端二进制
/var/www/ise-quick/public/      Hugo 静态站点文件
/var/lib/ise-quick/views.db     SQLite 浏览量数据库
/var/backups/ise-quick/         数据库备份
/etc/systemd/system/ise-view-counter.service
/etc/nginx/sites-available/ise-quick
```

公网只暴露：

- `80` HTTP
- `443` HTTPS

Go 后端只监听：

```text
127.0.0.1:8080
```

## 部署前准备

你需要确认：

- 域名已经解析到服务器公网 IP。
- 服务器防火墙允许 80 和 443。
- 本地或服务器已安装 Hugo Extended。
- 本地或服务器已安装 Go 1.22 或更高版本。
- 你有服务器 sudo 权限。

本项目当前本地已验证：

- Hugo Extended 可构建前端。
- Go 后端测试可通过。
- 前端构建后生成 83 个页面。

## 推荐部署方式

推荐使用“本地构建 + 上传产物”的方式：

```text
本地编辑内容
  |
  v
本地运行 Hugo 构建
  |
  v
上传 public 静态文件到服务器
  |
  v
需要后端变更时，单独构建并上传 Go 二进制
```

这样服务器不一定需要保留完整开发环境，维护起来更稳。

如果你希望服务器直接构建，也可以把完整 `ise-quick/` 上传到 `/opt/ise-quick/` 后在服务器上运行 Hugo 和 Go build。

## 服务器初始化

安装基础软件：

```bash
sudo apt update
sudo apt install -y nginx sqlite3 rsync
```

创建运行用户和目录：

```bash
sudo useradd --system --home /var/lib/ise-quick --shell /usr/sbin/nologin ise
sudo install -d -o ise -g ise /var/lib/ise-quick
sudo install -d -o ise -g ise /var/backups/ise-quick
sudo install -d /opt/ise-quick/bin
sudo install -d /var/www/ise-quick/public
```

说明：

- `ise` 用户用于运行浏览量后端。
- `/var/lib/ise-quick/` 保存 SQLite 数据库。
- `/var/www/ise-quick/public/` 保存静态站点。

## 本地构建前端

在本机项目目录执行：

```bash
cd ise-quick/frontend
hugo --panicOnWarning --minify --destination public --cleanDestinationDir
```

构建成功后会生成：

```text
ise-quick/frontend/public/
```

上传到服务器：

```bash
rsync -az --delete ise-quick/frontend/public/ user@your-server:/tmp/ise-public/
ssh user@your-server "sudo rsync -az --delete /tmp/ise-public/ /var/www/ise-quick/public/"
```

注意：`--delete` 会删除目标目录里本地不存在的文件。这里只对 `/var/www/ise-quick/public/` 使用，不要对项目源码目录乱用。

## 构建后端

如果服务器是 x86_64，通常使用：

```bash
cd ise-quick/backend
GOOS=linux GOARCH=amd64 go build -o view-counter .
```

如果服务器是 ARM64，通常使用：

```bash
cd ise-quick/backend
GOOS=linux GOARCH=arm64 go build -o view-counter .
```

不确定服务器架构时，在服务器执行：

```bash
uname -m
```

常见对应关系：

| `uname -m` | Go 架构 |
| --- | --- |
| `x86_64` | `amd64` |
| `aarch64` | `arm64` |

上传二进制：

```bash
scp ise-quick/backend/view-counter user@your-server:/tmp/view-counter
ssh user@your-server "sudo install -m 755 /tmp/view-counter /opt/ise-quick/bin/view-counter"
```

上传浏览量初始值：

```bash
scp ise-quick/frontend/data/views-seed.json user@your-server:/tmp/views-seed.json
ssh user@your-server "sudo install -m 644 /tmp/views-seed.json /opt/ise-quick/views-seed.json"
```

## 配置 systemd 服务

在服务器创建：

```bash
sudo nano /etc/systemd/system/ise-view-counter.service
```

写入：

```ini
[Unit]
Description=ISE Quick View Counter API
After=network.target

[Service]
Type=simple
User=ise
Group=ise
Environment=VIEW_COUNTER_DB=/var/lib/ise-quick/views.db
Environment=VIEW_COUNTER_SEED_FILE=/opt/ise-quick/views-seed.json
Environment=ADDR=127.0.0.1:8080
ExecStart=/opt/ise-quick/bin/view-counter
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ise-view-counter
sudo systemctl status ise-view-counter
```

查看日志：

```bash
journalctl -u ise-view-counter -f
```

说明：

- `VIEW_COUNTER_SEED_FILE` 重复导入是幂等的，不会清零已有新增浏览量。
- 如果后续不想每次启动都检查 seed 文件，也可以在首次启动成功后移除该环境变量，再重启服务。

## 配置 Nginx

创建站点配置：

```bash
sudo nano /etc/nginx/sites-available/ise-quick
```

写入，记得把 `example.com` 换成真实域名：

```nginx
server {
    listen 80;
    server_name example.com;

    root /var/www/ise-quick/public;
    index index.html;

    access_log /var/log/nginx/ise-quick.access.log;
    error_log /var/log/nginx/ise-quick.error.log;

    location = /api/views {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ =404;
    }

    location ~* \.(css|js|png|jpg|jpeg|gif|svg|ico|webp|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public";
        try_files $uri =404;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/ise-quick /etc/nginx/sites-enabled/ise-quick
sudo nginx -t
sudo systemctl reload nginx
```

如果默认站点冲突，可以删除默认链接：

```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 配置 HTTPS

如果使用 Let's Encrypt，可以安装 Certbot：

```bash
sudo apt install -y certbot python3-certbot-nginx
```

申请证书，替换真实域名：

```bash
sudo certbot --nginx -d example.com
```

检查自动续期：

```bash
sudo systemctl list-timers | grep certbot
sudo certbot renew --dry-run
```

## 首次部署验收

检查首页：

```bash
curl -I http://example.com/
```

期望看到：

```text
HTTP/1.1 200 OK
```

检查 API：

```bash
curl "http://example.com/api/views?path=/news/news-64/"
```

检查 POST 计数：

```bash
curl -X POST "http://example.com/api/views" \
  -H "Content-Type: application/json" \
  -d '{"path":"/news/news-64/"}'
```

期望返回 JSON，包含：

```json
{
  "path": "/news/news-64/",
  "total": 713
}
```

实际数字会随浏览量变化。

检查服务状态：

```bash
sudo systemctl status ise-view-counter
sudo nginx -t
```

## 日常内容更新部署

只改新闻、活动、成员、项目、轮播等内容时：

1. 本地修改 `ise-quick/frontend/content/` 或 `ise-quick/frontend/data/`。
2. 本地构建：

```bash
cd ise-quick/frontend
hugo --panicOnWarning --minify --destination public --cleanDestinationDir
```

3. 上传静态文件：

```bash
rsync -az --delete ise-quick/frontend/public/ user@your-server:/tmp/ise-public/
ssh user@your-server "sudo rsync -az --delete /tmp/ise-public/ /var/www/ise-quick/public/"
```

4. 不需要重启 Go 后端。

## 后端更新部署

只有改了 `backend/` 后，才需要更新后端。

本地测试：

```bash
cd ise-quick/backend
go test ./...
```

构建并上传：

```bash
GOOS=linux GOARCH=amd64 go build -o view-counter .
scp view-counter user@your-server:/tmp/view-counter
ssh user@your-server "sudo install -m 755 /tmp/view-counter /opt/ise-quick/bin/view-counter && sudo systemctl restart ise-view-counter"
```

确认状态：

```bash
ssh user@your-server "sudo systemctl status ise-view-counter"
```

## 浏览量数据库备份

推荐定期备份：

```bash
sudo sqlite3 /var/lib/ise-quick/views.db ".backup '/var/backups/ise-quick/views-$(date +%F).db'"
```

可以加到 root 的 crontab：

```bash
sudo crontab -e
```

例如每天凌晨 3 点备份：

```cron
0 3 * * * sqlite3 /var/lib/ise-quick/views.db ".backup '/var/backups/ise-quick/views-$(date +\%F).db'"
```

保留最近 30 天备份：

```cron
30 3 * * * find /var/backups/ise-quick -name 'views-*.db' -mtime +30 -delete
```

## 回滚方案

静态站点回滚最简单的做法是保留上一次 `public` 目录备份。

部署前在服务器执行：

```bash
sudo cp -a /var/www/ise-quick/public /var/www/ise-quick/public.bak.$(date +%Y%m%d%H%M%S)
```

如果新页面有问题，找到上一次备份并恢复：

```bash
sudo rsync -az --delete /var/www/ise-quick/public.bak.YYYYMMDDHHMMSS/ /var/www/ise-quick/public/
```

后端回滚：

```bash
sudo cp /opt/ise-quick/bin/view-counter.bak /opt/ise-quick/bin/view-counter
sudo systemctl restart ise-view-counter
```

建议每次替换后端二进制前备份：

```bash
sudo cp /opt/ise-quick/bin/view-counter /opt/ise-quick/bin/view-counter.bak
```

## 常见问题

### 首页能打开，但浏览量一直是 `--`

检查：

```bash
sudo systemctl status ise-view-counter
curl "http://127.0.0.1:8080/api/views?path=/news/news-64/"
curl "http://example.com/api/views?path=/news/news-64/"
```

如果本机 `127.0.0.1:8080` 可以访问，但域名 `/api/views` 不行，通常是 Nginx 反代配置问题。

### Hugo 构建失败

优先检查最近改过的：

- Markdown front matter 的 `---` 是否成对。
- JSON 是否有多余逗号。
- 日期是否是 `YYYY-MM-DD`。
- 图片路径是否正确。

### 403 Forbidden

检查静态目录权限：

```bash
ls -ld /var/www/ise-quick/public
sudo nginx -t
```

Nginx 需要能读取 `/var/www/ise-quick/public` 下的文件。

### 502 Bad Gateway

通常是 Go 后端没有启动或监听地址不一致：

```bash
sudo systemctl status ise-view-counter
journalctl -u ise-view-counter -n 100
```

确认 systemd 中：

```text
ADDR=127.0.0.1:8080
```

和 Nginx 中：

```text
proxy_pass http://127.0.0.1:8080;
```

一致。

### 新内容没有出现在页面上

检查：

- 是否重新运行了 Hugo 构建。
- 是否上传了最新 `public/`。
- Markdown 是否 `draft: true`。
- 新闻/活动日期是否太旧，首页只显示最新几条。

## 部署检查清单

上线前逐项确认：

- `hugo --panicOnWarning` 构建通过。
- `go test ./...` 后端测试通过。
- Nginx `nginx -t` 通过。
- `ise-view-counter` systemd 服务正常。
- 首页、新闻、活动、成员、科研项目、关于我们、诚聘英才能打开。
- 详情页浏览量能显示数字。
- SQLite 数据库已经进入备份计划。
- 服务器没有公开旧项目源码、迁移原始导出或临时文件。
