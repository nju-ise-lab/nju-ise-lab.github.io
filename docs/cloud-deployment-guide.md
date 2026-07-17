# ISE Quick 静态网站部署指南

当前网站是 Hugo 静态网站，不再需要 Go、SQLite、systemd 或浏览量 API。

## 部署结构

```text
Hugo 构建
   ↓
public/
   ↓
上传服务器
   ↓
Nginx 托管
```

服务器只需要开放 80/443 端口。

## 本地构建

在项目根目录执行：

```bash
cd ise-quick/frontend

hugo --panicOnWarning --minify \
  --destination /private/tmp/ise-quick-public \
  --cleanDestinationDir
```

## 服务器目录

建议：

```text
/var/www/ise-quick/public/
```

让部署用户拥有目录权限：

```bash
sudo install -d /var/www/ise-quick/public
sudo chown -R deploy:deploy /var/www/ise-quick/public
```

## Nginx 配置

创建：

```text
/etc/nginx/sites-available/ise-quick
```

内容：

```nginx
server {
    listen 80;
    server_name example.com;

    root /var/www/ise-quick/public;
    index index.html;

    access_log /var/log/nginx/ise-quick.access.log;
    error_log /var/log/nginx/ise-quick.error.log;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~* \\.(css|js|png|jpg|jpeg|gif|svg|ico|webp|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public";
        try_files $uri =404;
    }
}
```

启用：

```bash
sudo ln -s /etc/nginx/sites-available/ise-quick /etc/nginx/sites-enabled/ise-quick
sudo nginx -t
sudo systemctl reload nginx
```

如果软链接已经存在，不要重复创建。

## 上传静态文件

```bash
rsync -az --delete \
  /private/tmp/ise-quick-public/ \
  deploy@example.com:/var/www/ise-quick/public/
```

如果服务器不允许部署用户直接写入目标目录，可以先上传到临时目录，再使用 sudo 同步。

## HTTPS

域名解析完成且 80 端口可以访问后：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com
```

## 发布流程

```text
修改 Markdown 或 JSON
        ↓
本地 hugo server 预览
        ↓
Hugo 构建
        ↓
rsync 上传 public/
        ↓
Nginx 自动提供新页面
```

静态文件上传后不需要重启服务。

## 常见检查

```bash
sudo nginx -t
curl -I https://example.com/
```

如果修改内容后页面没有变化，确认：

1. Hugo 是否重新构建。
2. rsync 的目标目录是否正确。
3. Nginx 的 root 是否指向最新的 public 目录。
4. 浏览器是否缓存了旧资源。

## 图片注意事项

页面图片、成员头像和正文图片已经随 Hugo 页面包本地化，轮播图位于 `frontend/static/images/slides/`；正式部署前只需检查构建产物中不再出现旧站图片域名。
