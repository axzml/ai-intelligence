#!/usr/bin/env bash
# AI Intelligence System — OpenClaw Cron Setup
# Run this once on the server after all skills are manually verified.
#
# Daily pipeline: collect(17:00) → analyze(17:30) → notify(18:00) → report(19:00)
#
# Ref: https://github.com/openclaw/openclaw (docs/automation/cron-jobs.md)

set -euo pipefail

echo "=== Registering AI Intelligence cron jobs ==="

# 17:00 — Data collection
openclaw cron add \
  --name "ais-collect" \
  --cron "0 17 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "Run the ais-collect skill to fetch today's AI news from all configured sources. Follow the ais-collect skill instructions exactly." \
  --light-context

echo "[OK] ais-collect: daily at 17:00 CST"

# 17:30 — Analysis
openclaw cron add \
  --name "ais-analyze" \
  --cron "30 17 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "Run the ais-analyze skill to process unprocessed raw_items into scored events. Follow the ais-analyze skill instructions exactly." \
  --light-context

echo "[OK] ais-analyze: daily at 17:30 CST"

# 18:00 — Notifications
openclaw cron add \
  --name "ais-notify" \
  --cron "0 18 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "Run the ais-notify skill to send Telegram notifications for any events with score >= 7 that haven't been notified yet. Follow the ais-notify skill instructions exactly." \
  --light-context

echo "[OK] ais-notify: daily at 18:00 CST"

# 19:00 — Daily report
openclaw cron add \
  --name "ais-report" \
  --cron "0 19 * * *" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --message "Run the ais-report skill to generate and send today's daily intelligence report. Follow the ais-report skill instructions exactly." \
  --announce \
  --channel telegram

echo "[OK] ais-report: daily at 19:00 CST, announce to Telegram"

echo ""
echo "=== Done. Verify with: openclaw cron list ==="
echo ""
echo "Daily pipeline: 17:00 collect → 17:30 analyze → 18:00 notify → 19:00 report"
echo ""
echo "  ais-query: no cron, user-triggered on demand"
echo ""
echo "To remove all jobs:  openclaw cron list  then  openclaw cron remove <jobId>"
echo "To force-run a job:  openclaw cron run <jobId>"
