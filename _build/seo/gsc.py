# -*- coding: utf-8 -*-
"""gsc.py — доступ к Google Search Console API через сервисный аккаунт.

Как работает: сервисный аккаунт — это «робот-пользователь». Вы добавляете его
email в Search Console как пользователя ресурса, и он получает те же права.
Ключ (JSON) не истекает, повторная авторизация в браузере не нужна.

Ключ НИКОГДА не коммитится. Храните его вне репозитория:
    C:\\Users\\<вы>\\.gsc\\service-account.json

Команды:
    python _build/seo/gsc.py whoami
    python _build/seo/gsc.py sitemaps
    python _build/seo/gsc.py submit
    python _build/seo/gsc.py inspect https://raschet.net/ipoteka/
    python _build/seo/gsc.py inspect-all [--out report.json]
    python _build/seo/gsc.py queries [--days 28] [--limit 50]

Общие флаги: --key ПУТЬ, --site URL
"""
import argparse
import json
import os
import re
import sys
import time
from urllib.parse import quote

# Консоль Windows по умолчанию cp1251 — принудительно UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

SCOPE = "https://www.googleapis.com/auth/webmasters"
DEFAULT_SITE = "https://raschet.net/"
DEFAULT_KEY = os.path.join(os.path.expanduser("~"), ".gsc", "service-account.json")
WM_BASE = "https://www.googleapis.com/webmasters/v3"
INSPECT_URL = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"

# URL Inspection API: квоты — 2000 запросов/день и 600/минуту на ресурс.
# Держим паузу, чтобы не поймать 429 на 78 страницах.
INSPECT_PAUSE = 0.2


def die(msg):
    print("ОШИБКА: " + msg)
    sys.exit(1)


def load_creds(key_path):
    if not os.path.isfile(key_path):
        die("не найден ключ: %s\n"
            "Скачайте JSON-ключ сервисного аккаунта и положите по этому пути,\n"
            "либо укажите другой через --key." % key_path)
    try:
        creds = service_account.Credentials.from_service_account_file(key_path, scopes=[SCOPE])
    except Exception as e:
        # не печатаем содержимое файла — только тип ошибки
        die("не удалось прочитать ключ (%s). Проверьте, что это JSON сервисного аккаунта." % type(e).__name__)
    try:
        creds.refresh(Request())
    except Exception as e:
        die("не удалось получить токен (%s).\n"
            "Проверьте: включён ли Search Console API в проекте и не отозван ли ключ." % type(e).__name__)
    return creds


def api(creds, method, url, **kw):
    headers = kw.pop("headers", {})
    headers["Authorization"] = "Bearer " + creds.token
    r = requests.request(method, url, headers=headers, timeout=60, **kw)
    if r.status_code == 401:
        die("401: сервисный аккаунт не авторизован. Добавьте его email в GSC → Настройки → Пользователи.")
    return r


def enc(site):
    return quote(site, safe="")


def cmd_whoami(creds, key_path, site):
    with open(key_path, encoding="utf-8") as f:
        info = json.load(f)
    print("Сервисный аккаунт: %s" % info.get("client_email", "?"))
    print("Проект:            %s" % info.get("project_id", "?"))
    r = api(creds, "GET", "%s/sites" % WM_BASE)
    if r.status_code != 200:
        die("не удалось получить список ресурсов (HTTP %d): %s" % (r.status_code, r.text[:300]))
    sites = [s.get("siteUrl") for s in r.json().get("siteEntry", [])]
    print("Доступные ресурсы (%d):" % len(sites))
    for s in sites:
        print("  " + s)
    if site not in sites:
        print("\nВНИМАНИЕ: %s отсутствует в списке. Добавьте сервисный аккаунт как пользователя в GSC." % site)
    return 0


def cmd_sitemaps(creds, site):
    r = api(creds, "GET", "%s/sites/%s/sitemaps" % (WM_BASE, enc(site)))
    if r.status_code != 200:
        die("HTTP %d: %s" % (r.status_code, r.text[:300]))
    items = r.json().get("sitemap", [])
    if not items:
        print("Карт нет.")
        return 0
    for s in items:
        print("%s" % s.get("path"))
        print("   последнее чтение: %s | тип: %s" % (s.get("lastDownloaded"), s.get("type")))
        for k in ("contents",):
            for c in s.get(k, []) or []:
                print("   %s: отправлено %s, проиндексировано %s" % (
                    c.get("type"), c.get("submitted"), c.get("indexed")))
        errs = s.get("errors") or 0
        warns = s.get("warnings") or 0
        if errs or warns:
            print("   ОШИБКИ: %s | предупреждения: %s" % (errs, warns))
    return 0


def cmd_submit(creds, site):
    feed = site.rstrip("/") + "/sitemap.xml"
    r = api(creds, "PUT", "%s/sites/%s/sitemaps/%s" % (WM_BASE, enc(site), enc(feed)))
    if r.status_code in (200, 204):
        print("Отправлено: %s" % feed)
        return 0
    die("HTTP %d: %s" % (r.status_code, r.text[:400]))


def cmd_inspect(creds, site, url):
    body = {"inspectionUrl": url, "siteUrl": site}
    r = api(creds, "POST", INSPECT_URL, json=body)
    if r.status_code != 200:
        return {"url": url, "error": "HTTP %d: %s" % (r.status_code, r.text[:200])}
    res = r.json().get("inspectionResult", {})
    idx = res.get("indexStatusResult", {}) or {}
    return {
        "url": url,
        "verdict": idx.get("verdict"),
        "coverageState": idx.get("coverageState"),
        "robotsTxtState": idx.get("robotsTxtState"),
        "indexingState": idx.get("indexingState"),
        "pageFetchState": idx.get("pageFetchState"),
        "lastCrawlTime": idx.get("lastCrawlTime"),
        "googleCanonical": idx.get("googleCanonical"),
        "userCanonical": idx.get("userCanonical"),
        "crawledAs": idx.get("crawledAs"),
    }


def cmd_inspect_all(creds, site, out_path):
    # список URL берём из локального sitemap.xml — он совпадает с продом
    sm_path = os.path.join(os.getcwd(), "sitemap.xml")
    if os.path.isfile(sm_path):
        with open(sm_path, encoding="utf-8") as f:
            urls = re.findall(r"<loc>([^<]+)</loc>", f.read())
        print("URL из sitemap.xml: %d" % len(urls))
    else:
        die("не найден sitemap.xml в текущей папке")

    results = []
    for i, u in enumerate(urls, 1):
        results.append(cmd_inspect(creds, site, u))
        if i % 10 == 0 or i == len(urls):
            print("  проверено %d / %d" % (i, len(urls)))
        time.sleep(INSPECT_PAUSE)

    ok = [r for r in results if r.get("verdict") == "PASS"]
    err = [r for r in results if r.get("error")]
    other = [r for r in results if not r.get("error") and r.get("verdict") != "PASS"]

    print("\n=== ИТОГ ===")
    print("Проиндексировано (PASS): %d из %d" % (len(ok), len(results)))
    if err:
        print("Ошибок запроса: %d" % len(err))
    if other:
        print("Не проиндексировано: %d" % len(other))
        for r in other[:20]:
            print("  %s -> %s" % (r["url"], r.get("coverageState") or r.get("verdict")))

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("Отчёт сохранён: %s" % out_path)
    return 0


def cmd_queries(creds, site, days, limit):
    import datetime
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["query"],
        "rowLimit": limit,
    }
    r = api(creds, "POST", "%s/sites/%s/searchAnalytics/query" % (WM_BASE, enc(site)), json=body)
    if r.status_code != 200:
        die("HTTP %d: %s" % (r.status_code, r.text[:400]))
    rows = r.json().get("rows", [])
    if not rows:
        print("Данных пока нет (нормально для нового ресурса — нужно 2-3 дня).")
        return 0
    print("%-50s %8s %8s %8s %8s" % ("ЗАПРОС", "КЛИКИ", "ПОКАЗЫ", "CTR%", "ПОЗИЦИЯ"))
    for row in rows:
        q = (row.get("keys") or ["?"])[0]
        print("%-50s %8d %8d %7.1f%% %8.1f" % (
            q[:50], row.get("clicks", 0), row.get("impressions", 0),
            (row.get("ctr") or 0) * 100, row.get("position") or 0))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Google Search Console через сервисный аккаунт")
    ap.add_argument("command", choices=["whoami", "sitemaps", "submit", "inspect", "inspect-all", "queries"])
    ap.add_argument("target", nargs="?", help="URL для inspect")
    ap.add_argument("--key", default=os.environ.get("GSC_KEY", DEFAULT_KEY))
    ap.add_argument("--site", default=DEFAULT_SITE)
    ap.add_argument("--out", default=None)
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    creds = load_creds(args.key)

    if args.command == "whoami":
        return cmd_whoami(creds, args.key, args.site)
    if args.command == "sitemaps":
        return cmd_sitemaps(creds, args.site)
    if args.command == "submit":
        return cmd_submit(creds, args.site)
    if args.command == "inspect":
        if not args.target:
            die("укажите URL: gsc.py inspect https://raschet.net/")
        print(json.dumps(cmd_inspect(creds, args.site, args.target), ensure_ascii=False, indent=2))
        return 0
    if args.command == "inspect-all":
        return cmd_inspect_all(creds, args.site, args.out)
    if args.command == "queries":
        return cmd_queries(creds, args.site, args.days, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())