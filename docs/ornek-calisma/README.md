# Örnek çalışma: uçtan uca sınama

Bu klasör, skill'in bütün akışının (tohum sözlük, paralel çevirmen ve terim araştırmacısı, sözlük birleştirme, otomatik denetim, denetçi, düzeltme, son denetim) sentetik bir kaynak üzerinde bir kez çalıştırılmasının ham çıktısıdır. Kaynak metin `tests/fixtures/en_source.md` dosyasıdır; gerçek bir makale değildir.

Dosyalardaki mutlak yollar okunabilirlik için kısaltıldı: `WS` çalışma klasörü, `SKILL_DIR` bu depo, `ORNEK` çalıştırmanın üst klasörüdür. Bunun dışında ajanların yazdığı dosyalar değiştirilmedi; yazım hataları da olduğu gibi duruyor.

| Dosya | Yazan |
|---|---|
| source.md, structure-manifest.md, params.json | prepare_source.py |
| seed-glossary.json | seed_glossary.py |
| first-pass.md, structure-report.md, final-translation.md | çevirmen ajan |
| glossary-research.json | terim araştırmacısı ajan |
| terminology-glossary.json | merge_glossaries.py |
| qa-report-1.md, qa-report-2.md | qa_checks.py |
| review-feedback.md | denetçi ajan |
| ceviri-raporu.md | yönetici |

`glossary-research.json` içindeki kaynak adresleri terim araştırmacısının arama sonuçlarında gördüğü adreslerdir; çalıştırma ortamı sayfa açmaya izin vermediği için sayfalar açılmadı. Bu dosya doğrulanmış bir sözlük değildir ve alan paketine eklenmedi.
