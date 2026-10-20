#!/usr/bin/env python3
"""Tohum sözlüğü ile terim araştırmacısının sözlüğünü birleştirir (Aşama 1.5).

Kullanım:
    python scripts/merge_glossaries.py WS/seed-glossary.json WS/glossary-research.json [...] \
        --out WS/terminology-glossary.json

Kurallar:
- Girdiler `original` alanına göre (büyük-küçük harf duyarsız) eşlenir.
- Öncelik: status "bağlayıcı" > araştırmacının kaynaklı kararı (status "araştırıldı"
  ya da alan paketi dışından gelen, karşılığı dolu girdi) > alan paketinden gelen,
  karşılığı dolu girdi > karşılığı boş girdi. Eşit öncelikte sonra verilen dosya
  kazanır; bu yüzden araştırma dosyası tohum dosyasından sonra verilir.
- status "bağlayıcı-bağlamlı" girdi (örnek: eşik = sill, yalnız yarı-variogram) bağlayıcı
  sayılmaz. Yönetici, bağlam bu belgede yoksa status "bağlam-dışı" bir girdiyle onu ezer.
- Araştırmacı bağlayıcı bir girdiye farklı karşılık önerirse bağlayıcı girdi kalır;
  öneri metadata.conflicts listesine yazılır. Bu liste çeviri raporunda
  "kullanıcı kararı gerekir" diye verilir.
- Metadata sayıları yeniden hesaplanır; global_forbidden ve consistency_groups birleştirilir.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def rank(t: dict) -> int:
    """Küçük değer öncelikli. Eşitlikte sonra verilen dosyanın girdisi kazanır."""
    if t.get("status") == "bağlayıcı":
        return 0
    if t.get("status") == "bağlam-dışı":
        # Yönetici kararı: bağlama bağlı bir eşleme bu belgede uygulanmaz.
        return 0
    if not t.get("translation"):
        return 4
    origin = str(t.get("origin", ""))
    if t.get("status") == "araştırıldı" or not origin.startswith("domain:"):
        return 1
    return 2


def merge(glossaries: list[dict]) -> dict:
    by_key: dict[str, dict] = {}
    conflicts: list[dict] = []
    forbidden: list[str] = []
    groups: list[dict] = []
    meta0 = glossaries[0].get("metadata", {})
    failures = 0
    for g in glossaries:
        m = g.get("metadata", {})
        failures += int(m.get("web_search_failures") or 0)
        for f in m.get("global_forbidden", []):
            if f not in forbidden:
                forbidden.append(f)
        for grp in m.get("consistency_groups", []):
            if grp not in groups:
                groups.append(grp)
        for t in g.get("terms", []):
            key = str(t.get("original", "")).strip().lower()
            if not key:
                continue
            cur = by_key.get(key)
            if cur is None:
                by_key[key] = t
                continue
            if cur.get("status") == "bağlayıcı" and t.get("translation") and t.get("translation") != cur.get("translation") \
                    and t.get("status") != "bağlam-dışı":
                conflicts.append({"original": t["original"], "binding": cur.get("translation"), "proposed": t.get("translation"),
                                  "notes": t.get("notes", "")})
                continue
            if rank(t) <= rank(cur):
                by_key[key] = t
    terms = list(by_key.values())
    seed_n = sum(1 for t in terms if str(t.get("origin", "")).startswith("domain:"))
    return {
        "metadata": {
            "source_language": meta0.get("source_language"),
            "target_language": meta0.get("target_language"),
            "document_type": next((g["metadata"].get("document_type") for g in glossaries if g.get("metadata", {}).get("document_type")), None),
            "domain_packs": meta0.get("domain_packs", []),
            "total_terms": len(terms),
            "high_confidence": sum(1 for t in terms if t.get("confidence") == "high"),
            "medium_confidence": sum(1 for t in terms if t.get("confidence") == "medium"),
            "low_confidence": sum(1 for t in terms if t.get("confidence") == "low"),
            "seed_terms": seed_n,
            "researched_terms": len(terms) - seed_n,
            "start_time": meta0.get("start_time"),
            "end_time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "web_search_failures": failures,
            "global_forbidden": forbidden,
            "consistency_groups": groups,
            "conflicts": conflicts,
        },
        "terms": terms,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    data = merge([json.loads(p.read_text(encoding="utf-8")) for p in a.inputs])
    a.out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    m = data["metadata"]
    print(f"{a.out}: {m['total_terms']} terim (high {m['high_confidence']}, medium {m['medium_confidence']}, low {m['low_confidence']}); "
          f"çelişki {len(m['conflicts'])}")
    for c in m["conflicts"]:
        print(f"ÇELİŞKİ: '{c['original']}' bağlayıcı '{c['binding']}', önerilen '{c['proposed']}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
