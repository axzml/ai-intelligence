# Heartbeat Checklist — AI Intelligence System

On each heartbeat cycle, check the following items and surface anything that needs attention.

- Check if there are unprocessed raw_items piling up (run `sqlite3 ~/ai-intelligence/data/intelligence.db "SELECT COUNT(*) FROM raw_items WHERE processed = 0;"` — if count > 50, warn about backlog)
- Check if there are high-score events pending notification (run `sqlite3 ~/ai-intelligence/data/intelligence.db "SELECT COUNT(*) FROM events WHERE score >= 7 AND notified = 0;"` — if count > 0, run the ais-notify skill)
- Check if today's daily report has been generated (run `sqlite3 ~/ai-intelligence/data/intelligence.db "SELECT COUNT(*) FROM daily_reports WHERE report_date = date('now');"` — if 0 and current time is past 19:30, warn that daily report may have failed)
- If any fetch_log entries from the last 4 hours show status='error', report which sources failed
