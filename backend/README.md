# raschet-backend

Бэкенд для сайта калькуляторов «Расчёт.рф» (статический фронт на GitHub Pages).
Python 3.9+, FastAPI + SQLite, uvicorn, за nginx.

## Функции

| Эндпоинт | Описание |
|---|---|
| `GET /api/rates` | Курсы валют ЦБ РФ. Кэш 6 ч (память + SQLite); при недоступности ЦБ — последний кэш с `"stale": true`; если кэша нет — 503 |
| `POST /api/feedback` | Обратная связь: валидация, honeypot `website`, rate limit 10/час по IP, запись в SQLite + email через SMTP (если настроен) |
| `POST /api/event` | Аналитика `{type: "view"\|"calc", page, meta?}` — инкремент агрегатных счётчиков; rate limit 60/мин по IP |
| `GET /api/popular?limit=10` | Топ страниц по view+calc за 30 дней |
| `GET /api/health` | Проверка живости |

## Локальный запуск

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Проверка: `curl http://127.0.0.1:8000/api/health` → `{"ok":true}`.

## Деплой на Ubuntu (VPS)

### 1. Код и окружение

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx

sudo mkdir -p /opt/raschet-backend
sudo chown $USER:$USER /opt/raschet-backend
# скопировать код: git clone ... /opt/raschet-backend  или  scp -r ./raschet-backend user@host:/opt/

cd /opt/raschet-backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env            # заполнить SMTP_* и FEEDBACK_TO
```

### 2. systemd unit

`/etc/systemd/system/raschet-backend.service`:

```ini
[Unit]
Description=raschet-backend (FastAPI)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/raschet-backend
EnvironmentFile=/opt/raschet-backend/.env
ExecStart=/opt/raschet-backend/venv/bin/uvicorn main:app \
    --host 127.0.0.1 --port 8000 \
    --proxy-headers --forwarded-allow-ips 127.0.0.1
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /opt/raschet-backend/data
sudo chown -R www-data:www-data /opt/raschet-backend/data
sudo chmod 600 /opt/raschet-backend/.env
sudo chown root:root /opt/raschet-backend/.env   # root читает unit, www-data — нет...
# Проще: EnvironmentFile читает systemd (root), поэтому владелец root:root 600 — ок.
sudo systemctl daemon-reload
sudo systemctl enable --now raschet-backend
systemctl status raschet-backend
journalctl -u raschet-backend -f   # логи
```

`--proxy-headers --forwarded-allow-ips 127.0.0.1` важны: uvicorn берёт IP клиента
из `X-Forwarded-For`, который ставит nginx, — от этого зависят rate limits.

### 3. nginx reverse proxy

`/etc/nginx/sites-available/raschet-backend`:

```nginx
server {
    listen 80;
    server_name api.ваш-домен.ru;   # заменить

    client_max_body_size 64k;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 15s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/raschet-backend /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. HTTPS (certbot)

```bash
sudo certbot --nginx -d api.ваш-домен.ru
# certbot сам добавит listen 443, редирект 80→443 и автообновление сертификата
```

HSTS добавить в server-блок 443 (опционально, но рекомендуется):
`add_header Strict-Transport-Security "max-age=31536000" always;`

### 5. Обслуживание

```bash
# логи
journalctl -u raschet-backend -n 200 --no-pager

# бэкап БД (SQLite): файл data/app.db (+ .wal)
sqlite3 /opt/raschet-backend/data/app.db ".backup '/root/app-backup.db'"

# обновление кода
cd /opt/raschet-backend && git pull && ./venv/bin/pip install -r requirements.txt
sudo systemctl restart raschet-backend
```

## Контракт для фронта (мягкая деградация)

Фронт (GitHub Pages) обязан вызывать API с **таймаутом 3 секунды** и иметь
фолбэки на случай недоступности:

```js
async function apiFetch(path, options = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 3000);
  try {
    const r = await fetch(API_BASE + path, { ...options, signal: ctrl.signal });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } finally {
    clearTimeout(timer);
  }
}
```

| Вызов | Если API недоступен |
|---|---|
| `GET /api/rates` | Конвертер использует офлайн-курс, зашитый в фронт, и **показывает его дату**: «курс от 12.10.2026 (офлайн)». Если API ответил с `"stale": true` — курс применяется, показывается плашка «курсы от {date}, обновление временно недоступно» |
| `POST /api/feedback` | Форма показывает mailto-фолбэк: «Не удалось отправить. Напишите нам: you@example.com» |
| `GET /api/popular` | Блок «Популярное» показывает статичный дефолтный список из фронта |
| `POST /api/event` | Молча пропускаем (fire-and-forget, `.catch(() => {})`), никаких повторов и очередей |

Формат `GET /api/rates`:

```json
{
  "date": "2026-10-15",
  "base": "RUB",
  "rates": {"USD": 81.2345, "EUR": 94.12, "CNY": 11.4, "GBP": 108.3, "...": "..."},
  "stale": true
}
```

- `rates` — все валюты из дневной выгрузки ЦБ, значение — рублей за 1 единицу валюты (номинал уже учтён).
- `stale` присутствует и равно `true` только когда ЦБ недоступен и отдан кэш.

## Безопасность и приватность

- Все SQL-запросы параметризованные; `eval`/`exec` нет; секреты только из `.env`.
- Заголовки: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Content-Security-Policy: default-src 'none'`; лимит тела запроса 32 КБ (плюс 64 КБ в nginx).
- CORS — строгий список origins: `https://mrsn0wman.github.io` + `CORS_ORIGINS` из `.env`. localhost-origins включаются только при `ENV=dev` в `.env` (в проде не ставить!).
- При недоступности ЦБ `/api/rates` отдаёт последний кэш со `stale:true`; повторный поход к ЦБ — не чаще раза в 60 с (negative-кэш), чтобы не усиливать чужой сбой.
- Rate limits хранятся в SQLite, работают под несколькими воркерами; IP хэшируется HMAC-SHA256 (секрет генерируется при первом запуске, таблица `settings`), сырой IP нигде не сохраняется.
- Аналитика — только агрегаты `(day, page, type, count)`. Поле `meta` принимается и валидируется, но **не сохраняется**.
- В логах — только метаданные (id обращения, тип ошибки); текст сообщений не логируется.
- Форма: honeypot-поле `website` — боты получают `{"ok": true}`, но ничего не сохраняется.
