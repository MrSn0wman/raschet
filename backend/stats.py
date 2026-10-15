"""Своя аналитика: POST /api/event и GET /api/popular.

Храним только агрегаты (day, page, type, count). Поле meta принимаем для
совместимости контракта, валидируем по размеру и НЕ сохраняем — персональные
данные не нужны, агрегатам meta не требуется.
"""
import json
import re
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

import db

router = APIRouter()

PAGE_RE = re.compile(r"^[a-z0-9][a-z0-9\-_/]{0,99}$")
EVENT_LIMIT = 60          # запросов
EVENT_WINDOW = 60         # в минуту
META_MAX_BYTES = 1024
POPULAR_DAYS = 30


class EventIn(BaseModel):
    type: str
    page: str = Field(max_length=100)
    meta: Optional[Dict[str, Any]] = None

    @field_validator("type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in ("view", "calc"):
            raise ValueError("type must be 'view' or 'calc'")
        return v

    @field_validator("page")
    @classmethod
    def _check_page(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not PAGE_RE.match(v):
            raise ValueError("invalid page slug")
        return v

    @field_validator("meta")
    @classmethod
    def _check_meta(cls, v):
        if v is None:
            return None
        if len(json.dumps(v, ensure_ascii=False)) > META_MAX_BYTES:
            raise ValueError("meta too large")
        return v


def _bump(ev: EventIn) -> None:
    day = time.strftime("%Y-%m-%d", time.gmtime())
    conn = db.connect()
    try:
        conn.execute(
            "INSERT INTO stats_daily (day, page, type, count) VALUES (?, ?, ?, 1) "
            "ON CONFLICT(day, page, type) DO UPDATE SET count = count + 1",
            (day, ev.page, ev.type),
        )
        conn.commit()
    finally:
        conn.close()


def _top_pages(limit: int) -> List[dict]:
    conn = db.connect()
    try:
        rows = conn.execute(
            "SELECT page, "
            "SUM(CASE WHEN type = 'view' THEN count ELSE 0 END) AS views, "
            "SUM(CASE WHEN type = 'calc' THEN count ELSE 0 END) AS calcs, "
            "SUM(count) AS total "
            "FROM stats_daily "
            "WHERE day >= date('now', '-30 days') "
            "GROUP BY page ORDER BY total DESC, page ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"page": r["page"], "views": r["views"], "calcs": r["calcs"], "total": r["total"]}
            for r in rows
        ]
    finally:
        conn.close()


@router.post("/api/event")
def track_event(ev: EventIn, request: Request):
    ip = request.client.host if request.client else "unknown"
    if not db.rate_limit("event", db.client_key(ip), EVENT_LIMIT, EVENT_WINDOW):
        raise HTTPException(status_code=429, detail="too many requests")
    _bump(ev)
    return {"ok": True}


@router.get("/api/popular")
def popular(limit: int = Query(default=10, ge=1, le=50)):
    return {"days": POPULAR_DAYS, "items": _top_pages(limit)}
