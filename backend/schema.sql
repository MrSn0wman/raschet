-- Схема БД «Расчёт.net» (SQLite). Применяется автоматически при старте (init_db).

-- Кэш курсов ЦБ РФ: всегда одна строка (id = 1).
CREATE TABLE IF NOT EXISTS rates_cache (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    payload    TEXT NOT NULL,          -- JSON: {date, base, rates:{...}}
    fetched_at INTEGER NOT NULL        -- unixtime последнего успешного забора с ЦБ
);

-- Обращения из формы обратной связи.
CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at INTEGER NOT NULL,       -- unixtime (UTC)
    name       TEXT,
    email      TEXT,
    topic      TEXT NOT NULL,
    message    TEXT NOT NULL,
    page       TEXT,
    ip_hash    TEXT,                   -- HMAC-SHA256(IP), сырой IP не храним
    emailed    INTEGER NOT NULL DEFAULT 0  -- 1 = письмо ушло через SMTP
);

-- Агрегированная аналитика: счётчики по дню/странице/типу. Без персональных данных.
CREATE TABLE IF NOT EXISTS stats_daily (
    day   TEXT NOT NULL,               -- YYYY-MM-DD (UTC)
    page  TEXT NOT NULL,               -- slug страницы: "ipoteka", "valyuta", ...
    type  TEXT NOT NULL CHECK (type IN ('view', 'calc')),
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (day, page, type)
);
CREATE INDEX IF NOT EXISTS idx_stats_day ON stats_daily(day);

-- Счётчики rate limit (фиксированное окно). ident — хэш IP, не сам IP.
CREATE TABLE IF NOT EXISTS rate_limits (
    bucket       TEXT NOT NULL,        -- 'feedback' | 'event'
    ident        TEXT NOT NULL,
    window_start INTEGER NOT NULL,     -- unixtime начала окна
    count        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (bucket, ident, window_start)
);

-- Служебные ключи (например, секрет для HMAC хэширования IP).
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
