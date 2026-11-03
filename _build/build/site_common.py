# -*- coding: utf-8 -*-
"""Shared paths, URL mapping and lossless canonical part rendering."""
import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PARTS = REPO / "_build" / "parts"
SOURCES = REPO / "_build" / "sources"
DEFAULT_SITE = REPO / "_build" / "out"
BASE_URL = "https://raschet.net/"

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




VERIFICATION_RE = re.compile(r"^(?:yandex_[0-9a-f]+|google[0-9a-f]+)\.html$")
EXCLUDED = {"_build", "backend", "assets", ".git", ".github", "tests"}

def read(path):
    return Path(path).read_bytes().decode("utf-8")

def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))

def html_files(site, full=False):
    site = Path(site)
    for path in sorted(site.rglob("*.html")):
        rel = path.relative_to(site)
        if any(part in EXCLUDED for part in rel.parts[:-1]):
            continue
        if full and (VERIFICATION_RE.fullmatch(rel.as_posix()) or rel.name.startswith("calc-")):
            continue
        yield path

def site_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE, help="Explicit output tree (default: _build/out; never repository root)")
    return parser

def safe_destination(path):
    path = Path(path).resolve()
    if path == REPO or path in REPO.parents or path == PARTS or path == SOURCES:
        raise ValueError("Refusing protected build destination: " + str(path))
    return path

def validate_manifest(manifest):
    if manifest.get("version") != 1:
        raise ValueError("Unsupported source manifest")
    pages, redirects, static = (manifest.get(k, []) for k in ("pages", "redirects", "static"))
    expected = {"index.html", "404.html"} | {slug + "/index.html" for slug in list(LINK_MAP.values()) + ["about", "privacy", "advertising", "feedback"]}
    if len(pages) != 79 or {p.get("path") for p in pages} != expected or sum(p.get("calculator") is True for p in pages) != 73:
        raise ValueError("Expected exact page inventory: 79 full pages / 73 calculators")
    for page in pages:
        if not re.fullmatch(r"[a-z0-9-]+", page.get("source", "")):
            raise ValueError("Unsafe page source id")
    if len(redirects) != 60 or {r.get("path") for r in redirects} != set(SLUG_MAP):
        raise ValueError("Expected exact 60 historical redirects")
    for item in redirects:
        if item.get("target") != SLUG_MAP[item["path"]] + "/":
            raise ValueError("Unsafe/mismatched redirect target")
    if len(static) != 2 or len(set(static)) != 2 or any(not VERIFICATION_RE.fullmatch(p) for p in static):
        raise ValueError("Expected exactly two search verification files")
    return manifest

def part_values(parts, prefix, page_css=""):
    parts = Path(parts)
    css = read(parts / "fonts.css").replace("__PREFIX__", prefix) + "\n" + read(parts / "style.css")
    return {"HEADER": rewrite_links(read(parts / "header.html"), prefix).rstrip("\n"),
            "FOOTER": rewrite_links(read(parts / "footer.html"), prefix).rstrip("\n"),
            "UI": rewrite_links(read(parts / "ui.js"), prefix).rstrip("\n"),
            "HEAD_INIT": read(parts / "head-init.html").rstrip("\n"),
            "STYLE": css.rstrip("\n") + page_css + "\n"}

def substitute(template, values):
    def replace(m):
        key = m.group(1)
        if key not in values:
            raise ValueError("Unknown canonical token: " + key)
        return values[key]
    return re.sub(r"@@RASCHET_([A-Z_]+)@@", replace, template)
