#!/usr/bin/env python3
"""Kaynak metinde geçen alan terimlerinden tohum terim sözlüğü üretir.

Kullanım:
    python scripts/seed_glossary.py --source WS/source.md --direction en-tr \
        --domain domains/toprak-bilimi --out WS/seed-glossary.json

Ne yapar:
1. Alan paketindeki bağlayıcı sözlüğü (baglayici.json) ve öneri listelerini
   (oneriler.json) okur.
2. Kaynak dildeki her terimi kaynak metinde arar (Türkçe için ek almış
   biçimler de yakalanır; sezgisel eşleşme).
3. Bulunan terimleri references/glossary-schema.md şemasında yazar.

Öncelik: bağlayıcı sözlük > öneri listesi. Bir öneri terimi, bağlayıcı bir
terimin içinde kalıyorsa (örnek: "environmental covariates" içindeki
"covariate") o eşleşme sayılmaz.
Kaynakta bir terimin yalnız kısaltması geçiyorsa girdi kısaltmanın kendisi
olur ve kısaltma korunur; tam adın çevirisi beklenmez.
Güven düzeyi: bağlayıcı = high; öneri listesinde "yerleşik" ve en az iki
kanıt bağlantısı = high; "yerleşik" ve tek kanıt ya da "değişken" = medium;
"yerleşmemiş" ya da karşılığı belirlenemeyen = low.
Bu betik web araması yapmaz. Tohum sözlükte olmayan terimleri terim
araştırmacısı ekler.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trtext import abbreviation_pattern, find_spans, normalize, split_sentences, strip_code_and_links  # noqa: E402

ABBR_RE = re.compile(r"[A-Z][A-Za-z0-9-]{1,10}")


def is_abbr(key: str) -> bool:
    return bool(ABBR_RE.fullmatch(key)) and key.upper() == key


def _context(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    line = text[start: end if end != -1 else len(text)]
    offset = 0
    for s in split_sentences(line):
        idx = line.find(s, offset)
        if idx != -1 and idx <= pos - start <= idx + len(s):
            return s[:300]
        offset = max(offset, idx)
    return line[:300]


def _spans(text: str, key: str, lang: str) -> list[tuple[int, int]]:
    if is_abbr(key):
        return [m.span() for m in abbreviation_pattern(key).finditer(text)]
    return find_spans(text, key, lang)


def _outside(spans: list[tuple[int, int]], taken: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return [s for s in spans if not any(a <= s[0] < b for a, b in taken)]


def _confidence(status: str, n_evidence: int, has_translation: bool) -> str:
    if not has_translation:
        return "low"
    if status == "bağlayıcı":
        return "high"
    if status == "yerleşik":
        return "high" if n_evidence >= 2 else "medium"
    if status == "değişken":
        return "medium"
    return "low"


def _abbr_only_term(abbr: str, spans, text, origin, sources, notes) -> dict:
    return {
        "original": abbr,
        "translation": abbr,
        "alternatives": [],
        "forbidden": [],
        "abbreviation": {"source": abbr, "target": abbr},
        "category": "abbreviation",
        "status": "kısaltma",
        "confidence": "medium",
        "origin": origin,
        "context": _context(text, spans[0][0]),
        "occurrences": len(spans),
        "sources": sources,
        "notes": "Kaynakta yalnız kısaltma geçiyor; kısaltma korunur. Kaynak belgede tanımı yoksa çeviride de eklenmez, raporda belirtilir. " + notes,
        "enforce": True,
    }


def seed(source_text: str, direction: str, domains: list[Path]) -> dict:
    src_lang, tgt_lang = direction.split("-")
    text = normalize(strip_code_and_links(source_text))
    terms: list[dict] = []
    taken: list[tuple[int, int]] = []
    global_forbidden: list[str] = []
    groups: list[dict] = []

    for domain in domains:
        bind = json.loads((domain / "baglayici.json").read_text(encoding="utf-8"))
        props_path = domain / "oneriler.json"
        props = json.loads(props_path.read_text(encoding="utf-8")) if props_path.exists() else {"entries": []}
        groups.extend(bind.get("consistency_groups", []))
        if tgt_lang == "en":
            global_forbidden.extend(g["term"] for g in bind.get("global_forbidden_en", []))
        bind_src = f"{domain.name}/{bind['source_file']} (sürüm {bind['source_version']})"

        # 1. Bağlayıcı girdiler
        for e in bind["entries"]:
            keys = [e[src_lang]] + e.get(f"{src_lang}_alternatives", [])
            full = _outside([s for k in keys for s in _spans(text, k, src_lang)], taken)
            abbr_src = e.get(f"abbr_{src_lang}") or (e.get("abbr_en") if src_lang == "tr" else None)
            abbr = _outside(_spans(text, abbr_src, src_lang), taken) if abbr_src else []
            if not full and not abbr:
                continue
            taken.extend(full + abbr)
            origin = f"domain:{domain.name}/baglayici"
            if not full:
                terms.append(_abbr_only_term(abbr_src, abbr, text, origin, [bind_src], e.get("note", "")))
                continue
            forbidden = e.get("forbidden_en", []) + e.get("forbidden_en_if_source", []) if tgt_lang == "en" else []
            abbr_tgt = e.get(f"abbr_{tgt_lang}") or e.get("abbr_en")
            terms.append(
                {
                    "original": e[src_lang],
                    "translation": e[tgt_lang],
                    "alternatives": e.get(f"{tgt_lang}_alternatives", []),
                    "forbidden": forbidden,
                    "abbreviation": {"source": abbr_src, "target": abbr_tgt} if (abbr_src or abbr_tgt) else None,
                    "category": "technical",
                    "status": "bağlayıcı",
                    "confidence": "high",
                    "origin": origin,
                    "context": _context(text, min(full)[0]),
                    "occurrences": len(full),
                    "sources": [bind_src],
                    "notes": e.get("note", ""),
                    "enforce": e.get("qa", True),
                }
            )

        # 2. Öneri listeleri
        for e in props["entries"]:
            origin = f"domain:{domain.name}/oneriler:{e['id']}"
            if e.get("pairs"):
                for p in e["pairs"]:
                    sp = _outside(_spans(text, p[src_lang], src_lang), taken)
                    if not sp:
                        continue
                    taken.extend(sp)
                    terms.append(_prop_term(e, origin, p[src_lang], p[tgt_lang], [], sp, text))
                continue

            if src_lang == "en":
                full_keys = [k for k in e["en_keys"] if not is_abbr(k)]
                abbr_keys = [k for k in e["en_keys"] if is_abbr(k)]
            else:
                full_keys = list(e["tr_variants"])
                if e.get("preferred_tr") and e["preferred_tr"] not in full_keys:
                    full_keys.insert(0, e["preferred_tr"])
                abbr_keys = [k for k in e["en_keys"] if is_abbr(k)]
            full_hits = {k: _outside(_spans(text, k, src_lang), taken) for k in full_keys}
            full_hits = {k: v for k, v in full_hits.items() if v}
            abbr_hits = {k: _outside(_spans(text, k, src_lang), taken) for k in abbr_keys}
            abbr_hits = {k: v for k, v in abbr_hits.items() if v}
            if not full_hits and not abbr_hits:
                continue
            for v in list(full_hits.values()) + list(abbr_hits.values()):
                taken.extend(v)
            if not full_hits:
                k, sp = next(iter(abbr_hits.items()))
                terms.append(_abbr_only_term(k, sp, text, origin, e["evidence"], e["note"]))
                continue
            original, sp = next(iter(full_hits.items()))
            if tgt_lang == "tr":
                translation = e.get("preferred_tr")
                alternatives = [v for v in e["tr_variants"] if v != translation]
            else:
                plain = [k for k in e["en_keys"] if not is_abbr(k)]
                translation = plain[0] if len(plain) == 1 else None
                alternatives = []
            all_spans = sorted(s for v in full_hits.values() for s in v)
            terms.append(_prop_term(e, origin, original, translation, alternatives, all_spans, text))

    meta_counts = {c: sum(1 for t in terms if t["confidence"] == c) for c in ("high", "medium", "low")}
    return {
        "metadata": {
            "source_language": src_lang,
            "target_language": tgt_lang,
            "document_type": None,
            "domain_packs": [d.name for d in domains],
            "total_terms": len(terms),
            "high_confidence": meta_counts["high"],
            "medium_confidence": meta_counts["medium"],
            "low_confidence": meta_counts["low"],
            "seed_terms": len(terms),
            "researched_terms": 0,
            "start_time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "end_time": None,
            "web_search_failures": 0,
            "global_forbidden": global_forbidden,
            "consistency_groups": groups,
        },
        "terms": terms,
    }


def _prop_term(e: dict, origin: str, original: str, translation, alternatives, spans, text) -> dict:
    status = e["status"]
    has_tr = bool(translation)
    notes = e["note"]
    if status == "yerleşmemiş":
        notes = "Yerleşmemiş terim: Türkçe ad uydurma; İngilizce terimi ilk geçişte bir cümleyle açıkla. " + notes
    elif not has_tr:
        notes = "Satır birden çok kavram ya da biçim içeriyor; karşılığı terim araştırmacısı seçer. " + notes
    return {
        "original": original,
        "translation": translation,
        "alternatives": alternatives,
        "forbidden": [],
        "abbreviation": None,
        "category": "technical",
        "status": status,
        "confidence": _confidence(status, len(e["evidence"]), has_tr),
        "origin": origin,
        "context": _context(text, spans[0][0]),
        "occurrences": len(spans),
        "sources": e["evidence"],
        "notes": notes,
        "enforce": bool(has_tr and status != "yerleşmemiş"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--direction", required=True, choices=["en-tr", "tr-en"])
    ap.add_argument("--domain", action="append", type=Path, default=[], help="Alan paketi klasörü; birden çok kez verilebilir")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    if not a.domain:
        a.domain = [Path(__file__).resolve().parent.parent / "domains" / "toprak-bilimi"]
    data = seed(a.source.read_text(encoding="utf-8"), a.direction, a.domain)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    m = data["metadata"]
    print(f"{a.out}: {m['total_terms']} terim (high {m['high_confidence']}, medium {m['medium_confidence']}, low {m['low_confidence']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
