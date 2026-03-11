English | [中文](README_CN.md)

# AI Intelligence System (AIS)

> Live demo: [contents.voxlinkai.com](https://contents.voxlinkai.com)

An OpenClaw skill package that builds a fully automated AI news intelligence pipeline — collecting, analyzing, notifying, reporting, and querying — all powered by LLM-driven agent skills.

## What It Does

```
17:00  ais-collect   → Fetches from RSS, Hacker News, X/Twitter, GitHub Trending
17:30  ais-analyze   → LLM clusters items into scored events
18:00  ais-notify    → Sends Telegram alerts for critical events (score ≥ 7)
19:00  ais-report    → Generates & emails a daily HTML report
 any   ais-query     → Natural language Q&A over your intelligence database
```

## Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| `ais-collect` | Cron 17:00 | Multi-source data collection (RSS, HN, X, GitHub) |
| `ais-analyze` | Cron 17:30 | LLM-powered event clustering, scoring (1-10), categorization |
| `ais-notify` | Cron 18:00 | Telegram instant alerts for high-score events |
| `ais-report` | Cron 19:00 | Daily HTML/text report via email (Resend SMTP) |
| `ais-query` | On demand | Natural language knowledge base queries |

## Quick Start

### Prerequisites

- [OpenClaw](https://openclaw.com) installed and configured
- Python 3.8+
- SQLite3
- (Optional) Resend account for email reports
- (Optional) Telegram bot via OpenClaw for notifications

### 1. Install skills

Clone the repository:
```bash
git clone https://github.com/axzml/ai-intelligence.git ~/ai-intelligence
```

Then install the skills into OpenClaw using one of the two methods below.

**Method A: Copy to OpenClaw's default skills directory**

```bash
cp -r ~/ai-intelligence/skills/ais-* ~/.openclaw/workspace/skills/
```

Verify the skills are recognized — ask OpenClaw:

```
What skills do you have? Do you see ais-collect, ais-analyze, ais-notify, ais-report, ais-query?
```

OpenClaw should list all 5 `ais-*` skills. If not, check that the directory structure is correct: each skill folder should contain a `SKILL.md` file.

**Method B: Add a custom skills path in `openclaw.json`**

Edit your OpenClaw config file (usually `~/.openclaw/openclaw.json`) and add the `skills` field pointing to this repo's skills directory:

```json
{
  "skills": {
    "load": {
      "extraDirs": ["/home/<YOUR_USER_NAME>/ai-intelligence/skills"],
      "watch": true
    }
  }
}
```

Replace `<YOUR_USER_NAME>` with your actual system username. The `watch: true` option makes OpenClaw auto-reload when skill files change.

### 2. Initialize the database

```bash
python scripts/init_db.py
```

### 3. Configure data sources

Edit `config/rss_feeds.json` to customize RSS feeds, HN keywords, X/Twitter accounts, and GitHub trending filters.

### 4. Configure settings

Edit `config/settings.json`:
- `scoring.user_interests` — your interest tags for relevance scoring
- `schedule` — adjust pipeline timing
- `webapp.domain` — your web dashboard domain (if deploying the webapp)

### 5. Set up email (optional)

```sql
sqlite3 ~/ai-intelligence/data/intelligence.db
UPDATE config SET value = 'your-resend-api-key' WHERE key = 'resend_api_key';
UPDATE config SET value = 'noreply@yourdomain.com' WHERE key = 'email_sender';
UPDATE config SET value = 'you@example.com' WHERE key = 'email_recipient';
```

### 6. Set up cron jobs

```bash
bash scripts/setup_cron.sh
```

Or manually add to crontab (times in your server timezone):
```cron
0 17 * * * openclaw run ais-collect
30 17 * * * openclaw run ais-analyze
0 18 * * * openclaw run ais-notify
0 19 * * * openclaw run ais-report
```

### 7. Deploy web dashboard (optional)

See `deploy/SERVER_DEPLOY_GUIDE.md` for Nginx + systemd setup.

```bash
cd webapp
pip install -r requirements.txt
python app.py
```

## Project Structure

```
├── skills/                  # OpenClaw agent skills (the core)
│   ├── ais-collect/         # Data collection from 4 sources
│   ├── ais-analyze/         # LLM analysis & event generation
│   ├── ais-notify/          # Telegram notifications
│   ├── ais-report/          # Daily email reports
│   └── ais-query/           # Natural language queries
├── config/
│   ├── settings.json        # System configuration
│   └── rss_feeds.json       # Data source definitions
├── scripts/
│   ├── init_db.py           # Database initialization
│   └── setup_cron.sh        # Cron job installer
├── heartbeat/
│   └── HEARTBEAT.md         # Health-check checklist for monitoring
├── webapp/                  # Flask web dashboard
└── deploy/                  # Server deployment configs
```

## Heartbeat (Health Monitoring)

The `heartbeat/HEARTBEAT.md` defines a checklist that OpenClaw runs periodically to monitor system health:

- Detects unprocessed item backlog (raw_items piling up)
- Alerts if high-score events are pending notification
- Warns if the daily report failed to generate
- Reports data source fetch errors

To enable it, append the heartbeat checklist to OpenClaw's workspace:

```bash
cat ~/ai-intelligence/heartbeat/HEARTBEAT.md >> ~/.openclaw/workspace/HEARTBEAT.md
```

OpenClaw will automatically pick up `HEARTBEAT.md` and run the checks on its configured heartbeat cycle. You can also trigger it manually by asking OpenClaw: "Run the heartbeat check."

## Scoring System

Events are scored 1-10 using weighted criteria:

| Weight | Criterion | Description |
|--------|-----------|-------------|
| 25% | Source Authority | Official blogs score higher than personal posts |
| 25% | Interest Match | Relevance to your configured interests |
| 20% | Novelty | New concepts score higher than incremental updates |
| 15% | Community Heat | Engagement metrics (upvotes, likes, comments) |
| 15% | Timeliness | Breaking news scores higher than old items |

## License

MIT
