# -*- coding: utf-8 -*-
# =========================================================
# Генератор сайта «Расчёт.рф» v1.0
# Вход:  C:\Kimi\raschet\            (старый сайт, 60 calc-*.html + статика)
#        C:\Kimi\raschet-redesign\parts\   (канонические части v2)
#        C:\Kimi\raschet-redesign\build\tools\*.py  (дескрипторы новых инструментов, опционально)
# Выход: C:\Kimi\raschet-site\       (чистое дерево, пересоздаётся каждый прогон)
# =========================================================
import io
import os
import re
import json
import shutil
import importlib.util
import traceback
from html import escape as html_escape

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD = os.path.join(os.path.dirname(_REPO), "raschet-old")   # соседняя папка рядом с репо
PARTS = os.path.join(_REPO, "_build", "parts")
TOOLS_DIR = os.path.join(_REPO, "_build", "build", "tools")
OUT = os.path.join(_REPO, "_build", "out")  # ВНИМАНИЕ: rmtree при каждом прогоне — только эта папка
REPORT_PATH = os.path.join(_REPO, "_build", "build", "build_report.txt")
BASE_URL = "https://mrsn0wman.github.io/raschet/"

# --- Карта slug: старый файл -> ЧПУ slug (60 шт.; calc-pension добавлен: в задании
#     «60 файлов», в карте было 59 — pension есть на диске и в шапке/футере/ui.js) ---
SLUG_MAP = {
    "calc-mortgage.html": "ipoteka",
    "calc-mortgage-early.html": "dosrochnoe-pogashenie",
    "calc-credit.html": "kredit",
    "calc-deposit.html": "vklad",
    "calc-car-loan.html": "avtokredit",
    "calc-refinancing.html": "refinansirovanie",
    "calc-microloan.html": "mikrozaim",
    "calc-loan-interest.html": "procenty-po-zaimu",
    "calc-iis.html": "iis",
    "calc-tax-deduction.html": "nalogovyy-vychet-kvartira",
    "calc-property-sale-tax.html": "nalog-s-prodazhi-kvartiry",
    "calc-ndfl.html": "ndfl",
    "calc-vat.html": "nds",
    "calc-samozanyaty.html": "nalog-samozanyatyh",
    "calc-shares-apartment.html": "doli-v-kvartire",
    "calc-maternal-capital-shares.html": "doli-po-materinskomu-kapitalu",
    "calc-insurance-contributions.html": "strahovye-vznosy-ip",
    "calc-transport-tax.html": "transportnyy-nalog",
    "calc-fuel.html": "rashod-topliva",
    "calc-osago.html": "osago",
    "calc-customs-clearance.html": "rastamozhka",
    "calc-recycling-fee.html": "utilsbor",
    "calc-work-experience.html": "trudovoy-stazh",
    "calc-vacation-days.html": "otpusknye-dni",
    "calc-vacation-pay.html": "otpusknye",
    "calc-sick-leave.html": "bolnichnyy",
    "calc-maternity-leave.html": "dekretnye",
    "calc-penalty-tax.html": "peni-po-nalogam",
    "calc-penalty-contract.html": "neustoika-po-dogovoru",
    "calc-art395.html": "procenty-395-gk",
    "calc-penalty-ddu.html": "neustoika-po-ddu",
    "calc-amount-in-words.html": "summa-propisyu",
    "calc-percent.html": "procenty",
    "calc-area.html": "ploshad",
    "calc-volume.html": "obem",
    "calc-fractions.html": "drobi",
    "calc-power.html": "stepeni",
    "calc-gcd.html": "nod",
    "calc-lcm.html": "nok",
    "calc-factorization.html": "razlozhenie-na-mnozhiteli",
    "calc-number-base.html": "sistemy-schisleniya",
    "calc-days.html": "dni",
    "calc-age.html": "vozrast",
    "calc-timezone.html": "chasovye-poyasa",
    "calc-bmi.html": "imt",
    "calc-weight.html": "idealnyy-ves",
    "calc-unit-converter.html": "konverter-edinic",
    "calc-compound-interest.html": "slozhnyy-procent",
    "calc-discount.html": "skidki",
    "calc-tip.html": "chaevye",
    "calc-random-number.html": "sluchaynye-chisla",
    "calc-random-pick.html": "sluchaynyy-vybor",
    "calc-shuffle-list.html": "peremeshat-spisok",
    "calc-split-groups.html": "razdelit-na-gruppy",
    "calc-compare-lists.html": "sravnenie-spiskov",
    "calc-password-generator.html": "generator-paroley",
    "calc-promo-generator.html": "generator-promokodov",
    "calc-qr-generator.html": "qr-generator",
    "calc-ev-charging.html": "zaryadka-elektromobilya",
    "calc-pension.html": "pensiya",  # добавлено, см. комментарий выше
}

# --- Новые инструменты (дескрипторы в tools/*.py пишутся параллельно) ---
NEW_TOOL_SLUGS = {
    "calc-currency.html": "konverter-valyut",
    "calc-word-counter.html": "schetchik-slov",
    "calc-translit.html": "transliteraciya",
    "calc-dedupe-lines.html": "udalenie-dubley-strok",
    "calc-inn.html": "proverka-inn",
    "calc-snils.html": "proverka-snils",
    "calc-bank-card.html": "proverka-nomera-karty",
    "calc-uuid.html": "uuid-generator",
    "calc-lorem.html": "lorem-ipsum",
    "calc-nickname.html": "generator-nikneimov",
    "calc-unix-time.html": "unix-vremya",
    "calc-workdays.html": "rabochie-dni",
    "calc-countdown.html": "obratnyy-otschet",
}

LINK_MAP = {}
LINK_MAP.update(SLUG_MAP)
LINK_MAP.update(NEW_TOOL_SLUGS)

STATIC_LINKS = {
    "about.html": "about/",
    "privacy.html": "privacy/",
    "advertising.html": "advertising/",
    "feedback.html": "feedback/",
}

REPORT = {"pages": [], "patch_miss": [], "exceptions": [], "warnings": [], "checks": []}
SLUG_TITLES = {}  # slug -> короткое название (h1) для related-ссылок и заглушек


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, text):
    d = os.path.dirname(p)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def must(pattern, text, flags=0, name=""):
    m = re.search(pattern, text, flags)
    if not m:
        raise SystemExit("NOT FOUND: " + name)
    return m


# ---------------------------------------------------------------------------
# Переписывание ссылок
# ---------------------------------------------------------------------------
def rewrite_links(text, prefix):
    """prefix='' для корня, '../' для подпапок, '/raschet/' для 404."""
    home = prefix if prefix else "./"
    pairs = []
    # 1) абсолютные ссылки на старый домен с известными именами
    for old in sorted(LINK_MAP, key=len, reverse=True):
        pairs.append(("https://raschet.rf/" + old, BASE_URL + LINK_MAP[old] + "/"))
    for old, new in STATIC_LINKS.items():
        pairs.append(("https://raschet.rf/" + old, BASE_URL + new))
    pairs.append(("https://raschet.rf/index.html", BASE_URL))
    pairs.append(("https://raschet.rf/", BASE_URL))
    pairs.append(("https://raschet.rf", BASE_URL.rstrip("/")))  # голый домен без слэша
    # 2) абсолютные ссылки на НОВЫЙ домен со старыми именами (после шага 1 не должно
    #    остаться, но на случай готовых абсолютных ссылок в контенте)
    for old in sorted(LINK_MAP, key=len, reverse=True):
        pairs.append((BASE_URL + old, BASE_URL + LINK_MAP[old] + "/"))
    for old, new in STATIC_LINKS.items():
        pairs.append((BASE_URL + old, BASE_URL + new))
    pairs.append((BASE_URL + "index.html", BASE_URL))
    # 3) относительные ссылки
    pairs.append(("index.html#", home + "#"))
    for old in sorted(LINK_MAP, key=len, reverse=True):
        pairs.append((old, prefix + LINK_MAP[old] + "/"))
    for old, new in STATIC_LINKS.items():
        pairs.append((old, prefix + new))
    pairs.append(("index.html", home))
    for a, b in pairs:
        text = text.replace(a, b)
    return text


# ---------------------------------------------------------------------------
# Части v2
# ---------------------------------------------------------------------------
STYLE_CSS = read(os.path.join(PARTS, "style.css"))
HEADER = read(os.path.join(PARTS, "header.html"))
FOOTER = read(os.path.join(PARTS, "footer.html"))
HEAD_INIT = read(os.path.join(PARTS, "head-init.html"))
UI_JS_RAW = read(os.path.join(PARTS, "ui.js"))


# 28.10.2026: патч удалён — parts/ui.js сам хранит полный pathname (pagePath()),
# а панель избранного лечит легаси-записи по slug. (Старый патч заменял
# split('/').pop() → pathname и падал бы на assert после правки parts.)
UI_JS = UI_JS_RAW


def parts_for(prefix):
    return (rewrite_links(HEADER, prefix),
            rewrite_links(FOOTER, prefix),
            rewrite_links(UI_JS, prefix))


# ---------------------------------------------------------------------------
# Утилиты разметки
# ---------------------------------------------------------------------------
def extract_balanced(text, start_marker):
    """Извлечь блок <div ...> ... </div> по балансу вложенных div."""
    i = text.find(start_marker)
    assert i >= 0, start_marker
    depth = 0
    j = i
    while True:
        nxt_open = text.find("<div", j)
        nxt_close = text.find("</div>", j)
        if nxt_close < 0:
            raise SystemExit("unbalanced: " + start_marker)
        if 0 <= nxt_open < nxt_close:
            depth += 1
            j = nxt_open + 4
        else:
            depth -= 1
            j = nxt_close + 6
            if depth == 0:
                return text[i:j]


AD_STUB = ('<div class="ad-slot ad-slot--inline" role="complementary" aria-label="Рекламный блок">'
           '<span class="tag">Реклама</span><span>Место для партнёрских предложений</span></div>')

FAV_BTN = ('<button class="action-btn" id="fav-toggle" type="button" aria-pressed="false">'
           '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3.6l2.5 5.2 5.7.7-4.2 3.9 1.1 5.6-5.1-2.8-5.1 2.8 1.1-5.6L3.8 9.5l5.7-.7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'
           '<span>В избранное</span></button>')
SHARE_BTN = ('<button class="action-btn" id="share-btn" type="button">'
             '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="18" cy="5" r="2.6" stroke="currentColor" stroke-width="1.6"/><circle cx="6" cy="12" r="2.6" stroke="currentColor" stroke-width="1.6"/><circle cx="18" cy="19" r="2.6" stroke="currentColor" stroke-width="1.6"/><path d="M8.2 10.6l7.6-4.4M8.2 13.4l7.6 4.4" stroke="currentColor" stroke-width="1.6"/></svg>'
             '<span>Поделиться</span></button>')
PRINT_BTN = ('<button class="action-btn" id="print-btn" type="button">'
             '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7 8V3h10v5" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><rect x="3" y="8" width="18" height="9" rx="1.8" stroke="currentColor" stroke-width="1.6"/><path d="M7 13.5h10V21H7z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'
             '<span>Печать</span></button>')


def copy_btn(target):
    return ('<button class="action-btn" id="copy-btn" type="button" data-copy-target="%s">'
            '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.6"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
            '<span>Копировать</span></button>') % target


def action_bar(copy_target):
    btns = [FAV_BTN, SHARE_BTN]
    if copy_target:
        btns.append(copy_btn(copy_target))
    btns.append(PRINT_BTN)
    lines = ["", '          <div class="action-bar">']
    for b in btns:
        lines.append("            " + b)
    lines.append("          </div>")
    lines.append("")
    return "\n".join(lines)


def first_r_value_id(html):
    m = re.search(r'class="r-value"[^>]*\bid="([^"]+)"', html)
    if not m:
        m = re.search(r'id="([^"]+)"[^>]*class="r-value"', html)
    return m.group(1) if m else None


# action-bar для страниц без result-panel и без <form>: перед блоком вывода
ACTIONBAR_MARKERS = {
    "calc-compare-lists.html": '<div class="compare-output"',
    "calc-split-groups.html": '<div class="groups-output"',
}


def add_data_share(main):
    """Всем input/select/textarea с id внутри <form> добавить data-share="<id>"."""
    def fix_form(m):
        form = m.group(0)
        def fix_tag(tm):
            tag = tm.group(0)
            if "data-share=" in tag:
                return tag
            idm = re.search(r'\bid="([^"]+)"', tag)
            if not idm:
                return tag
            if tag.endswith("/>"):
                return tag[:-2] + ' data-share="%s"/>' % idm.group(1)
            return tag[:-1] + ' data-share="%s">' % idm.group(1)
        return re.sub(r'<(?:input|select|textarea)\b[^>]*>', fix_tag, form)
    return re.sub(r'(?s)<form\b.*?</form>', fix_form, main)


def add_error_roles(main):
    def fix(m):
        tag = m.group(0)
        if "role=" in tag:
            return tag
        return tag.replace('class="error-msg"', 'class="error-msg" role="alert"', 1)
    return re.sub(r'<div class="error-msg"[^>]*>', fix, main)


def span_body_to_div(main):
    """<span class="body"> -> <div class="body">, state machine по отступам."""
    lines = main.split("\n")
    out_lines = []
    pending_close_indent = None
    count = 0
    for ln in lines:
        stripped = ln.strip()
        if stripped == '<span class="body">':
            indent = ln[: len(ln) - len(ln.lstrip())]
            out_lines.append(indent + '<div class="body">')
            pending_close_indent = indent
            count += 1
            continue
        if (pending_close_indent is not None and stripped == "</span>"
                and ln[: len(ln) - len(ln.lstrip())] == pending_close_indent):
            out_lines.append(pending_close_indent + "</div>")
            pending_close_indent = None
            continue
        out_lines.append(ln)
    return "\n".join(out_lines), count


def transform_main(main, old_name, prefix):
    """Общие правки <main> старой calc-страницы. Возвращает (main, copy_target)."""
    # нормализация: у некоторых страниц calc-page на внутреннем контейнере
    main = main.replace('<div class="container calc-page">', '<div class="container">')

    # (b) referral-block -> нейтральная рекламная заглушка (только разметка, не CSS)
    while '<div class="referral-block"' in main:
        block = extract_balanced(main, '<div class="referral-block"')
        main = main.replace(block, AD_STUB, 1)

    # (c) data-share на полях форм
    main = add_data_share(main)

    # (d) role="alert" для error-msg
    main = add_error_roles(main)

    # (f) action-bar перед первым result-panel; иначе — после последнего </form>;
    #     иначе — перед известным блоком вывода (страницы-исключения)
    copy_target = first_r_value_id(main)
    bar = action_bar(copy_target)
    idx = main.find('<div class="result-panel"')
    if idx >= 0:
        main = main[:idx] + bar + main[idx:]
    else:
        pos = main.rfind("</form>")
        if pos >= 0:
            pos += len("</form>")
            main = main[:pos] + bar + main[pos:]
        else:
            marker = ACTIONBAR_MARKERS.get(old_name)
            if marker and marker in main:
                idx = main.find(marker)
                main = main[:idx] + bar + main[idx:]
            else:
                REPORT["patch_miss"].append("%s action-bar: нет result-panel/</form>/маркера" % old_name)

    # ссылки — в последнюю очередь (новые блоки ссылок не содержат)
    main = rewrite_links(main, prefix)
    return main, copy_target


# ---------------------------------------------------------------------------
# Мета и JSON-LD
# ---------------------------------------------------------------------------
def extract_meta(old, old_name):
    title = must(r"<title>(.*?)</title>", old, re.S, old_name + " title").group(1).strip()
    m = re.search(r'<meta name="description" content="([^"]*)"', old)
    desc = m.group(1) if m else title
    if not m:
        REPORT["warnings"].append(old_name + ": нет meta description, взят title")
    m = re.search(r'<meta property="og:title" content="([^"]*)"', old)
    og_title = m.group(1) if m else title
    m = re.search(r'<meta property="og:description" content="([^"]*)"', old)
    og_desc = m.group(1) if m else desc
    return title, desc, og_title, og_desc


def fix_ld_block(raw, old_name):
    """Домен + ЧПУ в JSON-LD, удаление potentialAction."""
    try:
        obj = json.loads(raw)
    except Exception:
        REPORT["warnings"].append(old_name + ": JSON-LD не парсится, перенесён как есть (с заменой домена)")
        return rewrite_links(raw, "")
    def fix(node):
        if isinstance(node, dict):
            node.pop("potentialAction", None)
            for k, v in list(node.items()):
                if isinstance(v, str):
                    node[k] = rewrite_links(v, "")
                else:
                    fix(v)
        elif isinstance(node, list):
            for item in node:
                fix(item)
    fix(obj)
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Точечные патчи скриптов
# ---------------------------------------------------------------------------
SECURE_INDEX_FN = ("function secureIndex(max){const a=new Uint32Array(1);"
                   "const limit=Math.floor(4294967296/max)*max;let x;"
                   "do{crypto.getRandomValues(a);x=a[0];}while(x>=limit);return x%max;}\n\n")

P2_OLD_1 = "numberIsWhatPercentOf(part, whole){ return (part / whole) * 100; }"
P2_NEW_1 = "numberIsWhatPercentOf(part, whole){ if (whole === 0) return NaN; return (part / whole) * 100; }"
P2_OLD_2 = "percentChange(oldValue, newValue){ return ((newValue - oldValue) / oldValue) * 100; }"
P2_NEW_2 = "percentChange(oldValue, newValue){ if (oldValue === 0) return NaN; return ((newValue - oldValue) / oldValue) * 100; }"


def patch_script(src, old_name):
    """Точечные патчи P1/P2 внутри сохраняемых скриптов."""
    # P2: гарды деления на ноль в Calc (только там, где есть ОПРЕДЕЛЕНИЕ функций)
    if "numberIsWhatPercentOf(part, whole){" in src:
        if src.count(P2_OLD_1) == 1:
            src = src.replace(P2_OLD_1, P2_NEW_1)
        else:
            REPORT["patch_miss"].append("%s P2 numberIsWhatPercentOf (count=%d)" % (old_name, src.count(P2_OLD_1)))
    if "percentChange(oldValue, newValue){" in src:
        if src.count(P2_OLD_2) == 1:
            src = src.replace(P2_OLD_2, P2_NEW_2)
        else:
            REPORT["patch_miss"].append("%s P2 percentChange (count=%d)" % (old_name, src.count(P2_OLD_2)))
    # P1: криптостойкий выбор символов в генераторе паролей
    if old_name == "calc-password-generator.html" and "function generatePassword(" in src:
        old_expr = "chars[Math.floor(Math.random()*chars.length)]"
        if src.count(old_expr) == 1:
            src = src.replace(old_expr, "chars[secureIndex(chars.length)]")
        else:
            REPORT["patch_miss"].append("%s P1 Math.random expr (count=%d)" % (old_name, src.count(old_expr)))
        old_fn = "function generatePassword("
        if src.count(old_fn) == 1:
            src = src.replace(old_fn, SECURE_INDEX_FN + old_fn)
        else:
            REPORT["patch_miss"].append("%s P1 generatePassword decl (count=%d)" % (old_name, src.count(old_fn)))
    # P5: криптостойкие промокоды (Math.random → crypto)
    if old_name == "calc-promo-generator.html" and "function generatePromoCodes(" in src:
        old_expr = "charset[Math.floor(Math.random()*charset.length)]"
        if src.count(old_expr) == 1:
            src = src.replace(old_expr, "charset[secureIndex(charset.length)]")
        else:
            REPORT["patch_miss"].append("%s P5 Math.random expr (count=%d)" % (old_name, src.count(old_expr)))
        old_fn = "function generatePromoCodes("
        if src.count(old_fn) == 1:
            src = src.replace(old_fn, SECURE_INDEX_FN + old_fn)
        else:
            REPORT["patch_miss"].append("%s P5 generatePromoCodes decl (count=%d)" % (old_name, src.count(old_fn)))
    return src


# ---------------------------------------------------------------------------
# Шаблон страницы
# ---------------------------------------------------------------------------
def render_page(title, desc, canonical, og_title, og_desc, page_css, ld_blocks,
                body_attrs, header, main, footer, scripts):
    """scripts — список: ('inline', текст) или ('src', тег целиком)."""
    css = STYLE_CSS + "\n"
    if page_css:
        css += "\n/* --- страничные стили --- */\n" + page_css.strip() + "\n"
    ld_html = ""
    for b in ld_blocks:
        ld_html += '<script type="application/ld+json">\n%s\n</script>\n' % b
    js_html = ""
    for kind, payload in scripts:
        if kind == "inline":
            js_html += "<script>\n%s\n</script>\n" % payload
        else:
            js_html += payload + "\n"
    return """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://mc.yandex.ru; font-src 'self'; connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com https://www.googletagmanager.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:url" content="%s">
<meta property="og:site_name" content="Расчёт.рф">
<meta property="og:image" content="https://mrsn0wman.github.io/raschet/assets/og-cover.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="https://mrsn0wman.github.io/raschet/assets/og-cover.png">
%s<style>
%s</style>
%s</head>
<body%s>
%s
<main id="main-content" class="calc-page">%s</main>
%s
%s</body>
</html>
""" % (title, desc, canonical, og_title, og_desc, canonical, og_title, og_desc,
       HEAD_INIT, css, ld_html, body_attrs, header, main, footer, js_html)


def extract_page_css(old):
    """Содержимое ВТОРОГО <style>-блока (страничное), если блоков два."""
    blocks = re.findall(r"(?s)<style>(.*?)</style>", old)
    if len(blocks) >= 2:
        return blocks[1]
    return ""


def extract_scripts(old, old_name, prefix):
    """Возвращает (externals[list тегов], kept[list inline-кода]).
    Отбрасывает старый UI (nav-drop-btn / finder-input). Применяет патчи и ссылки."""
    externals, kept = [], []
    for m in re.finditer(r"(?s)<script([^>]*)>(.*?)</script>", old):
        attrs, body = m.group(1), m.group(2)
        if "application/ld+json" in attrs:
            continue
        if "src=" in attrs:
            tag = m.group(0)
            # P3: CDN QR-библиотеки — crossorigin/referrerpolicy/onerror
            if "qrcode" in attrs:
                if old_name == "calc-qr-generator.html":
                    new_tag = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" '
                               'crossorigin="anonymous" referrerpolicy="no-referrer" '
                               'onerror="document.getElementById(\'qr-error\').style.display=\'block\'">'
                               '</script>')
                    externals.append(new_tag)
                    REPORT["warnings"].append("calc-qr-generator: SRI-хеш не вычислен (CDN не скачивался)")
                else:
                    externals.append(tag)
            else:
                externals.append(tag)
            continue
        if "nav-drop-btn" in body or "finder-input" in body:
            continue  # старый UI — заменяется parts/ui.js
        body = patch_script(body, old_name)
        body = rewrite_links(body, prefix)
        kept.append(body)
    return externals, kept


def check_ids(page_html, scripts_text, page_name):
    """Все getElementById('X') в страничных скриптах должны существовать в разметке."""
    ids = set(re.findall(r"getElementById\(\s*['\"]([\w-]+)['\"]", scripts_text))
    missing = [i for i in sorted(ids) if ('id="%s"' % i) not in page_html]
    if missing:
        raise AssertionError("%s: getElementById без элемента: %s" % (page_name, ", ".join(missing)))


def build_calc_page(old_name, slug):
    old = read(os.path.join(OLD, old_name))
    prefix = "../"
    title, desc, og_title, og_desc = extract_meta(old, old_name)
    canonical = BASE_URL + slug + "/"
    page_css = extract_page_css(old)
    ld_blocks = [fix_ld_block(b, old_name)
                 for b in re.findall(r'(?s)<script type="application/ld\+json">(.*?)</script>', old)]
    externals, kept = extract_scripts(old, old_name, prefix)

    main = must(r"(?s)<main[^>]*>(.*?)</main>", old, name=old_name + " main").group(1)
    main, _copy = transform_main(main, old_name, prefix)

    # P3 (разметка): qr-error рядом с контейнером QR
    if old_name == "calc-qr-generator.html":
        anchor = '<div id="qrcode-box"><div id="qrcode"></div></div>'
        qr_err = ('<div class="error-msg" id="qr-error" role="alert">'
                  'Не удалось загрузить библиотеку QR-кодов. Проверьте соединение и обновите страницу.</div>')
        if main.count(anchor) == 1:
            main = main.replace(anchor, anchor + qr_err)
        else:
            REPORT["patch_miss"].append("%s P3 qrcode-box anchor (count=%d)" % (old_name, main.count(anchor)))

    h1m = re.search(r"(?s)<h1>(.*?)</h1>", main)
    h1 = re.sub(r"<[^>]+>", "", h1m.group(1)).strip() if h1m else og_title
    SLUG_TITLES[slug] = h1

    header, footer, ui = parts_for(prefix)
    scripts = [("inline", ui)]
    for t in externals:
        scripts.append(("src", t))
    for s in kept:
        scripts.append(("inline", s))

    body_attrs = ' data-calc-slug="%s" data-calc-title="%s"' % (slug, html_escape(h1, quote=True))
    page = render_page(title, desc, canonical, og_title, og_desc, page_css, ld_blocks,
                       body_attrs, header, main, footer, scripts)
    check_ids(page, "\n".join(kept), old_name)
    out_path = os.path.join(OUT, slug, "index.html")
    write(out_path, page)
    REPORT["pages"].append(slug + "/ (" + old_name + ")")
    return page


# ---------------------------------------------------------------------------
# Ипотека — особая страница (логика build_mortgage.py, URL -> ЧПУ)
# ---------------------------------------------------------------------------
def build_mortgage_page():
    old_name = "calc-mortgage.html"
    slug = SLUG_MAP[old_name]
    prefix = "../"
    old = read(os.path.join(OLD, old_name))
    title, desc, og_title, og_desc = extract_meta(old, old_name)
    canonical = BASE_URL + slug + "/"

    ld_blocks = [fix_ld_block(b, old_name)
                 for b in re.findall(r'(?s)<script type="application/ld\+json">(.*?)</script>', old)]
    assert len(ld_blocks) == 2, "mortgage json-ld blocks: %d" % len(ld_blocks)

    breadcrumbs = must(r'<p class="breadcrumbs">.*?</p>', old, re.S, "breadcrumbs").group(0)
    form = must(r'<form id="mortgage-form".*?</form>', old, re.S, "form").group(0)
    result_panel = extract_balanced(old, '<div class="result-panel">')
    article = must(r'<article class="calc-explain">.*?</article>', old, re.S, "article").group(0)
    aside = must(r'<aside class="sidebar">.*?</aside>', old, re.S, "aside").group(0)

    # правки формы (как в build_mortgage.py)
    form = form.replace('<input type="text" id="m-amount" value="5000000" required>',
                        '<input type="text" id="m-amount" value="5000000" required inputmode="numeric" data-share="amount">')
    form = form.replace('<input type="number" id="m-rate" value="12" min="0" max="50" step="0.1" required>',
                        '<input type="number" id="m-rate" value="12" min="0" max="50" step="0.1" required data-share="rate">')
    form = form.replace('<input type="number" id="m-years" value="20" min="1" max="30" step="1" required>',
                        '<input type="number" id="m-years" value="20" min="1" max="30" step="1" required data-share="years">')
    form = form.replace('<input type="text" id="m-down" value="0">',
                        '<input type="text" id="m-down" value="0" inputmode="numeric" data-share="down">')
    form = form.replace('<div class="error-msg" id="m-error">', '<div class="error-msg" id="m-error" role="alert">')
    assert 'data-share="amount"' in form and 'data-share="down"' in form

    # библиотека Calc из старой страницы + P2-патч
    calc_lib = None
    for s in re.findall(r"(?s)<script>(.*?)</script>", old):
        if "annuityLoan" in s and "window.Calc" in s or (s and "annuityLoan" in s and "Calc" in s):
            calc_lib = s
            break
    assert calc_lib, "Calc lib not found"
    calc_lib = patch_script(calc_lib, old_name)

    ACTION_BAR = action_bar("#m-payment")

    CHART = """
          <div class="chart-wrap">
            <svg id="m-chart" width="140" height="140" viewBox="0 0 42 42" role="img" aria-label="Соотношение тела кредита и переплаты">
              <circle cx="21" cy="21" r="15.9155" fill="none" stroke="var(--gold-soft)" stroke-width="6"></circle>
              <circle id="m-chart-a" cx="21" cy="21" r="15.9155" fill="none" stroke="var(--accent)" stroke-width="6" pathLength="100" stroke-dasharray="61 39" stroke-dashoffset="25" transform="rotate(-90 21 21)"></circle>
              <circle id="m-chart-b" cx="21" cy="21" r="15.9155" fill="none" stroke="var(--gold)" stroke-width="6" pathLength="100" stroke-dasharray="39 61" stroke-dashoffset="-36" transform="rotate(-90 21 21)"></circle>
            </svg>
            <div class="chart-legend">
              <div><span class="sw" style="background:var(--accent)"></span>Тело кредита — <b id="m-legend-principal">5 000 000 ₽</b></div>
              <div><span class="sw" style="background:var(--gold)"></span>Переплата — <b id="m-legend-overpay">8 213 034 ₽</b></div>
            </div>
          </div>
"""

    SCHEDULE = """
          <div class="schedule-block">
            <div class="schedule-wrap">
              <table class="schedule-table">
                <thead><tr><th>Мес.</th><th>Платёж, ₽</th><th>Проценты, ₽</th><th>Тело, ₽</th><th>Остаток, ₽</th></tr></thead>
                <tbody id="m-schedule"></tbody>
              </table>
            </div>
            <button class="action-btn schedule-toggle" id="m-schedule-toggle" type="button"><span>Показать весь график</span></button>
          </div>
"""

    AD_PLACEHOLDER = """
          <div class="ad-slot ad-slot--inline" role="complementary" aria-label="Рекламный блок"><span class="tag">Реклама</span><span>Место для партнёрских предложений банков</span></div>
"""

    PAGE_JS = r"""
(function(){
  const amountEl = document.getElementById('m-amount');
  const rateEl = document.getElementById('m-rate');
  const yearsElRef = document.getElementById('m-years');
  const downEl = document.getElementById('m-down');
  const errorEl = document.getElementById('m-error');
  const tbody = document.getElementById('m-schedule');
  const toggleBtn = document.getElementById('m-schedule-toggle');
  let showAll = false;
  let schedule = [];

  attachThousandsInput(amountEl);
  attachThousandsInput(downEl);

  function renderChart(principal, totalInterest, totalPayment){
    const c1 = document.getElementById('m-chart-a');
    const c2 = document.getElementById('m-chart-b');
    if (!c1 || !c2 || !(totalPayment > 0)) return;
    const p = Math.max(0, Math.min(100, (principal / totalPayment) * 100));
    const o = 100 - p;
    c1.setAttribute('stroke-dasharray', p.toFixed(2) + ' ' + o.toFixed(2));
    c2.setAttribute('stroke-dasharray', o.toFixed(2) + ' ' + p.toFixed(2));
    c2.setAttribute('stroke-dashoffset', (25 - p).toFixed(2));
    document.getElementById('m-legend-principal').textContent = formatMoney(principal) + ' ₽';
    document.getElementById('m-legend-overpay').textContent = formatMoney(totalInterest) + ' ₽';
  }

  function buildSchedule(principal, rate, months, monthlyPayment){
    const rows = [];
    let balance = principal;
    const i = rate / 100 / 12;
    for (let m = 1; m <= months; m++){
      const interest = balance * i;
      let body = monthlyPayment - interest;
      if (body > balance) body = balance;
      balance = Math.max(0, balance - body);
      rows.push({ m: m, pay: interest + body, interest: interest, body: body, balance: balance });
      if (balance <= 0) break;
    }
    return rows;
  }

  function renderSchedule(){
    if (!tbody) return;
    const rows = showAll ? schedule : schedule.slice(0, 12);
    tbody.innerHTML = rows.map(function(r){
      return '<tr><td>' + r.m + '</td><td>' + formatMoney(r.pay) + '</td><td>' +
             formatMoney(r.interest) + '</td><td>' + formatMoney(r.body) + '</td><td>' +
             formatMoney(r.balance) + '</td></tr>';
    }).join('');
    if (toggleBtn){
      toggleBtn.style.display = schedule.length > 12 ? '' : 'none';
      toggleBtn.querySelector('span').textContent = showAll
        ? 'Свернуть график'
        : 'Показать весь график (' + schedule.length + ' мес.)';
    }
  }

  function render(){
    const amount = parseFormattedNumber(amountEl);
    const rate = parseFloat(rateEl.value);
    let years = parseFloat(yearsElRef.value);
    const down = parseFormattedNumber(downEl) || 0;

    const valid = amount > 0 && rate >= 0 && years > 0 && down >= 0 && down < amount;
    errorEl.classList.toggle('visible', !valid);
    if (!valid) return;

    // кламп срока: не больше 50 лет → максимум 600 итераций помесячного цикла
    years = Math.min(Math.max(years, 1), 50);

    const principal = amount - down;
    const months = Math.round(years * 12);
    const result = Calc.annuityLoan(principal, rate, months);

    document.getElementById('m-payment').textContent = formatMoney(result.monthlyPayment) + ' ₽';
    document.getElementById('m-total').textContent = formatMoney(result.totalPayment) + ' ₽';
    document.getElementById('m-overpay').textContent = formatMoney(result.totalInterest) + ' ₽';
    document.getElementById('m-principal').textContent = formatMoney(principal) + ' ₽';
    document.getElementById('m-months').textContent = months;

    renderChart(principal, result.totalInterest, result.totalPayment);
    schedule = buildSchedule(principal, rate, months, result.monthlyPayment);
    renderSchedule();
  }

  [amountEl, rateEl, yearsElRef, downEl].forEach(function(el){
    el.addEventListener('input', render);
  });
  if (toggleBtn){
    toggleBtn.addEventListener('click', function(){
      var blk = this.closest('.schedule-block');
      var anchorTop = showAll ? blk.getBoundingClientRect().top + window.scrollY : 0;
      showAll = !showAll;
      blk.classList.toggle('expanded', showAll);
      renderSchedule();
      // при сворачивании возвращаем к началу графика, а не роняем в подвал
      if (!showAll && window.scrollY > anchorTop - 80){
        window.scrollTo({ top: Math.max(anchorTop - 80, 0), behavior: 'smooth' });
      }
    });
  }
  render();
})();
"""

    # ссылки — в ЧПУ
    for part_name in ("breadcrumbs", "form", "article", "aside"):
        pass
    breadcrumbs = rewrite_links(breadcrumbs, prefix)
    form = rewrite_links(form, prefix)
    article = rewrite_links(article, prefix)
    aside = rewrite_links(aside, prefix)

    main_html = """
  <div class="container">
    %s
    <div class="calc-layout">
      <div class="calc-main">
        <div class="calc-card">
          <h1>Калькулятор ипотеки</h1>
          <p class="calc-sub">Рассчитайте ежемесячный платёж, переплату и общую стоимость ипотеки по аннуитетной схеме — так же, как считает банк.</p>
          %s
          %s
          %s
          %s
          %s
          %s
        </div>
        %s
      </div>
      %s
    </div>
  </div>
""" % (breadcrumbs, form, ACTION_BAR, result_panel, CHART, SCHEDULE, AD_PLACEHOLDER, article, aside)

    SLUG_TITLES[slug] = "Ипотека"
    header, footer, ui = parts_for(prefix)
    scripts = [("inline", ui), ("inline", calc_lib), ("inline", PAGE_JS)]
    page = render_page(title, desc, canonical, og_title, og_desc, "", ld_blocks,
                       ' data-calc-slug="%s" data-calc-title="Ипотека"' % slug,
                       header, main_html, footer, scripts)
    check_ids(page, calc_lib + "\n" + PAGE_JS, old_name)
    write(os.path.join(OUT, slug, "index.html"), page)
    REPORT["pages"].append(slug + "/ (" + old_name + ", особая сборка)")
    REPORT["exceptions"].append("calc-mortgage.html: сборка по build_mortgage.py (action-bar, donut, график, кламп лет), referral-block не переносился")
    return page


# ---------------------------------------------------------------------------
# Главная (логика build_index.py + ЧПУ-ссылки)
# ---------------------------------------------------------------------------
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
INDEX_SECTIONS = [
 ("finance", "Финансы", "Кредиты, вклады, валюта и инвестиции.",
  ["calc-mortgage.html","calc-mortgage-early.html","calc-credit.html","calc-deposit.html","calc-car-loan.html","calc-refinancing.html","calc-microloan.html","calc-loan-interest.html","calc-iis.html","calc-currency.html","calc-compound-interest.html"]),
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
 ("misc", "Разное", "Единицы, скидки, чаевые.",
  ["calc-unit-converter.html","calc-discount.html","calc-tip.html"]),
]

def new_index_card(href):
    t, d = NEW_CARD[href]
    return ('        <a class="calc-item" href="%s">\n'
            '          <span class="ico" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24" fill="none">%s</svg></span>\n'
            '          <div class="body">\n'
            '            <h3>%s</h3>\n'
            '            <span>%s</span>\n'
            '          </div>\n'
            '          <span class="arrow" aria-hidden="true">→</span>\n'
            '        </a>') % (href, NEW_ICON[href], t, d)

def build_index_page():
    old = read(os.path.join(OLD, "index.html"))
    prefix = ""
    title, desc, og_title, og_desc = extract_meta(old, "index.html")
    canonical = BASE_URL

    ld_blocks = [fix_ld_block(b, "index.html")
                 for b in re.findall(r'(?s)<script type="application/ld\+json">(.*?)</script>', old)]

    # hero из старой главной
    hero = must(r'(?s)<section class="hero">.*?</section>', old, name="hero").group(0)
    hero, n = re.subn(
        r'<button class="btn btn-primary" onclick="[^"]*">Найти</button>',
        '<button class="btn btn-primary" id="finder-btn" type="button">Найти</button>',
        hero)
    assert n == 1, "finder button replacements: %d" % n
    hero = hero.replace("60 калькуляторов · без регистрации", "73 инструмента · без регистрации")
    hero = hero.replace("55 054 ₽/мес", "55&nbsp;054&nbsp;₽/мес")
    hero = hero.replace("8 213 034 ₽", "8&nbsp;213&nbsp;034&nbsp;₽").replace("13 213 034 ₽", "13&nbsp;213&nbsp;034&nbsp;₽")

    # trust-strip из старой главной
    trust = extract_balanced(old, '<div class="trust-strip">')
    assert trust, "trust-strip not found"

    # карточки старого каталога: href → блок
    cards = {}
    for m in re.finditer(r'(?s)<a class="calc-item" href="(calc-[a-z0-9-]+\.html)">(.*?)</a>', old):
        block = m.group(0)
        block = block.replace('<span class="body">', '<div class="body">')
        block = re.sub(r'</span>\s*<span class="arrow"', '</div>\n          <span class="arrow"', block)
        block = block.replace("<h4>", "<h3>").replace("</h4>", "</h3>")
        cards[m.group(1)] = block
    assert len(cards) == 60, "cards: %d" % len(cards)

    sections_html = ""
    total_cards = 0
    for sid, name, lede, hrefs in INDEX_SECTIONS:
        sections_html += ('\n  <section class="section" id="%s">\n    <div class="container">\n'
                          '      <div class="section-head">\n        <div>\n          <h2>%s</h2>\n'
                          '          <p class="lede">%s</p>\n        </div>\n      </div>\n'
                          '      <div class="calc-list calc-list--dense">\n') % (sid, name, lede)
        for h in hrefs:
            sections_html += (cards.get(h) or new_index_card(h)) + "\n"
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
        <a class="pop-item" href="ipoteka/"><span class="pop-n">1</span>Ипотека</a>
        <a class="pop-item" href="vklad/"><span class="pop-n">2</span>Вклад</a>
        <a class="pop-item" href="kredit/"><span class="pop-n">3</span>Кредит</a>
        <a class="pop-item" href="procenty/"><span class="pop-n">4</span>Проценты</a>
        <a class="pop-item" href="imt/"><span class="pop-n">5</span>ИМТ</a>
        <a class="pop-item" href="ploshad/"><span class="pop-n">6</span>Площадь</a>
        <a class="pop-item" href="nds/"><span class="pop-n">7</span>НДС</a>
        <a class="pop-item" href="pensiya/"><span class="pop-n">8</span>Пенсия по баллам</a>
        <a class="pop-item" href="generator-paroley/"><span class="pop-n">9</span>Генератор паролей</a>
        <a class="pop-item" href="konverter-valyut/"><span class="pop-n">10</span>Конвертер валют</a>
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
    main_inner = rewrite_links(main_inner, prefix)

    header, footer, ui = parts_for(prefix)
    page = render_page(title, desc, canonical, og_title, og_desc, "", ld_blocks,
                       "", header, main_inner, footer, [("inline", ui)])
    page = page.replace('<main id="main-content" class="calc-page">', '<main id="main-content">')
    write(os.path.join(OUT, "index.html"), page)
    REPORT["pages"].append("index.html (главная, каталог 73)")
    return page


# ---------------------------------------------------------------------------
# Статические страницы (about/privacy/advertising)
# ---------------------------------------------------------------------------
def build_static_page(old_name, slug):
    old = read(os.path.join(OLD, old_name))
    prefix = "../"
    title, desc, og_title, og_desc = extract_meta(old, old_name)
    canonical = BASE_URL + slug + "/"
    main = must(r"(?s)<main[^>]*>(.*?)</main>", old, name=old_name + " main").group(1)
    main = add_error_roles(main)
    main = rewrite_links(main, prefix)
    header, footer, ui = parts_for(prefix)
    page = render_page(title, desc, canonical, og_title, og_desc, "", [],
                       "", header, main, footer, [("inline", ui)])
    write(os.path.join(OUT, slug, "index.html"), page)
    REPORT["pages"].append(slug + "/ (" + old_name + ")")
    return page


# ---------------------------------------------------------------------------
# feedback/ — новая страница
# ---------------------------------------------------------------------------
FEEDBACK_JS = r"""
(function(){
  var form = document.getElementById('feedback-form');
  var okBox = document.getElementById('fb-ok');
  var errBox = document.getElementById('fb-err');
  if (!form) return;

  function showOk(msg){
    okBox.textContent = msg;
    okBox.style.display = 'block';
    errBox.classList.remove('visible');
  }
  function showErr(msg){
    errBox.textContent = msg;
    errBox.classList.add('visible');
    okBox.style.display = 'none';
  }
  // почтовый адрес собирается из частей: домен проекта не светим в исходнике страницы
  var MAIL = ['helpraschet', 'gmail', 'com'];
  function mailtoFallback(payload){
    var subject = 'Расчёт.рф — ' + (payload.topic || 'обратная связь');
    var body = 'Имя: ' + payload.name + '\nEmail: ' + payload.email + '\n\n' + payload.message;
    window.location.href = 'mailto:' + MAIL[0] + '@' + MAIL[1] + '.' + MAIL[2] +
                           '?subject=' + encodeURIComponent(subject) +
                           '&body=' + encodeURIComponent(body);
    showOk('Не удалось отправить через сайт — открываем почтовый клиент, письмо уже заполнено.');
  }

  form.addEventListener('submit', function(e){
    e.preventDefault();
    // honeypot: боты заполняют скрытое поле website — делаем вид, что всё хорошо
    if (form.website && form.website.value){ showOk('Спасибо! Сообщение отправлено.'); form.reset(); return; }
    var payload = {
      name: document.getElementById('fb-name').value.trim(),
      email: document.getElementById('fb-email').value.trim(),
      topic: document.getElementById('fb-topic').value,
      message: document.getElementById('fb-message').value.trim()
    };
    if (!payload.name || !payload.email || !payload.message){
      showErr('Заполните имя, email и текст сообщения.');
      return;
    }
    var base = window.RASCHET_API_BASE || '';
    if (!base){ mailtoFallback(payload); return; }
    var ctrl = new AbortController();
    setTimeout(function(){ ctrl.abort(); }, 3000);
    fetch(base + '/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: ctrl.signal
    }).then(function(r){
      if (r && r.ok){
        showOk('Спасибо! Сообщение отправлено — отвечаем обычно в течение пары дней.');
        form.reset();
      } else {
        mailtoFallback(payload);
      }
    }).catch(function(){ mailtoFallback(payload); });
  });
})();
"""


def build_feedback_page():
    prefix = "../"
    title = "Обратная связь — Расчёт.рф"
    desc = "Напишите нам: ошибка в расчёте, идея нового калькулятора или предложение по улучшению сайта."
    main = """
  <div class="container">
    <p class="breadcrumbs"><a href="../">Главная</a> / Обратная связь</p>
    <div class="calc-layout">
      <div class="calc-main">
        <div class="calc-card">
          <h1>Обратная связь</h1>
          <p class="calc-sub">Нашли ошибку в расчёте, хотите предложить новый калькулятор или просто написать нам? Заполните форму — читаем каждое сообщение.</p>

          <form id="feedback-form" novalidate>
            <div class="field-grid">
              <div class="field">
                <label for="fb-name">Ваше имя</label>
                <input type="text" id="fb-name" autocomplete="name" required>
              </div>
              <div class="field">
                <label for="fb-email">Email для ответа</label>
                <input type="email" id="fb-email" autocomplete="email" required>
              </div>
              <div class="field full">
                <label for="fb-topic">Тема</label>
                <select id="fb-topic">
                  <option value="bug">Ошибка в расчёте</option>
                  <option value="idea">Идея нового калькулятора</option>
                  <option value="content">Замечание по тексту</option>
                  <option value="other" selected>Другое</option>
                </select>
              </div>
              <div class="field full">
                <label for="fb-message">Сообщение</label>
                <textarea id="fb-message" rows="6" required></textarea>
              </div>
            </div>
            <div style="position:absolute;left:-9999px;top:-9999px;" aria-hidden="true">
              <label>Не заполняйте это поле<input type="text" name="website" tabindex="-1" autocomplete="off"></label>
            </div>
            <button class="btn btn-primary" type="submit">Отправить</button>
            <div class="error-msg" id="fb-err" role="alert"></div>
            <div class="result-panel" id="fb-ok" style="display:none;"></div>
          </form>
        </div>

        <article class="calc-explain">
          <h2>Как ещё с нами связаться</h2>
          <p>Если форма не сработала (например, нет соединения), откроется ваш почтовый клиент с уже заполненным письмом. По вопросам размещения рекламы смотрите страницу <a href="../advertising/">«Реклама и партнёрство»</a>.</p>
        </article>
      </div>

      <aside class="sidebar">
        <div class="side-card">
          <h4>Проект</h4>
          <a class="related-link" href="../about/">О проекте</a>
          <a class="related-link" href="../privacy/">Конфиденциальность</a>
          <a class="related-link" href="../advertising/">Реклама и партнёрство</a>
        </div>
      </aside>
    </div>
  </div>
"""
    header, footer, ui = parts_for(prefix)
    page = render_page(title, desc, BASE_URL + "feedback/", title, desc, "", [],
                       "", header, main, footer, [("inline", ui), ("inline", FEEDBACK_JS)])
    check_ids(page, FEEDBACK_JS, "feedback")
    write(os.path.join(OUT, "feedback", "index.html"), page)
    REPORT["pages"].append("feedback/ (новая)")


# ---------------------------------------------------------------------------
# 404.html — абсолютные пути (страница отдаётся с любой глубины)
# ---------------------------------------------------------------------------
def build_404_page():
    prefix = "/raschet/"
    title = "Страница не найдена — Расчёт.рф"
    desc = "Такой страницы нет. Возможно, ссылка устарела — попробуйте начать с главной или выбрать популярный калькулятор."
    popular = [("ipoteka", "Ипотека"), ("vklad", "Вклад"), ("kredit", "Кредит"),
               ("procenty", "Проценты"), ("imt", "ИМТ")]
    links = "\n".join(
        '          <a class="related-link" href="/raschet/%s/">%s</a>' % (s, t) for s, t in popular)
    main = """
  <div class="container">
    <div class="calc-card" style="max-width:640px;margin:40px auto;text-align:center;">
      <h1>Страница не найдена</h1>
      <p class="calc-sub">Такой страницы нет — возможно, ссылка устарела после обновления сайта. Начните с главной или выберите популярный калькулятор.</p>
      <p><a class="btn btn-primary" href="/raschet/">На главную</a></p>
    </div>
    <div class="side-card" style="max-width:640px;margin:0 auto;">
      <h4>Популярное</h4>
%s
    </div>
  </div>
""" % links
    header, footer, ui = parts_for(prefix)
    page = render_page(title, desc, BASE_URL + "404.html", title, desc, "", [],
                       "", header, main, footer, [("inline", ui)])
    write(os.path.join(OUT, "404.html"), page)
    REPORT["pages"].append("404.html")


# ---------------------------------------------------------------------------
# Новые инструменты из дескрипторов tools/*.py
# ---------------------------------------------------------------------------
def load_tools():
    tools = []
    if not os.path.isdir(TOOLS_DIR):
        REPORT["warnings"].append("tools/ отсутствует — новые инструменты не собраны (подхватятся при появлении)")
        return tools
    for fn in sorted(os.listdir(TOOLS_DIR)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        path = os.path.join(TOOLS_DIR, fn)
        try:
            spec = importlib.util.spec_from_file_location("tool_" + fn[:-3], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            t = mod.TOOL
            assert isinstance(t, dict), "TOOL не dict"
            for key in ("slug", "title", "meta_title", "meta_desc", "h1", "sub",
                        "category", "fields_html", "result_html", "explain_html",
                        "faq", "page_js", "related"):
                assert key in t, "нет ключа " + key
            t.setdefault("page_css", "")
            tools.append(t)
        except Exception as e:
            REPORT["warnings"].append("tools/%s пропущен: %s" % (fn, e))
            traceback.print_exc()
    return tools


def build_tool_page(t):
    slug = t["slug"]
    prefix = "../"
    if slug not in NEW_TOOL_SLUGS.values():
        REPORT["warnings"].append("tool slug '%s' не из карты новых инструментов" % slug)
    canonical = BASE_URL + slug + "/"

    fields = t["fields_html"]
    if "<form" not in fields:
        fields = '<form id="tool-form" novalidate>\n%s\n</form>' % fields
    fields = add_data_share(fields)

    copy_target = first_r_value_id(t["result_html"])
    bar = action_bar(copy_target)

    faq_html = ""
    if t["faq"]:
        items = []
        for q, a in t["faq"]:
            items.append("<details><summary>%s</summary><p>%s</p></details>" % (q, a))
        faq_html = '<h2>Частые вопросы</h2>\n          <div class="faq">%s</div>' % "".join(items)

    related = []
    for rslug in t["related"]:
        rtitle = SLUG_TITLES.get(rslug)
        if rtitle is None:
            rtitle = rslug
            REPORT["warnings"].append("%s: related slug '%s' без названия" % (slug, rslug))
        related.append('<a class="related-link" href="../%s/">%s</a>' % (rslug, rtitle))
    related_html = "\n          ".join(related)

    main = """
  <div class="container">
    <p class="breadcrumbs"><a href="../">Главная</a> / %s</p>
    <div class="calc-layout">
      <div class="calc-main">
        <div class="calc-card">
          <h1>%s</h1>
          <p class="calc-sub">%s</p>
          %s
%s
          %s
        </div>
        %s
        <article class="calc-explain">
          %s
          %s
        </article>
      </div>
      <aside class="sidebar">
        <div class="side-card">
          <h4>Похожие инструменты</h4>
          %s
        </div>
        <div class="ad-slot ad-slot--sidebar" role="complementary" aria-label="Рекламный блок">
          <span class="tag">Реклама</span>
          <span>300×250</span>
        </div>
      </aside>
    </div>
  </div>
""" % (t["title"], t["h1"], t["sub"], fields, bar, t["result_html"], AD_STUB,
       t["explain_html"], faq_html, related_html)

    main = add_error_roles(main)
    main = rewrite_links(main, prefix)

    page_js = t["page_js"]
    header, footer, ui = parts_for(prefix)
    scripts = [("inline", ui), ("inline", page_js)]
    body_attrs = ' data-calc-slug="%s" data-calc-title="%s"' % (slug, html_escape(t["h1"], quote=True))
    page = render_page(t["meta_title"], t["meta_desc"], canonical, t["meta_title"], t["meta_desc"],
                       t["page_css"], [], body_attrs, header, main, footer, scripts)
    check_ids(page, page_js, "tool:" + slug)
    write(os.path.join(OUT, slug, "index.html"), page)
    SLUG_TITLES[slug] = t["title"]
    REPORT["pages"].append(slug + "/ (новый инструмент)")


# ---------------------------------------------------------------------------
# Редирект-заглушки для 60 старых имён
# ---------------------------------------------------------------------------
def build_redirects():
    n = 0
    for old_name, slug in SLUG_MAP.items():
        title = SLUG_TITLES.get(slug, "Калькулятор")
        page = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://mc.yandex.ru; font-src 'self'; connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com https://www.googletagmanager.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'">
<meta http-equiv="refresh" content="0; url=%s/">
<link rel="canonical" href="%s%s/">
<title>%s — Расчёт.рф</title>
</head>
<body>
<p>Страница переехала: <a href="%s/">%s%s/</a></p>
</body>
</html>
""" % (slug, BASE_URL, slug, title, slug, BASE_URL, slug)
        write(os.path.join(OUT, old_name), page)
        n += 1
    assert n == 60, "redirect stubs: %d" % n
    REPORT["checks"].append("редирект-заглушек: %d" % n)


# ---------------------------------------------------------------------------
# sitemap.xml + robots.txt
# ---------------------------------------------------------------------------
def build_sitemap(tool_slugs):
    urls = [BASE_URL]
    for old_name in SLUG_MAP:
        urls.append(BASE_URL + SLUG_MAP[old_name] + "/")
    for s in tool_slugs:
        urls.append(BASE_URL + s + "/")
    for s in ("about", "privacy", "advertising", "feedback"):
        urls.append(BASE_URL + s + "/")
    import datetime
    lastmod = datetime.date.today().isoformat()
    items = "\n".join("  <url><loc>%s</loc><lastmod>%s</lastmod></url>" % (u, lastmod) for u in urls)
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
%s
</urlset>
""" % items
    write(os.path.join(OUT, "sitemap.xml"), xml)
    expected = 60 + len(tool_slugs) + 4 + 1
    assert len(urls) == expected, "sitemap urls: %d != %d" % (len(urls), expected)
    # sitemap URL сходятся с реальными папками
    for u in urls:
        path = u[len(BASE_URL):]
        if path == "":
            assert os.path.isfile(os.path.join(OUT, "index.html")), "no root index"
        else:
            assert os.path.isfile(os.path.join(OUT, path, "index.html")), "no folder for " + u
    REPORT["checks"].append("sitemap.xml: %d URL, все папки существуют" % len(urls))

    robots = """User-agent: *
Allow: /

Sitemap: %ssitemap.xml
""" % BASE_URL
    write(os.path.join(OUT, "robots.txt"), robots)


# ---------------------------------------------------------------------------
# Самопроверки по собранным страницам
# ---------------------------------------------------------------------------
def check_full_page(path, is_calc):
    html = read(path)
    for bad in ("raschet.rf", "nav-drop", '<div class="referral-block"', "@import",
                'href="calc-', "href='calc-"):
        assert bad not in html, "%s: forbidden token %r" % (path, bad)
    for tok in ('id="main-content"', 'id="theme-toggle"', 'id="mega-btn"'):
        assert tok in html, "%s: missing %s" % (path, tok)
    if is_calc:
        assert 'data-calc-slug="' in html, "%s: no data-calc-slug" % path


def run_global_checks(tool_slugs):
    # все полные страницы
    full_pages = [os.path.join(OUT, "index.html"), os.path.join(OUT, "404.html")]
    calc_dirs = list(SLUG_MAP.values()) + tool_slugs
    for s in calc_dirs + ["about", "privacy", "advertising", "feedback"]:
        full_pages.append(os.path.join(OUT, s, "index.html"))
    for p in full_pages:
        assert os.path.isfile(p), "missing page " + p
        check_full_page(p, os.path.basename(os.path.dirname(p)) in calc_dirs)
    REPORT["checks"].append("полных страниц проверено: %d (calc: %d)" % (len(full_pages), len(calc_dirs)))

    # редиректы
    for old_name, slug in SLUG_MAP.items():
        p = os.path.join(OUT, old_name)
        assert os.path.isfile(p), "no redirect " + old_name
        h = read(p)
        assert ('url=%s/' % slug) in h, "bad refresh in " + old_name
        assert (BASE_URL + slug + "/") in h, "bad canonical in " + old_name
        assert "raschet.rf" not in h, "raschet.rf in redirect " + old_name
    REPORT["checks"].append("редиректы: 60/60 валидны")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # файлы старого сайта на месте?
    for old_name in SLUG_MAP:
        if not os.path.isfile(os.path.join(OLD, old_name)):
            raise SystemExit("нет исходника: " + old_name)
    assert len(SLUG_MAP) == 60, "SLUG_MAP size: %d" % len(SLUG_MAP)

    # 60 старых calc-страниц (ипотека — особая)
    for old_name, slug in SLUG_MAP.items():
        if old_name == "calc-mortgage.html":
            build_mortgage_page()
        else:
            build_calc_page(old_name, slug)

    build_index_page()
    build_static_page("about.html", "about")
    build_static_page("privacy.html", "privacy")
    build_static_page("advertising.html", "advertising")
    build_feedback_page()
    build_404_page()

    tools = load_tools()
    # сначала регистрируем названия всех новых инструментов — related-ссылки
    # могут указывать на ещё не собранные страницы
    for t in tools:
        SLUG_TITLES[t["slug"]] = t["title"]
    tool_slugs = []
    for t in tools:
        build_tool_page(t)
        tool_slugs.append(t["slug"])
    for old_name, slug in NEW_TOOL_SLUGS.items():
        if slug not in tool_slugs:
            REPORT["warnings"].append("нет дескриптора для %s -> %s/" % (old_name, slug))

    build_redirects()
    build_sitemap(tool_slugs)
    run_global_checks(tool_slugs)

    # --- отчёт ---
    lines = []
    lines.append("ОТЧЁТ СБОРКИ «Расчёт.рф» v1.0")
    lines.append("=" * 50)
    lines.append("Страниц собрано: %d (60 старых + %d новых + 4 статических + index + 404)"
                 % (len(REPORT["pages"]), len(tool_slugs)))
    lines.append("Редирект-заглушек: 60")
    lines.append("")
    lines.append("Самопроверки:")
    for c in REPORT["checks"]:
        lines.append("  [OK] " + c)
    lines.append("")
    lines.append("Patch-miss (%d):" % len(REPORT["patch_miss"]))
    for pm in REPORT["patch_miss"]:
        lines.append("  - " + pm)
    lines.append("")
    lines.append("Страницы-исключения:")
    for e in REPORT["exceptions"]:
        lines.append("  - " + e)
    lines.append("  - calc-compare-lists.html, calc-split-groups.html: нет result-panel/<form> — action-bar перед блоком вывода")
    lines.append("  - calc-qr-generator.html: CDN qrcodejs с crossorigin/referrerpolicy/onerror; SRI не вычислен")
    lines.append("  - calc-pension.html -> pensiya/: в карте задания не было (59 из 60), slug добавлен")
    lines.append("")
    lines.append("Предупреждения (%d):" % len(REPORT["warnings"]))
    for w in REPORT["warnings"]:
        lines.append("  - " + w)
    lines.append("")
    lines.append("Страницы:")
    for p in REPORT["pages"]:
        lines.append("  " + p)
    report_text = "\n".join(lines)
    write(REPORT_PATH, report_text)
    print(report_text)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
