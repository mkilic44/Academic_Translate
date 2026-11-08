"""qa_checks.py, seed_glossary.py ve prepare_source.py için sınamalar.

Çalıştırma: python -m unittest discover -s tests -v
Sınama verisi tests/fixtures altındadır ve sentetiktir.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import merge_glossaries  # noqa: E402
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

    def test_unit_with_plus_sign(self):
        self.assertEqual(len(find_term("ranged to 38.9 cmol(+) kg-1.", "cmol(+) kg-1", "en")), 1)

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

    def test_dotted_versions_match_across_decimal_conventions(self):
        tr = [v for v, _ in extract_numbers("MOD13Q1 6.1 sürümü, eklenti 2.3.0; alan 6912,8 km²", ",")]
        en = [v for v, _ in extract_numbers("MOD13Q1 version 6.1, plugin 2.3.0; area 6912.8 km²", ".")]
        self.assertEqual(sorted(tr), sorted(en))

    def test_percent_range_is_not_negative(self):
        self.assertEqual([v for v, _ in extract_numbers("%62,6-%85,7", ",")], ["62.6", "85.7"])
        self.assertEqual([v for v, _ in extract_numbers("62.6%-85.7%", ".")], ["62.6", "85.7"])

    def test_unit_exponent_is_not_negative(self):
        self.assertEqual([v for v, _ in extract_numbers("1.35 g cm-3", ".")], ["1.35", "3"])

    def test_plural_word_end_is_sentence_end(self):
        s = split_sentences("The window lasted 30 days. The model was refitted. See s. 12 for details.")
        self.assertEqual(len(s), 3)

    def test_caption_panel_labels_start_sentences(self):
        s = split_sentences("Figure 2. Spatial design. (a, b) Fold maps for 2009. (c) Distances. (d) Counts.")
        self.assertEqual(len(s), 5)

    def test_english_page_abbreviation_is_not_sentence_end(self):
        s = split_sentences("The data were checked. See p. 4 and pp. 7-9 for details. It ended up.")
        self.assertEqual(len(s), 3)

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


class TestMergeGlossaries(unittest.TestCase):
    def test_binding_wins_and_conflict_recorded(self):
        seed = seed_glossary.seed((FIX / "en_source.md").read_text(encoding="utf-8"), "en-tr", [DOMAIN])
        research = {"metadata": {"web_search_failures": 2}, "terms": [
            {"original": "bulk density", "translation": "yığın yoğunluğu", "status": "araştırıldı", "confidence": "medium", "origin": "research"},
            {"original": "catchment", "translation": "havza", "status": "araştırıldı", "confidence": "medium", "origin": "research"},
            # Araştırmacı tohum girdisini güncellerken origin alanını olduğu gibi bırakabilir.
            {"original": "prediction", "translation": "tahmin", "status": "değişken", "confidence": "medium",
             "origin": "domain:toprak-bilimi/oneriler:A-035"},
        ]}
        m = merge_glossaries.merge([seed, research])
        pairs = {t["original"]: t["translation"] for t in m["terms"]}
        self.assertEqual(pairs["bulk density"], "hacim ağırlığı")
        self.assertEqual(pairs["catchment"], "havza")
        self.assertEqual(pairs["prediction"], "tahmin")
        self.assertEqual([c["original"] for c in m["metadata"]["conflicts"]], ["bulk density"])
        self.assertEqual(m["metadata"]["web_search_failures"], 2)
        self.assertEqual(m["metadata"]["total_terms"], len(m["terms"]))


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


class TestTrEnFeatures(unittest.TestCase):
    def _run(self, src_text, tgt_text, params):
        with tempfile.TemporaryDirectory() as tmp:
            s = Path(tmp) / "s.md"
            t = Path(tmp) / "t.md"
            s.write_text(src_text, encoding="utf-8")
            t.write_text(tgt_text, encoding="utf-8")
            return run_qa(s, t, "tr-en", params=params)

    def test_citation_alias_for_institutional_author(self):
        src = "Üretim azalmıştır (Türkiye İstatistik Kurumu, 2026).\n"
        tgt = "Production decreased (Turkish Statistical Institute, 2026).\n"
        r = self._run(src, tgt, {"source_decimal": ".", "citation_aliases": {"Türkiye İstatistik Kurumu": "Turkish Statistical Institute"}})
        self.assertEqual([f for f in r.findings if f["check"] == "citations"], [])

    def test_reference_connectors_mode(self):
        src = "Metin (Kaya ve ark., 2018).\n\n## Kaynaklar\n\nKaya, Ö., Köse, C. ve Geçim, T. (2018). An exothermic process. Sci. Hortic.\n\nMeteostat. (t.y.). Data [Veri kümesi]. Erişim: 13 Ekim 2026.\n"
        good = "Text (Kaya et al., 2018).\n\n## References\n\nKaya, Ö., Köse, C., & Geçim, T. (2018). An exothermic process. Sci. Hortic.\n\nMeteostat. (n.d.). Data [Data set]. Accessed: 13 October 2026.\n"
        bad = "Text (Kaya et al., 2018).\n\n## References\n\nKaya, Ö., Köse, C. ve Geçim, T. (2019). An exothermic process. Sci. Hortic.\n"
        p = {"source_decimal": ".", "translate_references": "connectors"}
        self.assertEqual([f for f in self._run(src, good, p).findings if f["check"] == "references"], [])
        msgs = " | ".join(f["message"] for f in self._run(src, bad, p).findings if f["check"] == "references")
        self.assertIn("girdi sayısı farklı", msgs)
        self.assertIn("girdisi 1 değişmiş", msgs)
        self.assertIn("Türkçe künye", msgs)

    def test_glossary_paragraph_level_catches_local_deviation(self):
        # Onaylı karşılık belgenin bir yerinde geçiyor; öteki paragraftaki sapma yine yakalanmalı.
        g = {"terms": [{"original": "ölüm eğrisi", "translation": "kill curve", "enforce": True}]}
        src = "Ölüm eğrisi kurulmuştur.\n\nÖlüm eğrisi kaydırılmıştır.\n"
        tgt = "The kill curve was built.\n\nThe mortality curve was shifted.\n"
        with tempfile.TemporaryDirectory() as tmp:
            s, t = Path(tmp) / "s.md", Path(tmp) / "t.md"
            s.write_text(src, encoding="utf-8")
            t.write_text(tgt, encoding="utf-8")
            r = run_qa(s, t, "tr-en", glossary=g, params={"source_decimal": "."})
        msgs = [f for f in r.findings if f["check"] == "glossary"]
        self.assertEqual(len(msgs), 1)
        self.assertIn("Paragrafta onaylı karşılık yok", msgs[0]["message"])
        self.assertEqual(msgs[0]["location"], "paragraf 2")
        self.assertEqual(r.stats["glossary"]["compliant"], 1)

    def test_turkish_leftovers_in_english(self):
        r = self._run("Bahçe verimi ölçülmüştür.\n", "Orchard yield ölçülmüştür ve recorded.\n", {"source_decimal": "."})
        self.assertTrue(any("Türkçe sözcük" in f["message"] for f in r.findings))


@unittest.skipUnless(shutil.which("pandoc"), "pandoc yok")
class TestDocxSegments(unittest.TestCase):
    def setUp(self):
        import docx_segments
        self.ds = docx_segments
        self.tmp = Path(tempfile.mkdtemp())
        md = self.tmp / "k.md"
        md.write_text(
            "# Giriş\n\nKayısıda (*Prunus armeniaca* L.) don, $T_{50} = 2$ ile hesaplanmıştır; GDH~gece~ değeri.\n\n"
            "| Evre | Gün |\n|---|---|\n| Tam çiçek | 0 |\n\nBağlantı: <https://doi.org/10.5555/x>\n",
            encoding="utf-8")
        self.docx = self.tmp / "k.docx"
        subprocess.run(["pandoc", str(md), "-o", str(self.docx)], check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_identity_roundtrip_and_translation(self):
        seg = self.tmp / "seg"
        info = self.ds.extract(self.docx, seg)
        self.assertEqual(info["placeholders"].get("M"), 1)
        src = (seg / "source.txt").read_text(encoding="utf-8")
        self.assertIn("<i>Prunus armeniaca</i>", src)
        self.assertIn("<sub>gece</sub>", src)
        # Kimlik: çeviri = kaynak, metin aynı kalmalı
        same = self.tmp / "same.docx"
        rep = self.ds.apply(self.docx, seg, seg / "source.txt", same, None, None, None, None)
        self.assertEqual(rep["problems"], {})
        a = subprocess.run(["pandoc", str(self.docx), "-t", "plain"], capture_output=True, text=True).stdout
        b = subprocess.run(["pandoc", str(same), "-t", "plain"], capture_output=True, text=True).stdout
        self.assertEqual(a, b)
        # Çeviri: etiketler ve yer tutucu korunur, denklem içi alt simge eşlemesi uygulanır
        lines = []
        for ln in src.splitlines():
            m = self.ds.LINE_RE.match(ln)
            t = m.group(2)
            t = t.replace("Giriş", "Introduction").replace("Tam çiçek", "Full bloom").replace("Evre", "Stage").replace("Gün", "Day")
            t = t.replace("Kayısıda", "In apricot").replace("ile hesaplanmıştır", "was computed").replace("değeri", "value").replace("gece", "night")
            t = t.replace("Bağlantı", "Link").replace("don,", "frost,")
            lines.append(f"[[{m.group(1)}]] {t}")
        tr = self.tmp / "tr.txt"
        tr.write_text("\n".join(lines) + "\n", encoding="utf-8")
        out = self.tmp / "out.docx"
        rep = self.ds.apply(self.docx, seg, tr, out, "en-GB", {"gece": "night"}, "Title EN", None)
        self.assertEqual(rep["problems"], {})
        txt = subprocess.run(["pandoc", str(out), "-t", "markdown"], capture_output=True, text=True).stdout
        self.assertIn("*Prunus armeniaca*", txt)
        self.assertIn("night", txt)
        self.assertIn("Full bloom", txt)
        self.assertIn("https://doi.org/10.5555/x", txt)
        self.assertIn("T_{50}", txt)

    def test_placeholder_loss_is_rejected(self):
        seg = self.tmp / "seg"
        self.ds.extract(self.docx, seg)
        src = (seg / "source.txt").read_text(encoding="utf-8")
        broken = re.sub(r"\{M1\}", "", src)
        tr = self.tmp / "tr.txt"
        tr.write_text(broken, encoding="utf-8")
        rep = self.ds.apply(self.docx, seg, tr, self.tmp / "x.docx", None, None, None, None)
        self.assertTrue(rep["problems"])


@unittest.skipUnless(shutil.which("pandoc"), "pandoc yok")
class TestDocxTracked(unittest.TestCase):
    def setUp(self):
        import docx_segments
        import docx_tracked
        self.ds, self.dt = docx_segments, docx_tracked
        self.tmp = Path(tempfile.mkdtemp())
        md = self.tmp / "k.md"
        md.write_text(
            "Ana örneklem 14 bağlı grup içerir ve Tablo E4'te verilmiştir.\n\n"
            "| Evre | Gün |\n|---|---|\n| Tam çiçek | 0 |\n\n"
            "Breiman, L. (2001). Random forests. Machine Learning, 45, 5-32.\n",
            encoding="utf-8")
        self.docx = self.tmp / "k.docx"
        subprocess.run(["pandoc", str(md), "-o", str(self.docx)], check=True)
        self.seg = self.tmp / "seg"
        self.ds.extract(self.docx, self.seg)
        segs = json.loads((self.seg / "segments.json").read_text(encoding="utf-8"))
        self.pid = {s["text"][:8]: s["id"] for s in segs}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _plain(self, path, track="accept"):
        return subprocess.run(["pandoc", f"--track-changes={track}", str(path), "-t", "plain"],
                              capture_output=True, text=True).stdout

    def test_minimal_span(self):
        s, e, mid = self.dt.minimal_span("14 bağlı grup vardır", "14 bağımlılık grubu vardır")
        self.assertEqual("14 bağlı grup vardır"[s:e], "bağlı grup")
        self.assertEqual(mid, "bağımlılık grubu")

    def test_apply_and_accept(self):
        p_text, p_ref = self.pid["Ana örne"], self.pid["Breiman,"]
        edits = [
            {"op": "replace", "pid": p_text, "old": "14 bağlı grup içerir", "new": "14 bağımlılık grubu içerir"},
            {"op": "replace", "pid": p_text, "old": "Tablo E4\u2019te", "new": "Tablo E6\u2019da"},
            {"op": "italic", "pid": p_ref, "text": "Machine Learning"},
            {"op": "insert_paragraph", "before_table": 0, "style_like_pid": p_text, "text": "Tablo E1. Evreler."},
        ]
        out = self.tmp / "izlenen.docx"
        log = self.dt.apply_edits(self.docx, self.seg / "segments.json", edits, out, "Claude", "2026-10-20T00:00:00Z")
        self.assertEqual(len(log), 4)
        xml = zipfile.ZipFile(out).read("word/document.xml").decode()
        self.assertIn("w:delText", xml)
        self.assertIn("bağımlılık grubu", xml)
        self.assertIn("w:rPrChange", xml)
        # Silinen ve eklenen metin ayrı görünür; kabul edilince yalnız yeni metin kalır.
        allv = self._plain(out, "all")
        self.assertIn("bağlı grup", allv)
        clean = self.tmp / "temiz.docx"
        self.dt._rewrite(out, clean, self.dt.accept_tree)
        acc = self._plain(clean)
        self.assertIn("14 bağımlılık grubu içerir", acc)
        self.assertIn("Tablo E6\u2019da", acc)
        self.assertNotIn("bağlı grup", acc)
        self.assertIn("Tablo E1. Evreler.", acc)
        self.assertLess(acc.index("Tablo E1. Evreler."), acc.index("Tam çiçek"))
        cx = zipfile.ZipFile(clean).read("word/document.xml").decode()
        self.assertNotIn("w:ins ", cx)
        self.assertNotIn("w:del ", cx)

    def test_delete_paragraph_and_unique_ids(self):
        p_ref, p_text = self.pid["Breiman,"], self.pid["Ana örne"]
        edits = [
            {"op": "format_paragraph", "pid": p_text, "like_pid": p_ref},
            {"op": "italic", "pid": p_text, "text": "bağlı grup"},
            {"op": "delete_paragraph", "pid": p_ref},
        ]
        out = self.tmp / "izlenen.docx"
        self.dt.apply_edits(self.docx, self.seg / "segments.json", edits, out, "Claude", "2026-10-20T00:00:00Z")
        xml = zipfile.ZipFile(out).read("word/document.xml").decode()
        ids = re.findall(r'<w:(?:ins|del|rPrChange|pPrChange) w:id="(\d+)"', xml)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("Breiman", self._plain(out, "all"))
        clean = self.tmp / "temiz.docx"
        self.dt._rewrite(out, clean, self.dt.accept_tree)
        acc = self._plain(clean)
        self.assertNotIn("Breiman", acc)
        self.assertIn("Ana örneklem", acc)

    def test_ambiguous_old_is_rejected(self):
        edits = [{"op": "replace", "pid": self.pid["Breiman,"], "old": "s", "new": "x"}]
        with self.assertRaises(self.dt.EditError):
            self.dt.apply_edits(self.docx, self.seg / "segments.json", edits, self.tmp / "x.docx", "Claude", "2026-10-20T00:00:00Z")
