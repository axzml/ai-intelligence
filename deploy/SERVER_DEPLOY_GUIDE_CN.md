[English](SERVER_DEPLOY_GUIDE.md) | 中文

# 服务器部署指南

在 Debian/Ubuntu 服务器上部署 AI 情报系统的完整步骤。

---

## 步骤 1：克隆仓库

```bash
cd ~
git clone git@github.com:YOUR_USERNAME/ai-intelligence.git
cd ~/ai-intelligence
```

---

## 步骤 2：创建运行时目录

仓库不包含运行时目录（data、logs 等），需手动创建：

```bash
mkdir -p ~/ai-intelligence/{data,logs}
```

---

## 步骤 3：初始化数据库

```bash
cd ~/ai-intelligence
python3 scripts/init_db.py
```

预期输出：
```
Database initialized at: /home/YOUR_USER/ai-intelligence/data/intelligence.db
Tables created: raw_items, events, daily_reports, fetch_log, config
WAL mode enabled for concurrent read/write
```

验证：
```bash
sqlite3 ~/ai-intelligence/data/intelligence.db ".tables"
# 应看到: config  daily_reports  events  fetch_log  raw_items
```

---

## 步骤 4：安装 Python 依赖

```bash
cd ~/ai-intelligence

# 创建虚拟环境（Python 3.8+ 即可）
python3 -m venv ~/ai-intelligence/.venv
source ~/ai-intelligence/.venv/bin/activate

pip install -r webapp/requirements.txt
```

> 注意：使用虚拟环境后，systemd service 的 ExecStart 路径需相应修改：
> `ExecStart=/home/YOUR_USER/ai-intelligence/.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8080`

---

## 步骤 5：配置 DNS

将子域名指向你的服务器。以 Cloudflare 为例：

1. 登录 DNS 管理面板
2. 添加 A 记录：
   ```
   Type: A
   Name: contents（或你喜欢的子域名）
   IPv4: 你的服务器 IP
   ```
3. 等待 DNS 生效（通常几分钟）

验证：
```bash
dig contents.your-domain.com
```

---

## 步骤 6：配置 Nginx

```bash
# 1. 复制配置文件
sudo cp ~/ai-intelligence/deploy/nginx-contents.conf /etc/nginx/sites-available/ai-intelligence

# 2. 编辑：将 "your-domain.com" 替换为你的实际域名
sudo nano /etc/nginx/sites-available/ai-intelligence

# 3. 启用站点
sudo ln -s /etc/nginx/sites-available/ai-intelligence /etc/nginx/sites-enabled/

# 4. 测试并重载
sudo nginx -t
sudo systemctl reload nginx
```

---

## 步骤 7：启用 HTTPS（二选一）

仓库中的 `nginx-contents.conf` 只监听 80 端口（HTTP）。生产环境需要 HTTPS，根据你的情况选择：

### 方案 A：Cloudflare Proxy（服务器无需证书）

如果你使用 Cloudflare 并开启了 Proxy（橙色云朵图标），Cloudflare 会自动处理用户到 Cloudflare 边缘节点之间的 HTTPS。Cloudflare 到你服务器的流量走 HTTP 80 端口。

无需任何改动 — 默认的 nginx 配置直接可用。

> 如需端到端加密，将 Cloudflare SSL/TLS 模式设为 "Full (strict)"，并配合下面的方案 B 在服务器上也安装证书。

### 方案 B：Certbot（Let's Encrypt 免费证书）

如果你不使用 Cloudflare Proxy，或者需要端到端加密，用 certbot 获取 Let's Encrypt 免费 SSL 证书。

1. 安装 certbot 和 Nginx 插件：
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

2. 获取证书并自动配置 Nginx：
```bash
sudo certbot --nginx -d contents.your-domain.com
```

这一条命令会自动完成所有工作：
- 向 Let's Encrypt 申请免费 SSL 证书
- 在 Nginx 配置中添加 `listen 443 ssl` 块和证书路径
- 添加 HTTP → HTTPS 的 301 自动跳转（80 端口）
- 重载 Nginx 使配置生效

3. 验证自动续期是否正常：
```bash
sudo certbot renew --dry-run
```

Let's Encrypt 证书有效期 90 天。certbot 会安装 systemd 定时器（或 cron 任务）在到期前自动续期 — `--dry-run` 用于确认续期机制正常工作。

certbot 完成后，你的 Nginx 配置大致如下（自动生成，无需手动编辑）：

```nginx
server {
    listen 80;
    server_name contents.your-domain.com;
    return 301 https://$host$request_uri;    # ← 自动添加的跳转
}

server {
    listen 443 ssl;                           # ← 自动添加
    server_name contents.your-domain.com;
    ssl_certificate /etc/letsencrypt/live/contents.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/contents.your-domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    # ... 你原来的 proxy_pass 等指令保持不变
}
```

---

## 步骤 8：配置 systemd 服务

```bash
# 1. 复制 service 文件
sudo cp ~/ai-intelligence/deploy/ai-intelligence-web.service /etc/systemd/system/

# 2. 编辑：将 YOUR_USERNAME 替换为你的实际用户名
sudo nano /etc/systemd/system/ai-intelligence-web.service

# 3. 启用并启动
sudo systemctl daemon-reload
sudo systemctl enable ai-intelligence-web
sudo systemctl start ai-intelligence-web
```

---

## 步骤 9：安装 MCP Server（在 OpenClaw 中）

### RSS 阅读器

**方案 A**：安装专用 RSS MCP server：
```bash
npm install -g rss-reader-mcp
```

然后在 OpenClaw MCP 配置中添加：
```json
{
  "mcpServers": {
    "rss-reader": {
      "command": "rss-reader-mcp",
      "args": []
    }
  }
}
```

**方案 B**：使用已有的 web-reader MCP（如果支持 RSS/Atom）。可用 `https://blog.google/technology/ai/rss/` 测试。

### Xpoz MCP（X/Twitter）

通过 ClawHub 安装：
```bash
clawhub install xpoz-social-search
# 或
clawhub install xpoz-setup
```

> 首次使用需完成 OAuth2.1 认证 — OpenClaw 会输出认证链接，在浏览器中完成登录即可。

---

## 步骤 10：配置 Resend SMTP（可选）

用于邮件日报功能：

1. 注册 https://resend.com
2. 添加并验证你的域名（添加 DKIM + SPF DNS 记录）
3. 在 https://resend.com/api-keys 创建 API Key
4. 将凭据写入数据库：

```bash
sqlite3 ~/ai-intelligence/data/intelligence.db <<EOF
UPDATE config SET value = 're_YOUR_API_KEY' WHERE key = 'resend_api_key';
UPDATE config SET value = 'noreply@your-domain.com' WHERE key = 'email_sender';
UPDATE config SET value = 'you@example.com' WHERE key = 'email_recipient';
EOF
```

> Resend 免费额度：3,000 封/月（100 封/天），日报完全够用。
> SMTP 配置：host=smtp.resend.com, port=465 (SSL), username=resend, password=API Key

---

## 验证清单

- [ ] `~/ai-intelligence/data/intelligence.db` 存在且有 5 张表
- [ ] `~/ai-intelligence/config/rss_feeds.json` 存在
- [ ] `~/ai-intelligence/config/settings.json` 存在
- [ ] Python 虚拟环境创建成功，依赖已安装
- [ ] DNS 记录已配置且可解析
- [ ] Nginx 配置测试通过（`sudo nginx -t`）
- [ ] HTTPS 正常工作（`curl -I https://contents.your-domain.com`）
- [ ] systemd 服务运行中（`systemctl status ai-intelligence-web`）
- [ ] Resend SMTP 已配置（如使用邮件报告）
- [ ] RSS MCP server 可正常抓取 feed（测试）
- [ ] Xpoz MCP 可搜索 X/Twitter 内容（测试）

---

## 更新

```bash
cd ~/ai-intelligence
git pull origin master
sudo systemctl restart ai-intelligence-web
```
