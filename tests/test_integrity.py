"""Skill dosyalarının bütünlük sınamaları.

- SKILL.md biçimi, uzunluğu, aşamaları ve istemleri.
- Belgelerdeki göreli bağlantıların var olan dosyalara gitmesi.
- baglayici.json girdilerinin kullanıcı sözlüğüne birebir bağlı olması.
- oneriler.json'un kaynak listelerin sayım çizelgeleriyle uyuşması ve güncel olması.
- Betiklerin --help ile çalışması.
- Yazılan belgelerde U+2013, U+2014, U+2212 bulunmaması (kullanıcı kuralı).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = ROOT / "domains" / "toprak-bilimi"
sys.path.insert(0, str(ROOT / "scripts"))

from trtext import tr_lower  # noqa: E402

AUTHORED_DOCS = (
    [ROOT / "SKILL.md", ROOT / "README.md"]
    + sorted((ROOT / "references").glob("*.md"))
    + sorted((ROOT / "docs").glob("*.md"))
    + [DOMAIN / "README.md", DOMAIN / "alan-notlari.md"]
)


class TestSkillFile(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    def test_length(self):
        self.assertLessEqual(len(self.text.splitlines()), 500)

    def test_frontmatter(self):
        m = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: \"(.+?)\"\n---\n", self.text, re.DOTALL)
        self.assertIsNotNone(m, "frontmatter name/description bulunamadı")
        self.assertEqual(m.group(1), "bilimsel-ceviri-tr-en")
        self.assertLessEqual(len(m.group(2)), 1024)

    def test_phases_in_order(self):
        positions = [self.text.find(f"## Aşama {p}") for p in ("0", "1:", "1.5", "2", "3", "4")]
        self.assertTrue(all(p >= 0 for p in positions), positions)
        self.assertEqual(positions, sorted(positions))

    def test_prompts_present(self):
        for name in ("Çevirmen istemi", "Terim araştırmacısı istemi", "Denetçi istemi"):
            self.assertIn(name, self.text)


class TestLinks(unittest.TestCase):
    def test_relative_links_resolve(self):
        missing = []
        for doc in AUTHORED_DOCS:
            for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                path = (doc.parent / target.split("#")[0]).resolve()
                if not path.exists():
                    missing.append(f"{doc.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_backtick_paths_in_skill_resolve(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        paths = set(re.findall(r"(?:scripts|references|domains)/[\w./-]+\.(?:py|md|json)", text))
        missing = [p for p in paths if not (ROOT / p).exists()]
        self.assertEqual(missing, [])


class TestDomainPack(unittest.TestCase):
    def test_binding_entries_trace_to_user_glossary(self):
        sozluk = (DOMAIN / "kaynak" / "sozluk.md").read_text(encoding="utf-8")
        data = json.loads((DOMAIN / "baglayici.json").read_text(encoding="utf-8"))
        problems = []
        for e in data["entries"]:
            frag = e["kaynak"]
            if frag not in sozluk:
                problems.append(f"kaynak parçası sozluk.md'de yok: {frag}")
                continue
            words = set(re.findall(r"[\wçğıöşüâîû'-]+", tr_lower(frag)))
            for field in ("tr", "en"):
                for term in [e[field]] + e.get(f"{field}_alternatives", []):
                    for w in re.findall(r"[\wçğıöşüâîû'-]+", tr_lower(term)):
                        if w not in words:
                            problems.append(f"'{term}' sözcüğü '{w}' kaynak parçasında yok: {frag}")
        for g in data.get("global_forbidden_en", []) + data.get("consistency_groups", []):
            if g["kaynak"] not in sozluk:
                problems.append(f"kaynak parçası sozluk.md'de yok: {g['kaynak']}")
        self.assertEqual(problems, [])

    def _sayim(self, path: Path) -> Counter:
        text = path.read_text(encoding="utf-8")
        sec = text[text.index("Sayım"):]
        lines = [ln for ln in sec.splitlines() if ln.startswith("|")]
        header = [c.strip().lower() for c in lines[0].strip("|").split("|")]
        total = next(ln for ln in lines if ln.startswith("| Toplam"))
        cells = [c.strip() for c in total.strip("|").split("|")]
        out = Counter()
        for name, val in zip(header, cells):
            if name in {"yerleşik", "değişken", "yerleşmemiş"}:
                out[name] = int(val)
        return out

    def test_proposal_counts_match_source_tables(self):
        data = json.loads((DOMAIN / "oneriler.json").read_text(encoding="utf-8"))
        for list_id in ("A", "B"):
            got = Counter(e["status"] for e in data["entries"] if e["list"] == list_id)
            expected = self._sayim(DOMAIN / "kaynak" / f"terim_onerileri_{list_id}.md")
            self.assertEqual(got, expected, f"liste {list_id}")

    def test_proposals_json_is_up_to_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            dom = Path(tmp) / DOMAIN.name
            shutil.copytree(DOMAIN / "kaynak", dom / "kaynak")
            subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "build_domain_glossary.py"), str(dom)], check=True, capture_output=True)
            fresh = json.loads((dom / "oneriler.json").read_text(encoding="utf-8"))
            current = json.loads((DOMAIN / "oneriler.json").read_text(encoding="utf-8"))
            self.assertEqual(fresh["entries"], current["entries"], "oneriler.json eski; build_domain_glossary.py çalıştır")


class TestScripts(unittest.TestCase):
    def test_help(self):
        for script in ("qa_checks.py", "seed_glossary.py", "prepare_source.py", "export_docx.py", "merge_glossaries.py", "build_domain_glossary.py"):
            args = [sys.executable, "-I", str(ROOT / "scripts" / script)]
            args += [] if script == "build_domain_glossary.py" else ["--help"]
            res = subprocess.run(args, capture_output=True, text=True)
            expected = 2 if script == "build_domain_glossary.py" else 0
            self.assertEqual(res.returncode, expected, f"{script}: {res.stderr[:200]}")


class TestTypographyOfDocs(unittest.TestCase):
    def test_no_forbidden_dashes(self):
        bad = {"\u2013": "en dash", "\u2014": "em dash", "\u2212": "eksi işareti"}
        found = []
        files = AUTHORED_DOCS + sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "tests").glob("*.py"))
        for f in files:
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), start=1):
                for ch, name in bad.items():
                    if ch in line:
                        found.append(f"{f.relative_to(ROOT)}:{i} {name}")
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
