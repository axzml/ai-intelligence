#!/usr/bin/env python3
"""
AI Intelligence System — 数据库初始化脚本
运行: python scripts/init_db.py
"""

import sqlite3
import os
import sys

DB_DIR = os.path.expanduser("~/ai-intelligence/data")
DB_PATH = os.path.join(DB_DIR, "intelligence.db")


def init_database():
    """创建数据库和所有表结构"""
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 启用 WAL 模式: 允许读写并发
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")

    # 表1: raw_items — 原始采集数据
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS raw_items (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        source       TEXT NOT NULL,
        source_id    TEXT,
        url          TEXT,
        title        TEXT NOT NULL,
        content      TEXT,
        author       TEXT,
        metrics      TEXT DEFAULT '{}',
        published_at DATETIME,
        fetched_at   DATETIME DEFAULT (datetime('now')),
        processed    INTEGER DEFAULT 0,
        UNIQUE(source, source_id)
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_items_processed ON raw_items(processed);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_items_fetched ON raw_items(fetched_at);")

    # 表2: events — 去重聚类后的事件
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT NOT NULL,
        summary      TEXT,
        impact       TEXT,
        category     TEXT NOT NULL,
        domain       TEXT NOT NULL,
        score        INTEGER NOT NULL CHECK(score BETWEEN 1 AND 10),
        sources      TEXT DEFAULT '[]',
        raw_item_ids TEXT DEFAULT '[]',
        created_at   DATETIME DEFAULT (datetime('now')),
        notified     INTEGER DEFAULT 0,
        in_daily     INTEGER DEFAULT 0,
        daily_date   TEXT
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_score ON events(score);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_domain ON events(domain);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_notified ON events(notified);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_daily ON events(in_daily, daily_date);")

    # 表3: daily_reports — 日报存档
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_reports (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        report_date     TEXT UNIQUE NOT NULL,
        total_collected INTEGER DEFAULT 0,
        total_notable   INTEGER DEFAULT 0,
        total_critical  INTEGER DEFAULT 0,
        content_html    TEXT,
        content_text    TEXT,
        sent_at         DATETIME,
        created_at      DATETIME DEFAULT (datetime('now'))
    );
    """)

    # 表4: fetch_log — 采集日志
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fetch_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        source      TEXT NOT NULL,
        started_at  DATETIME DEFAULT (datetime('now')),
        finished_at DATETIME,
        item_count  INTEGER DEFAULT 0,
        status      TEXT DEFAULT 'running',
        error_msg   TEXT
    );
    """)

    # 表5: config — 系统配置
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        key         TEXT PRIMARY KEY,
        value       TEXT NOT NULL,
        description TEXT,
        updated_at  DATETIME DEFAULT (datetime('now'))
    );
    """)

    # 插入默认配置
    default_config = [
        ("score_threshold_notify", "7", "即时通知最低分数"),
        ("score_threshold_daily", "4", "进入日报最低分数"),
        ("daily_report_time", "19:00", "日报发送时间"),
        ("collect_interval_hours", "2", "采集间隔(小时)"),
        ("analyze_interval_hours", "2", "分析间隔(小时)"),
        (
            "user_interests",
            '["大模型进展","Agent应用","AI商业化","AI安全"]',
            "用户兴趣标签",
        ),
        ("resend_api_key", "", "Resend SMTP API key (用作密码)"),
        ("email_sender", "", "发件地址 (需在 Resend 验证域名)"),
        ("email_recipient", "", "收件地址"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO config (key, value, description) VALUES (?, ?, ?)",
        default_config,
    )

    conn.commit()
    conn.close()

    print(f"Database initialized at: {DB_PATH}")
    print(f"Tables created: raw_items, events, daily_reports, fetch_log, config")
    print(f"WAL mode enabled for concurrent read/write")


if __name__ == "__main__":
    init_database()
