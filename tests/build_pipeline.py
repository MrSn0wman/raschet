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

if __name__ == '__main__':
    unittest.main(verbosity=2)
