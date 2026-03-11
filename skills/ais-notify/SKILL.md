---
name: ais-notify
description: >
  AI Intelligence notifier. Sends Telegram messages for high-score events (score >= 7) that haven't been notified yet.
  Trigger: Run after analyze completes, or manually when needed.
---

# Skill: notify — Telegram Instant Notification

You are a notification agent. Your job is to send formatted Telegram messages for high-scoring AI intelligence events that haven't been notified yet.

## Setup

**Database path**: `~/ai-intelligence/data/intelligence.db`

## Step 1: Query Pending Notifications

```sql
sqlite3 -json ~/ai-intelligence/data/intelligence.db "SELECT id, title, summary, impact, category, domain, score, sources, created_at FROM events WHERE score >= 7 AND notified = 0 ORDER BY score DESC, created_at DESC;"
```

If no results, report "No pending notifications" and exit.

## Step 2: Format and Send Messages

For each event, compose a Telegram message in the following format:

```
🔴 Score: {score}/10 | {category_emoji} {category_label}

📌 {title}

📝 Summary:
{summary}

💡 Impact:
{impact}

🔗 Sources:
{for each source: "• [{platform}] {source_title} — {url}"}

🏷 Domain: {domain} | ⏰ {created_at}
```

**Category emoji mapping:**
- model_release: 🚀
- open_source_tool: 🔧
- paper: 📄
- industry: 🏢
- product_update: 📦
- tutorial: 📚

**Category label mapping:**
- model_release: Model Release
- open_source_tool: Open Source
- paper: Research Paper
- industry: Industry News
- product_update: Product Update
- tutorial: Tutorial

### Sending

Use the **OpenClaw Telegram Bot** to send each message. The bot should be accessible through OpenClaw's built-in messaging capability.

If OpenClaw provides a `send_telegram` or similar function, use it directly. Otherwise, compose the message and instruct the system to deliver it via the bound Telegram bot.

**Important**: Send messages one at a time with a 1-second pause between them to avoid rate limiting.

## Step 3: Mark as Notified

After each message is successfully sent, update the database:

```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "UPDATE events SET notified = 1 WHERE id = <event_id>;"
```

Only mark as notified if the send was confirmed successful. If a send fails, leave `notified = 0` so it will be retried next run.

## Step 4: Summary

Report the results:
```
=== Notifications Sent ===
Total: X messages sent
Events: [list event IDs and titles]
Failed: Y messages (if any)
===========================
```

## Error Handling

- If Telegram sending fails for a specific event, skip it and continue with the next
- Do NOT mark failed sends as notified
- If all sends fail, report the error but do not retry indefinitely
- If the database is locked, wait 5 seconds and retry up to 3 times
