# -*- coding: utf-8 -*-
"""Idempotent title shortening on output only; page sources retain SEO metadata."""
import io, os, re
from site_common import read, write, site_parser

NEW = {
    "": "Расчёт.net — онлайн-калькуляторы: ипотека, налоги, проценты",
    "avtokredit": "Калькулятор автокредита 2026 — платёж и переплата",
    "dekretnye": "Калькулятор декретных 2026 — расчёт пособия | Расчёт.net",
    "dni": "Калькулятор дней — разница между датами | Расчёт.net",
    "doli-v-kvartire": "Калькулятор долей в квартире — площадь и стоимость",
    "dosrochnoe-pogashenie": "Досрочное погашение ипотеки — срок или платёж | Расчёт.net",
    "drobi": "Калькулятор дробей онлайн — все действия | Расчёт.net",
    "generator-promokodov": "Генератор промокодов онлайн — пачка уникальных кодов",
    "iis": "Калькулятор ИИС 2026 — вычет на взнос и доход",
    "ipoteka": "Калькулятор ипотеки онлайн — платёж и переплата",
    "konverter-edinic": "Конвертер единиц — длина, вес, температура, объём",
    "mikrozaim": "Калькулятор микрозайма 2026 — переплата с лимитом",
    "ndfl": "Калькулятор НДФЛ 2026 — шкала 13-22% | Расчёт.net",
    "nds": "Калькулятор НДС 2026 — начислить или выделить",
    "neustoika-po-ddu": "Неустойка по ДДУ 2026 — калькулятор просрочки | Расчёт.net",
    "neustoika-po-dogovoru": "Калькулятор неустойки по договору — с лимитом",
    "nod": "Калькулятор НОД — наибольший общий делитель",
    "nok": "Калькулятор НОК — наименьшее общее кратное",
    "osago": "Калькулятор ОСАГО 2026 — стоимость полиса",
    "otpusknye": "Калькулятор отпускных 2026 — по среднему заработку",
    "otpusknye-dni": "Калькулятор отпускных дней — сколько накопилось",
    "peni-po-nalogam": "Пени по налогам 2026 — 1/300 и 1/150 ставки ЦБ",
    "ploshad": "Калькулятор площади — прямоугольник, круг, треугольник",
    "procenty": "Калькулятор процентов — доля, изменение, соотношение",
    "rashod-topliva": "Калькулятор расхода топлива — стоимость поездки",
    "rastamozhka": "Растаможка автомобиля 2026 — калькулятор для физлиц",
    "refinansirovanie": "Рефинансирование кредита 2026 — экономия | Расчёт.net",
    "sravnenie-spiskov": "Сравнение списков онлайн — общие и уникальные элементы",
    "summa-propisyu": "Сумма прописью онлайн — рубли, доллары, евро",
    "utilsbor": "Утильсбор 2026 — калькулятор для физлиц | Расчёт.net",
    "vozrast": "Калькулятор возраста — годы, месяцы, дни | Расчёт.net",
    "zaryadka-elektromobilya": "Зарядка электромобиля — время и стоимость | Расчёт.net",
}

def patch_title(path, new_title):
    t = read(path)
    m = re.search(r"(?s)<title>(.*?)</title>", t)
    if not m:
        return False
    t2 = t[:m.start(1)] + new_title + t[m.end(1):]
    if t2 != t:
        write(path, t2)
        return True
    return False

def process(site):
    from site_common import safe_destination
    site = safe_destination(site)
    count = 0
    for slug, title in NEW.items():
        if len(title) > 60: raise ValueError("Title exceeds limit: " + slug)
        path = site / (slug + "/index.html" if slug else "index.html")
        if path.is_file() and patch_title(path, title): count += 1
    print("Titles shortened:", count)

if __name__ == "__main__":
    process(site_parser(__doc__).parse_args().site)
