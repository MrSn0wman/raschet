# -*- coding: utf-8 -*-
# Главная v2: hero (из старой), «Популярное», каталог 13 секций × 73 карточки
# (60 старых переиспользуются с иконками, 13 новых — синтез), trust-strip.
import json
import re
import io
import os

SRC = r"C:\Kimi\raschet\index.html"
PARTS = r"C:\Kimi\raschet-redesign\parts"
OUT = r"C:\Kimi\raschet-redesign\index.html"
BASE_URL = "https://mrsn0wman.github.io/raschet/"

def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

style_css = read(os.path.join(PARTS, "style.css"))
fonts_css = read(os.path.join(PARTS, "fonts.css")).replace("__PREFIX__", "")
style_css = fonts_css + "\n" + style_css
header = read(os.path.join(PARTS, "header.html"))
footer = read(os.path.join(PARTS, "footer.html"))
head_init = read(os.path.join(PARTS, "head-init.html"))
ui_js = read(os.path.join(PARTS, "ui.js"))

old = read(SRC)

def must(pattern, text, flags=0, name=""):
    m = re.search(pattern, text, flags)
    if not m:
        raise SystemExit("NOT FOUND: " + name)
    return m

title = must(r"<title>(.*?)</title>", old, re.S, "title").group(1).strip()
desc = must(r'<meta name="description" content="([^"]*)"', old, 0, "description").group(1)
og_title = must(r'<meta property="og:title" content="([^"]*)"', old, 0, "og:title").group(1)
og_desc = must(r'<meta property="og:description" content="([^"]*)"', old, 0, "og:description").group(1)

ld_raw = must(r'<script type="application/ld\+json">(.*?)</script>', old, re.S, "json-ld").group(1)
ld = json.loads(ld_raw)

def fix_node(node):
    if isinstance(node, dict):
        node.pop("potentialAction", None)
        for k, v in list(node.items()):
            if isinstance(v, str) and "raschet.rf" in v:
                node[k] = v.replace("https://raschet.rf/", BASE_URL)
            else:
                fix_node(v)
    elif isinstance(node, list):
        for item in node:
            fix_node(item)

fix_node(ld)
ld_out = json.dumps(ld, ensure_ascii=False, indent=2)

# --- hero из старой главной ---
hero = must(r'<section class="hero">.*?</section>', old, re.S, "hero").group(0)
hero, n = re.subn(r'<button class="btn btn-primary" onclick="[^"]*">Найти</button>',
                  '<button class="btn btn-primary" id="finder-btn" type="button">Найти</button>', hero)
assert n == 1
hero = hero.replace("60 калькуляторов · без регистрации", "73 инструмента · без регистрации")
hero = hero.replace("55 054 ₽/мес", "55 054&nbsp;₽/мес")
hero = hero.replace("8 213 034 ₽", "8 213 034&nbsp;₽").replace("13 213 034 ₽", "13 213 034&nbsp;₽")

# --- trust-strip (балансированный div) ---
def extract_balanced_div(text, start_marker):
    i = text.find(start_marker)
    assert i >= 0, start_marker
    depth = 0
    j = i
    while True:
        nxt_open = text.find("<div", j)
        nxt_close = text.find("</div>", j)
        assert nxt_close >= 0
        if 0 <= nxt_open < nxt_close:
            depth += 1
            j = nxt_open + 4
        else:
            depth -= 1
            j = nxt_close + 6
            if depth == 0:
                return text[i:j]

trust = extract_balanced_div(old, '<div class="trust-strip">')

# --- карточки старого каталога: href → блок ---
cards = {}
for m in re.finditer(r'<a class="calc-item" href="(calc-[a-z0-9-]+\.html)">(.*?)</a>', old, re.S):
    block = m.group(0)
    block = block.replace('<span class="body">', '<div class="body">')
    # закрывающий </span> тела — последний </span> перед arrow
    block = re.sub(r'</span>\s*<span class="arrow"', '</div>\n          <span class="arrow"', block)
    block = block.replace("<h4>", "<h3>").replace("</h4>", "</h3>")
    cards[m.group(1)] = block
assert len(cards) == 60, "cards: %d" % len(cards)

# --- новые карточки (иконка + название + описание) ---
NEW_ICON = {
 'calc-currency.html': '<path d="M4 8h13m0 0l-3-3m3 3l-3 3M20 16H7m0 0l3-3m-3 3l3 3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
 'calc-word-counter.html': '<path d="M4 5h16M4 10h16M4 15h10M4 20h7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
 'calc-translit.html': '<path d="M3.5 17l3.8-9 3.8 9M4.9 13.5h4.8M14.5 8.5h6M17.5 8.5V17" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
 'calc-dedupe-lines.html': '<path d="M4 6h16M4 11h16M4 16h8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M14.5 17.5l2.2 2.2 4.3-4.7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
 'calc-inn.html': '<path d="M12 3l7 3v6c0 4.4-3 7.4-7 9-4-1.6-7-4.6-7-9V6z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M9 11.8l2.1 2.1 3.9-4.3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
 'calc-snils.html': '<path d="M12 3l7 3v6c0 4.4-3 7.4-7 9-4-1.6-7-4.6-7-9V6z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M9.2 9.5h5.6M9.2 12.5h5.6M9.2 15.5h3.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
 'calc-bank-card.html': '<rect x="3" y="5.5" width="18" height="13" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M3 9.5h18M6 14.5h5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
 'calc-uuid.html': '<path d="M9 4v16M15 4v16M4 9h16M4 15h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
 'calc-lorem.html': '<path d="M10 4h8M12.5 4v16M10 20h6M12.5 4a3.5 3.5 0 000 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
 'calc-nickname.html': '<circle cx="12" cy="8.5" r="3.2" stroke="currentColor" stroke-width="1.6"/><path d="M5.5 19.5c1.2-3.6 3.7-5.3 6.5-5.3s5.3 1.7 6.5 5.3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
 'calc-unix-time.html': '<circle cx="12" cy="12" r="8.5" stroke="currentColor" stroke-width="1.6"/><path d="M12 7.5V12l3 2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
 'calc-workdays.html': '<rect x="4" y="5.5" width="16" height="15" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M4 10.5h16M8.5 3.5v4M15.5 3.5v4M8.5 14.5l2 2 4-4.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>',
 'calc-countdown.html': '<path d="M6 3.5h12M6 20.5h12M7.5 3.5c0 4.2 2.7 5.4 4.5 6.5-1.8 1.1-4.5 2.3-4.5 6.5h9c0-4.2-2.7-5.4-4.5-6.5 1.8-1.1 4.5-2.3 4.5-6.5z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
}
NEW_CARD = {
 'calc-currency.html': ('Конвертер валют', 'Курсы ЦБ РФ, онлайн и офлайн'),
 'calc-word-counter.html': ('Счётчик слов', 'Символы, слова, время чтения'),
 'calc-translit.html': ('Транслитерация', 'Кириллица → латиница, для URL'),
 'calc-dedupe-lines.html': ('Удаление дублей строк', 'С сохранением порядка'),
 'calc-inn.html': ('Проверка ИНН', '10 и 12 цифр, контрольные суммы'),
 'calc-snils.html': ('Проверка СНИЛС', 'Контрольное число по весам'),
 'calc-bank-card.html': ('Проверка номера карты', 'Алгоритм Луна и платёжная система'),
 'calc-uuid.html': ('Генератор UUID', 'Криптостойкие v4, до 50 штук'),
 'calc-lorem.html': ('Lorem ipsum', 'Рыбный текст: абзацы, предложения, слова'),
 'calc-nickname.html': ('Генератор никнеймов', '10 вариантов за раз, клик копирует'),
 'calc-unix-time.html': ('Unix-время', 'Timestamp ↔ дата, живой тикер'),
 'calc-workdays.html': ('Рабочие дни', 'Между датами и +N дней, праздники РФ'),
 'calc-countdown.html': ('Обратный отсчёт', 'Таймер до даты с прогресс-баром'),
}

def new_card(href):
    t, d = NEW_CARD[href]
    return ('        <a class="calc-item" href="%s">\n'
            '          <span class="ico" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24" fill="none">%s</svg></span>\n'
            '          <div class="body">\n'
            '            <h3>%s</h3>\n'
            '            <span>%s</span>\n'
            '          </div>\n'
            '          <span class="arrow" aria-hidden="true">→</span>\n'
            '        </a>') % (href, NEW_ICON[href], t, d)

# --- таксономия v2: (id, название, лиде, [href...]) ---
SECTIONS = [
 ("finance", "Финансы", "Кредиты, вклады, валюта и инвестиции.",
  ["calc-mortgage.html","calc-mortgage-early.html","calc-credit.html","calc-deposit.html","calc-car-loan.html","calc-refinancing.html","calc-microloan.html","calc-loan-interest.html","calc-iis.html","calc-currency.html"]),
 ("realty", "Недвижимость и налоги", "Квартира, НДФЛ, НДС, взносы.",
  ["calc-tax-deduction.html","calc-property-sale-tax.html","calc-ndfl.html","calc-vat.html","calc-samozanyaty.html","calc-shares-apartment.html","calc-maternal-capital-shares.html","calc-insurance-contributions.html"]),
 ("labor", "Труд и соцзащита", "Стаж, отпуск, больничные, пенсия.",
  ["calc-work-experience.html","calc-vacation-days.html","calc-vacation-pay.html","calc-sick-leave.html","calc-maternity-leave.html","calc-pension.html"]),
 ("auto", "Авто", "Налог, топливо, ОСАГО, растаможка.",
  ["calc-transport-tax.html","calc-fuel.html","calc-osago.html","calc-customs-clearance.html","calc-recycling-fee.html","calc-ev-charging.html"]),
 ("legal", "Юридические", "Пени, неустойки, суммы прописью.",
  ["calc-penalty-tax.html","calc-penalty-contract.html","calc-art395.html","calc-penalty-ddu.html","calc-amount-in-words.html"]),
 ("math", "Математика", "Проценты, площади, дроби, степени.",
  ["calc-percent.html","calc-area.html","calc-volume.html","calc-fractions.html","calc-power.html","calc-gcd.html","calc-lcm.html","calc-factorization.html","calc-number-base.html"]),
 ("dates", "Даты и время", "Дни, возраст, часовые пояса, таймеры.",
  ["calc-days.html","calc-age.html","calc-timezone.html","calc-unix-time.html","calc-workdays.html","calc-countdown.html"]),
 ("health", "Здоровье", "Индекс массы тела и нормы веса.",
  ["calc-bmi.html","calc-weight.html"]),
 ("text", "Текст", "Слова, транслитерация, дубли строк.",
  ["calc-word-counter.html","calc-translit.html","calc-dedupe-lines.html"]),
 ("validators", "Валидаторы", "ИНН, СНИЛС, банковские карты.",
  ["calc-inn.html","calc-snils.html","calc-bank-card.html"]),
 ("generators", "Генераторы", "Пароли, промокоды, QR, UUID, тексты, ники.",
  ["calc-password-generator.html","calc-promo-generator.html","calc-qr-generator.html","calc-uuid.html","calc-lorem.html","calc-nickname.html"]),
 ("lists", "Списки и случайность", "Случайные числа, выбор, группы.",
  ["calc-random-number.html","calc-random-pick.html","calc-shuffle-list.html","calc-split-groups.html","calc-compare-lists.html"]),
 ("misc", "Разное", "Единицы, сложный процент, скидки, чаевые.",
  ["calc-unit-converter.html","calc-compound-interest.html","calc-discount.html","calc-tip.html"]),
]

sections_html = ""
total_cards = 0
for sid, name, lede, hrefs in SECTIONS:
    sections_html += '\n  <section class="section" id="%s">\n    <div class="container">\n      <div class="section-head">\n        <div>\n          <h2>%s</h2>\n          <p class="lede">%s</p>\n        </div>\n      </div>\n      <div class="calc-list calc-list--dense">\n' % (sid, name, lede)
    for h in hrefs:
        block = cards.get(h) or new_card(h)
        sections_html += block + "\n"
        total_cards += 1
    sections_html += '      </div>\n    </div>\n  </section>\n'
assert total_cards == 73, "total cards: %d" % total_cards

POPULAR = """
  <section class="section" id="popular" style="padding-top:0;">
    <div class="container">
      <div class="section-head">
        <div>
          <h2>Популярное</h2>
          <p class="lede">Чем чаще всего пользуются — под рукой.</p>
        </div>
      </div>
      <div class="pop-strip" id="popular-strip">
        <a class="pop-item" href="calc-mortgage.html"><span class="pop-n">1</span>Ипотека</a>
        <a class="pop-item" href="calc-deposit.html"><span class="pop-n">2</span>Вклад</a>
        <a class="pop-item" href="calc-credit.html"><span class="pop-n">3</span>Кредит</a>
        <a class="pop-item" href="calc-percent.html"><span class="pop-n">4</span>Проценты</a>
        <a class="pop-item" href="calc-bmi.html"><span class="pop-n">5</span>ИМТ</a>
        <a class="pop-item" href="calc-area.html"><span class="pop-n">6</span>Площадь</a>
        <a class="pop-item" href="calc-vat.html"><span class="pop-n">7</span>НДС</a>
        <a class="pop-item" href="calc-pension.html"><span class="pop-n">8</span>Пенсия по баллам</a>
        <a class="pop-item" href="calc-password-generator.html"><span class="pop-n">9</span>Генератор паролей</a>
        <a class="pop-item" href="calc-currency.html"><span class="pop-n">10</span>Конвертер валют</a>
      </div>
    </div>
  </section>
"""

AD_LEADER = """
  <div class="container">
    <div class="ad-slot ad-slot--leader" role="complementary" aria-label="Рекламный блок">
      <span class="tag">Реклама</span>
      <span>728×90 — баннер под шапкой</span>
    </div>
  </div>
"""

TRUST_SECTION = """
  <section class="section">
    <div class="container">
      %s
    </div>
  </section>
""" % trust

main_inner = "\n" + hero + POPULAR + AD_LEADER + sections_html + TRUST_SECTION

page = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:url" content="%s">
%s<style>
%s
</style>
<script type="application/ld+json">
%s
</script>
</head>
<body>
%s
<main id="main-content">%s</main>
%s
<script>
%s
</script>
</body>
</html>
""" % (title, desc, BASE_URL, og_title, og_desc, BASE_URL,
       head_init, style_css, ld_out, header, main_inner, footer, ui_js)

with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(page)

print("OK written:", OUT, len(page), "chars")
for token in ['id="finder-input"', 'id="finder-btn"', 'id="theme-toggle"', 'id="mega-btn"',
              'id="fav-btn"', 'id="popular-strip"', 'calc-list--dense', '73 инструмента']:
    assert token in page, "missing " + token
for bad in ['raschet.rf', 'onclick=', 'potentialAction', '@import', '<span class="body">', 'nav-drop-btn', '<h4>']:
    assert bad not in page, "forbidden token present: " + bad
n_items = page.count('<a class="calc-item"')
assert n_items == 73, "calc-item count: %d" % n_items
print("self-checks: ALL PASS, cards:", n_items)
