"""Minimal i18n support — UI string translations for en/zh."""

TRANSLATIONS = {
    # ── Navigation ──
    "site_title": {"en": "AI Intelligence Hub", "zh": "AI 情报中心"},
    "nav_home": {"en": "Home", "zh": "首页"},
    "nav_events": {"en": "Events", "zh": "事件"},
    "nav_daily": {"en": "Daily Reports", "zh": "日报"},
    "nav_stats": {"en": "Stats", "zh": "统计"},
    "search_placeholder": {"en": "Search events...", "zh": "搜索事件..."},
    "footer_text": {"en": "AI Intelligence Hub — Powered by OpenClaw", "zh": "AI 情报中心 — 由 OpenClaw 驱动"},

    # ── Home Page ──
    "today": {"en": "Today:", "zh": "今日："},
    "collected": {"en": "collected", "zh": "已采集"},
    "notable": {"en": "notable", "zh": "值得关注"},
    "critical": {"en": "critical", "zh": "紧急"},
    "critical_title": {"en": "Critical", "zh": "紧急事件"},
    "notable_title": {"en": "Notable", "zh": "值得关注"},
    "no_critical": {"en": "No critical events today", "zh": "今日暂无紧急事件"},
    "no_notable": {"en": "No notable events today", "zh": "今日暂无值得关注的事件"},
    "no_data_today": {"en": "No data collected today yet", "zh": "今日暂未采集数据"},
    "impact_label": {"en": "Impact:", "zh": "影响："},
    "view_all_events": {"en": "View All Events", "zh": "查看全部事件"},
    "daily_reports_link": {"en": "Daily Reports", "zh": "日报"},

    # ── Events Page ──
    "events_title": {"en": "Events", "zh": "事件列表"},
    "total_label": {"en": "total", "zh": "总计"},
    "filter_category": {"en": "Category", "zh": "分类"},
    "filter_domain": {"en": "Domain", "zh": "领域"},
    "filter_score_min": {"en": "Score Min", "zh": "最低分"},
    "filter_score_max": {"en": "Score Max", "zh": "最高分"},
    "filter_from": {"en": "From", "zh": "开始日期"},
    "filter_to": {"en": "To", "zh": "结束日期"},
    "filter_search": {"en": "Search", "zh": "搜索"},
    "filter_keyword": {"en": "Keyword...", "zh": "关键词..."},
    "btn_filter": {"en": "Filter", "zh": "筛选"},
    "btn_clear": {"en": "Clear", "zh": "清除"},
    "all_option": {"en": "All", "zh": "全部"},
    "sources_count": {"en": "sources", "zh": "来源"},
    "page_of": {"en": "Page {page} of {total_pages} ({total} events)", "zh": "第 {page}/{total_pages} 页（共 {total} 条）"},
    "prev": {"en": "Prev", "zh": "上一页"},
    "next": {"en": "Next", "zh": "下一页"},
    "no_events_found": {"en": "No events found", "zh": "未找到事件"},
    "no_events_hint": {"en": "Try adjusting your filters or search terms.", "zh": "请尝试调整筛选条件或搜索词。"},
    "reset_filters": {"en": "Reset Filters", "zh": "重置筛选"},

    # ── Event Detail ──
    "back_to_events": {"en": "Back to Events", "zh": "返回事件列表"},
    "summary": {"en": "Summary", "zh": "概要"},
    "impact_analysis": {"en": "Impact Analysis", "zh": "影响分析"},
    "sources": {"en": "Sources", "zh": "来源"},
    "related_events": {"en": "Related Events", "zh": "相关事件"},
    "event_not_found": {"en": "Event not found", "zh": "事件不存在"},

    # ── Daily Reports ──
    "daily_title": {"en": "Daily Reports", "zh": "每日报告"},
    "daily_subtitle": {"en": "AI intelligence summaries delivered daily at 19:00", "zh": "每日 19:00 推送 AI 情报摘要"},
    "col_date": {"en": "Date", "zh": "日期"},
    "col_collected": {"en": "Collected", "zh": "已采集"},
    "col_notable": {"en": "Notable", "zh": "关注"},
    "col_critical": {"en": "Critical", "zh": "紧急"},
    "btn_view": {"en": "View", "zh": "查看"},
    "no_reports_title": {"en": "No Reports Yet", "zh": "暂无报告"},
    "no_reports_hint": {"en": "Daily reports will appear here once the system starts collecting data.", "zh": "系统开始采集数据后，日报将在此显示。"},
    "back_to_daily": {"en": "Back to Daily Reports", "zh": "返回日报列表"},
    "daily_report_title": {"en": "Daily Report", "zh": "日报"},
    "report_not_found": {"en": "Report not found", "zh": "报告不存在"},
    "report_no_content": {"en": "Report content not available.", "zh": "报告内容不可用。"},

    # ── Stats Page ──
    "stats_title": {"en": "Statistics — Last {days} days", "zh": "统计 — 最近 {days} 天"},
    "time_range": {"en": "Time Range:", "zh": "时间范围："},
    "days_label": {"en": "{d} days", "zh": "{d} 天"},
    "chart_daily_events": {"en": "Daily Event Count", "zh": "每日事件数"},
    "chart_category": {"en": "Category Distribution", "zh": "分类分布"},
    "chart_domain": {"en": "Domain Distribution", "zh": "领域分布"},
    "chart_score": {"en": "Average Score Trend", "zh": "平均分趋势"},
    "source_distribution": {"en": "Source Distribution", "zh": "来源分布"},
    "no_source_data": {"en": "No source data available", "zh": "暂无来源数据"},

    # ── Common ──
    "lang_toggle": {"en": "中文", "zh": "English"},
}


def get_translator(lang: str):
    """Return a translation function for the given language."""
    def t(key: str, **kwargs) -> str:
        entry = TRANSLATIONS.get(key)
        if entry is None:
            return key
        text = entry.get(lang, entry.get("en", key))
        if kwargs:
            text = text.format(**kwargs)
        return text
    return t
