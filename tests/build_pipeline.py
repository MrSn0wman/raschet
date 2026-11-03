# -*- coding: utf-8 -*-
"""Offline build safety, roundtrip, idempotence and strict-gate regression tests.

Run: python tests/build_pipeline.py (no old tree/network/browser dependency).
"""
import contextlib
import copy
import hashlib
import io
import json
import re
import sys
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '_build/build'))
import build_all
import extract_sources
import integrate_pwa
import integrate_rsya
import site_common
import test_site

class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(site_common.read(site_common.SOURCES / 'manifest.json'))
        cls.temp = tempfile.TemporaryDirectory(prefix='raschet-build-test-')
        cls.work = Path(cls.temp.name)
        cls.out = cls.work / 'out'
        with contextlib.redirect_stdout(io.StringIO()):
            build_all.build(cls.out)
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
    def hashes(self):
        return {p.relative_to(self.out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.out.rglob('*') if p.is_file()}
    def test_exact_inventory(self):
        site_common.validate_manifest(self.manifest)
        self.assertEqual(len(self.manifest['pages']), 79)
        self.assertEqual(len(self.manifest['redirects']), 60)
        self.assertEqual(len(self.manifest['static']), 2)
    def test_roundtrip_all_pages_without_duplicate_parts(self):
        for page in self.manifest['pages']:
            with self.subTest(page=page['path']):
                html = build_all.render_source(site_common.SOURCES, page)
                files = extract_sources.decompose(html, page['path'], site_common.PARTS)
                self.assertEqual(extract_sources.render_files(files, site_common.PARTS, page['path']), html)
                self.assertNotIn('Общая логика интерфейса', files['scripts.html'])
                self.assertNotIn('<footer class="site-footer">', files['body.html'])
                self.assertNotIn('@font-face', files['page.css'])
    def test_rebuild_is_identical(self):
        before = self.hashes()
        with contextlib.redirect_stdout(io.StringIO()): build_all.build(self.out)
        self.assertEqual(before, self.hashes())
    def test_postprocessors_idempotent(self):
        before = self.hashes()
        with contextlib.redirect_stdout(io.StringIO()):
            integrate_rsya.process(self.out)
            integrate_pwa.process(self.out)
        self.assertEqual(before, self.hashes())
    def test_hash_excludes_sw_and_json(self):
        expected = integrate_pwa.tree_hash(self.out)
        sw = self.out / 'sw.js'
        original = sw.read_bytes()
        sw.write_bytes(original + b'\n// irrelevant self mutation')
        sample = self.out / 'rates.json'
        existed = sample.exists()
        old_json = sample.read_bytes() if existed else None
        sample.write_text('{"test":123}', encoding='utf-8')
        try: self.assertEqual(expected, integrate_pwa.tree_hash(self.out))
        finally:
            sw.write_bytes(original)
            if existed: sample.write_bytes(old_json)
            else: sample.unlink()
    def test_hash_includes_binary_assets(self):
        expected = integrate_pwa.tree_hash(self.out)
        asset = self.out / 'assets/og-cover.png'
        original = asset.read_bytes()
        asset.write_bytes(original + b'0')
        try: self.assertNotEqual(expected, integrate_pwa.tree_hash(self.out))
        finally: asset.write_bytes(original)
    def test_worker_aliases_query_api_private_bypass(self):
        node = os.environ.get("NODE") or shutil.which("node") or str(Path.home() / ".dsh/dsh-runtimes/dsh-primary-runtime/dependencies/node/bin/node.exe")
        subprocess.run([node, str(ROOT / "tests/build_sw.js"), str(self.out)], check=True)
    def test_postprocessors_reject_root_before_writes(self):
        from fix_csp import process as csp
        from fix_seo_meta import process as seo
        from fix_titles import process as titles
        for process in (csp, seo, titles, integrate_pwa.process, integrate_rsya.process):
            with self.subTest(process=process.__module__), self.assertRaises(ValueError): process(ROOT)
    def test_root_pwa_excludes_internal_directories(self):
        for path in integrate_pwa.public_files(ROOT):
            self.assertFalse(any(part in ('_build','backend','tests','scripts','.git') for part in path.relative_to(ROOT).parts))
    def test_static_assets_and_verifications_preserved(self):
        for source in (ROOT / 'assets').rglob('*'):
            if source.is_file() and source.name != 'privacy.js':
                self.assertEqual(source.read_bytes(), (self.out / 'assets' / source.relative_to(ROOT / 'assets')).read_bytes())
        for rel in self.manifest['static'] + ['CNAME','.nojekyll','robots.txt','sitemap.xml']:
            self.assertEqual((ROOT / rel).read_bytes(), (self.out / rel).read_bytes())
    def test_ad_boundary_cleanup_preserves_meaningful_whitespace(self):
        protected = '<textarea>\n \t\nvalue  \n</textarea>\n<pre>\n \t\nkept  \n</pre>\n<style>\n \t\n.a{color:red}  \n</style>\n<script>const value = `\n \t\nkept  \n`;\n</script>\n'
        html = '\n   <div class="ad-slot ad-slot--inline"><div></div></div>\n   <script>window.yaContextCb=[];</script>\n' + protected
        cleaned = integrate_rsya.remove_ads(html)
        self.assertEqual(cleaned, "\n\n\n" + protected)
        self.assertEqual(integrate_rsya.remove_ads(cleaned), cleaned)
    def test_home_ad_placements(self):
        text = site_common.read(self.out / "index.html")
        prefix = "yandex_rtb_R-A-20316097-1"
        placements = (("labor", "auto"), ("math", "dates"), ("validators", "generators"))
        ids = re.findall(r'<div id="(yandex_rtb_[^"]+)">', text)
        self.assertEqual(ids, [prefix] + [prefix + "-" + before + "-" + after for before, after in placements])
        self.assertEqual(len(set(ids)), 4)
        self.assertEqual(text.count('class="ad-slot ad-slot--leader"'), 4)
        calls = re.findall(r'Ya\.Context\.AdvManager\.render\(\{\s*"blockId": "([^"]+)",\s*"renderTo": "([^"]+)"\s*\}\)', text)
        self.assertEqual(calls, [("R-A-20316097-1", target) for target in ids])
        self.assertEqual(text.count('<script src="https://yandex.ru/ads/system/context.js" async></script>'), 1)
        self.assertLess(text.index('<script src="assets/privacy.js"></script>'), text.index("context.js"))
        self.assertEqual(text.count('class="calc-item"'), 73)
        for before, after in placements:
            start = text.index('<section class="section" id="' + before + '">')
            end = text.index("</section>", start)
            next_section = text.index("<section", end)
            self.assertEqual(next_section, text.index('<section class="section" id="' + after + '">'))
            gap = text[end:next_section]
            self.assertIn('<div id="' + prefix + "-" + before + "-" + after + '"></div>', gap)
            self.assertEqual(gap.count('class="ad-slot ad-slot--leader"'), 1)
    def test_all_tool_ad_coverage(self):
        private = integrate_rsya.sensitive_routes()
        tools = [page for page in self.manifest['pages'] if page['calculator']]
        self.assertEqual(sum(page['path'].split('/')[0] not in private for page in tools), 59)
        self.assertEqual(sum(page['path'].split('/')[0] in private for page in tools), 14)
        self.assertEqual(test_site.ad_coverage_checks(self.out, self.manifest), [])
        self.assertEqual(test_site.static_checks(self.out), [])

    def test_sensitive_pages_have_no_ads_analytics_or_sharing(self):
        for route in integrate_rsya.sensitive_routes():
            text = site_common.read(self.out / route / 'index.html')
            for token in ('context.js','Ya.Context.AdvManager.render','window.yaContextCb','assets/analytics.js','data-share=','class="ad-slot '):
                self.assertNotIn(token, text, route)
    def test_refuses_unowned_and_protected_outputs(self):
        unowned = self.work / 'unowned'
        unowned.mkdir()
        witness = unowned / 'user.txt'
        witness.write_text('keep', encoding='utf-8')
        for output in (unowned, ROOT, ROOT.parent, site_common.SOURCES, site_common.PARTS, ROOT / 'backend'):
            with self.subTest(output=str(output)), self.assertRaises(ValueError): build_all.build(output)
        self.assertEqual(witness.read_text(), 'keep')
    def test_missing_source_preflight_preserves_owned_output(self):
        bad = self.work / 'bad-sources'
        bad.mkdir()
        (bad / 'manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        before = self.hashes()
        with self.assertRaises(OSError): build_all.build(self.out, sources=bad)
        self.assertEqual(before, self.hashes())
    def test_source_manifest_rejects_traversal_and_missing_pages(self):
        for mutation in ('missing','source','redirect','verification'):
            bad = copy.deepcopy(self.manifest)
            if mutation == 'missing': bad['pages'].pop()
            elif mutation == 'source': bad['pages'][0]['source'] = '../../private'
            elif mutation == 'redirect': bad['redirects'][0]['target'] = '//foreign.invalid/'
            else: bad['static'][0] = '../private.html'
            with self.assertRaises(ValueError): site_common.validate_manifest(bad)
    def test_extraction_refuses_root_output(self):
        with self.assertRaises(ValueError): extract_sources.extract(ROOT, ROOT, site_common.PARTS)
    def test_gate_missing_done_missing_duplicate_errors(self):
        records = [{'page':p['path'],'rendered':True,'interactive':True,'errors':[]} for p in self.manifest['pages']]
        self.assertEqual(test_site.validate_records({'complete':True,'pages':records}, self.manifest), [])
        cases = ({'pages':records}, {'complete':True,'pages':[]}, {'complete':True,'pages':records[:-1]}, {'complete':True,'pages':records+[records[0]]}, {'complete':True,'pages':[dict(records[0],errors=['injected'])]+records[1:]})
        for case in cases: self.assertTrue(test_site.validate_records(case, self.manifest))
    def test_gate_missing_page_is_failure(self):
        path = self.out / self.manifest['pages'][0]['path']
        original = path.read_bytes()
        path.unlink()
        try: self.assertTrue(test_site.static_checks(self.out))
        finally: path.write_bytes(original)

class AdCoverageTests(unittest.TestCase):
    """Offline DOM mutations: manifest/config determine routes, not a tool allowlist."""
    def setUp(self):
        self.manifest = json.loads(site_common.read(site_common.SOURCES / 'manifest.json'))
        private = integrate_rsya.sensitive_routes()
        self.public = [page['path'] for page in self.manifest['pages']
                       if page['calculator'] and page['path'].split('/')[0] not in private]
        self.private = [page['path'] for page in self.manifest['pages'] if page['path'].split('/')[0] in private]
        self.temp = tempfile.TemporaryDirectory(prefix='raschet-ad-gate-test-')
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        self.inline = integrate_rsya.slot_html('inline', integrate_rsya.BLOCK_INLINE)
        self.sidebar = integrate_rsya.slot_html('sidebar', integrate_rsya.BLOCK_SIDEBAR)
        self.good = self.document(self.inline)
        for page in self.manifest['pages']:
            path = self.site / page['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.good if page['path'] in self.public else self.document(), encoding='utf-8')
        self.assertEqual(self.errors(), [])  # Negatives must not pass on unrelated fixture failures.

    def document(self, inline='', after='', outside=''):
        return ('<!doctype html><html><head><script src="../assets/privacy.js"></script></head><body>'
                '<main><div class="calc-card"><h1>Fixture</h1><div id="result"><input><br></div>'
                + inline + after + '</div>' + outside + '</main><aside>'
                + (self.sidebar if inline else '') + '</aside></body></html>')

    def errors(self):
        return test_site.ad_coverage_checks(self.site, self.manifest)

    @contextlib.contextmanager
    def mutation(self, rel, text):
        path = self.site / rel
        original = path.read_bytes()
        path.write_text(text, encoding='utf-8')
        try:
            yield
        finally:
            path.write_bytes(original)

    def assert_rejected(self, rel, text, diagnostic):
        with self.mutation(rel, text):
            errors = self.errors()
            self.assertTrue(any(error.startswith(rel + ':') and diagnostic in error for error in errors), errors)
            # This is the same entry point used by build_all --test and publish sync.
            self.assertTrue(any('ad coverage' in error and error.startswith(rel + ':')
                                for error in test_site.static_checks(self.site)), diagnostic)

    def test_positive_manifest_coverage_and_read_only(self):
        before = {path: path.read_bytes() for path in self.site.rglob('*.html')}
        self.assertEqual(self.errors(), [])
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        # Class token order, attribute quotes/case, nested result divs, comments and whitespace.
        varied = self.good.replace('class="ad-slot ad-slot--inline"', "CLASS='extra ad-slot--inline ad-slot'")
        varied = varied.replace('</script></div>', '</script> \n<!-- Formatting comment -->\n</div>')
        varied += '\n<!-- <div class="ad-slot--inline">fake</div> -->'
        with self.mutation(self.public[0], varied):
            self.assertEqual(self.errors(), [])
        custom_target = self.good.replace('yandex_rtb_' + integrate_rsya.BLOCK_INLINE, 'yandex_rtb_custom-inline')
        with self.mutation(self.public[0], custom_target):
            self.assertEqual(self.errors(), [])

    def test_missing_inline_on_every_non_sensitive_tool(self):
        for rel in self.public:
            with self.subTest(page=rel):
                # Leave the valid sidebar: it must never substitute for the inline slot.
                self.assert_rejected(rel, self.good.replace(self.inline, ''), 'exactly one inline slot')

    def test_duplicate_inline_and_dom_ids(self):
        rel = self.public[0]
        cases = ((self.good.replace(self.inline, self.inline + self.inline), 'exactly one inline slot'),
                 (self.good.replace('id="result"', 'id="theme-toggle"') + '<div id="theme-toggle"></div>', 'duplicate DOM id'),
                 (self.good.replace('<aside>', '<aside><div id="yandex_rtb_' + integrate_rsya.BLOCK_INLINE + '"></div>'), 'duplicate DOM id'),
                 (self.good.replace('id="result"', 'id="result" id="other"'), 'duplicate id attribute'))
        for text, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                self.assert_rejected(rel, text, diagnostic)

    def test_misplaced_inline_and_trailing_content(self):
        rel = self.public[0]
        cases = ((self.good.replace(self.inline, '<section>' + self.inline + '</section>'), 'direct child'),
                 (self.document(outside=self.inline), 'direct child'),
                 (self.good.replace('<main>', '<main><template>').replace('</main>', '</template></main>'), 'direct child'),
                 (self.good.replace('<main>', '<main><noscript>').replace('</main>', '</noscript></main>'), 'direct child'),
                 (self.document(self.inline, after='<div>Late result</div>'), 'last content'),
                 (self.document(self.inline, after='<p>Late explanation</p>'), 'last content'),
                 (self.document(self.inline, after='Late text'), 'last content'),
                 (self.document(self.inline, after='<script>console.log(1)</script>'), 'last content'),
                 (self.good.replace('<div id="result">', '<div id="result"><div>'), 'unclosed div/script'))
        for text, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                self.assert_rejected(rel, text, diagnostic)

    def test_rtb_container_and_render_contract(self):
        rel = self.public[0]
        target = 'yandex_rtb_' + integrate_rsya.BLOCK_INLINE
        container = '<div id="' + target + '"></div>'
        render = integrate_rsya.RENDER % (integrate_rsya.BLOCK_INLINE, integrate_rsya.BLOCK_INLINE)
        cases = ((self.good.replace(container, ''), 'exactly one RTB container'),
                 (self.good.replace(container, '<template>' + container + '</template>'), 'exactly one RTB container'),
                 (self.good.replace(container, '<noscript>' + container + '</noscript>'), 'exactly one RTB container'),
                 (self.good.replace(container, container + '<div id="yandex_rtb_extra"></div>'), 'exactly one RTB container'),
                 (self.good.replace(render, ''), 'last content'),
                 (self.good.replace(render, render.replace('"renderTo": "' + target + '"', '"renderTo": "missing"')), 'renderTo/blockId mismatch'),
                 (self.good.replace(render, render.replace('"blockId": "' + integrate_rsya.BLOCK_INLINE + '"', '"blockId": "wrong"')), 'renderTo/blockId mismatch'),
                 (self.good + render, 'exactly one render call'),
                 (self.good + '<script>Ya.Context.AdvManager.render({renderTo: "' + target + '"});</script>', 'exactly one render call'),
                 (self.good.replace(render, render.replace('<script>', '<script type="application/json">')), 'render'),
                 (self.good.replace(render, render.replace('<script>', '<script nomodule>')), 'render'),
                 (self.good.replace(render, render.replace('<script>', '<script src="">')), 'render'),
                 (self.good.replace(render, render.replace('<script>', '<script language="vbscript">')), 'render'),
                 (self.good.replace(render, render.replace('<script>', '<script type="application/json" type="text/javascript">')), 'duplicate type attribute'),
                 (self.good.replace(render, render.replace('<script>', '<script src="fake.js" src="">')), 'duplicate src attribute'))
        for text, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                self.assert_rejected(rel, text, diagnostic)

    def test_sensitive_ads_blocked_even_without_complete_slot(self):
        fragments = (self.inline, self.sidebar, '<div class="ad-slot--inline"></div>',
                     '<div id="yandex_rtb_orphan"></div>', integrate_rsya.LOADER,
                     '<script src="https://yandex.ru/ads/system/context.js" async></script>',
                     '<script>window.yaContextCb=[];</script>',
                     '<script>Ya . Context . AdvManager . render({});</script>',
                     '<script>const ad = document.createElement("script"); ad.src = "https://yandex.ru/ads/system/context.js"; document.head.append(ad);</script>',
                     '<button onclick="Ya.Context.AdvManager.render({})">Blocked</button>',
                     '<a href="javascript:window.yaContextCb.push(() => {})">Blocked</a>')
        for rel in self.private:  # Includes all 14 private tools and configured non-tool routes.
            for fragment in fragments:
                with self.subTest(page=rel, fragment=fragment):
                    self.assert_rejected(rel, self.document(outside=fragment), 'sensitive route contains')

    def test_missing_manifest_page_and_privacy_configuration_fail_closed(self):
        path = self.site / self.public[-1]
        original = path.read_bytes()
        path.unlink()
        try:
            self.assertTrue(any('ad coverage missing page' in error for error in self.errors()))
        finally:
            path.write_bytes(original)
        errors = test_site.ad_coverage_checks(self.site, self.manifest, parts=self.site / 'missing-config')
        self.assertTrue(any('invalid privacy configuration' in error for error in errors), errors)


if __name__ == '__main__':
    unittest.main(verbosity=2)
