# -*- coding: utf-8 -*-
# Полный прогон собранного сайта C:\Kimi\raschet-site в headless Chrome
# с инструментацией (__errs hook) и сверкой против baseline.json.
import io
import json
import os
import re
import shutil
import subprocess
import sys

SITE = r"C:\Kimi\raschet"
WORK = r"C:\Kimi\raschet-test\site-instr"
HARNESS_SRC = r"C:\Kimi\raschet-test\instrumented\harness.html"
BASELINE = r"C:\Kimi\raschet-test\baseline.json"
RESULT = r"C:\Kimi\raschet-test\site-result.json"
PORT = 8322
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

HOOK = ('<script>window.__errs=[];window.addEventListener("error",function(e){'
        '__errs.push(String(e.message||e.error||"err")+" @"+String(e.filename||"").split("/").pop()+":"+e.lineno)});</script>')

def read(p):
    with io.open(p, "r", encoding="utf-8") as f:
        return f.read()

# --- 1. instrumented copy ---
if os.path.exists(WORK):
    shutil.rmtree(WORK, onerror=lambda f, p, e: (os.chmod(p, 0o777), os.unlink(p)))
shutil.copytree(SITE, WORK, ignore=shutil.ignore_patterns(".git", "_build", "backend"))

pages = []
for root, dirs, files in os.walk(WORK):
    dirs[:] = [d for d in dirs if d not in ("_build", "backend", "assets")]
    for fn in files:
        if not fn.endswith(".html"):
            continue
        rel = os.path.relpath(os.path.join(root, fn), WORK).replace("\\", "/")
        # редирект-заглушки не тестируем (они уводят навигацию)
        if re.match(r"^calc-[a-z0-9-]+\.html$", rel):
            continue
        text = read(os.path.join(root, fn))
        text = text.replace("<head>", "<head>" + HOOK, 1)
        with io.open(os.path.join(root, fn), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        pages.append(rel if rel == "index.html" or rel == "404.html" else rel.replace("/index.html", "/"))

pages.sort()
with io.open(os.path.join(WORK, "pages.json"), "w", encoding="utf-8") as f:
    json.dump(pages, f)
shutil.copy(HARNESS_SRC, os.path.join(WORK, "harness.html"))
print("instrumented pages:", len(pages))

# --- 2. server + chrome ---
server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "--directory", WORK],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    import time
    time.sleep(1.5)
    out = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                          "--user-data-dir=" + r"C:\Kimi\raschet-test\chrome-sitetest",
                          "--virtual-time-budget=420000",
                          "--dump-dom", "http://127.0.0.1:%d/harness.html" % PORT],
                         capture_output=True, timeout=600)
    dom = out.stdout.decode("utf-8", "ignore")
finally:
    server.kill()

# --- 3. parse ---
records = []
for ln in dom.splitlines():
    ln = ln.strip()
    if ln.startswith("{") and '"page"' in ln or '"__done__"' in ln:
        try:
            records.append(json.loads(ln))
        except Exception:
            pass

done = [r for r in records if r.get("__done__")]
recs = [r for r in records if r.get("page")]
with io.open(RESULT, "w", encoding="utf-8") as f:
    json.dump(recs, f, ensure_ascii=False, indent=2)

print("records:", len(recs))
if done:
    print("summary:", json.dumps(done[0], ensure_ascii=False))

# --- 4. сверка с baseline ---
if os.path.exists(BASELINE):
    base = json.load(open(BASELINE, encoding="utf-8"))
    if isinstance(base, dict):
        base = base.get("pages", [])
    # карта old calc-xxx.html -> slug/ из редирект-заглушек
    m = {}
    for fn in os.listdir(SITE):
        if re.match(r"^calc-[a-z0-9-]+\.html$", fn):
            t = read(os.path.join(SITE, fn))
            mm = re.search(r'url=([a-z0-9-]+)/"', t)
            if mm:
                m[fn] = mm.group(1) + "/"
    base_by_new = {}
    for b in base:
        newp = m.get(b["page"], b["page"])
        base_by_new[newp] = b
    regressions = []
    for r in recs:
        b = base_by_new.get(r["page"])
        if not b:
            continue
        if b.get("errors") == [] and r.get("errors"):
            regressions.append((r["page"], "JS errors appeared", r["errors"]))
        if b.get("result_found") and not r.get("result_found"):
            regressions.append((r["page"], "result lost", None))
        if b.get("interactive") is True and r.get("interactive") is False:
            regressions.append((r["page"], "interactive lost", None))
    print("regressions vs baseline:", len(regressions))
    for rg in regressions:
        print("  -", rg)
