#!/usr/bin/env python3
"""Kaynak ve çeviri arasında kural tabanlı denetim.

Kullanım:
    python scripts/qa_checks.py --source WS/source.md --target WS/first-pass.md \
        --direction en-tr [--glossary WS/terminology-glossary.json] \
        [--params WS/params.json] [--out-md WS/qa-report.md] [--out-json WS/qa-report.json] [--strict]

Denetimler:
    numbers     Sayılar ondalık ayırıcı dönüşümünden sonra birebir korunmuş mu?
    citations   Metin içi atıflar (yazar-yıl ve numaralı), DOI ve adresler korunmuş mu?
    references  Kaynakça çevrilmeyecekse değişmeden kalmış mı?
    structure   Başlık düzeyleri, çizelgeler (satır x sütun), şekil ve çizelge
                numaraları, denklemler, liste imleri, paragraf sayısı.
    glossary    Onaylı terim karşılığı hedefte geçiyor mu? Yasak biçim var mı?
                Değişken terimde aynı metinde iki biçim kullanılmış mı?
    typography  Hedef dilin sayı, yüzde ve atıf yazımı; yasak tire işaretleri;
                çevirmenin bıraktığı [?...?] ve [kaynakta belirsiz: ...] işaretleri.
    sentences   Hedef metinde sınırı aşan uzun cümleler.

Bu betiğin bulguları adaydır. Kural tabanlı eşleşme yanlış alarm verebilir
(örnek: kaynakta yazıyla, çeviride rakamla yazılmış sayı). Denetçi her adayı
kaynak metne bakarak doğrular ya da reddeder.
Çıkış kodu: --strict verilirse kritik aday varsa 1, yoksa 0. Varsayılan 0.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trtext import (  # noqa: E402
    DASH_CHARS,
    DOI_RE,
    URL_RE,
    abbreviation_pattern,
    extract_numbers,
    find_term,
    iter_prose_paragraphs,
    mask_section_numbers,
    normalize,
    split_references,
    split_sentences,
    strip_code_and_links,
    tr_lower,
    word_count,
)

SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2, "info": 3}

DEFAULTS = {
    "en-tr": {
        "source_decimal": ".",
        "target_decimal": ",",
        "target_percent": "prefix",
        "etal_target": "ve ark.",
        "figure_label_target": "Şekil",
        "table_label_target": "Çizelge",
        "max_sentence_words": 30,
    },
    "tr-en": {
        "source_decimal": ",",
        "target_decimal": ".",
        "target_percent": "suffix",
        "etal_target": "et al.",
        "figure_label_target": "Figure",
        "table_label_target": "Table",
        "max_sentence_words": 35,
    },
}
COMMON_DEFAULTS = {"forbid_dashes": True, "translate_references": False}


class Report:
    def __init__(self) -> None:
        self.findings: list[dict] = []
        self.stats: dict[str, dict] = {}

    def add(self, check: str, severity: str, type_: str, message: str, location: str = "", detail: str = "") -> None:
        self.findings.append(
            {"check": check, "severity": severity, "type": type_, "message": message, "location": location, "detail": detail}
        )

    def counts(self) -> dict[str, int]:
        c = Counter(f["severity"] for f in self.findings)
        return {k: c.get(k, 0) for k in SEVERITY_ORDER}


# ---------------------------------------------------------------------------
# Sayılar
# ---------------------------------------------------------------------------


def check_numbers(src: str, tgt: str, p: dict, r: Report) -> None:
    sb, _ = split_references(src)
    tb, _ = split_references(tgt)
    sn = extract_numbers(mask_section_numbers(strip_code_and_links(sb)), p["source_decimal"])
    tn = extract_numbers(mask_section_numbers(strip_code_and_links(tb)), p["target_decimal"])
    sc, tc = Counter(v for v, _ in sn), Counter(v for v, _ in tn)
    missing = sc - tc
    extra = tc - sc
    r.stats["numbers"] = {"source": sum(sc.values()), "target": sum(tc.values()), "missing": sum(missing.values()), "extra": sum(extra.values())}
    s_lines: dict[str, list[int]] = {}
    for v, ln in sn:
        s_lines.setdefault(v, []).append(ln)
    t_lines: dict[str, list[int]] = {}
    for v, ln in tn:
        t_lines.setdefault(v, []).append(ln)
    for v, n in sorted(missing.items()):
        r.add("numbers", "critical", "NUMERIC", f"Kaynaktaki {v} değeri çeviride {n} kez eksik", f"kaynak satır {s_lines[v][:5]}",
              "Ondalık ayırıcı dönüşümünü, sondaki sıfırları ve yazıyla yazılmış sayıyı kontrol et.")
    for v, n in sorted(extra.items()):
        r.add("numbers", "critical", "NUMERIC", f"Çeviride kaynakta olmayan {v} değeri {n} kez geçiyor", f"hedef satır {t_lines[v][:5]}",
              "Uydurma sayı, yanlış ayırıcı ya da rakama çevrilmiş sözcük olabilir.")


# ---------------------------------------------------------------------------
# Atıflar
# ---------------------------------------------------------------------------

SURNAME = r"[A-ZÇĞİÖŞÜ][\w'’\-]+(?:\s+(?:van|de|der|von|da|di|le|du)\s+[A-ZÇĞİÖŞÜ][\w'’\-]+)?"
YEAR = r"(?:19|20)\d{2}[a-z]?"
CONNECT = r"(?:\s+(?:et al\.|ve ark\.|vd\.|ve diğ\.)|\s+(?:and|ve|&)\s+" + SURNAME + r")?"
PAREN_RE = re.compile(r"\(([^()]*?" + YEAR + r"[^()]*)\)")
IN_PAREN_RE = re.compile(r"(" + SURNAME + r")" + CONNECT + r",?\s+(" + YEAR + r"(?:\s*,\s*" + YEAR + r")*)")
NARRATIVE_RE = re.compile(r"(" + SURNAME + r")" + CONNECT + r"\s*\((" + YEAR + r"(?:\s*,\s*" + YEAR + r")*)\)")
NUMBERED_RE = re.compile(r"\[(\d+(?:\s*[-,\u2013]\s*\d+)*)\]")
_NOT_NAMES = {"Table", "Tables", "Figure", "Figures", "Fig", "Çizelge", "Tablo", "Şekil", "Eq", "Equation", "Denklem", "See", "Bkz"}


def _surname_key(name: str) -> str:
    name = re.split(r"['’]", name)[0]
    return tr_lower(name)


def extract_citations(text: str) -> Counter:
    out: Counter = Counter()
    spans: list[tuple[int, int]] = []
    for m in PAREN_RE.finditer(text):
        spans.append(m.span())
        for part in m.group(1).split(";"):
            for cm in IN_PAREN_RE.finditer(part):
                name = cm.group(1)
                if name.split()[0] in _NOT_NAMES:
                    continue
                for y in re.findall(YEAR, cm.group(2)):
                    out[(_surname_key(name), y)] += 1
    for m in NARRATIVE_RE.finditer(text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        name = m.group(1)
        if name.split()[0] in _NOT_NAMES:
            continue
        for y in re.findall(YEAR, m.group(2)):
            out[(_surname_key(name), y)] += 1
    return out


def extract_numbered(text: str) -> Counter:
    out: Counter = Counter()
    for m in NUMBERED_RE.finditer(text):
        for part in re.split(r"\s*,\s*", m.group(1)):
            if re.search(r"[-\u2013]", part):
                a, b = re.split(r"\s*[-\u2013]\s*", part)[:2]
                if a.isdigit() and b.isdigit() and int(b) - int(a) < 200:
                    for i in range(int(a), int(b) + 1):
                        out[i] += 1
            elif part.isdigit():
                out[int(part)] += 1
    return out


def _apply_aliases(text: str, aliases: dict) -> str:
    for a, b in (aliases or {}).items():
        text = text.replace(a, b)
    return text


def check_citations(src: str, tgt: str, p: dict, r: Report) -> None:
    sb, _ = split_references(src)
    tb, _ = split_references(tgt)
    # Kurumsal yazar adları çevrilir ("Türkiye İstatistik Kurumu" -> "Turkish Statistical Institute");
    # params.json citation_aliases ile kaynak metindeki ad hedefteki adla eşlenir.
    sb = _apply_aliases(sb, p.get("citation_aliases"))
    sb_c, tb_c = strip_code_and_links(sb), strip_code_and_links(tb)
    sc, tc = extract_citations(sb_c), extract_citations(tb_c)
    for (name, y), n in sorted((sc - tc).items()):
        r.add("citations", "critical", "CITATION", f"Atıf eksik ya da değişmiş: {name} {y} ({n} kez)")
    for (name, y), n in sorted((tc - sc).items()):
        r.add("citations", "critical", "CITATION", f"Kaynakta olmayan atıf: {name} {y} ({n} kez)")
    sn, tn = extract_numbered(sb_c), extract_numbered(tb_c)
    for k, n in sorted((sn - tn).items()):
        r.add("citations", "critical", "CITATION", f"Numaralı atıf [{k}] çeviride eksik ({n} kez)")
    for k, n in sorted((tn - sn).items()):
        r.add("citations", "critical", "CITATION", f"Numaralı atıf [{k}] kaynakta yok ({n} kez)")
    s_ids = set(DOI_RE.findall(src)) | set(URL_RE.findall(src))
    t_ids = set(DOI_RE.findall(tgt)) | set(URL_RE.findall(tgt))
    for x in sorted(s_ids - t_ids):
        r.add("citations", "critical", "CITATION", f"DOI ya da adres çeviride yok ya da değişmiş: {x}")
    for x in sorted(t_ids - s_ids):
        r.add("citations", "major", "CITATION", f"Çeviride kaynakta olmayan DOI ya da adres: {x}")
    r.stats["citations"] = {
        "author_year_source": sum(sc.values()), "author_year_target": sum(tc.values()),
        "numbered_source": sum(sn.values()), "numbered_target": sum(tn.values()),
        "ids_source": len(s_ids), "ids_target": len(t_ids),
    }


def check_references(src: str, tgt: str, p: dict, r: Report) -> None:
    _, sr = split_references(src)
    _, trf = split_references(tgt)
    r.stats["references"] = {"source_chars": len(sr.strip()), "target_chars": len(trf.strip())}
    if not sr.strip():
        r.add("references", "info", "STRUCTURE", "Kaynakta kaynakça başlığı bulunamadı; kaynakça denetimi atlandı")
        return
    if not trf.strip():
        r.add("references", "critical", "OMISSION", "Çeviride kaynakça bölümü bulunamadı")
        return
    mode = p.get("translate_references")
    if mode == "connectors":
        _check_reference_identity(sr, trf, p, r)
        return
    if mode:
        return
    norm = lambda s: re.sub(r"\s+", " ", normalize(s)).strip()  # noqa: E731
    if norm(sr) != norm(trf):
        s_lines = [norm(x) for x in sr.splitlines() if x.strip()]
        t_lines = set(norm(x) for x in trf.splitlines() if x.strip())
        changed = [x for x in s_lines if x not in t_lines]
        r.add("references", "major", "STRUCTURE",
              f"Kaynakça çevrilmeyecekti ama {len(changed)} girdi değişmiş görünüyor",
              detail="; ".join(c[:80] for c in changed[:5]))


def _ref_entries(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if re.search(r"\((?:19|20)\d{2}[a-z]?|\((?:t\.y\.|n\.d\.)\)", ln)]


def _check_reference_identity(sr: str, trf: str, p: dict, r: Report) -> None:
    """Kaynakçada yalnız bağlaç ve künye sözcükleri çevrildiğinde girdilerin kimliğini denetler.

    Her kaynak girdisi için ilk yazar soyadı (ya da kurum adı), yıl ve harf eki
    hedefte aynı sırada bulunmalıdır. DOI ve adresler check_citations içinde denetlenir.
    """
    src_e = _ref_entries(_apply_aliases(sr, p.get("citation_aliases")))
    tgt_e = _ref_entries(trf)
    key = lambda e: (tr_lower(re.split(r"[,.(]", e)[0].strip()), (re.search(r"\(((?:19|20)\d{2}[a-z]?|t\.y\.|n\.d\.)\)", e) or [None, ""])[1].replace("t.y.", "n.d."))  # noqa: E731
    sk, tk = [key(e) for e in src_e], [key(e) for e in tgt_e]
    if len(sk) != len(tk):
        r.add("references", "critical", "OMISSION", f"Kaynakça girdi sayısı farklı: kaynak {len(sk)}, çeviri {len(tk)}")
    for i, (a, b) in enumerate(zip(sk, tk), start=1):
        if a != b:
            r.add("references", "critical", "CITATION", f"Kaynakça girdisi {i} değişmiş: kaynak {a}, çeviri {b}")
    if p.get("direction") == "tr-en":
        for i, e in enumerate(tgt_e, start=1):
            if re.search(r"\bve ark\.|\(t\.y\.\)|\bErişim\b|\[Veri\b| ve [A-ZÇĞİÖŞÜ]", e):
                r.add("references", "major", "TYPOGRAPHY", f"Kaynakça girdisi {i}: Türkçe künye sözcüğü kalmış", detail=e[:100])


# ---------------------------------------------------------------------------
# Yapı
# ---------------------------------------------------------------------------

FIG_RE = re.compile(r"\b(?:Figure|Figures|Fig\.|Figs\.|Şekil)\s*(\d+)", re.IGNORECASE)
TAB_RE = re.compile(r"\b(?:Table|Tables|Çizelge|Tablo)\s*(\d+)", re.IGNORECASE)


def _md_tables(text: str) -> list[tuple[int, int]]:
    tables, rows, cols, in_t = [], 0, 0, False
    for line in text.splitlines() + [""]:
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and len(s) > 1:
            if not in_t:
                in_t, rows, cols = True, 0, 0
            if re.fullmatch(r"\|[\s:|-]+\|", s) and "-" in s:
                continue
            rows += 1
            cols = max(cols, s.count("|") - 1 - s.count("\\|"))
        elif in_t:
            tables.append((rows, cols))
            in_t = False
    return tables


def _html_tables(text: str) -> list[tuple[int, int]]:
    out = []
    for t in re.findall(r"<table\b.*?</table>", text, re.IGNORECASE | re.DOTALL):
        rows = re.findall(r"<tr\b.*?</tr>", t, re.IGNORECASE | re.DOTALL)
        cols = max((len(re.findall(r"<t[dh]\b", row, re.IGNORECASE)) for row in rows), default=0)
        out.append((len(rows), cols))
    return out


def structure_stats(text: str) -> dict:
    body, _ = split_references(text)
    nocode = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    headings = Counter(len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s+\S", nocode, re.MULTILINE))
    return {
        "headings": {f"H{k}": v for k, v in sorted(headings.items())},
        "tables": _md_tables(nocode) + _html_tables(nocode),
        "figure_numbers": sorted(set(int(x) for x in FIG_RE.findall(nocode))),
        "table_numbers": sorted(set(int(x) for x in TAB_RE.findall(nocode))),
        "display_equations": len(re.findall(r"\$\$", nocode)) // 2
        + len(re.findall(r"\\begin\{(?:equation|align)\*?\}", nocode)),
        "inline_math": len(re.findall(r"(?<!\$)\$[^$\n]+\$(?!\$)", nocode)),
        "list_items": len(re.findall(r"^\s*(?:[-*+]|\d+[.)])\s+\S", nocode, re.MULTILINE)),
        "paragraphs": sum(1 for _ in iter_prose_paragraphs(nocode)),
        "colspan_rowspan": len(re.findall(r"colspan|rowspan", nocode, re.IGNORECASE)),
    }


def check_structure(src: str, tgt: str, p: dict, r: Report) -> None:
    s, t = structure_stats(src), structure_stats(tgt)
    r.stats["structure"] = {"source": s, "target": t}
    if s["headings"] != t["headings"]:
        r.add("structure", "critical", "STRUCTURE", f"Başlık düzeyleri farklı: kaynak {s['headings']}, çeviri {t['headings']}")
    if len(s["tables"]) != len(t["tables"]):
        r.add("structure", "critical", "STRUCTURE", f"Çizelge sayısı farklı: kaynak {len(s['tables'])}, çeviri {len(t['tables'])}")
    for i, (a, b) in enumerate(zip(s["tables"], t["tables"]), start=1):
        if a != b:
            r.add("structure", "critical", "STRUCTURE", f"Çizelge {i}: kaynak {a[0]} satır x {a[1]} sütun, çeviri {b[0]} satır x {b[1]} sütun")
    for key, label in (("figure_numbers", "Şekil"), ("table_numbers", "Çizelge")):
        if s[key] != t[key]:
            r.add("structure", "major", "STRUCTURE", f"{label} numaraları farklı: kaynak {s[key]}, çeviri {t[key]}")
    for key, label, sev in (("display_equations", "Ayrık denklem", "critical"), ("inline_math", "Satır içi matematik", "major")):
        if s[key] != t[key]:
            r.add("structure", sev, "STRUCTURE", f"{label} sayısı farklı: kaynak {s[key]}, çeviri {t[key]}")
    if s["list_items"] != t["list_items"]:
        r.add("structure", "major", "STRUCTURE", f"Liste imi sayısı farklı: kaynak {s['list_items']}, çeviri {t['list_items']}")
    if s["paragraphs"] != t["paragraphs"]:
        r.add("structure", "major", "STRUCTURE", f"Paragraf sayısı farklı: kaynak {s['paragraphs']}, çeviri {t['paragraphs']}",
              detail="Paragraf birleştirme, bölme ya da atlama olabilir.")
    if s["colspan_rowspan"]:
        r.add("structure", "info", "STRUCTURE", f"Kaynakta {s['colspan_rowspan']} birleştirilmiş hücre var; elle doğrula")


# ---------------------------------------------------------------------------
# Terim sözlüğü
# ---------------------------------------------------------------------------


def _present(text: str, term: str, lang: str) -> int:
    if re.fullmatch(r"[A-Z][A-Za-z0-9-]{1,10}", term) and term.upper() == term:
        return len(abbreviation_pattern(term).findall(text))
    return len(find_term(text, term, lang))


def check_glossary(src: str, tgt: str, glossary: dict, direction: str, r: Report) -> None:
    src_lang, tgt_lang = direction.split("-")
    sb = normalize(strip_code_and_links(split_references(src)[0]))
    tb = normalize(strip_code_and_links(split_references(tgt)[0]))
    checked = ok = 0
    for t in glossary.get("terms", []):
        if not t.get("enforce", True) or not t.get("translation"):
            continue
        if not _present(sb, t["original"], src_lang):
            continue
        checked += 1
        forms = [t["translation"]] + list(t.get("alternatives") or [])
        if any(_present(tb, f, tgt_lang) for f in forms):
            ok += 1
        else:
            r.add("glossary", "major", "TERMINOLOGY", f"Onaylı karşılık bulunamadı: '{t['original']}' -> '{t['translation']}'",
                  detail=f"kaynak: {t.get('origin', '')}")
        for bad in t.get("forbidden") or []:
            n = _present(tb, bad, tgt_lang)
            if n:
                r.add("glossary", "major", "TERMINOLOGY", f"Yasak biçim kullanılmış: '{bad}' ({n} kez); onaylı biçim '{t['translation']}'")
    para = _check_glossary_by_paragraph(sb, tb, glossary, src_lang, tgt_lang, r)
    meta = glossary.get("metadata", {})
    for bad in meta.get("global_forbidden", []):
        n = _present(tb, bad, tgt_lang)
        if n:
            r.add("glossary", "major", "TERMINOLOGY", f"Hiçbir bağlamda kullanılmayacak sözcük: '{bad}' ({n} kez)")
    for g in meta.get("consistency_groups", []):
        if g.get("lang") != tgt_lang:
            continue
        used = {}
        for v in g["variants"]:
            if g.get("match") == "abbr":
                n = len(abbreviation_pattern(v).findall(tb))
            elif g.get("match") == "word":
                n = len(re.findall(rf"(?<![\wçğıöşü]){re.escape(tr_lower(v))}[\wçğıöşü']*", tr_lower(tb)))
            else:
                n = _present(tb, v, tgt_lang)
            if n:
                used[v] = n
        if len(used) > 1:
            r.add("glossary", "minor", "TERMINOLOGY", f"Aynı metinde değişken terimin iki biçimi: {used}",
                  detail="Bir biçim seçilir ve metin boyunca korunur.")
    r.stats["glossary"] = {"checked": checked, "compliant": ok}
    if para is not None:
        r.stats["glossary"]["paragraph_level"] = para


def _paragraphs(text: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def _check_glossary_by_paragraph(sb: str, tb: str, glossary: dict, src_lang: str, tgt_lang: str, r: Report):
    """Kaynak ve hedef paragraf sayısı eşitse terimi paragraf paragraf denetler.

    Belge düzeyindeki denetim, onaylı karşılık belgenin bir yerinde geçince geçer;
    başka bir paragraftaki sapmayı ("mortality curve" yanında başka yerde "kill curve") göremez.
    Paragraf eşleşmesi yoksa (sayılar farklı) bu denetim atlanır ve None döner.
    """
    sp, tp = _paragraphs(sb), _paragraphs(tb)
    if len(sp) != len(tp):
        return None
    checked = missing = 0
    for t in glossary.get("terms", []):
        if not t.get("enforce", True) or not t.get("translation"):
            continue
        forms = [t["translation"]] + list(t.get("alternatives") or [])
        miss_at = []
        for i, (s, g) in enumerate(zip(sp, tp), start=1):
            if not _present(s, t["original"], src_lang):
                continue
            checked += 1
            if not any(_present(g, f, tgt_lang) for f in forms):
                missing += 1
                miss_at.append(i)
        if miss_at:
            ex = tp[miss_at[0] - 1].strip()[:140]
            r.add("glossary", "minor", "TERMINOLOGY",
                  f"Paragrafta onaylı karşılık yok: '{t['original']}' -> '{t['translation']}' ({len(miss_at)} paragraf)",
                  f"paragraf {', '.join(map(str, miss_at[:8]))}",
                  f"Gönderme sözcüğü ('this window') ya da yeniden kurulan cümle olabilir; elle bak. İlk örnek: {ex}")
    return {"paragraphs": len(sp), "checked": checked, "missing": missing}


# ---------------------------------------------------------------------------
# Yazım
# ---------------------------------------------------------------------------


def check_typography(tgt: str, direction: str, p: dict, r: Report) -> None:
    tgt_lang = direction.split("-")[1]
    body, _ = split_references(tgt)
    body_nc = mask_section_numbers(strip_code_and_links(body))
    lines = body_nc.splitlines()
    counts: Counter = Counter()

    def flag(sev: str, msg: str, ln: int, line: str) -> None:
        counts[msg] += 1
        if counts[msg] <= 10:
            r.add("typography", sev, "TYPOGRAPHY", msg, f"hedef satır {ln}", line.strip()[:120])

    if p.get("forbid_dashes", True):
        for ln, line in enumerate(tgt.splitlines(), start=1):
            for ch, name in DASH_CHARS.items():
                if ch in line:
                    flag("minor", f"Yasak işaret: {name} (U+{ord(ch):04X})", ln, line)
    for ln, line in enumerate(lines, start=1):
        if p["target_decimal"] == ",":
            if re.search(r"(?<![\w.])\d+\.\d{1,2}(?![\d.])|(?<![\w.])\d+\.\d{4,}(?![\d.])|(?<![\w.])0\.\d+", line):
                flag("major", "Türkçe hedefte ondalık nokta kullanılmış olabilir", ln, line)
        else:
            if re.search(r"(?<![\w,])\d+,\d{1,2}(?![\d,])|(?<![\w,])\d+,\d{4,}(?![\d,])|(?<![\w,])0,\d+", line):
                flag("major", "İngilizce hedefte ondalık virgül kullanılmış olabilir", ln, line)
        if p["target_percent"] == "prefix" and re.search(r"\d\s?%(?!\s?\d)", line):
            flag("minor", "Türkçe hedefte yüzde işareti sayıdan sonra yazılmış (beklenen: %25)", ln, line)
        if p["target_percent"] == "suffix" and re.search(r"%\s?\d", line):
            flag("minor", "İngilizce hedefte yüzde işareti sayıdan önce yazılmış (beklenen: 25%)", ln, line)
        if tgt_lang == "tr":
            if "et al." in line and p["etal_target"] != "et al.":
                flag("minor", f"Türkçe hedefte 'et al.' kalmış (beklenen: '{p['etal_target']}')", ln, line)
            other = {"ve ark.": "vd.", "vd.": "ve ark."}.get(p["etal_target"])
            if other and re.search(rf"\b{re.escape(other)}", line):
                flag("minor", f"Atıf kısaltması karışık: '{other}' kullanılmış (seçilen: '{p['etal_target']}')", ln, line)
            for word in re.findall(r"\b[A-ZÇĞÖŞÜİI]{3,}\b", line):
                if "I" in word and word in {"GIRIŞ", "BILGI", "IÇIN", "ILE", "SONUÇLARI", "BULGULARI", "TEŞEKKÜRLERI", "IÇINDEKILER", "ÖZETI"}:
                    flag("major", f"Türkçe büyük harf hatası: '{word}' (i harfinin büyüğü İ)", ln, line)
        else:
            if re.search(r"\bve ark\.|\bvd\.", line):
                flag("minor", "İngilizce hedefte Türkçe atıf kısaltması kalmış (beklenen: 'et al.')", ln, line)
            hits = re.findall(r"(?<![\w])(ve|ile|bir|için|olarak|daha|veya|Tablo|Şekil|Eşitlik|Bölüm|Ek|yıl|gün|"
                              r"[a-zçğıöşü]+(?:mıştır|miştir|muştur|müştür|maktadır|mektedir|ları|leri|ının|inin))(?![\w])", line)
            if hits:
                flag("major", "İngilizce hedefte Türkçe sözcük kalmış olabilir", ln, ", ".join(sorted(set(hits)))[:120])
        fig_label = p["figure_label_target"]
        tab_label = p["table_label_target"]
        wrong_fig = {"Şekil": r"\b(?:Figure|Fig\.)\s*\d", "Figure": r"\bŞekil\s*\d", "Fig.": r"\bŞekil\s*\d"}.get(fig_label)
        wrong_tab = {"Çizelge": r"\b(?:Table|Tablo)\s*\d", "Tablo": r"\b(?:Table|Çizelge)\s*\d", "Table": r"\b(?:Çizelge|Tablo)\s*\d"}.get(tab_label)
        if wrong_fig and re.search(wrong_fig, line):
            flag("minor", f"Şekil etiketi '{fig_label}' olmalı", ln, line)
        if wrong_tab and re.search(wrong_tab, line):
            flag("minor", f"Çizelge etiketi '{tab_label}' olmalı", ln, line)
    for ln, line in enumerate(tgt.splitlines(), start=1):
        for m in re.finditer(r"\[\?[^\]]*\?\]|\[kaynakta belirsiz:[^\]]*\]", line):
            flag("major", "Çözülmemiş çevirmen işareti", ln, m.group(0))
    for msg, n in counts.items():
        if n > 10:
            r.add("typography", "info", "TYPOGRAPHY", f"'{msg}' bulgusu toplam {n} kez; ilk 10 tanesi listelendi")


# ---------------------------------------------------------------------------
# Cümle uzunluğu
# ---------------------------------------------------------------------------


def check_sentences(tgt: str, p: dict, r: Report) -> None:
    body, _ = split_references(tgt)
    limit = int(p["max_sentence_words"])
    long_n = total = 0
    for start, para in iter_prose_paragraphs(strip_code_and_links(body)):
        for s in split_sentences(para):
            total += 1
            n = word_count(s)
            if n > limit:
                long_n += 1
                if long_n <= 25:
                    r.add("sentences", "minor", "READABILITY", f"{n} sözcüklü cümle (sınır {limit})", f"hedef paragraf satır {start}", s[:160])
    r.stats["sentences"] = {"total": total, "over_limit": long_n, "limit": limit}


# ---------------------------------------------------------------------------
# Rapor
# ---------------------------------------------------------------------------


def to_markdown(r: Report, args: argparse.Namespace) -> str:
    c = r.counts()
    out = [
        "# Otomatik denetim raporu (qa_checks.py)",
        "",
        f"Kaynak: `{args.source}`  ",
        f"Çeviri: `{args.target}`  ",
        f"Yön: {args.direction}",
        "",
        "Bu bulgular kural tabanlı adaylardır. Denetçi her adayı kaynakla karşılaştırıp doğrular ya da reddeder.",
        "",
        "| Önem | Sayı |",
        "|---|---|",
    ]
    out += [f"| {k} | {v} |" for k, v in c.items()]
    out += ["", "## İstatistikler", "", "```json", json.dumps(r.stats, ensure_ascii=False, indent=1), "```", ""]
    for sev in SEVERITY_ORDER:
        items = [f for f in r.findings if f["severity"] == sev]
        if not items:
            continue
        out += [f"## {sev}", ""]
        for i, f in enumerate(items, start=1):
            loc = f" [{f['location']}]" if f["location"] else ""
            det = f" | {f['detail']}" if f["detail"] else ""
            out.append(f"{i}. {f['type']} ({f['check']}){loc}: {f['message']}{det}")
        out.append("")
    return "\n".join(out)


_SEG_LINE = re.compile(r"^\[\[[a-z0-9]+(?:\|[^\]]*)?\]\]\s?", re.MULTILINE)


def _from_segments(text: str) -> str:
    """docx_segments.py parça biçimini ("[[p0042|biçem]] metin") düz metne çevirir.

    Kimlik ve biçem etiketi atılır, satırlar paragraf olur, başlık biçemi Markdown başlığına döner.
    """
    if not _SEG_LINE.search(text):
        return text
    out = []
    for ln in text.splitlines():
        m = re.match(r"^\[\[[a-z0-9]+(?:\|([^\]]*))?\]\]\s?(.*)$", ln)
        if not m:
            continue
        style, body = (m.group(1) or "").lower(), m.group(2)
        body = re.sub(r"</?(?:i|b|u|sub|sup|x\d+)>", "", body)
        if style.startswith(("heading 1", "balk1")):
            body = "# " + body
        elif style.startswith(("heading 2", "balk2")):
            body = "## " + body
        out.append(body)
    return "\n\n".join(out) + "\n"


def run(args: argparse.Namespace) -> Report:
    src = _from_segments(args.source.read_text(encoding="utf-8"))
    tgt = _from_segments(args.target.read_text(encoding="utf-8"))
    p = dict(COMMON_DEFAULTS)
    p.update(DEFAULTS[args.direction])
    if args.params:
        p.update(json.loads(args.params.read_text(encoding="utf-8")))
    p["direction"] = args.direction
    r = Report()
    checks = set(args.only.split(",")) if args.only else None

    def on(name: str) -> bool:
        return checks is None or name in checks

    if on("numbers"):
        check_numbers(src, tgt, p, r)
    if on("citations"):
        check_citations(src, tgt, p, r)
    if on("references"):
        check_references(src, tgt, p, r)
    if on("structure"):
        check_structure(src, tgt, p, r)
    if on("glossary") and args.glossary:
        check_glossary(src, tgt, json.loads(args.glossary.read_text(encoding="utf-8")), args.direction, r)
    if on("typography"):
        check_typography(tgt, args.direction, p, r)
    if on("sentences"):
        check_sentences(tgt, p, r)
    r.findings.sort(key=lambda f: SEVERITY_ORDER[f["severity"]])
    return r


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--target", required=True, type=Path)
    ap.add_argument("--direction", required=True, choices=["en-tr", "tr-en"])
    ap.add_argument("--glossary", type=Path)
    ap.add_argument("--params", type=Path, help="params.json; varsayılanları ezer")
    ap.add_argument("--only", help="Virgülle ayrılmış denetim adları, örnek: numbers,citations")
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    r = run(args)
    md = to_markdown(r, args)
    if args.out_md:
        args.out_md.write_text(md + "\n", encoding="utf-8")
    if args.out_json:
        args.out_json.write_text(json.dumps({"counts": r.counts(), "stats": r.stats, "findings": r.findings}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c = r.counts()
    print(f"critical {c['critical']}, major {c['major']}, minor {c['minor']}, info {c['info']}")
    if not args.out_md:
        print(md)
    return 1 if (args.strict and c["critical"]) else 0


if __name__ == "__main__":
    sys.exit(main())
