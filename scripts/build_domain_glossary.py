#!/usr/bin/env python3
"""Alan paketindeki öneri listelerini (Markdown çizelgeleri) JSON'a dönüştürür.

Kullanım:
    python scripts/build_domain_glossary.py domains/toprak-bilimi

Girdi: <alan>/kaynak/terim_onerileri_*.md
Çıktı: <alan>/oneriler.json

Her çizelge satırı bir girdi olur. Alanlar:
    id, list, section, en_raw, en_keys, tr_raw, tr_variants, status,
    preferred_tr, evidence, note
- en_keys: kaynak metinde aranacak İngilizce anahtarlar. "A / B C" biçimi
  "A C" ve "B C" diye açılır; parantez içi açıklama atılır, kısaltma ayrı
  anahtar olur.
- preferred_tr: nottaki "Öneri: ..." ifadesi Türkçe karşılık sütununda
  geçiyorsa o biçim; durum "yerleşik" ve tek karşılık varsa o karşılık;
  aksi durumda null. Null girdide karar terim araştırmacısına kalır.
Dönüştürme kuralları satırın anlamını değiştirmez; ham sütunlar da saklanır.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trtext import tr_lower  # noqa: E402

STATUSES = {"yerleşik", "değişken", "yerleşmemiş"}


def _split_cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _expand_slash(part: str) -> list[str]:
    """'supervised / unsupervised classification' -> iki anahtar."""
    if "/" not in part:
        return [part]
    pieces = [p.strip() for p in part.split("/")]
    last = pieces[-1].split()
    if len(last) >= 2 and all(len(p.split()) == 1 for p in pieces[:-1]):
        tail = " ".join(last[1:])
        return [f"{p} {tail}" for p in pieces[:-1]] + [pieces[-1]]
    return pieces


def en_keys(raw: str) -> list[str]:
    keys: list[str] = []
    for abbr in re.findall(r"\(([A-Z][A-Za-z0-9-]{1,10})\)", raw):
        keys.append(abbr)
    text = re.sub(r"\([^)]*\)", " ", raw)
    for part in text.split(";"):
        part = " ".join(part.split())
        if not part:
            continue
        if "," in part and "/" not in part:
            # "argillic, cambic, calcic" gibi ad listeleri
            subparts = [p.strip() for p in part.split(",")]
        else:
            subparts = [part]
        for sp in subparts:
            for k in _expand_slash(sp):
                k = k.strip(" .")
                if k and k not in keys:
                    keys.append(k)
    return keys


def tr_variants(raw: str, en_raw: str = "") -> list[str]:
    """Türkçe karşılık sütununu biçimlere ayırır.

    "A / B C" biçimi yalnız İngilizce sütunda da "/" varsa "A C" ve "B C"
    diye açılır (koşut yapı). Aksi durumda "/" iki ayrı biçimi ayırır.
    Birden çok biçim varken 5 karakterden kısa parçalar atılır; bunlar
    "kalibrasyon kümesi veya seti" gibi eksiltili yazımdan kalan parçalardır.
    """
    if raw.lower().startswith(("tutarlı karşılık yok", "yerleşik türkçe karşılık yok")):
        return []
    text = re.sub(r"\([^)]*\)", " ", raw)
    out: list[str] = []
    for part in re.split(r";| veya |,", text):
        part = " ".join(part.split()).strip(" .")
        if not part or ":" in part:
            continue
        if "/" in part:
            pieces = _expand_slash(part) if "/" in en_raw else [x.strip() for x in part.split("/")]
        else:
            pieces = [part]
        for v in pieces:
            if v and v not in out:
                out.append(v)
    if len(out) > 1:
        out = [v for v in out if len(v) >= 5]
    return out


def preferred(status: str, variants: list[str], note: str, tr_raw: str) -> str | None:
    if re.search(r"Öneri:\s*(baştaki|ilk) biçim", note) and variants:
        return variants[0]
    m = re.search(r"Öneri:\s*([^.;(]+)", note)
    if m:
        cand = m.group(1).strip().strip('"').strip()
        cand = re.split(r",\s*(?:kısaltma|ilk geç)", cand)[0].strip().strip('"')
        low = tr_lower(cand)
        for v in variants:
            if tr_lower(v) == low:
                return v
        if low and low in tr_lower(tr_raw) and len(low.split()) <= 6:
            return cand
    if status == "yerleşik" and len(variants) == 1:
        return variants[0]
    return None


def pairs(status: str, en_raw: str, tr_raw: str) -> list[dict]:
    """Çok kavramlı satırda İngilizce ve Türkçe parçaları sırayla eşler.

    Yalnız güvenli durumda çalışır: durum "yerleşik", iki sütunda da ";" ile
    ayrılmış parça sayısı eşit ve 1'den büyük, hiçbir parçada "/" ya da ":" yok.
    """
    if status != "yerleşik":
        return []
    en_parts = [" ".join(re.sub(r"\([^)]*\)", " ", p).split()) for p in en_raw.split(";")]
    tr_parts = [" ".join(re.sub(r"\([^)]*\)", " ", p).split()) for p in tr_raw.split(";")]
    if len(en_parts) < 2 or len(en_parts) != len(tr_parts):
        return []
    if any("/" in p or ":" in p or "karşılık yok" in p for p in en_parts + tr_parts):
        return []
    return [{"en": e, "tr": t} for e, t in zip(en_parts, tr_parts)]


def parse_file(path: Path, list_id: str) -> list[dict]:
    entries: list[dict] = []
    section = ""
    in_table = False
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            in_table = False
            continue
        if line.startswith("| İngilizce"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        if re.match(r"^\|\s*-{3,}", line):
            continue
        cells = _split_cells(line)
        if len(cells) < 5 or cells[2] not in STATUSES:
            continue
        n += 1
        en_raw, tr_raw, status, ev_raw, note = cells[:5]
        evidence = re.findall(r"https?://[^\s<|]+", ev_raw)
        variants = tr_variants(tr_raw, en_raw)
        entries.append(
            {
                "id": f"{list_id}-{n:03d}",
                "list": list_id,
                "section": section,
                "en_raw": en_raw,
                "en_keys": en_keys(en_raw),
                "tr_raw": tr_raw,
                "tr_variants": variants,
                "status": status,
                "preferred_tr": preferred(status, variants, note, tr_raw),
                "pairs": pairs(status, en_raw, tr_raw),
                "evidence": evidence,
                "note": note,
            }
        )
    return entries


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    domain = Path(argv[1])
    src = domain / "kaynak"
    all_entries: list[dict] = []
    files = sorted(src.glob("terim_onerileri_*.md"))
    for f in files:
        list_id = f.stem.split("_")[-1]
        all_entries.extend(parse_file(f, list_id))
    out = {
        "domain": domain.name,
        "list": "oneriler",
        "source_files": [f"kaynak/{f.name}" for f in files],
        "status_note": (
            "Öneri listeleri bağlayıcı değildir. 'değişken' terimde preferred_tr "
            "kullanılır ve metin boyunca korunur; 'yerleşmemiş' terimde Türkçe ad "
            "uydurulmaz, İngilizce terim ilk geçişte bir cümleyle açıklanır."
        ),
        "entries": all_entries,
    }
    target = domain / "oneriler.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    counts: dict[str, int] = {}
    for e in all_entries:
        counts[e["list"]] = counts.get(e["list"], 0) + 1
    print(f"{target}: {len(all_entries)} girdi {counts}")
    with_pref = sum(1 for e in all_entries if e["preferred_tr"])
    print(f"preferred_tr belirlenen: {with_pref}; belirlenemeyen: {len(all_entries) - with_pref}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
