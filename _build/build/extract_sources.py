# -*- coding: utf-8 -*-
"""One-time/explicit lossless page decomposition; never part of the build.

Use --site an immutable HEAD snapshot first; refresh patched pages only after
their owner signals. Full HTML is not copied: shared parts are factored out.
"""
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from site_common import PARTS, SOURCES, VERIFICATION_RE, html_files, part_values, read, substitute, write, validate_manifest

TOKEN = lambda key: "@@RASCHET_" + key + "@@"

def span(pattern, text, label):
    matches = list(re.finditer(pattern, text, re.S))
    if len(matches) != 1:
        raise ValueError("Expected exactly one " + label + ", got " + str(len(matches)))
    return matches[0]

def decompose(text, rel, parts):
    prefix = "../" * rel.count("/")
    values = part_values(parts, prefix)
    head = span(r"(?<=<head>).*?(?=</head>)", text, "head")
    header = span(r'<a class="skip-link".*?<div class="ruler" aria-hidden="true"></div>', text, "header")
    footer = span(r'<footer class="site-footer">.*?</footer>', text, "footer")
    main = span(r"<main\b.*?</main>", text, "main")
    if not head.end() < header.start() < main.start() < main.end() <= footer.start():
        raise ValueError("Invalid page ordering: " + rel)
    page_head = head.group(0)
    css = span(r"(?<=<style>\n).*?(?=</style>)", page_head, "style")
    css_raw = css.group(0)
    common_css = values["STYLE"]
    if css_raw == common_css:
        page_css = ""
    elif css_raw.startswith(common_css.rstrip("\n")):
        page_css = css_raw[len(common_css.rstrip("\n")):].removesuffix("\n")
    else:
        raise ValueError("Shared CSS drift; sync approved parts before extraction: " + rel)
    values = part_values(parts, prefix, page_css)
    if css_raw != values["STYLE"]:
        raise ValueError("CSS lossless check failed: " + rel)
    page_head = page_head[:css.start()] + TOKEN("STYLE") + page_head[css.end():]
    if page_head.count(values["HEAD_INIT"]) != 1:
        raise ValueError("Head-init drift: " + rel)
    page_head = page_head.replace(values["HEAD_INIT"], TOKEN("HEAD_INIT"), 1)
    if header.group(0) != values["HEADER"] or footer.group(0) != values["FOOTER"]:
        raise ValueError("Shared header/footer drift: " + rel)
    scripts = text[footer.end():]
    ui = [m for m in re.finditer(r"<script>\n(.*?)\n</script>", scripts, re.S) if "// Общая логика интерфейса" in m.group(1)]
    if len(ui) != 1:
        raise ValueError("Missing/duplicate common UI: " + rel)
    m = ui[0]
    if m.group(1) != values["UI"]:
        raise ValueError("Shared UI drift: " + rel)
    scripts = scripts[:m.start(1)] + TOKEN("UI") + scripts[m.end(1):]
    shell = text[:head.start()] + TOKEN("HEAD") + text[head.end():header.start()] + TOKEN("HEADER") + text[header.end():main.start()] + TOKEN("BODY") + text[main.end():footer.start()] + TOKEN("FOOTER") + TOKEN("SCRIPTS")
    files = {"shell.html": shell, "head.html": page_head, "body.html": main.group(0), "scripts.html": scripts, "page.css": page_css}
    reconstructed = render_files(files, parts, rel)
    if reconstructed != text:
        raise ValueError("Lossless roundtrip failed: " + rel)
    return files

def render_files(files, parts, rel):
    values = part_values(parts, "../" * rel.count("/"), files["page.css"])
    values.update({"HEAD": substitute(files["head.html"], values), "BODY": files["body.html"], "SCRIPTS": substitute(files["scripts.html"], values)})
    return substitute(files["shell.html"], values)

def extract(site, sources, parts, only=None):
    site, sources, parts = map(Path, (site, sources, parts))
    destination = sources.resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if destination != SOURCES.resolve() and temp not in destination.parents:
        raise ValueError("Extraction output must be canonical _build/sources or an explicit TEMP subdirectory")
    if destination == site.resolve() or destination in site.resolve().parents:
        raise ValueError("Sources must not overwrite input site or ancestors")
    manifest_path = sources / "manifest.json"
    manifest = json.loads(read(manifest_path)) if only and manifest_path.exists() else {"version": 1, "pages": [], "redirects": [], "static": []}
    pages = []
    pending_writes = []
    for path in html_files(site):
        rel = path.relative_to(site).as_posix()
        if only and rel not in only:
            continue
        text = read(path)
        if VERIFICATION_RE.fullmatch(rel):
            if only: continue
            manifest["static"].append(rel)
            continue
        if rel.startswith("calc-"):
            if only: continue
            target = span(r'<meta http-equiv="refresh" content="0; url=([^";]+)"', text, "redirect").group(1)
            title = span(r"<title>(.*?)</title>", text, "redirect title").group(1)
            manifest["redirects"].append({"path": rel, "target": target, "title": title})
            continue
        files = decompose(text, rel, parts)
        key = "home" if rel == "index.html" else "not-found" if rel == "404.html" else rel.removesuffix("/index.html")
        for name, value in files.items():
            pending_writes.append((sources / "pages" / key / name, value))
        pages.append({"path": rel, "source": key, "sha256": hashlib.sha256(text.encode()).hexdigest(), "calculator": re.search(r'^<body[^>\n]*\bdata-calc-slug="', text, re.M) is not None})
    if only:
        done = {p["path"] for p in pages}
        if done != set(only): raise ValueError("Refresh missing pages: " + str(set(only) - done))
        manifest["pages"] = [p for p in manifest["pages"] if p["path"] not in done] + pages
    else:
        manifest["pages"] = pages
    manifest["pages"].sort(key=lambda p: p["path"])
    validate_manifest(manifest)
    for path, value in pending_writes:
        write(path, value)
    write(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("Extracted lossless page sources:", len(pages))
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--sources", type=Path, default=SOURCES)
    parser.add_argument("--parts", type=Path, default=PARTS)
    parser.add_argument("--only", nargs="+", help="Explicit owner-approved page refresh")
    args = parser.parse_args()
    extract(args.site, args.sources, args.parts, args.only)

if __name__ == "__main__":
    main()
