# -*- coding: utf-8 -*-
# SEO-мета: og:image + twitter cards + добивка JSON-LD (WebApplication, FAQPage).
# Пост-процессор по образцу fix_footer.py / fix_csp.py. Идемпотентен.
# Зеркало для будущих пересборок: render_page() в build_all.py.
import io, os, re, json, html as htmllib

SITE = r"C:\Kimi\raschet"
BASE = "https://mrsn0wman.github.io/raschet/"
OG_IMG = BASE + "assets/og-cover.png"
TODAY = "2026-10-18"

FINANCE = set("""ipoteka dosrochnoe-pogashenie vklad kredit avtokredit refinansirovanie mikrozaim
procenty-po-zaimu iis konverter-valyut nalogovyy-vychet-kvartira nalog-s-prodazhi-kvartiry ndfl nds
nalog-samozanyatyh doli-v-kvartire doli-po-materinskomu-kapitalu strahovye-vznosy-ip trudovoy-stazh
otpusknye-dni otpusknye bolnichnyy dekretnye pensiya transportnyy-nalog rashod-topliva osago
rastamozhka utilsbor zaryadka-elektromobilya peni-po-nalogam neustoika-po-dogovoru procenty-395-gk
neustoika-po-ddu summa-propisyu slozhnyy-procent skidki chaevye""".split())
SERVICE = {"", "404", "about", "privacy", "advertising", "feedback"}

def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()

def write(p, t):
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)

def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

stats = {"og": 0, "webapp": 0, "faq": 0}
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", ".git")]
    for fn in files:
        if fn != "index.html":
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, SITE).replace("\\", "/")
        slug = "" if rel == "index.html" else rel[:-len("/index.html")]
        t = read(p)
        orig = t

        # --- 1. og:image + twitter cards ---
        if 'property="og:image"' not in t:
            og_t = (re.search(r'<meta property="og:title" content="([^"]*)"', t) or [None, ""])[1] if re.search(r'<meta property="og:title" content="([^"]*)"', t) else ""
            og_d_m = re.search(r'<meta property="og:description" content="([^"]*)"', t)
            og_d = og_d_m.group(1) if og_d_m else ""
            block = (
                '<meta property="og:site_name" content="Расчёт.рф">\n'
                '<meta property="og:image" content="%s">\n' % OG_IMG +
                '<meta property="og:image:width" content="1200">\n'
                '<meta property="og:image:height" content="630">\n'
                '<meta name="twitter:card" content="summary_large_image">\n'
                '<meta name="twitter:title" content="%s">\n' % og_t +
                '<meta name="twitter:description" content="%s">\n' % og_d +
                '<meta name="twitter:image" content="%s">\n' % OG_IMG
            )
            m = re.search(r'(<meta property="og:url" content="[^"]*">\n)', t)
            if m:
                t = t.replace(m.group(1), m.group(1) + block, 1)
                stats["og"] += 1

        if slug in SERVICE:
            if t != orig:
                write(p, t)
            continue

        # --- 2. JSON-LD ---
        has_ld = 'application/ld+json' in t
        has_faqpage = '"FAQPage"' in t
        canon_m = re.search(r'<link rel="canonical" href="([^"]*)"', t)
        canon = canon_m.group(1) if canon_m else BASE + slug + "/"
        h1_m = re.search(r"(?s)<h1[^>]*>(.*?)</h1>", t)
        h1 = strip_tags(h1_m.group(1)) if h1_m else slug
        desc_m = re.search(r'<meta name="description" content="([^"]*)"', t)
        desc = desc_m.group(1) if desc_m else ""
        inject = ""

        if not has_ld:
            webapp = {
                "@context": "https://schema.org",
                "@type": "WebApplication",
                "name": h1,
                "description": desc,
                "applicationCategory": "FinanceApplication" if slug in FINANCE else "UtilitiesApplication",
                "operatingSystem": "Any",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "RUB"},
                "url": canon,
                "dateModified": TODAY,
                "inLanguage": "ru-RU",
            }
            inject += '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(webapp, ensure_ascii=False, indent=2)
            stats["webapp"] += 1

        # FAQPage из существующей разметки details/summary (контент совпадает с видимым)
        faq_m = re.search(r'(?s)<div class="faq"[^>]*>(.*?)</div>\s*(?=<)', t)
        if faq_m and not has_faqpage:
            qa = []
            for dm in re.finditer(r"(?s)<details[^>]*>(.*?)</details>", faq_m.group(1)):
                sm = re.search(r"(?s)<summary[^>]*>(.*?)</summary>", dm.group(1))
                if not sm:
                    continue
                q = strip_tags(sm.group(1))
                a = strip_tags(dm.group(1)[sm.end():])
                if q and a:
                    qa.append({"@type": "Question", "name": q,
                               "acceptedAnswer": {"@type": "Answer", "text": a}})
            if qa:
                faqld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa}
                inject += '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(faqld, ensure_ascii=False, indent=2)
                stats["faq"] += 1

        if inject:
            t = t.replace("</head>", inject + "</head>", 1)

        if t != orig:
            write(p, t)

print("og/twitter injected:", stats["og"], "| WebApplication:", stats["webapp"], "| FAQPage:", stats["faq"])
# самопроверка: все страницы с og:image; LD валиден
bad = []
for root, dirs, files in os.walk(SITE):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets", ".git")]
    for fn in files:
        if fn != "index.html":
            continue
        p = os.path.join(root, fn)
        t = read(p)
        if 'property="og:image"' not in t:
            bad.append(os.path.relpath(p, SITE))
        for blk in re.findall(r'(?s)<script type="application/ld\+json">(.*?)</script>', t):
            try:
                json.loads(blk)
            except Exception as e:
                bad.append(os.path.relpath(p, SITE) + " LD-PARSE " + str(e))
print("problems:", bad if bad else "none")
