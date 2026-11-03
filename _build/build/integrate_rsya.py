# -*- coding: utf-8 -*-
# Интеграция РСЯ (Яндекс.RTB) поверх собранного сайта:
# 1) загрузчик context.js в <head> страниц со слотами;
# 2) плейсхолдеры ad-slot → реальные RTB-блоки
#    (inline R-A-20316097-1, sidebar R-A-20316097-2, leader на index → -1);
# 3) CSP расширен под yandex.ru/yastatic.net + frame-src/img-src/media-src.
# Идемпотентен: повторный запуск ничего не меняет.
import io
import os
import re

from pathlib import Path
import json
from site_common import PARTS, VERIFICATION_RE, html_files, read, site_parser, write

BLOCK_INLINE = "R-A-20316097-1"
BLOCK_SIDEBAR = "R-A-20316097-2"

OLD_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru "
           "https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; "
           "img-src 'self' data: https://mc.yandex.ru; font-src 'self'; "
           "connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com "
           "https://www.googletagmanager.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")

NEW_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru "
           "https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru "
           "https://yastatic.net https://*.yandex.net; "
           "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
           "font-src 'self' https://yastatic.net; "
           "connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com "
           "https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru "
           "https://*.yandex.net https://yastatic.net; "
           "frame-src https://yandex.ru https://an.yandex.ru https://*.yandex.net https://mc.yandex.ru https://yastatic.net; "
           "media-src https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")

# предыдущие версии CSP — мигрируем на NEW_CSP
CSP_PREV = [("default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru "
             "https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru "
             "https://yastatic.net https://*.yandex.net; "
             "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
             "font-src 'self' https://yastatic.net; "
             "connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com "
             "https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru "
             "https://*.yandex.net https://yastatic.net; "
             "frame-src https://yandex.ru https://an.yandex.ru https://*.yandex.net https://mc.yandex.ru; "
             "media-src https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"),
            ("default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru "
             "https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru "
             "https://yastatic.net https://*.yandex.net; "
             "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; "
             "connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com "
             "https://www.googletagmanager.com https://yandex.ru https://an.yandex.ru "
             "https://*.yandex.net https://yastatic.net; "
             "frame-src https://yandex.ru https://an.yandex.ru https://*.yandex.net; media-src https:; "
             "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"),
            ("default-src 'self'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru "
             "https://www.googletagmanager.com https://yandex.ru https://*.yandex.ru https://yastatic.net; "
             "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; "
             "connect-src 'self' https://mc.yandex.ru https://www.google-analytics.com "
             "https://www.googletagmanager.com https://yandex.ru https://*.yandex.ru https://yastatic.net; "
             "frame-src https://yandex.ru https://*.yandex.ru; media-src https:; "
             "frame-ancestors 'none'; base-uri 'self'; form-action 'self'")]

REFERRER_META = '<meta name="referrer" content="strict-origin-when-cross-origin">\n'

LOADER = ("<script>window.yaContextCb=window.yaContextCb||[]</script>\n"
          "<script src=\"https://yandex.ru/ads/system/context.js\" async></script>\n")

RENDER = """
<script>
window.yaContextCb.push(() => {
    Ya.Context.AdvManager.render({
        "blockId": "%s",
        "renderTo": "yandex_rtb_%s"
    })
})
</script>"""


def slot_html(cls, block_id):
    return ('<div class="ad-slot ad-slot--%s" role="complementary" aria-label="Рекламный блок">'
            '<span class="tag">Реклама</span>'
            '<div id="yandex_rtb_%s"></div></div>' % (cls, block_id)) + "\n" + (RENDER % (block_id, block_id))


def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()


def write(p, text):
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sensitive_routes(parts=PARTS):
    config = json.loads(read(Path(parts) / "privacy-routes.json"))
    routes = config.get("sensitiveRoutes", config.get("routes"))
    if not isinstance(routes, list) or not routes or any(not re.fullmatch(r"[a-z0-9-]+", r) for r in routes):
        raise ValueError("Invalid privacy route configuration")
    js = read(Path(parts) / "privacy.js")
    match = re.search(r"const sensitiveRoutes = Object.freeze\(\[(.*?)\]\)", js, re.S)
    if not match or re.findall(r"[\"']([a-z0-9-]+)[\"']", match.group(1)) != routes:
        raise ValueError("Privacy JS/JSON route lists differ")
    return set(routes)

def privacy_loader(text, prefix):
    text = re.sub(r'<script\b[^>]*src=["\'][^"\']*assets/privacy\.js["\'][^>]*>\s*</script>\s*', '', text)
    loader = '<script src="%sassets/privacy.js"></script>\n' % prefix
    charset = re.search(r'<meta charset="[^"]+">\n?', text)
    if charset:
        return text[:charset.end()] + loader + text[charset.end():]
    if "<head>" not in text: raise ValueError("No head for early privacy loader")
    return text.replace("<head>", "<head>\n" + loader, 1)

def remove_ads(text):
    def keep_script(match):
        script = match.group(0)
        if any(token in script for token in ("yandex.ru/ads/system/context.js", "window.yaContextCb", "Ya.Context.AdvManager.render", "assets/analytics.js")):
            return ""
        return script
    text = re.sub(r'(?m)(?:^[ \t]*)?<script\b[^>]*>.*?</script>', keep_script, text, flags=re.S)
    # Balance actual div tags; nested RTB placeholders must not leave a stray close.
    while True:
        start = re.search(r'<div\b[^>]*class="[^"]*\bad-slot\b[^"]*"[^>]*>', text)
        if not start: break
        depth = 1
        end = None
        for tag in re.finditer(r'</?div\b[^>]*>', text[start.end():]):
            depth += -1 if tag.group(0).startswith("</") else 1
            if depth == 0:
                end = start.end() + tag.end()
                break
        if end is None: raise ValueError("Unbalanced ad slot")
        line_start = text.rfind("\n", 0, start.start()) + 1
        remove_start = line_start if not text[line_start:start.start()].strip(" \t") else start.start()
        text = text[:remove_start] + text[end:]
    text = re.sub(r'\sdata-share="[^"]*"', '', text)
    return text


def process(site, parts=PARTS):
    from site_common import safe_destination
    site = safe_destination(site)
    sensitive = sensitive_routes(parts)
    stats = {"csp": 0, "loader": 0, "inline": 0, "sidebar": 0, "leader": 0, "files": 0}
    for root, dirs, files in os.walk(site):
        dirs[:] = [d for d in dirs if d not in ("_build", "backend", ".git", ".github", "assets")]
        for fn in files:
            if not fn.endswith(".html"):
                continue
            path = os.path.join(root, fn)
            text = read(path)
            orig = text
            rel = Path(path).relative_to(site).as_posix()
            if VERIFICATION_RE.fullmatch(rel):
                continue
            text = privacy_loader(text, "../" * rel.count("/"))
            slug = rel.split("/")[0] if "/" in rel else ""
            if slug in sensitive or rel.startswith("calc-"):
                text = remove_ads(text)
                if text != orig:
                    write(path, text)
                    stats["files"] += 1
                continue

            # --- CSP ---
            if OLD_CSP in text:
                text = text.replace(OLD_CSP, NEW_CSP)
                stats["csp"] += 1
            else:
                for prev in CSP_PREV:
                    if prev in text:
                        text = text.replace(prev, NEW_CSP)
                        stats["csp"] += 1
                        break
                else:
                    if NEW_CSP not in text and "Content-Security-Policy" in text:
                        print("WARN: неизвестный CSP в", path)

            # --- Referrer-Policy (защита URL страниц от утечки трекерам) ---
            if '<meta name="referrer"' not in text:
                m = re.search(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n', text)
                if m:
                    text = text[:m.end()] + REFERRER_META + text[m.end():]

            # --- слоты ---
            has_slots = 'ad-slot ad-slot--' in text
            if has_slots and "yandex_rtb_" not in text:
                if 'ad-slot ad-slot--inline' in text:
                    text = re.sub(
                        r'(?s)<div class="ad-slot ad-slot--inline"[^>]*>.*?</div>',
                        lambda m: slot_html("inline", BLOCK_INLINE),
                        text, count=1)
                    stats["inline"] += 1
                if 'ad-slot ad-slot--sidebar' in text:
                    text = re.sub(
                        r'(?s)<div class="ad-slot ad-slot--sidebar"[^>]*>.*?</div>',
                        lambda m: slot_html("sidebar", BLOCK_SIDEBAR),
                        text, count=1)
                    stats["sidebar"] += 1
                if 'ad-slot ad-slot--leader' in text:
                    text = re.sub(
                        r'(?s)<div class="ad-slot ad-slot--leader"[^>]*>.*?</div>',
                        lambda m: slot_html("leader", BLOCK_INLINE),
                        text, count=1)
                    stats["leader"] += 1

            # --- загрузчик ---
            if ('yandex_rtb_' in text or has_slots) and "context.js" not in text:
                m = re.search(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n', text)
                if m:
                    text = text[:m.end()] + LOADER + text[m.end():]
                    stats["loader"] += 1
                else:
                    print("WARN: нет CSP-меты для вставки загрузчика:", path)

            if text != orig:
                write(path, text)
                stats["files"] += 1

    print("Интеграция РСЯ: %(csp)d CSP, %(loader)d загрузчиков, "
          "%(inline)d inline, %(sidebar)d sidebar, %(leader)d leader; файлов изменено: %(files)d" % stats)


if __name__ == "__main__":
    parser = site_parser(__doc__)
    parser.add_argument("--parts", type=Path, default=PARTS)
    args = parser.parse_args()
    process(args.site, args.parts)
