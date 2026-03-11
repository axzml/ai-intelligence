---
name: ais-analyze
description: >
  AI Intelligence analyzer. Processes unprocessed raw_items using LLM for event clustering, scoring, and summary generation. Writes results to the events table.
  Trigger: Cron daily at 17:30 CST. Runs after ais-collect.
---

# Skill: ais-analyze — Analysis & Event Generation

You are an AI intelligence analyst. Process raw collected items, cluster them into events, score them, and generate summaries. Use LLM for analysis.

## Setup

**Database path**: `~/ai-intelligence/data/intelligence.db`

Check unprocessed count:
```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "SELECT COUNT(*) FROM raw_items WHERE processed = 0;"
```

If 0, report "No new items to process" and skip to Step 4.

## Step 1: Load Data

### 1a: Unprocessed items (max 100)
```sql
sqlite3 -json ~/ai-intelligence/data/intelligence.db "SELECT id, source, url, title, content, author, metrics, published_at FROM raw_items WHERE processed = 0 ORDER BY fetched_at DESC LIMIT 100;"
```

If `-json` is not supported:
```sql
sqlite3 -header -separator '|||' ~/ai-intelligence/data/intelligence.db "SELECT id, source, url, title, content, author, metrics, published_at FROM raw_items WHERE processed = 0 ORDER BY fetched_at DESC LIMIT 100;"
```

### 1b: Recent events for dedup
```sql
sqlite3 -header -separator '|||' ~/ai-intelligence/data/intelligence.db "SELECT id, title, category, domain FROM events WHERE created_at >= datetime('now', '-48 hours');"
```

## Step 2: Analyze with LLM (Single Pass)

Send ALL loaded items to LLM in **one call**. If there are more than 60 items, split into 2 batches max.

**LLM Prompt:**

```
You are an AI industry intelligence analyst. Analyze these raw items and produce structured events.

## Instructions

1. **Cluster**: Group items about the same news/topic into one event. Merge cross-source duplicates.

2. **Score** 1-10 using weighted criteria:
   - Source Authority (25%): Official blog=9-10, Major media=7-8, Community=5-6, Personal=3-4
   - Community Heat (15%): >1000 engagement=9-10, >100=6-8, <100=3-5
   - Timeliness (15%): Breaking=9-10, Same day=7-8, 1-2 days=5-6, Older=3-4
   - Interest Match (25%): Matches [大模型进展, Agent应用, AI商业化/赚钱, AI安全]. Direct=9-10, Related=6-8, Tangential=3-5
   - Novelty (20%): New concept=9-10, Major update=7-8, Incremental=5-6, Known=3-4

3. **Categorize**: model_release | open_source_tool | paper | industry | product_update | tutorial

4. **Domain**: llm | agent | multimodal | security | application | business

5. **Output per event**:
   - title: English, concise, max 120 chars
   - summary: English, 3-5 sentences
   - impact: Only if score >= 7 (2-3 sentences on implications), otherwise null

6. **Dedup**: Skip events that match these existing titles:
{RECENT_EVENTS_TITLES}

7. **Be selective**: Only create events for genuinely noteworthy items. Routine arXiv papers without standout results should be scored 3 or below. Aim for 15-30 events from ~100 raw items.

## Raw Items
{RAW_ITEMS_JSON}

## Output: JSON array only
[{
  "title": "...",
  "summary": "...",
  "impact": "... or null",
  "category": "...",
  "domain": "...",
  "score": 7,
  "sources": [{"platform": "hn", "url": "...", "title": "...", "metrics": {...}}],
  "raw_item_ids": [1, 2, 3],
  "is_duplicate": false
}]
```

## Step 3: Write Results

For each event where `is_duplicate` is false:

### 3a: Validate
- score: 1-10
- category: one of 6 valid values
- domain: one of 6 valid values
- Skip invalid events

### 3b: Insert
```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "INSERT INTO events (title, summary, impact, category, domain, score, sources, raw_item_ids) VALUES ('<title>', '<summary>', '<impact_or_null>', '<category>', '<domain>', <score>, '<sources_json>', '<raw_item_ids_json>');"
```

Escape single quotes (`'` → `''`).

### 3c: Mark all loaded raw items as processed
```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "UPDATE raw_items SET processed = 1 WHERE processed = 0 AND id <= <max_id_from_batch>;"
```

This marks both clustered and noise items as done in one statement.

## Step 4: Check Notifications

```sql
sqlite3 ~/ai-intelligence/data/intelligence.db "SELECT COUNT(*) FROM events WHERE score >= 7 AND notified = 0;"
```

Report:
```
=== Analysis Complete ===
New events: X (Critical: Y, Notable: Z)
Pending notifications: N
Suggestion: Run ais-notify if N > 0
===========================
```

## Error Handling

- LLM returns invalid JSON → retry once with "output JSON array only, no markdown"
- Batch fails twice → mark items as processed = -1, report error
- Database locked → wait 5s, retry 3 times

## Scoring Reference
- 9-10: Major event (frontier model launch, major acquisition)
- 7-8: Significant (impactful release, policy change)
- 5-6: Noteworthy (interesting project, discussion)
- 4: General info (routine update)
- 1-3: Noise
