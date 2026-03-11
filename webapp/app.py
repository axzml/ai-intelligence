import math
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

import database
from i18n import get_translator

app = FastAPI(title="AI Intelligence Hub")

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

CATEGORY_LABELS = {
    "en": {
        "model_release": "Model Release",
        "open_source_tool": "Open Source",
        "paper": "Paper",
        "industry": "Industry",
        "product_update": "Product Update",
        "tutorial": "Tutorial",
    },
    "zh": {
        "model_release": "模型发布",
        "open_source_tool": "开源工具",
        "paper": "论文",
        "industry": "行业动态",
        "product_update": "产品更新",
        "tutorial": "教程",
    },
}

DOMAIN_LABELS = {
    "en": {
        "llm": "LLM",
        "agent": "Agent",
        "multimodal": "Multimodal",
        "security": "Security",
        "application": "Application",
        "business": "Business",
    },
    "zh": {
        "llm": "大模型",
        "agent": "智能体",
        "multimodal": "多模态",
        "security": "安全",
        "application": "应用",
        "business": "商业",
    },
}

templates.env.globals["math"] = math


def get_lang(request: Request) -> str:
    """Get language from ?lang= param, cookie, or default to en."""
    lang = request.query_params.get("lang")
    if lang in ("en", "zh"):
        return lang
    cookie_lang = request.cookies.get("lang")
    if cookie_lang in ("en", "zh"):
        return cookie_lang
    return "en"


def make_ctx(request: Request, **extra) -> dict:
    """Build common template context with i18n support."""
    lang = get_lang(request)
    t = get_translator(lang)
    ctx = {
        "request": request,
        "lang": lang,
        "t": t,
        "category_labels": CATEGORY_LABELS.get(lang, CATEGORY_LABELS["en"]),
        "domain_labels": DOMAIN_LABELS.get(lang, DOMAIN_LABELS["en"]),
    }
    ctx.update(extra)
    return ctx


def set_lang_cookie(response: Response, lang: str) -> Response:
    """Set language preference cookie (30 days)."""
    response.set_cookie("lang", lang, max_age=30 * 86400, httponly=True, samesite="lax")
    return response


# ── Health ──────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ── HTML Pages ──────────────────────────────────────────

@app.get("/")
async def index(request: Request):
    try:
        data = await database.get_today_events()
        ctx = make_ctx(request,
            critical_events=data["critical"],
            notable_events=data["notable"],
            stats=data["stats"],
            error=None,
        )
    except Exception as e:
        ctx = make_ctx(request,
            critical_events=[],
            notable_events=[],
            stats={"total_collected": 0, "total_notable": 0, "total_critical": 0},
            error=str(e),
        )
    response = templates.TemplateResponse("index.html", ctx)
    return set_lang_cookie(response, ctx["lang"])


@app.get("/events")
async def events_page(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    score_min: Optional[int] = None,
    score_max: Optional[int] = None,
    category: Optional[str] = None,
    domain: Optional[str] = None,
    q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    try:
        events, total = await database.get_events(
            page=page, per_page=per_page, score_min=score_min,
            score_max=score_max, category=category, domain=domain,
            search=q, date_from=date_from, date_to=date_to,
        )
        total_pages = max(1, math.ceil(total / per_page))
        ctx = make_ctx(request,
            events=events, page=page, total=total, total_pages=total_pages,
            filters={
                "score_min": score_min, "score_max": score_max,
                "category": category, "domain": domain,
                "q": q, "date_from": date_from, "date_to": date_to,
            },
            error=None,
        )
    except Exception as e:
        ctx = make_ctx(request,
            events=[], page=1, total=0, total_pages=1,
            filters={}, error=str(e),
        )
    response = templates.TemplateResponse("events.html", ctx)
    return set_lang_cookie(response, ctx["lang"])


@app.get("/events/{event_id}")
async def event_detail(request: Request, event_id: int):
    event = await database.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    related = await database.get_related_events(event_id, limit=5)
    ctx = make_ctx(request, event=event, related_events=related)
    response = templates.TemplateResponse("event_detail.html", ctx)
    return set_lang_cookie(response, ctx["lang"])


@app.get("/daily")
async def daily_page(request: Request):
    try:
        reports = await database.get_daily_reports(limit=60)
        ctx = make_ctx(request, reports=reports, error=None)
    except Exception as e:
        ctx = make_ctx(request, reports=[], error=str(e))
    response = templates.TemplateResponse("daily.html", ctx)
    return set_lang_cookie(response, ctx["lang"])


@app.get("/daily/{report_date}")
async def daily_detail_page(request: Request, report_date: str):
    report = await database.get_daily_report_by_date(report_date)
    if report is None:
        raise HTTPException(status_code=404, detail="Daily report not found")
    ctx = make_ctx(request, report=report)
    response = templates.TemplateResponse("daily_detail.html", ctx)
    return set_lang_cookie(response, ctx["lang"])


@app.get("/stats")
async def stats_page(request: Request, days: int = Query(30, ge=1, le=365)):
    try:
        stats = await database.get_stats(days=days)
        ctx = make_ctx(request, stats=stats, days=days, error=None)
    except Exception as e:
        ctx = make_ctx(request, stats={}, days=days, error=str(e))
    response = templates.TemplateResponse("stats.html", ctx)
    return set_lang_cookie(response, ctx["lang"])


# ── JSON API ────────────────────────────────────────────

@app.get("/api/events")
async def api_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    score_min: Optional[int] = None,
    score_max: Optional[int] = None,
    category: Optional[str] = None,
    domain: Optional[str] = None,
    q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    events, total = await database.get_events(
        page=page, per_page=per_page, score_min=score_min,
        score_max=score_max, category=category, domain=domain,
        search=q, date_from=date_from, date_to=date_to,
    )
    return {
        "events": events,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, math.ceil(total / per_page)),
        },
    }


@app.get("/api/events/{event_id}")
async def api_event(event_id: int):
    event = await database.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.get("/api/search")
async def api_search(q: str = Query(..., min_length=1)):
    events, _ = await database.get_events(page=1, per_page=50, search=q)
    return events


@app.get("/api/stats")
async def api_stats(days: int = Query(30, ge=1, le=365)):
    return await database.get_stats(days=days)


@app.get("/api/daily/{report_date}")
async def api_daily(report_date: str):
    report = await database.get_daily_report_by_date(report_date)
    if report is None:
        raise HTTPException(status_code=404, detail="Daily report not found")
    return report
