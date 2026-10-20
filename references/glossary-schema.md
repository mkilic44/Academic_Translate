# Terim sözlüğü JSON şeması

Üç dosya bu şemayı kullanır: `seed-glossary.json` (betik), `glossary-research.json` (terim araştırmacısı) ve `terminology-glossary.json` (yönetici birleştirir). `qa_checks.py --glossary` son dosyayı okur.

## Şema

```json
{
  "metadata": {
    "source_language": "string: 'en' ya da 'tr'",
    "target_language": "string: 'tr' ya da 'en'",
    "document_type": "string: örnek: 'araştırma makalesi', 'derleme', 'tez bölümü'",
    "domain_packs": ["string: kullanılan alan paketleri, örnek: 'toprak-bilimi'"],
    "total_terms": "number",
    "high_confidence": "number",
    "medium_confidence": "number",
    "low_confidence": "number",
    "seed_terms": "number: alan paketinden gelen terim sayısı",
    "researched_terms": "number: terim araştırmacısının eklediği terim sayısı",
    "start_time": "string: ISO 8601",
    "end_time": "string: ISO 8601",
    "web_search_failures": "number",
    "global_forbidden": ["string: hedef metinde hiçbir bağlamda kullanılmayacak sözcükler"],
    "consistency_groups": ["object: aynı metinde birlikte kullanılmayacak biçim grupları"]
  },
  "terms": [
    {
      "original": "string: kaynak metindeki terim",
      "translation": "string: onaylı karşılık; karar verilemediyse null",
      "alternatives": ["string: hedefte kabul edilen öteki biçimler"],
      "forbidden": ["string: hedefte kullanılmayacak biçimler"],
      "abbreviation": {"source": "string: kaynaktaki kısaltma", "target": "string: hedefteki kısaltma"},
      "category": "string: technical, method, statistic, abbreviation, taxon, organization, person, place, instrument, software, unit",
      "status": "string: bağlayıcı, yerleşik, değişken, yerleşmemiş, kısaltma, araştırıldı",
      "confidence": "string: high, medium, low",
      "origin": "string: 'domain:toprak-bilimi/baglayici', 'domain:toprak-bilimi/oneriler:A-001' ya da 'research'",
      "context": "string: terimin kaynakta geçtiği ilk cümle",
      "occurrences": "number",
      "sources": ["string: kanıt adresleri ya da dosya adı"],
      "notes": "string: seçim gerekçesi, bağlam ayrımı, ilk geçişte verilecek açıklama",
      "enforce": "boolean: qa_checks.py bu karşılığı hedefte arasın mı"
    }
  ]
}
```

## Durum değerleri

| status | Anlamı | Çevirmen ne yapar |
|---|---|---|
| bağlayıcı | Kullanıcının bağlayıcı sözlüğünden | Yakın anlamlısını kullanmaz |
| yerleşik | Türkçe literatürde tek baskın biçim | Önerilen biçimi kullanır |
| değişken | Birden çok yaygın biçim var; biri önerildi | Önerilen biçimi kullanır ve metin boyunca korur |
| yerleşmemiş | Tutarlı Türkçe karşılık yok | Türkçe ad uydurmaz; İngilizce terimi ilk geçişte bir cümleyle açıklar |
| kısaltma | Kaynakta yalnız kısaltma geçiyor | Kısaltmayı korur |
| araştırıldı | Terim araştırmacısının kaynaklı kararı | Önerilen biçimi kullanır |

## Güven düzeyi

| confidence | Ölçüt |
|---|---|
| high | Bağlayıcı sözlük; ya da aynı biçimi kullanan, farklı yazar gruplarından en az iki hakemli yayın |
| medium | Tek hakemli yayın; ya da "değişken" terimde öneri |
| low | Kanıt yok, arama başarısız ya da karar verilemedi |

Birbirini kopyalayan sayfalar iki kaynak sayılmaz. Sözlük sitelerindeki makine çevirisi kanıt değildir.

## `enforce` alanı

`qa_checks.py`, `enforce: true` ve `translation` dolu girdiler için şunu denetler: kaynak terim kaynak metinde geçiyorsa, `translation` ya da `alternatives` biçimlerinden biri hedef metinde geçmeli. `forbidden` biçimleri hedefte geçmemeli. Kısa ve çok anlamlı terimlerde (kil, kum, eşik, range) yanlış alarmı önlemek için `enforce: false` yazılır; bu terimleri denetçi bağlama bakarak okur.

## Örnek

```json
{
  "metadata": {
    "source_language": "en",
    "target_language": "tr",
    "document_type": "araştırma makalesi",
    "domain_packs": ["toprak-bilimi"],
    "total_terms": 2,
    "high_confidence": 1,
    "medium_confidence": 1,
    "low_confidence": 0,
    "seed_terms": 1,
    "researched_terms": 1,
    "start_time": "2026-10-20T07:00:00+00:00",
    "end_time": "2026-10-20T07:12:00+00:00",
    "web_search_failures": 0,
    "global_forbidden": [],
    "consistency_groups": []
  },
  "terms": [
    {
      "original": "bulk density",
      "translation": "hacim ağırlığı",
      "alternatives": [],
      "forbidden": [],
      "abbreviation": null,
      "category": "technical",
      "status": "bağlayıcı",
      "confidence": "high",
      "origin": "domain:toprak-bilimi/baglayici",
      "context": "Bulk density was 1.35 g cm-3 on average.",
      "occurrences": 2,
      "sources": ["toprak-bilimi/kaynak/sozluk.md (sürüm 1.2)"],
      "notes": "",
      "enforce": true
    },
    {
      "original": "random forest",
      "translation": "rastgele orman",
      "alternatives": ["rassal orman"],
      "forbidden": [],
      "abbreviation": {"source": "RF", "target": "RF"},
      "category": "method",
      "status": "değişken",
      "confidence": "medium",
      "origin": "domain:toprak-bilimi/oneriler:A-039",
      "context": "Random forest predicted SOC with a root mean squared error (RMSE) of 0.42%.",
      "occurrences": 1,
      "sources": ["https://doi.org/10.29128/geomatik.476668"],
      "notes": "Türkçe kısaltma RO kullanılmaz.",
      "enforce": true
    }
  ]
}
```

Örnekteki zaman değerleri ve sayılar gösterim içindir.
