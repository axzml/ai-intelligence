import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

import aiosqlite

DB_PATH = str(Path.home() / "ai-intelligence" / "data" / "intelligence.db")


@asynccontextmanager
async def get_db():
    """Get a read-only database connection."""
    db_uri = f"file:{DB_PATH}?mode=ro"
    async with aiosqlite.connect(db_uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        yield conn


def _parse_event(event: dict) -> dict:
    """Parse JSON fields in an event dict."""
    if event is None:
        return None
    result = dict(event)
    for field in ("sources", "raw_item_ids"):
        if field in result and isinstance(result[field], str):
            try:
                result[field] = json.loads(result[field])
            except (json.JSONDecodeError, TypeError):
                result[field] = []
    return result


async def get_events(
    page: int = 1,
    per_page: int = 20,
    score_min: int = None,
    score_max: int = None,
    category: str = None,
    domain: str = None,
    search: str = None,
    date_from: str = None,
    date_to: str = None,
) -> tuple[list[dict], int]:
    """Get paginated events with optional filters."""
    conditions = []
    params = []

    if score_min is not None:
        conditions.append("score >= ?")
        params.append(score_min)
    if score_max is not None:
        conditions.append("score <= ?")
        params.append(score_max)
    if category:
        conditions.append("category = ?")
        params.append(category)
    if domain:
        conditions.append("domain = ?")
        params.append(domain)
    if search:
        conditions.append("(title LIKE ? OR summary LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if date_from:
        conditions.append("date(created_at) >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date(created_at) <= ?")
        params.append(date_to)

    where = " AND ".join(conditions) if conditions else "1=1"

    async with get_db() as conn:
        async with conn.execute(f"SELECT COUNT(*) as cnt FROM events WHERE {where}", params) as cur:
            total_count = (await cur.fetchone())["cnt"]

        offset = (page - 1) * per_page
        query = f"SELECT * FROM events WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        async with conn.execute(query, params + [per_page, offset]) as cur:
            events = [_parse_event(dict(row)) for row in await cur.fetchall()]

    return events, total_count


async def get_event_by_id(event_id: int) -> dict | None:
    """Get a single event by ID."""
    async with get_db() as conn:
        async with conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)) as cur:
            row = await cur.fetchone()
            return _parse_event(dict(row)) if row else None


async def get_today_events() -> dict:
    """Get today's events split into critical (>=7) and notable (4-6)."""
    today = date.today().isoformat()

    async with get_db() as conn:
        async with conn.execute(
            "SELECT * FROM events WHERE date(created_at) = ? AND score >= 7 ORDER BY score DESC",
            (today,),
        ) as cur:
            critical = [_parse_event(dict(r)) for r in await cur.fetchall()]

        async with conn.execute(
            "SELECT * FROM events WHERE date(created_at) = ? AND score >= 4 AND score < 7 ORDER BY score DESC",
            (today,),
        ) as cur:
            notable = [_parse_event(dict(r)) for r in await cur.fetchall()]

        async with conn.execute(
            "SELECT COUNT(*) as cnt FROM raw_items WHERE date(fetched_at) = ?",
            (today,),
        ) as cur:
            total_collected = (await cur.fetchone())["cnt"]

    return {
        "critical": critical,
        "notable": notable,
        "stats": {
            "total_collected": total_collected,
            "total_notable": len(notable),
            "total_critical": len(critical),
        },
    }


async def get_related_events(event_id: int, limit: int = 5) -> list[dict]:
    """Get related events in the same domain."""
    async with get_db() as conn:
        async with conn.execute("SELECT domain FROM events WHERE id = ?", (event_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return []
            domain = row["domain"]

        async with conn.execute(
            "SELECT * FROM events WHERE domain = ? AND id != ? ORDER BY created_at DESC LIMIT ?",
            (domain, event_id, limit),
        ) as cur:
            return [_parse_event(dict(r)) for r in await cur.fetchall()]


async def get_daily_reports(limit: int = 30) -> list[dict]:
    """Get daily reports, most recent first."""
    async with get_db() as conn:
        async with conn.execute(
            "SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT ?",
            (limit,),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_daily_report_by_date(date_str: str) -> dict | None:
    """Get a daily report by date string (YYYY-MM-DD)."""
    async with get_db() as conn:
        async with conn.execute(
            "SELECT * FROM daily_reports WHERE report_date = ?",
            (date_str,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_stats(days: int = 30) -> dict:
    """Get statistics for the last N days."""
    interval = f"-{days} days"

    async with get_db() as conn:
        async with conn.execute(
            "SELECT date(created_at) as date, COUNT(*) as count FROM events "
            "WHERE created_at >= date('now', ?) GROUP BY date(created_at) ORDER BY date",
            (interval,),
        ) as cur:
            daily_trend = [{"date": r["date"], "count": r["count"]} for r in await cur.fetchall()]

        async with conn.execute(
            "SELECT category, COUNT(*) as count FROM events "
            "WHERE created_at >= date('now', ?) GROUP BY category ORDER BY count DESC",
            (interval,),
        ) as cur:
            category_distribution = [{"category": r["category"], "count": r["count"]} for r in await cur.fetchall()]

        async with conn.execute(
            "SELECT domain, COUNT(*) as count FROM events "
            "WHERE created_at >= date('now', ?) GROUP BY domain ORDER BY count DESC",
            (interval,),
        ) as cur:
            domain_distribution = [{"domain": r["domain"], "count": r["count"]} for r in await cur.fetchall()]

        async with conn.execute(
            "SELECT source, COUNT(*) as count FROM raw_items "
            "WHERE fetched_at >= date('now', ?) GROUP BY source ORDER BY count DESC",
            (interval,),
        ) as cur:
            source_distribution = [{"source": r["source"], "count": r["count"]} for r in await cur.fetchall()]

        async with conn.execute(
            "SELECT date(created_at) as date, ROUND(AVG(score), 2) as avg_score FROM events "
            "WHERE created_at >= date('now', ?) GROUP BY date(created_at) ORDER BY date",
            (interval,),
        ) as cur:
            avg_score_trend = [
                {"date": r["date"], "avg_score": r["avg_score"] or 0}
                for r in await cur.fetchall()
            ]

    return {
        "daily_trend": daily_trend,
        "category_distribution": category_distribution,
        "domain_distribution": domain_distribution,
        "source_distribution": source_distribution,
        "avg_score_trend": avg_score_trend,
    }
