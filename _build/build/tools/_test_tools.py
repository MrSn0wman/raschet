# -*- coding: utf-8 -*-
# Валидация дескрипторов инструментов: ключи, лимиты меты, XSS-гигиена page_js.
import importlib.util
import os
import re
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

REQUIRED_KEYS = [
    "slug", "title", "meta_title", "meta_desc", "h1", "sub", "category",
    "fields_html", "result_html", "explain_html", "faq", "page_js", "page_css",
    "related",
]

ALLOWED_RELATED = set("""
ipoteka kredit vklad avtokredit refinansirovanie mikrozaim procenty-po-zaimu iis
nalogovyy-vychet-kvartira nalog-s-prodazhi-kvartiry ndfl nds nalog-samozanyatyh
doli-v-kvartire doli-po-materinskomu-kapitalu strahovye-vznosy-ip transportnyy-nalog
rashod-topliva osago rastamozhka utilsbor trudovoy-stazh otpusknye-dni otpusknye
bolnichnyy dekretnye peni-po-nalogam neustoika-po-dogovoru procenty-395-gk
neustoika-po-ddu summa-propisyu procenty ploshad obem drobi stepeni nod nok
razlozhenie-na-mnozhiteli sistemy-schisleniya dni vozrast chasovye-poyasa imt
idealnyy-ves konverter-edinic slozhnyy-procent skidki chaevye sluchaynye-chisla
sluchaynyy-vybor peremeshat-spisok razdelit-na-gruppy sravnenie-spiskov
generator-paroley generator-promokodov qr-generator zaryadka-elektromobilya
konverter-valyut schetchik-slov transliteraciya udalenie-dubley-strok proverka-inn
proverka-snils proverka-nomera-karty uuid-generator lorem-ipsum generator-nikneimov
unix-vremya rabochie-dni obratnyy-otschet
""".split())

EXPECTED_SLUGS = [
    "konverter-valyut", "schetchik-slov", "transliteraciya",
    "udalenie-dubley-strok", "proverka-inn", "proverka-snils",
    "proverka-nomera-karty", "uuid-generator", "lorem-ipsum",
    "generator-nikneimov", "unix-vremya", "rabochie-dni", "obratnyy-otschet",
]

errors = []
ok_count = 0

for fname in sorted(os.listdir(TOOLS_DIR)):
    if not fname.endswith(".py") or fname.startswith("_"):
        continue
    path = os.path.join(TOOLS_DIR, fname)
    stem = fname[:-3]
    spec = importlib.util.spec_from_file_location("tool_" + stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        errors.append("%s: import failed: %r" % (fname, e))
        continue

    tool = getattr(mod, "TOOL", None)
    if not isinstance(tool, dict):
        errors.append("%s: TOOL missing or not a dict" % fname)
        continue

    problems = []

    for key in REQUIRED_KEYS:
        if key not in tool:
            problems.append("missing key '%s'" % key)

    if problems:
        errors.append("%s: %s" % (fname, "; ".join(problems)))
        continue

    if tool["slug"] != stem:
        problems.append("slug '%s' != filename '%s'" % (tool["slug"], stem))
    if stem not in EXPECTED_SLUGS:
        problems.append("unexpected slug (not in task list)")

    mt = tool["meta_title"]
    md = tool["meta_desc"]
    if len(mt) > 60:
        problems.append("meta_title %d chars > 60" % len(mt))
    if len(md) > 160:
        problems.append("meta_desc %d chars > 160" % len(md))

    faq = tool["faq"]
    if not isinstance(faq, list) or not (3 <= len(faq) <= 4):
        problems.append("faq must be list of 3-4 pairs, got %s" %
                        (len(faq) if isinstance(faq, list) else type(faq).__name__))
    else:
        for pair in faq:
            if not (isinstance(pair, tuple) and len(pair) == 2 and all(isinstance(x, str) for x in pair)):
                problems.append("faq pair malformed: %r" % (pair,))

    js = tool["page_js"]
    if "eval(" in js:
        problems.append("page_js contains eval(")
    if "document.write" in js:
        problems.append("page_js contains document.write")
    for m in re.finditer(r"innerHTML", js):
        ctx = js[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        problems.append("page_js contains innerHTML — context: ...%s..." % ctx)

    rel = tool["related"]
    if not isinstance(rel, list) or not (3 <= len(rel) <= 4):
        problems.append("related must be list of 3-4 slugs")
    else:
        bad = [r for r in rel if r not in ALLOWED_RELATED]
        if bad:
            problems.append("related not in allowed list: %s" % bad)

    for htmlkey in ("fields_html", "result_html"):
        if not isinstance(tool[htmlkey], str) or not tool[htmlkey].strip():
            problems.append("%s is empty" % htmlkey)

    if problems:
        errors.append("%s: %s" % (fname, "; ".join(problems)))
    else:
        ok_count += 1
        print("OK  %-28s meta_title=%2d meta_desc=%3d faq=%d related=%d" %
              (stem, len(mt), len(md), len(faq), len(rel)))

missing = [s for s in EXPECTED_SLUGS if not os.path.exists(os.path.join(TOOLS_DIR, s + ".py"))]
if missing:
    errors.append("missing files: %s" % missing)

print()
if errors:
    print("ERRORS:")
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("ALL CHECKS PASSED: %d tools" % ok_count)
