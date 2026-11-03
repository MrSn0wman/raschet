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
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from site_common import BASE_URL, PARTS, REPO, SOURCES, VERIFICATION_RE, html_files, read, site_parser
from integrate_rsya import BLOCK_INLINE, sensitive_routes

CHROME = Path(os.environ.get('CHROME', r'C:\Program Files\Google\Chrome\Application\chrome.exe'))

class _HTMLNode:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.duplicate_attrs = {name for name, count in Counter(key for key, value in attrs).items() if count > 1}
        self.children = []

    def has_class(self, name):
        return name in (self.attrs.get('class') or '').split()


class _AdHTMLParser(HTMLParser):
    """Small static DOM: script data is opaque; comments/formatting are not content."""
    VOID = frozenset('area base br col embed hr img input link meta param source track wbr'.split())

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _HTMLNode('#document')
        self.stack, self.nodes, self.errors = [self.root], [], []

    def handle_starttag(self, tag, attrs):
        node = _HTMLNode(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        # Browsers keep the first duplicate attribute; dict(attrs) keeps the last.
        # Reject ambiguity instead of letting inactive scripts or duplicate IDs pass.
        for name in node.duplicate_attrs:
            self.errors.append('duplicate ' + name + ' attribute')
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                # Broken div/script nesting must not manufacture a valid ad placement.
                if any(node.tag in ('div', 'script') for node in self.stack[index + 1:]):
                    self.errors.append('unclosed div/script before </' + tag + '>')
                del self.stack[index:]
                return
        if tag in ('div', 'script'):
            self.errors.append('unmatched </' + tag + '>')

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].children.append(data)

    def close(self):
        super().close()
        if any(node.tag in ('div', 'script') for node in self.stack[1:]):
            self.errors.append('unclosed div/script at EOF')


def _descendants(node):
    for child in node.children:
        if isinstance(child, _HTMLNode):
            yield child
            yield from _descendants(child)


def _inactive(node):
    while node is not None:
        if node.tag in ('template', 'noscript'):
            return True
        node = node.parent
    return False


# Accept the generated callback contract, not arbitrary executable JavaScript.
_RENDER_SCRIPT = re.compile(
    r'\s*window\s*\.\s*yaContextCb\s*\.\s*push\s*\(\s*\(\s*\)\s*=>\s*\{\s*'
    r'Ya\s*\.\s*Context\s*\.\s*AdvManager\s*\.\s*render\s*\(\s*(\{[^{}]*\})\s*\)\s*;?\s*'
    r'\}\s*\)\s*;?\s*', re.S)
_AD_SCRIPT = re.compile(r'yaContextCb|Ya\s*\.\s*Context\s*\.\s*AdvManager\s*\.\s*render|/ads/system/context\.js')
_RENDER_TO = re.compile(r'''(?:["']renderTo["']|\brenderTo)\s*:\s*(["'])([^"']+)\1''')


def _render_config(node):
    if (node.tag != 'script' or 'src' in node.attrs or 'language' in node.attrs or
            node.duplicate_attrs or 'nomodule' in node.attrs or
            (node.attrs.get('type') or '').lower() not in ('', 'text/javascript', 'application/javascript')):
        return None
    match = _RENDER_SCRIPT.fullmatch(''.join(child for child in node.children if isinstance(child, str)))
    if not match:
        return None
    try:
        pairs = json.loads(match.group(1), object_pairs_hook=list)
    except ValueError:
        return None
    if len(pairs) != 2 or {key for key, value in pairs} != {'blockId', 'renderTo'}:
        return None
    return dict(pairs)


def ad_coverage_checks(site, manifest, parts=PARTS):
    """All manifest tools need bottom inline RTB; configured private routes need none.

    Read-only and shared by static_checks, build_all --test and local publish sync.
    Sidebar ads remain allowed, but cannot satisfy the bottom inline requirement.
    """
    errors = []
    try:
        private = sensitive_routes(parts)
    except (OSError, ValueError, TypeError) as exc:
        return ['Ad coverage: invalid privacy configuration: ' + str(exc)]
    for page in manifest['pages']:
        rel = page['path']
        is_private = rel.split('/')[0] in private
        if not page['calculator'] and not is_private:
            continue
        path = Path(site) / rel
        if not path.is_file():
            errors.append(rel + ': ad coverage missing page')
            continue
        dom = _AdHTMLParser()
        try:
            dom.feed(read(path))
            dom.close()
        except (OSError, ValueError) as exc:
            errors.append(rel + ': ad coverage HTML parse failed: ' + str(exc))
            continue
        errors.extend(rel + ': ad coverage ' + error for error in dom.errors)
        ids = Counter(node.attrs['id'] for node in dom.nodes if node.attrs.get('id'))
        for value, count in ids.items():
            if count > 1:
                errors.append(rel + ': ad coverage duplicate DOM id ' + value)
        slots = [node for node in dom.nodes if node.has_class('ad-slot') or any(
            cls.startswith('ad-slot--') for cls in (node.attrs.get('class') or '').split())]
        rtb = [node for node in dom.nodes if (node.attrs.get('id') or '').startswith('yandex_rtb_')]
        scripts = [node for node in dom.nodes if node.tag == 'script']
        ad_scripts = [node for node in scripts if _AD_SCRIPT.search(
            ''.join(child for child in node.children if isinstance(child, str))) or
            '/ads/system/context.js' in (node.attrs.get('src') or '').lower()]
        if is_private:
            ad_attrs = any(_AD_SCRIPT.search(value or '') or '/ads/system/context.js' in (value or '').lower()
                           for node in dom.nodes for value in node.attrs.values())
            if slots or rtb or ad_scripts or ad_attrs:
                errors.append(rel + ': ad coverage sensitive route contains slot/loader/render')
            continue
        inline = [node for node in slots if node.has_class('ad-slot--inline')]
        if len(inline) != 1:
            errors.append(rel + ': ad coverage expected exactly one inline slot, got ' + str(len(inline)))
            continue
        slot = inline[0]
        card = slot.parent
        if (slot.tag != 'div' or not slot.has_class('ad-slot') or card.tag != 'div' or
                not card.has_class('calc-card') or _inactive(slot)):
            errors.append(rel + ': ad coverage inline slot must be a direct child div of calc-card')
            continue
        following = card.children[card.children.index(slot) + 1:]
        render = _render_config(following[0]) if len(following) == 1 and isinstance(following[0], _HTMLNode) else None
        if render is None:
            errors.append(rel + ': ad coverage inline slot must be last content with only its render script after')
        targets = [node for node in _descendants(slot) if (node.attrs.get('id') or '').startswith('yandex_rtb_')
                   and not _inactive(node)]
        if len(targets) != 1 or targets[0].tag != 'div':
            errors.append(rel + ': ad coverage inline slot needs exactly one RTB container div')
            continue
        target = targets[0].attrs['id']
        if render != {'blockId': BLOCK_INLINE, 'renderTo': target}:
            errors.append(rel + ': ad coverage inline renderTo/blockId mismatch')
        # Count targets even in a duplicate non-canonical callback elsewhere.
        matching = sum(match.group(2) == target for node in scripts for match in _RENDER_TO.finditer(
            ''.join(child for child in node.children if isinstance(child, str))))
        if matching != 1:
            errors.append(rel + ': ad coverage inline RTB container needs exactly one render call')
    return sorted(set(errors))


def static_checks(site, sources=SOURCES):
    site, sources = Path(site), Path(sources)
    errors = []
    try: manifest = json.loads(read(sources / 'manifest.json'))
    except Exception as exc: return ['Missing/invalid source manifest: ' + str(exc)]
    errors.extend(ad_coverage_checks(site, manifest))
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
