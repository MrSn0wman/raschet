# -*- coding: utf-8 -*-
# Укорочение title до ≤60 символов (пиксельный лимит выдачи ~600px).
# Патчит сгенерированные страницы; зеркало — old-источники и tools-дескрипторы ниже.
import io, os, re, sys

SITE = r"C:\Kimi\raschet"
OLD = r"C:\Kimi\raschet-old"
sys.path.insert(0, r"C:\Kimi\raschet\_build\build")
import build_all  # noqa: E402  (импорт без запуска: main() под guard)

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

for slug, nt in NEW.items():
    assert len(nt) <= 60, (slug, len(nt))

def patch_title(path, new_title):
    t = io.open(path, encoding="utf-8").read()
    m = re.search(r"(?s)<title>(.*?)</title>", t)
    if not m:
        return False
    t2 = t[:m.start(1)] + new_title + t[m.end(1):]
    if t2 != t:
        io.open(path, "w", encoding="utf-8", newline="\n").write(t2)
        return True
    return False

# обратная карта slug -> старое имя calc-*.html
rev = {v: k for k, v in build_all.LINK_MAP.items()}

done_site, done_old, missed_old = 0, 0, []
for slug, nt in NEW.items():
    page = os.path.join(SITE, "index.html" if slug == "" else slug + r"\index.html")
    if os.path.isfile(page) and patch_title(page, nt):
        done_site += 1
    old_name = rev.get(slug)
    if old_name:
        op = os.path.join(OLD, old_name)
        if os.path.isfile(op) and patch_title(op, nt):
            done_old += 1
        else:
            missed_old.append(slug)
    else:
        missed_old.append(slug)  # главная и tools-страницы — источник не в raschet-old

print("site pages patched:", done_site, "| old sources patched:", done_old)
print("no old-source (main/tools):", missed_old)
