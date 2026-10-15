"""Доступ к SQLite: соединения, инициализация схемы, rate limit, хэширование IP.

Все запросы параметризованные. Сырые IP нигде не храним — только HMAC-SHA256
с серверным секретом, который генерируется при первом запуске и лежит в settings.
"""
import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("DB_PATH") or str(BASE_DIR / "data" / "app.db")
_SCHEMA_FILE = BASE_DIR / "schema.sql"

_init_lock = threading.Lock()
_initialized = False
_secret_lock = threading.Lock()
_secret_cache: Optional[bytes] = None


def connect() -> sqlite3.Connection:
    """Новое соединение на операцию. SQLite + WAL этого достаточно для нашей нагрузки."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Создать каталог БД и применить schema.sql. Идемпотентно, один раз на процесс."""
    global _initialized
    with _init_lock:
        if _initialized:
            return
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = connect()
        try:
            with open(str(_SCHEMA_FILE), "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def _get_secret() -> bytes:
    """Серверный секрет для хэширования IP; создаётся при первом запуске."""
    global _secret_cache
    if _secret_cache is not None:
        return _secret_cache
    with _secret_lock:
        if _secret_cache is not None:
            return _secret_cache
        conn = connect()
        try:
            # INSERT OR IGNORE + SELECT: безопасно при гонке первых запросов
            # от нескольких воркеров uvicorn.
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('rl_secret', ?)",
                (secrets.token_bytes(32).hex(),),
            )
            conn.commit()
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'rl_secret'"
            ).fetchone()
            secret = bytes.fromhex(row["value"])
        finally:
            conn.close()
        _secret_cache = secret
        return secret


def client_key(ip: str) -> str:
    """Стабильный ключ клиента по IP без хранения самого IP."""
    return hmac.new(_get_secret(), ip.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def rate_limit(bucket: str, ident: str, limit: int, window_seconds: int) -> bool:
    """Фиксированное окно в SQLite. True — запрос разрешён.

    Окно фиксированное (не скользящее): на границе окон возможен всплеск до 2x
    лимита — для наших лимитов (10/час, 60/мин) это приемлемо.
    """
    now = int(time.time())
    window_start = now - (now % window_seconds)
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO rate_limits (bucket, ident, window_start, count) "
            "VALUES (?, ?, ?, 1) "
            "ON CONFLICT(bucket, ident, window_start) DO UPDATE SET count = count + 1",
            (bucket, ident, window_start),
        )
        row = conn.execute(
            "SELECT count FROM rate_limits "
            "WHERE bucket = ? AND ident = ? AND window_start = ?",
            (bucket, ident, window_start),
        ).fetchone()
        # Оппортунистическая чистка старых окон, чтобы таблица не росла.
        conn.execute("DELETE FROM rate_limits WHERE window_start < ?", (now - 172800,))
        conn.commit()
        return int(row["count"]) <= limit
    finally:
        conn.close()
