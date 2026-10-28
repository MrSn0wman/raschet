#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Курсы ЦБ РФ → assets/rates.json (только stdlib, для GitHub Actions и локального запуска).
# При любой проблеме — ненулевой выход, Action не коммитит мусор.
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

URL = "https://www.cbr.ru/scripts/XML_daily.asp"
CODES = ["USD", "EUR", "CNY", "GBP", "TRY", "AED", "KZT", "BYN", "UAH"]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "rates.json")


def main():
    # Аргумент командной строки: путь к локальному XML (для тестов/локального запуска
    # без TLS-проблем встроенного Python). Без аргумента — скачиваем с cbr.ru.
    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as f:
            raw = f.read()
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": "raschet-rates-bot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
    if len(raw) > 2_000_000:
        sys.exit("XML слишком большой: %d байт" % len(raw))

    root = ET.fromstring(raw.decode("windows-1251"))
    date_str = root.attrib.get("Date", "")
    date = datetime.strptime(date_str, "%d.%m.%Y").date().isoformat()

    rates = {}
    for v in root.findall("Valute"):
        code = v.findtext("CharCode")
        if code in CODES:
            nominal = float(v.findtext("Nominal").replace(",", "."))
            value = float(v.findtext("Value").replace(",", "."))
            if nominal > 0:
                rates[code] = round(value / nominal, 6)

    missing = [c for c in CODES if c not in rates]
    if missing:
        sys.exit("В ответе ЦБ нет валют: " + ", ".join(missing))
    for c, val in rates.items():
        if not (0.001 < val < 10000):
            sys.exit("Подозрительный курс %s = %s" % (c, val))

    payload = {"date": date, "source": "cbr.ru", "rates": rates}
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, OUT)
    print("rates.json: курсы ЦБ на %s (%d валют)" % (date, len(rates)))


if __name__ == "__main__":
    main()
