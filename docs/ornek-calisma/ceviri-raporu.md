# Çeviri raporu: sentetik sınama makalesi (en-tr)

Bu rapor `references/ceviri-raporu-sablonu.md` şablonuyla yazıldı. Çalıştırmanın amacı skill'in ajan istemlerini ve dosya sözleşmelerini uçtan uca sınamaktır. Kaynak metin sentetiktir (`tests/fixtures/en_source.md`).

## 1. Belge ve parametreler

- Kaynak dosya: `ORNEK/ornek-makale.md` (`tests/fixtures/en_source.md` kopyası); biçim: md
- Yön: en-tr
- Belge türü: araştırma makalesi biçiminde sentetik sınama metni
- Hedef dergi: belirtilmedi; skill varsayılanları kullanıldı
- Ana metin sözcük sayısı: 168. Hafif mod eşiğinin (300) altında olduğu halde, akışı sınamak için bilerek tam mod çalıştırıldı.
- params.json: varsayılanlar değiştirilmedi (ondalık virgül, yüzde işareti önde, "ve ark.", "Çizelge", "Şekil", kaynakça çevrilmez, tire yasağı, cümle sınırı 30)

## 2. Süreç

| Aşama | Yapan | Çıktı |
|---|---|---|
| Hazırlık | yönetici, `prepare_source.py` | source.md, structure-manifest.md, params.json |
| Tohum sözlük | `seed_glossary.py` | seed-glossary.json: 12 terim (9 bağlayıcı, 2 öneri listesi, 1 kısaltma) |
| İlk çeviri | çevirmen ajan (sonnet) | first-pass.md, structure-report.md |
| Terim araştırması | terim araştırmacısı ajan (sonnet), çevirmenle paralel | glossary-research.json: 10 yeni terim |
| Sözlük birleştirme | `merge_glossaries.py` | terminology-glossary.json: 22 terim; çelişki 0 (aşağıdaki nota bakınız) |
| Otomatik denetim 1 | `qa_checks.py` | qa-report-1.md |
| Denetim | denetçi ajan (opus) | review-feedback.md |
| Düzeltme | çevirmen ajan (sonnet) | final-translation.md |
| Otomatik denetim 2 | `qa_checks.py` | qa-report-2.md |
| Çıktı | `export_docx.py --pdf` | .docx ve .pdf (depoya eklenmedi) |
| Son doğrulama | yönetici | bu rapor |

## 3. Sonuçlar

| Ölçüt | Denetim 1 (first-pass.md) | Denetim 2 (final-translation.md) |
|---|---|---|
| Otomatik kritik aday | 0 | 0 |
| Otomatik büyük aday | 2 (çözülmemiş çevirmen işareti) | 0 |
| Otomatik küçük aday | 1 (31 sözcüklü cümle) | 0 |
| Denetçinin doğruladığı / reddettiği aday | 2 / 1 | - |
| Denetçi kritik / büyük / küçük bulgu | 0 / 2 / 0 | - |
| Uygulanan / uygulanmayan bulgu | - | 2 / 0 |
| Terim uyumu, otomatik (uyan / denetlenen, enforce=true) | 16 / 16 | 16 / 16 |
| Sayılar (kaynak / hedef, eksik, fazla) | 31 / 31, 0, 0 | 31 / 31, 0, 0 |

Denetçinin iki büyük bulgusu:

1. Özet: "R2 [?tanımsız kısaltma: R2?]" işareti metinde kalmıştı. Düzeltme: işaret kaldırıldı; tanım eklenmedi.
2. Yöntem: "10 kat [?terim: folds?] kullanılmış" ifadesi "on kez" diye de okunabiliyordu. Düzeltme: "10 katlı çapraz doğrulama kullanılmış".

`diff first-pass.md final-translation.md` yalnız bu iki satırı gösterdi.

Birleştirme hatası ve düzeltmesi: ilk birleştirmede `merge_glossaries.py`, terim araştırmacısının "prediction -> tahmin" kararını atıp tohum sözlükteki karşılığı boş girdiyi tuttu. Araştırmacı girdinin `origin` alanını tohumdaki gibi bıraktığı için iki girdi eşit önceliğe düşmüş, ilk gelen kazanmıştı. Kural düzeltildi (karşılığı dolu girdi boş girdiye, eşitlikte araştırma dosyası tohum dosyasına üstün gelir) ve bir regresyon sınaması eklendi. Sözlük yeniden birleştirildi; iki otomatik denetim yeni sözlükle yeniden çalıştırıldı ve yukarıdaki çizelge yeni sonuçları gösterir (önceki birleştirmeyle sonuçlar 15 / 15 idi; bulgu sayıları değişmedi). Denetçi ajan önceki birleştirilmiş sözlüğü okudu; o sürümde "prediction" girdisinin karşılığı boştu. Denetçi `review-feedback.md` içinde 22 terimin 21'ini uyumlu saydı ve uymayan tek terim olarak "folds" yazdı.

## 4. Kapsam ayrımı

- Kural tabanlı betikle denetlenenler: sayılar, atıflar, DOI ve adresler, kaynakça, başlık, çizelge, şekil ve denklem yapısı, onaylı terimler, yasak biçimler, yazım kuralları, çevirmen işaretleri, cümle uzunluğu.
- Yalnız denetçi ajanın okuduğu alanlar: anlam kayması ve savın kesinlik düzeyi ("suggest" -> "düşündürmektedir", "may control" -> "denetleyebileceğini" korunmuş bulundu), uydurma ve eksiltme, terimin bağlama uygunluğu, üslup.
- Bağımsızlık sınırı: denetçi ve çevirmen aynı model ailesindendir. Denetçi okuması ayrı bağlamda yapılan ikinci okumadır, bağımsız uzman gözlemi değildir.
- Yöneticinin rastgele örneklemi: ana metinde 4 paragraf var; `random.seed(20261020)` ile 5 paragraf istendiğinde 4 paragrafın tamamı seçildi. Dört paragraf ve çizelge kaynakla cümle cümle karşılaştırıldı; uyuşmazlık bulunmadı.

## 5. Çözülmemiş noktalar

- Kaynakta tanımsız kısaltma: R2. Hangi ölçünün hesaplandığı (korelasyon katsayısının karesi mi, model etkinliği ölçüsü mü) yazara sorulmalı.
- Kaynakta belirsiz ilişki: "10 folds" ile "25% of the data were held out" arasındaki ilişki yazılmamış. Çeviri bu ilişkiyi eklemedi.
- Düşük güvenli terimler (6): folds -> kat, held out (yerleşmemiş; çeviride "ayrı tutulmuştur"), summary statistics -> özet istatistikler, standard deviation -> standart sapma, samples -> örnek, cmol(+) kg-1 (birim, değişmedi). Terim araştırmacısı bu ortamda hiçbir sayfayı açamadı (WebFetch ve doğrudan bağlantı engellendi; yalnız web araması çalıştı). Bu yüzden yeni terimlerin hiçbiri "high" güvene çıkarılmadı. `metadata.web_search_failures` = 4.
- Şekil içindeki metin: Şekil 1 metinde anılıyor; kaynakta görsel yok.
- PDF dönüşümü: kullanılmadı.

## 6. Büyük dil modeli kullanım kaydı

| Alan | Değer |
|---|---|
| Araç | Claude Code, skill: bilimsel-ceviri-tr-en (bu raporla aynı commit) |
| Yönetici modeli | claude-opus-5-5 (oturum bilgisi: session_context.model ve last_served_model) |
| Alt ajan modelleri | çevirmen: sonnet; terim araştırmacısı: sonnet; denetçi: opus. Takma ada karşılık gelen sürüm ulaşılamadı |
| Erişim tarihi | 2026-10-20 |
| Üretim ayarları (sıcaklık vb.) | ulaşılamadı |
| İstem metni | SKILL.md içindeki çevirmen, terim araştırmacısı ve denetçi istemleri; yer tutucular betikle dolduruldu, kalan yer tutucu yok |
| Tekrar sayısı | 1 çeviri + 1 düzeltme turu |
| Birleştirme kuralı | Tek çeviri; denetçi bulguları çevirmen tarafından uygulandı |
| Bağımsız sınama | qa_checks.py; insan uzman okuması yapılmadı |
