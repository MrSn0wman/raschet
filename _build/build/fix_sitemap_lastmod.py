# -*- coding: utf-8 -*-
"""fix_sitemap_lastmod.py — проставляет в sitemap.xml реальные даты последних
изменений файлов по истории git вместо единой даты сборки.

Зачем: build_all.py ставит lastmod = дата сборки для ВСЕХ URL сразу. После
нескольких правок отдельных страниц карта врёт, Google перестаёт доверять
lastmod и реже переобходит сайт.

Запуск (из корня репозитория, после build_all.py):
    python _build/build/fix_sitemap_lastmod.py
    python _build/build/fix_sitemap_lastmod.py --site C:\\САЙТ --dry-run
"""
import argparse
import io
import os
import re
import subprocess
import sys

# Консоль Windows по умолчанию cp1251 — принудительно UTF-8, иначе падаем
# на символах вроде «×» при печати отчёта.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_URL = "https://raschet.net/"
DEFAULT_SITE = r"C:\САЙТ"


def git_date(repo, rel_path):
    """Дата последнего коммита, затронувшего файл (YYYY-MM-DD) или None."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", rel_path],
            cwd=repo, capture_output=True, text=True, timeout=30,
        )
        d = out.stdout.strip()
        return d if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else None
    except Exception:
        return None


def url_to_file(url):
    """https://raschet.net/ipoteka/ -> ipoteka/index.html"""
    if not url.startswith(BASE_URL):
        return None
    rel = url[len(BASE_URL):].strip("/")
    return "index.html" if rel == "" else rel + "/index.html"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=DEFAULT_SITE, help="корень репозитория")
    ap.add_argument("--dry-run", action="store_true", help="только показать, не писать")
    args = ap.parse_args()

    site = os.path.abspath(args.site)
    smap = os.path.join(site, "sitemap.xml")
    if not os.path.isfile(smap):
        sys.exit("не найден " + smap)

    text = io.open(smap, encoding="utf-8").read()
    locs = re.findall(r"<loc>([^<]+)</loc>", text)
    if not locs:
        sys.exit("в sitemap нет <loc>")

    changed, missing, dates = [], [], {}
    for url in locs:
        rel = url_to_file(url)
        if rel is None:
            missing.append((url, "URL вне BASE_URL"))
            continue
        if not os.path.isfile(os.path.join(site, rel.replace("/", os.sep))):
            missing.append((url, "нет файла " + rel))
            continue
        d = git_date(site, rel)
        if d is None:
            missing.append((url, "нет истории git для " + rel))
            continue
        dates[url] = d

    def repl(m):
        url = m.group(1)
        d = dates.get(url)
        return "<loc>%s</loc><lastmod>%s</lastmod>" % (url, d) if d else m.group(0)

    new_text, n = re.subn(r"<loc>([^<]+)</loc><lastmod>[^<]*</lastmod>", repl, text)

    # отчёт
    uniq = {}
    for d in dates.values():
        uniq[d] = uniq.get(d, 0) + 1
    print("URL в карте: %d | обновлено lastmod: %d" % (len(locs), n))
    print("дат: %s" % ", ".join("%s×%d" % (k, v) for k, v in sorted(uniq.items())))
    if missing:
        print("ПРОПУЩЕНО (%d):" % len(missing))
        for u, why in missing:
            print("  %s — %s" % (u, why))

    if args.dry_run:
        print("--dry-run: файл не изменён")
        return

    if new_text == text:
        print("sitemap.xml уже актуален — изменений нет")
        return

    if len(re.findall(r"<loc>", new_text)) != len(locs):
        sys.exit("ОТКАЗ: число <loc> изменилось — правка отменена")
    io.open(smap, "w", encoding="utf-8", newline="\n").write(new_text)
    print("sitemap.xml обновлён")


if __name__ == "__main__":
    main()