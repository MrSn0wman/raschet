"""GET /api/rates — курсы валют ЦБ РФ.

Источник: https://www.cbr.ru/scripts/XML_daily.asp (XML, windows-1251).
Кэш: in-memory + SQLite, TTL 6 часов. Если ЦБ недоступен — отдаём последний
кэш с флагом stale:true. Если кэша нет вообще — 503.
"""
import asyncio
import json
import logging
import time
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Response

import db

log = logging.getLogger("raschet.rates")

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
TTL_SECONDS = 6 * 3600
HTTP_TIMEOUT = 8.0
MAX_XML_BYTES = 2_000_000  # защита от раздува; реальный ответ ЦБ ~30 КБ

router = APIRouter()

_lock = asyncio.Lock()
_mem_cache: Optional[dict] = None
_mem_fetched_at: float = 0.0
_last_attempt: float = 0.0  # negative-кэш: не дёргаем ЦБ чаще раза в минуту при сбоях
MIN_REFETCH_SECONDS = 60.0


def _parse_cbr(content: bytes) -> dict:
    """Разбор XML ЦБ. bytes — чтобы ElementTree сам применил encoding из декларации.

    Внешние сущности ElementTree не разрешает; раздутый XML отсекаем лимитом
    размера выше.
    """
    if len(content) > MAX_XML_BYTES:
        raise ValueError("CBR response too large")
    root = ET.fromstring(content)
    date_raw = root.attrib.get("Date", "")
    date_iso = date_raw
    try:
        day, month, year = date_raw.split(".")
        date_iso = "%s-%s-%s" % (year, month, day)
    except ValueError:
        pass
    rates = {}
    for valute in root.findall("Valute"):
        code = (valute.findtext("CharCode") or "").strip()
        nominal_raw = (valute.findtext("Nominal") or "1").strip()
        value_raw = (valute.findtext("Value") or "").strip()
        if not code or not value_raw:
            continue
        try:
            nominal = float(nominal_raw.replace(",", "."))
            value = float(value_raw.replace(",", "."))
            if nominal <= 0:
                continue
            rates[code] = round(value / nominal, 6)
        except ValueError:
            continue
    if not rates:
        raise ValueError("no rates parsed from CBR response")
    return {"date": date_iso, "base": "RUB", "rates": rates}


def _load_db_cache() -> Optional[Tuple[dict, int]]:
    conn = db.connect()
    try:
        row = conn.execute(
            "SELECT payload, fetched_at FROM rates_cache WHERE id = 1"
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"]), int(row["fetched_at"])
    finally:
        conn.close()


def _save_db_cache(payload: dict, fetched_at: int) -> None:
    conn = db.connect()
    try:
        conn.execute(
            "INSERT INTO rates_cache (id, payload, fetched_at) VALUES (1, ?, ?) "
            "ON CONFLICT(id) DO UPDATE "
            "SET payload = excluded.payload, fetched_at = excluded.fetched_at",
            (json.dumps(payload, ensure_ascii=False), fetched_at),
        )
        conn.commit()
    finally:
        conn.close()


async def _fetch_cbr() -> dict:
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.get(CBR_URL)
        resp.raise_for_status()
        return _parse_cbr(resp.content)


def _with_stale(payload: dict) -> dict:
    out = dict(payload)
    out["stale"] = True
    return out


@router.get("/api/rates")
async def get_rates(response: Response):
    global _mem_cache, _mem_fetched_at, _last_attempt
    now = time.time()
    if _mem_cache is not None and now - _mem_fetched_at < TTL_SECONDS:
        response.headers["Cache-Control"] = "public, max-age=3600"
        return _mem_cache

    async with _lock:
        now = time.time()
        if _mem_cache is not None and now - _mem_fetched_at < TTL_SECONDS:
            response.headers["Cache-Control"] = "public, max-age=3600"
            return _mem_cache

        cached = await asyncio.to_thread(_load_db_cache)
        if cached is not None and now - cached[1] < TTL_SECONDS:
            _mem_cache, _mem_fetched_at = cached[0], float(cached[1])
            response.headers["Cache-Control"] = "public, max-age=3600"
            return _mem_cache

        # negative-кэш: если недавняя попытка обновления упала — не ходим к ЦБ
        # чаще раза в MIN_REFETCH_SECONDS, отдаём устаревший кэш (или 503).
        if _last_attempt and now - _last_attempt < MIN_REFETCH_SECONDS:
            stale_source = cached if cached is not None else (
                (_mem_cache, int(_mem_fetched_at)) if _mem_cache is not None else None
            )
            if stale_source is None:
                raise HTTPException(status_code=503, detail="rates unavailable")
            _mem_cache, _mem_fetched_at = stale_source[0], float(stale_source[1])
            response.headers["Cache-Control"] = "public, max-age=300"
            return _with_stale(stale_source[0])

        try:
            _last_attempt = now
            fresh = await _fetch_cbr()
        except Exception as exc:
            # В лог — только тип ошибки, без тела ответа.
            log.warning("CBR fetch failed: %s", type(exc).__name__)
            stale_source = cached if cached is not None else (
                (_mem_cache, int(_mem_fetched_at)) if _mem_cache is not None else None
            )
            if stale_source is None:
                raise HTTPException(status_code=503, detail="rates unavailable")
            _mem_cache, _mem_fetched_at = stale_source[0], float(stale_source[1])
            response.headers["Cache-Control"] = "public, max-age=300"
            return _with_stale(stale_source[0])

        ts = int(now)
        _mem_cache, _mem_fetched_at = fresh, float(ts)
        await asyncio.to_thread(_save_db_cache, fresh, ts)
        response.headers["Cache-Control"] = "public, max-age=3600"
        return fresh
