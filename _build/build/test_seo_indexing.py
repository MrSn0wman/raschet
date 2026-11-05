"""Noindex contract for legacy redirects; expectations captured from root HTML."""

import importlib.util
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://raschet.net/"
# Snapshot of the 60 existing redirect destinations, independent of SLUG_MAP.
REDIRECTS = {
    "calc-age.html": "vozrast",
    "calc-amount-in-words.html": "summa-propisyu",
    "calc-area.html": "ploshad",
    "calc-art395.html": "procenty-395-gk",
    "calc-bmi.html": "imt",
    "calc-car-loan.html": "avtokredit",
    "calc-compare-lists.html": "sravnenie-spiskov",
    "calc-compound-interest.html": "slozhnyy-procent",
    "calc-credit.html": "kredit",
    "calc-customs-clearance.html": "rastamozhka",
    "calc-days.html": "dni",
    "calc-deposit.html": "vklad",
    "calc-discount.html": "skidki",
    "calc-ev-charging.html": "zaryadka-elektromobilya",
    "calc-factorization.html": "razlozhenie-na-mnozhiteli",
    "calc-fractions.html": "drobi",
    "calc-fuel.html": "rashod-topliva",
    "calc-gcd.html": "nod",
    "calc-iis.html": "iis",
    "calc-insurance-contributions.html": "strahovye-vznosy-ip",
    "calc-lcm.html": "nok",
    "calc-loan-interest.html": "procenty-po-zaimu",
    "calc-maternal-capital-shares.html": "doli-po-materinskomu-kapitalu",
    "calc-maternity-leave.html": "dekretnye",
    "calc-microloan.html": "mikrozaim",
    "calc-mortgage-early.html": "dosrochnoe-pogashenie",
    "calc-mortgage.html": "ipoteka",
    "calc-ndfl.html": "ndfl",
    "calc-number-base.html": "sistemy-schisleniya",
    "calc-osago.html": "osago",
    "calc-password-generator.html": "generator-paroley",
    "calc-penalty-contract.html": "neustoika-po-dogovoru",
    "calc-penalty-ddu.html": "neustoika-po-ddu",
    "calc-penalty-tax.html": "peni-po-nalogam",
    "calc-pension.html": "pensiya",
    "calc-percent.html": "procenty",
    "calc-power.html": "stepeni",
    "calc-promo-generator.html": "generator-promokodov",
    "calc-property-sale-tax.html": "nalog-s-prodazhi-kvartiry",
    "calc-qr-generator.html": "qr-generator",
    "calc-random-number.html": "sluchaynye-chisla",
    "calc-random-pick.html": "sluchaynyy-vybor",
    "calc-recycling-fee.html": "utilsbor",
    "calc-refinancing.html": "refinansirovanie",
    "calc-samozanyaty.html": "nalog-samozanyatyh",
    "calc-shares-apartment.html": "doli-v-kvartire",
    "calc-shuffle-list.html": "peremeshat-spisok",
    "calc-sick-leave.html": "bolnichnyy",
    "calc-split-groups.html": "razdelit-na-gruppy",
    "calc-tax-deduction.html": "nalogovyy-vychet-kvartira",
    "calc-timezone.html": "chasovye-poyasa",
    "calc-tip.html": "chaevye",
    "calc-transport-tax.html": "transportnyy-nalog",
    "calc-unit-converter.html": "konverter-edinic",
    "calc-vacation-days.html": "otpusknye-dni",
    "calc-vacation-pay.html": "otpusknye",
    "calc-vat.html": "nds",
    "calc-volume.html": "obem",
    "calc-weight.html": "idealnyy-ves",
    "calc-work-experience.html": "trudovoy-stazh",
}
# The other 13 working tool directories observed in the current root tree.
TOOL_SLUGS = set(REDIRECTS.values()) | set("""
konverter-valyut schetchik-slov transliteraciya udalenie-dubley-strok
proverka-inn proverka-snils proverka-nomera-karty uuid-generator lorem-ipsum
generator-nikneimov unix-vremya rabochie-dni obratnyy-otschet
""".split())


class SEOHTML(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.in_head = False
        self.robots = []
        self.refresh = []
        self.canonicals = []
        self.links = []
        self.anchor = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "head":
            self.in_head = True
        elif tag == "meta":
            if (attrs.get("name") or "").lower() == "robots":
                self.robots.append((attrs.get("content"), self.in_head))
            if (attrs.get("http-equiv") or "").lower() == "refresh":
                self.refresh.append((attrs.get("content"), self.in_head))
        elif tag == "link" and "canonical" in (attrs.get("rel") or "").lower().split():
            self.canonicals.append((attrs.get("href"), self.in_head))
        elif tag == "a":
            self.anchor = [attrs.get("href"), "", self.in_head]

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
        elif tag == "a" and self.anchor is not None:
            self.links.append(tuple(self.anchor))
            self.anchor = None

    def handle_data(self, data):
        if self.anchor is not None:
            self.anchor[1] += data


class SEOIndexingTests(unittest.TestCase):
    def assert_redirects(self, directory):
        self.assertEqual({p.name for p in directory.glob("calc-*.html")}, set(REDIRECTS))
        for filename, slug in REDIRECTS.items():
            with self.subTest(file=filename):
                page = SEOHTML((directory / filename).read_text(encoding="utf-8"))
                relative = slug + "/"
                canonical = BASE_URL + relative
                self.assertEqual(page.refresh, [("0; url=" + relative, True)])
                self.assertEqual(page.canonicals, [(canonical, True)])
                self.assertEqual(page.links, [(relative, canonical, False)])
                self.assertEqual(len(page.robots), 1, "expected exactly one robots meta")
                content, in_head = page.robots[0]
                self.assertTrue(in_head, "robots meta must be inside the source head")
                self.assertCountEqual(
                    [token.strip().lower() for token in (content or "").split(",")],
                    ["noindex", "follow"],
                )

    def test_source_redirects(self):
        self.assert_redirects(ROOT)

    def test_generated_redirects(self):
        spec = importlib.util.spec_from_file_location(
            "seo_build_all", Path(__file__).with_name("build_all.py")
        )
        builder = importlib.util.module_from_spec(spec)
        # Import reads parts but must not leave bytecode in the source tree.
        with patch.object(sys, "dont_write_bytecode", True):
            spec.loader.exec_module(builder)
        with TemporaryDirectory() as out, patch.object(builder, "OUT", out):
            builder.build_redirects()
            self.assert_redirects(Path(out))

    def test_working_pages_remain_indexable(self):
        for slug in sorted(TOOL_SLUGS):
            with self.subTest(slug=slug):
                page = SEOHTML((ROOT / slug / "index.html").read_text(encoding="utf-8"))
                for content, _ in page.robots:
                    directives = {token.strip().lower() for token in (content or "").split(",")}
                    self.assertFalse(directives & {"noindex", "none"})


if __name__ == "__main__":
    unittest.main()
