"""FastAPI-приложение «Расчёт.рф»: курсы ЦБ, обратная связь, аналитика.

Запуск: uvicorn main:app --host 127.0.0.1 --port 8000 --proxy-headers
"""
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # до импорта db: там читается DB_PATH из окружения

import db  # noqa: E402
import feedback  # noqa: E402
import rates  # noqa: E402
import stats  # noqa: E402
from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("raschet")

MAX_BODY_BYTES = 32 * 1024  # сообщение обратной связи ≤ 5000 символов, хватит с запасом

PROD_ORIGINS = [
    "https://mrsn0wman.github.io",
]

DEV_ORIGINS = [
    # разработка фронта локально (только когда ENV != production)
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
]


def _allowed_origins():
    extra = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
    origins = list(PROD_ORIGINS) + extra
    if os.environ.get("ENV", "production") != "production":
        origins += DEV_ORIGINS
    return origins


@asynccontextmanager
async def lifespan(app):
    db.init_db()
    log.info("raschet-backend started, db=%s", db.DB_PATH)
    yield


app = FastAPI(
    title="raschet-backend",
    version="1.0.0",
    docs_url=None,       # в проде схема API не раздаётся
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    raw = request.headers.get("content-length")
    if raw is not None:
        try:
            if int(raw) > MAX_BODY_BYTES:
                return JSONResponse(status_code=413, content={"detail": "payload too large"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "bad content-length"})
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = "default-src 'none'"
    return resp


# CORS регистрируем последним: add_middleware ставит его снаружи остальных,
# чтобы CORS-заголовки были и на ответах об ошибках (413/429/500).
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    max_age=3600,
)


@app.get("/api/health")
def health():
    return {"ok": True}


app.include_router(rates.router)
app.include_router(feedback.router)
app.include_router(stats.router)
