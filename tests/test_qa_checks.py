"""qa_checks.py, seed_glossary.py ve prepare_source.py için sınamalar.

Çalıştırma: python -m unittest discover -s tests -v
Sınama verisi tests/fixtures altındadır ve sentetiktir.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import qa_checks  # noqa: E402
import seed_glossary  # noqa: E402
from trtext import extract_numbers, find_term, split_sentences, tr_lower, tr_upper  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
DOMAIN = ROOT / "domains" / "toprak-bilimi"


def run_qa(source: Path, target: Path, direction: str, glossary: dict | None = None, params: dict | None = None):
    with tempfile.TemporaryDirectory() as tmp:
        g = None
        if glossary is not None:
            g = Path(tmp) / "g.json"
            g.write_text(json.dumps(glossary, ensure_ascii=False), encoding="utf-8")
        p = None
        if params is not None:
            p = Path(tmp) / "p.json"
            p.write_text(json.dumps(params), encoding="utf-8")
        args = argparse.Namespace(source=source, target=target, direction=direction, glossary=g, params=p, only=None)
        return qa_checks.run(args)


def messages(report, check: str | None = None) -> list[str]:
    return [f["message"] for f in report.findings if check is None or f["check"] == check]


class TestTrText(unittest.TestCase):
    def test_turkish_case(self):
        self.assertEqual(tr_upper("giriş"), "GİRİŞ")
        self.assertEqual(tr_lower("IŞIK İLE"), "ışık ile")

    def test_inflected_terms(self):
        text = "Hacim ağırlıkları ve hacim ağırlığının değişimi; kireç içeriğinin etkisi; toprağın yapısı."
        self.assertEqual(len(find_term(text, "hacim ağırlığı", "tr")), 2)
        self.assertEqual(len(find_term(text, "kireç içeriği", "tr")), 1)
        self.assertEqual(len(find_term(text, "toprak", "tr")), 1)

    def test_short_word_not_overmatched(self):
        self.assertEqual(find_term("kilometre boyunca", "kil", "tr"), [])
        self.assertEqual(len(find_term("killi ve kilin oranı", "kil", "tr")), 2)

    def test_english_plural(self):
        self.assertEqual(len(find_term("Bulk densities and cation exchange capacities", "bulk density", "en")), 1)
        self.assertEqual(len(find_term("Bulk densities and cation exchange capacities", "cation exchange capacity", "en")), 1)

    def test_numbers_decimal_conversion(self):
        en = [v for v, _ in extract_numbers("p < 0.05, n = 1,234, -0.12, 0.50", ".")]
        tr = [v for v, _ in extract_numbers("p < 0,05, n = 1.234, -0,12, 0,50", ",")]
        self.assertEqual(en, tr)
        self.assertEqual(en, ["0.05", "1234", "-0.12", "0.50"])

    def test_trailing_zero_is_a_difference(self):
        self.assertNotEqual(extract_numbers("0.50", "."), extract_numbers("0,5", ","))

    def test_unit_exponent_is_not_negative(self):
        self.assertEqual([v for v, _ in extract_numbers("1.35 g cm-3", ".")], ["1.35", "3"])

    def test_sentence_split_keeps_abbreviations(self):
        s = split_sentences("Smith et al. (2019) found 0.5 g. Kılıç ve ark. (2020) bunu gösterdi.")
        self.assertEqual(len(s), 2)


class TestSeedGlossary(unittest.TestCase):
    def test_en_tr_seed(self):
        g = seed_glossary.seed((FIX / "en_source.md").read_text(encoding="utf-8"), "en-tr", [DOMAIN])
        pairs = {t["original"]: t["translation"] for t in g["terms"]}
        self.assertEqual(pairs["bulk density"], "hacim ağırlığı")
        self.assertEqual(pairs["calcium carbonate content"], "kireç içeriği")
        self.assertEqual(pairs["available phosphorus"], "alınabilir fosfor")
        self.assertEqual(pairs["random forest"], "rastgele orman")
        # "environmental covariates" içindeki "covariate" öneri satırını tetiklememeli
        self.assertNotIn("covariate", pairs)
        # Kaynakta yalnız kısaltma geçen terim kısaltma olarak korunur
        self.assertEqual(pairs["R2"], "R2")

    def test_tr_en_seed(self):
        g = seed_glossary.seed((FIX / "tr_target_good.md").read_text(encoding="utf-8"), "tr-en", [DOMAIN])
        pairs = {t["original"]: t["translation"] for t in g["terms"]}
        self.assertEqual(pairs["hacim ağırlığı"], "bulk density")
        self.assertEqual(pairs["kireç içeriği"], "calcium carbonate content")
        forb = {t["original"]: t["forbidden"] for t in g["terms"]}
        self.assertIn("lime content", forb["kireç içeriği"])
        self.assertIn("deterioration", g["metadata"]["global_forbidden"])


class TestQAGood(unittest.TestCase):
    def test_good_en_tr_has_no_findings(self):
        g = seed_glossary.seed((FIX / "en_source.md").read_text(encoding="utf-8"), "en-tr", [DOMAIN])
        r = run_qa(FIX / "en_source.md", FIX / "tr_target_good.md", "en-tr", g)
        self.assertEqual(r.findings, [], messages(r))

    def test_good_tr_en_has_no_findings(self):
        g = seed_glossary.seed((FIX / "tr_target_good.md").read_text(encoding="utf-8"), "tr-en", [DOMAIN])
        r = run_qa(FIX / "tr_target_good.md", FIX / "en_source.md", "tr-en", g)
        self.assertEqual(r.findings, [], messages(r))


class TestQABad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        g = seed_glossary.seed((FIX / "en_source.md").read_text(encoding="utf-8"), "en-tr", [DOMAIN])
        cls.r = run_qa(FIX / "en_source.md", FIX / "tr_target_bad.md", "en-tr", g)
        cls.all = " || ".join(messages(cls.r))

    def test_changed_number(self):
        self.assertIn("0.42 değeri çeviride", self.all)
        self.assertIn("0.24 değeri", self.all)

    def test_decimal_point_left_in_turkish(self):
        self.assertIn("ondalık nokta", self.all)

    def test_dropped_citation(self):
        self.assertIn("brown 2020a", self.all)

    def test_missing_table_row(self):
        self.assertIn("Çizelge 1: kaynak 3 satır x 3 sütun, çeviri 2 satır x 3 sütun", self.all)

    def test_wrong_term(self):
        self.assertIn("'bulk density' -> 'hacim ağırlığı'", self.all)

    def test_typography(self):
        self.assertIn("en dash", self.all)
        self.assertIn("'et al.' kalmış", self.all)
        self.assertIn("yüzde işareti sayıdan sonra", self.all)
        self.assertIn("GIRIŞ", self.all)
        self.assertIn("Çizelge etiketi", self.all)

    def test_long_sentence(self):
        self.assertTrue(any(f["type"] == "READABILITY" for f in self.r.findings))

    def test_claim_strength_is_not_detectable_by_rules(self):
        # "düşündürmektedir" -> "göstermektedir" (savın kesinliği artırılmış).
        # Kural tabanlı denetim bunu yakalamaz; denetçi ajanın MEANING_SHIFT denetimi gerekir.
        self.assertNotIn("göstermektedir", self.all)


class TestSectionNumbers(unittest.TestCase):
    def test_section_numbers_are_not_decimals(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp) / "s.md"
            t = Path(tmp) / "t.md"
            s.write_text("## 2.1 Study area\n\nAs described in Section 2.1, pH was 7.85 (see Section 3.2.1).\n", encoding="utf-8")
            t.write_text("## 2.1 Çalışma alanı\n\n2.1. bölümde anlatıldığı gibi pH 7,85 olmuştur (bkz. Bölüm 3.2.1).\n", encoding="utf-8")
            r = run_qa(s, t, "en-tr")
            bad = [f["message"] for f in r.findings if f["check"] in {"numbers", "typography"}]
            self.assertEqual(bad, [])

    def test_real_decimal_still_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp) / "s.md"
            t = Path(tmp) / "t.md"
            s.write_text("## 2.1 Study area\n\npH was 7.85.\n", encoding="utf-8")
            t.write_text("## 2.1 Çalışma alanı\n\npH 7.85 olmuştur.\n", encoding="utf-8")
            r = run_qa(s, t, "en-tr")
            self.assertTrue(any(f["check"] == "numbers" for f in r.findings))
            self.assertTrue(any("ondalık nokta" in f["message"] for f in r.findings))


class TestMarkers(unittest.TestCase):
    def test_unresolved_markers_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "t.md"
            text = (FIX / "tr_target_good.md").read_text(encoding="utf-8")
            text = text.replace("10 katman", "10 kat [?terim: folds?]").replace("R2 = 0,61", "R2 [?tanımsız kısaltma: R2?] = 0,61")
            t.write_text(text, encoding="utf-8")
            r = run_qa(FIX / "en_source.md", t, "en-tr")
            marks = [f for f in r.findings if f["message"] == "Çözülmemiş çevirmen işareti"]
            self.assertEqual(len(marks), 2)


class TestReferencesAndForbidden(unittest.TestCase):
    def test_reference_list_change_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "t.md"
            text = (FIX / "tr_target_good.md").read_text(encoding="utf-8").replace("Synthetic reference two", "Sentetik kaynak iki")
            t.write_text(text, encoding="utf-8")
            r = run_qa(FIX / "en_source.md", t, "en-tr")
            self.assertTrue(any("Kaynakça çevrilmeyecekti" in m for m in messages(r, "references")))

    def test_forbidden_english_terms(self):
        g = seed_glossary.seed((FIX / "tr_target_good.md").read_text(encoding="utf-8"), "tr-en", [DOMAIN])
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp) / "t.md"
            text = (FIX / "en_source.md").read_text(encoding="utf-8")
            text = text.replace("calcium carbonate content may control", "lime content may control")
            text = text.replace("Digital soil mapping uses", "Land deterioration and digital soil mapping use")
            t.write_text(text, encoding="utf-8")
            r = run_qa(FIX / "tr_target_good.md", t, "tr-en", g)
            joined = " || ".join(messages(r, "glossary"))
            self.assertIn("'lime content'", joined)
            self.assertIn("'deterioration'", joined)

    def test_variant_mixing(self):
        g = {"terms": [], "metadata": {"consistency_groups": json.loads((DOMAIN / "baglayici.json").read_text(encoding="utf-8"))["consistency_groups"]}}
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp) / "s.md"
            t = Path(tmp) / "t.md"
            s.write_text("Soil texture and kriging.\n", encoding="utf-8")
            t.write_text("Toprak tekstürü ve bünye; kriging ve krigleme.\n", encoding="utf-8")
            r = run_qa(s, t, "en-tr", g)
            mixing = [m for m in messages(r, "glossary") if "iki biçimi" in m]
            self.assertEqual(len(mixing), 2)


@unittest.skipUnless(shutil.which("pandoc"), "pandoc yok")
class TestPrepareRoundTrip(unittest.TestCase):
    def test_docx_roundtrip_keeps_numbers_citations_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            docx = Path(tmp) / "kaynak.docx"
            subprocess.run(["pandoc", str(FIX / "en_source.md"), "-o", str(docx)], check=True)
            subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "prepare_source.py"), "prepare", str(docx), "--direction", "en-tr"],
                           check=True, capture_output=True)
            src_md = Path(tmp) / "ceviri-kaynak" / "source.md"
            self.assertTrue(src_md.exists())
            r = run_qa(FIX / "en_source.md", src_md, "en-tr", params={"target_decimal": ".", "target_percent": "suffix"})
            bad = [f for f in r.findings if f["check"] in {"numbers", "citations", "structure"}]
            self.assertEqual(bad, [], [f["message"] for f in bad])

    def test_chunk_and_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "prepare_source.py"), "prepare", str(FIX / "en_source.md"),
                            "--direction", "en-tr", "--workspace", str(ws), "--chunk-words", "40"], check=True, capture_output=True)
            chunks = sorted((ws / "chunks").glob("chunk-*.md"))
            self.assertGreater(len(chunks), 1)
            for c in chunks:
                self.assertFalse(c.read_text(encoding="utf-8").rstrip().splitlines()[-1].startswith("#"), f"{c.name} başlıkla bitiyor")
                (ws / f"first-pass-{c.name}").write_text(c.read_text(encoding="utf-8"), encoding="utf-8")
            subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "prepare_source.py"), "merge", str(ws)], check=True, capture_output=True)
            r = run_qa(FIX / "en_source.md", ws / "first-pass.md", "en-tr", params={"target_decimal": ".", "target_percent": "suffix"})
            bad = [f for f in r.findings if f["check"] in {"numbers", "citations", "structure", "references"}]
            self.assertEqual(bad, [], [f["message"] for f in bad])


if __name__ == "__main__":
    unittest.main()
