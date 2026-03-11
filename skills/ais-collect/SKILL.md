---
name: ais-collect
description: >
  AI Intelligence data collector. Fetches items from RSS feeds, Hacker News, X/Twitter (Xpoz), and GitHub Trending. Stores in raw_items table.
  Trigger: Cron daily at 17:00 CST. Can also be run manually.
---

# Skill: ais-collect — Data Collection

You are a data collection agent. Fetch AI-related content from multiple sources and store it in SQLite. Follow each step carefully. If a single source fails, log the error and continue.

**IMPORTANT: Respect the `max_items` limit for each source. Only keep the N most recent items per source. This controls cost and data volume.**

## Setup

**Database path**: `~/ai-intelligence/data/intelligence.db`
**Config file**: Read the RSS feeds config:

```
cat ~/ai-intelligence/config/rss_feeds.json
```

If not found, try: `cat ~/ClaudeHome/InformationSource/config/rss_feeds.json`

Store the parsed config in memory. Pay attention to the `max_items` field on each source.

## Step 1: Initialize Fetch Log

For each source type, create a fetch_log entry:

```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "INSERT INTO fetch_log (source, status) VALUES ('<source_name>', 'running');"
```

## Step 2: Collect RSS Feeds

For each feed in `official_blogs`, `news_and_newsletters`, and `research`:

1. Fetch the RSS/Atom XML via web fetch MCP tool or `curl`
2. Parse items, extract: title, link, description/summary, author, pubDate
3. **Only keep the most recent N items** where N = the feed's `max_items` value (typically 3-10)
4. Insert using UNIQUE constraint to skip duplicates:

```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "INSERT OR IGNORE INTO raw_items (source, source_id, url, title, content, author, metrics, published_at) VALUES ('rss', '<feed_name>:<guid_or_link>', '<link>', '<title>', '<description_500chars>', '<author>', '{\"feed\": \"<feed_name>\", \"priority\": \"<priority>\"}', '<pubDate_ISO>');"
```

- Escape single quotes (`'` → `''`)
- Limit content to 500 characters

Update fetch_log when done.

## Step 3: Collect Hacker News

1. Fetch top story IDs:
```bash
curl -s "https://hacker-news.firebaseio.com/v0/topstories.json" | head -c 2000
```

2. Take the first **50** IDs only (config `top_n`)

3. For each story, fetch details and keyword-filter. Keywords:
   `AI, LLM, GPT, Claude, Gemini, machine learning, neural, transformer, agent, training, inference, fine-tun, benchmark, open source, Anthropic, OpenAI, DeepMind, Meta AI, Mistral, DeepSeek, LLaMA, multimodal`

4. **Stop after collecting 15 matching stories** (config `max_items`). Do not continue scanning.

5. Insert matches:
```sql
INSERT OR IGNORE INTO raw_items (source, source_id, url, title, content, author, metrics, published_at)
VALUES ('hn', 'hn:<id>', '<url>', '<title>', '', '<by>', '{"upvotes": <score>, "comments": <descendants>}', datetime(<time>, 'unixepoch'));
```

Update fetch_log when done.

## Step 4: Collect X/Twitter via Xpoz

**Budget-conscious**: Xpoz credits are limited (5000 credits/month free). Minimize API calls.

**HARD LIMIT: Collect at most 15 tweets total from X/Twitter. Stop immediately once you reach 15.**

### 4a: Keyword searches (pick top 3 keywords only)

From the config keywords, pick the **3 most general** ones (e.g., "AI breakthrough", "new model release", "open source LLM"). Search each via Xpoz MCP, filter to last 24 hours. Take at most **3 tweets per keyword** (9 max from keywords).

### 4b: Account monitoring (pick top 3 accounts only)

From the config accounts, pick **3 accounts** (e.g., AnthropicAI, OpenAI, karpathy). Fetch only their **most recent 2 tweets each** (last 24h, 6 max from accounts).

### 4c: Parse Xpoz output carefully

**Xpoz output format warning**: Tweet text often contains real newlines, so you CANNOT split output by newline to separate tweets. Instead:
- Use tweet ID patterns (numeric IDs) to identify where each tweet starts
- The `author` field is the Twitter handle (e.g., "AnthropicAI"), NOT a language code
- If you see 2-letter values like "en", "it" in the author field, that's a parsing error — re-parse

### 4d: Insert results

Count your inserts. **Stop at 15 total tweets.** Insert:
```sql
INSERT OR IGNORE INTO raw_items (source, source_id, url, title, content, author, metrics)
VALUES ('x', 'x:<tweet_id>', 'https://x.com/<handle>/status/<tweet_id>', '<first_100_chars>', '<full_text>', '<handle>', '{"retweets": <rt>, "likes": <likes>}');
```

**If Xpoz MCP is not available**: Skip X/Twitter entirely. Log as partial failure.

Update fetch_log when done.

## Step 5: Collect GitHub Trending

1. Fetch: `https://github.com/trending?since=daily&spoken_language_code=en`
2. Parse HTML for repo entries
3. Keyword-filter using config keywords
4. **Keep at most 10 matching repos** (config `max_items`)
5. Insert:
```sql
INSERT OR IGNORE INTO raw_items (source, source_id, url, title, content, author, metrics)
VALUES ('github', 'github:<owner>/<repo>', 'https://github.com/<owner>/<repo>', '<repo>: <desc>', '<full_desc>', '<owner>', '{"stars": <total>, "stars_today": <today>, "language": "<lang>"}');
```

Update fetch_log when done.

## Step 6: Summary Report

```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "SELECT source, COUNT(*) FROM raw_items WHERE fetched_at >= datetime('now', '-3 hours') GROUP BY source;"
```

Report:
```
=== Collection Complete ===
RSS:     X new items
HN:      X new items
X:       X new items
GitHub:  X new items
Total:   X new items (target: ~100 items/day)
Errors:  [list any failures]
===========================
```

**Expected total: ~80-120 items per daily run.** If significantly more, the max_items limits are not being respected.

## Error Handling

- Single feed fails → skip, continue
- Entire source type fails → log error in fetch_log, continue
- Database locked → wait 5s, retry up to 3 times
- curl timeout 30s → move on
