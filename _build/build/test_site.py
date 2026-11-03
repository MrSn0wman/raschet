# -*- coding: utf-8 -*-
"""Reproducible strict static + Chrome gate. Missing records/errors exit nonzero.

Runs against --site (default _build/out), never copies or instruments public root.
External requests and service workers are blocked by the CDP harness.
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from urllib.parse import unquote, urlsplit
from site_common import BASE_URL, REPO, SOURCES, VERIFICATION_RE, html_files, read, site_parser

CHROME = Path(os.environ.get('CHROME', r'C:\Program Files\Google\Chrome\Application\chrome.exe'))

def static_checks(site, sources=SOURCES):
    site, sources = Path(site), Path(sources)
    errors = []
    try: manifest = json.loads(read(sources / 'manifest.json'))
    except Exception as exc: return ['Missing/invalid source manifest: ' + str(exc)]
    expected = {p['path'] for p in manifest['pages']}
    if len(expected) != 79: errors.append('Expected exactly 79 full pages')
    if sum(p['calculator'] for p in manifest['pages']) != 73: errors.append('Expected 73 calculators')
    actual = {p.relative_to(site).as_posix() for p in html_files(site, full=True)}
    if expected != actual: errors.append('Full-page inventory mismatch: missing=%s extra=%s' % (sorted(expected-actual), sorted(actual-expected)))
    for rel in sorted(expected):
        path = site / rel
        if not path.is_file(): continue
        text = read(path)
        for token in ('id="main-content"', 'id="theme-toggle"', 'nav-cat-btn', 'nav-cat-panel', '// Общая логика интерфейса'):
            if token not in text: errors.append(rel + ': missing ' + token)
        for stale in ('id="mega-btn"', 'mega-grid', 'mega-panel', 'closeMegaCats', '@@RASCHET_', 'raschet.rf', "RASCHET_API_BASE = 'http"):
            if stale in text: errors.append(rel + ': stale/unsafe ' + stale)
        titles = re.findall(r'<title>(.*?)</title>', text, re.S)
        if len(titles) != 1 or not titles[0].strip() or len(titles[0]) > 60: errors.append(rel + ': title count/length invalid')
        for name in ('description',):
            if not re.search(r'<meta name="%s" content="[^"\n]+"' % name, text): errors.append(rel + ': missing SEO ' + name)
        expected_canonical = BASE_URL + ('' if rel == 'index.html' else rel.removesuffix('index.html') if rel.endswith('/index.html') else rel)
        if '<link rel="canonical" href="%s"' % expected_canonical not in text: errors.append(rel + ': wrong canonical')
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            try: json.loads(raw)
            except Exception as exc: errors.append(rel + ': invalid JSON-LD ' + str(exc))
        scripts = re.findall(r'<script\b[^>]*>', text)
        if not scripts or not re.fullmatch(r'<script src="[^"]*assets/privacy.js">', scripts[0]): errors.append(rel + ': privacy is not first synchronous script')
        urls = re.findall(r'(?:src|href)="([^"#]+)"', text) + re.findall(r"url\(['\"]?([^)'\"]+)", text)
        for url in urls:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or url.startswith(('data:', 'mailto:', 'tel:', 'javascript:')): continue
            target = (site / unquote(parsed.path.lstrip('/'))) if parsed.path.startswith('/') else path.parent / unquote(parsed.path)
            if parsed.path and not target.exists(): errors.append(rel + ': missing local URL ' + url)
    for item in manifest['redirects']:
        path = site / item['path']
        if not path.is_file() or 'url=%s' % item['target'] not in read(path): errors.append('Missing/invalid redirect: ' + item['path'])
    for rel in manifest['static'] + ['CNAME', '.nojekyll', 'robots.txt', 'sitemap.xml', 'manifest.webmanifest', 'sw.js', 'assets/analytics.js', 'assets/privacy.js', 'assets/og-cover.png']:
        if not (site / rel).is_file(): errors.append('Missing required file: ' + rel)
    try:
        sw = read(site / 'sw.js')
        if "url.search" not in sw or "!ALLOWED.has(url.pathname)" not in sw or "response.headers.has('set-cookie')" not in sw: errors.append('Unsafe SW cache gate')
        if './sw.js' in sw or './rates.json' in sw: errors.append('SW self/json precache is forbidden')
    except OSError: pass
    return sorted(set(errors))

def validate_records(result, manifest, baseline=None):
    errors = []
    if not isinstance(result, dict) or result.get('complete') is not True: return ['Chrome harness completion record is missing']
    records = result.get('pages', [])
    if not isinstance(records, list): return ['Chrome harness records are not a list']
    expected = {p['path'] for p in manifest['pages']}
    observed = [r.get('page') for r in records if isinstance(r, dict)]
    if len(observed) != len(records) or len(set(observed)) != len(observed): errors.append('Invalid/duplicate page records')
    if set(observed) != expected: errors.append('Missing/unexpected browser records: ' + str(sorted(expected-set(observed))))
    errors.extend(result.get('errors', []))
    for record in records:
        if not isinstance(record, dict): continue
        page = record.get('page', '<missing>')
        if record.get('errors'): errors.append(page + ': JS errors ' + str(record['errors']))
        if record.get('rendered') is not True: errors.append(page + ': page did not render')
        if record.get('interactive') is not True: errors.append(page + ': theme toggle failed')
        if baseline:
            base = next((r for r in baseline if r.get('page') == page), None)
            if base and base.get('result_found') and not record.get('result_found'): errors.append(page + ': baseline result lost')
    return errors

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def run_browser(site, sources, chrome=CHROME, node=None, result_path=None, baseline=None):
    node = node or os.environ.get('NODE') or shutil.which('node')
    if not node:
        bundled = Path.home() / '.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/node/bin/node.exe'
        if bundled.is_file(): node = str(bundled)
    if not node or not Path(chrome).is_file(): raise ValueError('Node/Chrome unavailable: pass --node and --chrome')
    manifest = json.loads(read(Path(sources) / 'manifest.json'))
    handler = functools.partial(QuietHandler, directory=str(Path(site).resolve()))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='raschet-test-') as work:
            output = Path(work) / 'records.json'
            pages = Path(work) / 'pages.json'
            pages.write_text(json.dumps([p['path'] for p in manifest['pages']]), encoding='utf-8')
            completed = subprocess.run([str(node), str(REPO / 'tests/build_harness.js'), '--url', 'http://127.0.0.1:%d/' % server.server_port, '--pages', str(pages), '--result', str(output), '--chrome', str(chrome)], timeout=600)
            if not output.is_file(): raise ValueError('Chrome produced no records (exit %s)' % completed.returncode)
            result = json.loads(read(output))
            if result_path: Path(result_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            errors = validate_records(result, manifest, baseline)
            if completed.returncode: errors.append('Chrome harness exit: %d' % completed.returncode)
            return result, errors
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

def main():
    parser = site_parser(__doc__)
    parser.add_argument('--sources', type=Path, default=SOURCES)
    parser.add_argument('--chrome', type=Path, default=CHROME)
    parser.add_argument('--node')
    parser.add_argument('--result', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--static-only', action='store_true')
    args = parser.parse_args()
    errors = static_checks(args.site, args.sources)
    if not errors and not args.static_only:
        baseline = json.loads(read(args.baseline)) if args.baseline else None
        if isinstance(baseline, dict): baseline = baseline.get('pages', [])
        try:
            result, browser_errors = run_browser(args.site, args.sources, args.chrome, args.node, args.result, baseline)
            errors += browser_errors
            print('Browser records:', len(result.get('pages', [])))
        except Exception as exc: errors.append('Browser harness failed: ' + str(exc))
    for error in errors: print('FAIL:', error)
    print('SITE GATE:', 'FAIL' if errors else 'PASS')
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
