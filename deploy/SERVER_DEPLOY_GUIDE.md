English | [中文](SERVER_DEPLOY_GUIDE_CN.md)

# Server Deployment Guide

Complete steps for deploying the AI Intelligence System on a Debian/Ubuntu server.

---

## Step 1: Clone the Repository

```bash
cd ~
git clone git@github.com:YOUR_USERNAME/ai-intelligence.git
cd ~/ai-intelligence
```

---

## Step 2: Create Runtime Directories

The repo does not include runtime directories (data, logs, etc.). Create them manually:

```bash
mkdir -p ~/ai-intelligence/{data,logs}
```

---

## Step 3: Initialize the Database

```bash
cd ~/ai-intelligence
python3 scripts/init_db.py
```

Expected output:
```
Database initialized at: /home/YOUR_USER/ai-intelligence/data/intelligence.db
Tables created: raw_items, events, daily_reports, fetch_log, config
WAL mode enabled for concurrent read/write
```

Verify:
```bash
sqlite3 ~/ai-intelligence/data/intelligence.db ".tables"
# Expected: config  daily_reports  events  fetch_log  raw_items
```

---

## Step 4: Install Python Dependencies

```bash
cd ~/ai-intelligence

# Create a virtual environment (use your preferred Python 3.8+)
python3 -m venv ~/ai-intelligence/.venv
source ~/ai-intelligence/.venv/bin/activate

pip install -r webapp/requirements.txt
```

> Note: When using a venv, update the systemd service `ExecStart` path accordingly:
> `ExecStart=/home/YOUR_USER/ai-intelligence/.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8080`

---

## Step 5: Configure DNS

Point a subdomain to your server. Example using Cloudflare:

1. Log in to your DNS provider dashboard
2. Add an A record:
   ```
   Type: A
   Name: contents  (or your preferred subdomain)
   IPv4: your server IP
   ```
3. Wait for DNS propagation (usually a few minutes)

Verify:
```bash
dig contents.your-domain.com
```

---

## Step 6: Configure Nginx

```bash
# 1. Copy the config file
sudo cp ~/ai-intelligence/deploy/nginx-contents.conf /etc/nginx/sites-available/ai-intelligence

# 2. Edit: replace "your-domain.com" with your actual domain
sudo nano /etc/nginx/sites-available/ai-intelligence

# 3. Enable the site
sudo ln -s /etc/nginx/sites-available/ai-intelligence /etc/nginx/sites-enabled/

# 4. Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 7: Enable HTTPS (Choose One)

The included `nginx-contents.conf` only listens on port 80 (HTTP). You need HTTPS for production. Choose the approach that matches your setup:

### Option A: Cloudflare Proxy (No certificate needed on server)

If you use Cloudflare with Proxy enabled (orange cloud icon), Cloudflare handles HTTPS automatically between the user and Cloudflare's edge. Traffic from Cloudflare to your server goes over HTTP on port 80.

No changes needed — the default nginx config works as-is.

> To enforce HTTPS end-to-end, set Cloudflare SSL/TLS mode to "Full (strict)" and use Option B below to also install a certificate on your server.

### Option B: Certbot (Let's Encrypt free certificate)

If you're not using Cloudflare Proxy, or want end-to-end encryption, use certbot to get a free SSL certificate from Let's Encrypt.

1. Install certbot and the Nginx plugin:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

2. Obtain the certificate and auto-configure Nginx:
```bash
sudo certbot --nginx -d contents.your-domain.com
```

This single command does everything:
- Requests a free SSL certificate from Let's Encrypt
- Adds a `listen 443 ssl` block to your Nginx config with the certificate paths
- Adds an automatic HTTP → HTTPS 301 redirect on port 80
- Reloads Nginx to apply changes

3. Verify auto-renewal is set up:
```bash
sudo certbot renew --dry-run
```

Let's Encrypt certificates expire every 90 days. Certbot installs a systemd timer (or cron job) that auto-renews before expiration — the `--dry-run` confirms this is working.

After certbot completes, your Nginx config will look roughly like this (auto-generated, no manual editing needed):

```nginx
server {
    listen 80;
    server_name contents.your-domain.com;
    return 301 https://$host$request_uri;    # ← auto-added redirect
}

server {
    listen 443 ssl;                           # ← auto-added
    server_name contents.your-domain.com;
    ssl_certificate /etc/letsencrypt/live/contents.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/contents.your-domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;

    # ... your original proxy_pass and other directives remain unchanged
}
```

---

## Step 8: Configure systemd Service

```bash
# 1. Copy the service file
sudo cp ~/ai-intelligence/deploy/ai-intelligence-web.service /etc/systemd/system/

# 2. Edit: replace YOUR_USERNAME with your actual username
sudo nano /etc/systemd/system/ai-intelligence-web.service

# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ai-intelligence-web
sudo systemctl start ai-intelligence-web
```

---

## Step 9: Install MCP Servers (in OpenClaw)

### RSS Reader

**Option A**: Install a dedicated RSS MCP server:
```bash
npm install -g rss-reader-mcp
```

Then add to your OpenClaw MCP config:
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

**Option B**: Use an existing web-reader MCP that supports RSS/Atom feeds. Test by fetching a feed URL like `https://blog.google/technology/ai/rss/`.

### Xpoz MCP (X/Twitter)

Install via ClawHub:
```bash
clawhub install xpoz-social-search
# or
clawhub install xpoz-setup
```

> First-time use requires OAuth2.1 authentication — OpenClaw will output an auth link to complete in your browser.

---

## Step 10: Configure Resend SMTP (Optional)

For email daily reports:

1. Sign up at https://resend.com
2. Add and verify your domain (add DKIM + SPF DNS records)
3. Create an API key at https://resend.com/api-keys
4. Write credentials to the database:

```bash
sqlite3 ~/ai-intelligence/data/intelligence.db <<EOF
UPDATE config SET value = 're_YOUR_API_KEY' WHERE key = 'resend_api_key';
UPDATE config SET value = 'noreply@your-domain.com' WHERE key = 'email_sender';
UPDATE config SET value = 'you@example.com' WHERE key = 'email_recipient';
EOF
```

> Resend free tier: 3,000 emails/month (100/day) — more than enough for daily reports.
> SMTP: host=smtp.resend.com, port=465 (SSL), username=resend, password=API Key

---

## Verification Checklist

- [ ] `~/ai-intelligence/data/intelligence.db` exists with 5 tables
- [ ] `~/ai-intelligence/config/rss_feeds.json` exists
- [ ] `~/ai-intelligence/config/settings.json` exists
- [ ] Python venv created, dependencies installed
- [ ] DNS record configured and resolving
- [ ] Nginx config test passes (`sudo nginx -t`)
- [ ] HTTPS working (`curl -I https://contents.your-domain.com`)
- [ ] systemd service running (`systemctl status ai-intelligence-web`)
- [ ] Resend SMTP configured (if using email reports)
- [ ] RSS MCP server can fetch feeds (test)
- [ ] Xpoz MCP can search X/Twitter (test)

---

## Updating

```bash
cd ~/ai-intelligence
git pull origin master
sudo systemctl restart ai-intelligence-web
```
