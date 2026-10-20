# Çeviri raporu şablonu

Yönetici her çeviri sonunda `WS/ceviri-raporu.md` dosyasını bu şablonla yazar. Rapor, yapılan denetimi ve sonucunu yazar; "kurala uygun olarak yapıldı" gibi beyan yerine geçmez. Ulaşılamayan bilgi "ulaşılamadı" diye yazılır.

```markdown
# Çeviri raporu: [BELGE ADI]

## 1. Belge ve parametreler

- Kaynak dosya: [yol]; biçim: [docx/pdf/tex/md]
- Yön: [en-tr / tr-en]
- Belge türü: [araştırma makalesi ...]
- Hedef dergi: [ad ya da "belirtilmedi; skill varsayılanları kullanıldı"]
- Ana metin sözcük sayısı: [N]; mod: [hafif/tam/parçalı, N parça]
- params.json: [değişen parametreler ve gerekçesi]

## 2. Süreç

| Aşama | Yapan | Girdi | Çıktı |
|---|---|---|---|
| Hazırlık | yönetici | [kaynak] | source.md, structure-manifest.md |
| Tohum sözlük | seed_glossary.py | source.md | seed-glossary.json ([N] terim) |
| İlk çeviri | çevirmen ajan | ... | first-pass.md |
| Terim araştırması | terim araştırmacısı ajan | ... | glossary-research.json ([N] terim) |
| Otomatik denetim 1 | qa_checks.py | ... | qa-report-1.md |
| Denetim | denetçi ajan | ... | review-feedback.md |
| Düzeltme | çevirmen ajan | ... | final-translation.md |
| Otomatik denetim 2 | qa_checks.py | ... | qa-report-2.md |
| Son doğrulama | yönetici | ... | bu rapor |

## 3. Sonuçlar

| Ölçüt | Denetim 1 | Denetim 2 |
|---|---|---|
| Otomatik kritik aday | N | N |
| Otomatik büyük aday | N | N |
| Denetçinin doğruladığı / reddettiği aday | N / N | - |
| Denetçi kritik / büyük / küçük bulgu | N / N / N | - |
| Uygulanan / uygulanmayan bulgu | - | N / N |
| Terim uyumu (uyan / denetlenen) | N / N | N / N |

Uygulanmayan bulgular ve gerekçeleri: [liste]

## 4. Kapsam ayrımı

- **Kural tabanlı betikle denetlenenler**: sayılar, atıflar, DOI ve adresler, kaynakça, başlık, çizelge, şekil ve denklem yapısı, onaylı terimler, yasak biçimler, yazım kuralları, cümle uzunluğu.
- **Yalnız denetçi ajanın okuduğu alanlar**: anlam kayması, savın kesinlik düzeyi, uydurma ve eksiltme (paragraf düzeyinde), terimin bağlama uygunluğu, üslup.
- **Bağımsızlık sınırı**: denetçi ve çevirmen aynı model ailesindendir. Denetçi okuması ayrı bağlamda yapılan ikinci okumadır, bağımsız uzman gözlemi değildir.
- **Yöneticinin rastgele örneklemi**: [N] paragraf, tohum [SEED]; sonuç: [uyuşmazlık sayısı ve türü].

## 5. Çözülmemiş noktalar

- Kaynakta belirsiz yerler: [konum ve kaynak metin]
- Kaynakta tanımsız kısaltmalar: [liste]
- Kullanıcı kararı gereken terimler (bağlayıcı sözlükle çelişen öneri, düşük güvenli terim): [liste]
- Şekil içindeki çevrilmemiş metin: [şekil numarası ve metin]
- PDF dönüşümünden kaynaklanan riskler ve elle düzeltilen yerler: [liste ya da "yok"]

## 6. Büyük dil modeli kullanım kaydı

Çeviri bir yayında kullanılacaksa dergi politikası büyük dil modeli kullanımının beyanını isteyebilir. Aşağıdaki kayıt yöntem bölümü ya da beyan için ham bilgidir.

| Alan | Değer |
|---|---|
| Araç | Claude Code, skill: bilimsel-ceviri-tr-en (depo commit: [hash]) |
| Yönetici modeli | [get_session ya da oturum bilgisinden; yoksa "ulaşılamadı"] |
| Alt ajan modelleri | çevirmen: [takma ad ve sürüm]; terim araştırmacısı: [...]; denetçi: [...] |
| Erişim tarihi | [YYYY-AA-GG] |
| Üretim ayarları (sıcaklık vb.) | ulaşılamadı (Claude Code bu ayarları kullanıcıya göstermez) |
| İstem metni | SKILL.md içindeki çevirmen, terim araştırmacısı ve denetçi istemleri (commit [hash]) |
| Tekrar sayısı | 1 çeviri + [N] düzeltme turu |
| Birleştirme kuralı | Tek çeviri; denetçi bulguları çevirmen tarafından uygulandı; birden çok çeviri adayı birleştirilmedi |
| Bağımsız sınama | Kural tabanlı betik (qa_checks.py); insan uzman okuması: [yapıldı/yapılmadı] |
```

## Doldurma kuralları

- Sayılar `qa-report-*.json` ve `review-feedback.md` dosyalarından alınır; bellekten yazılmaz.
- Model adı ve sürümü oturum bilgisinden alınır. Alt ajanın sürümü bilinmiyorsa takma ad (sonnet, opus) yazılır ve sürüm "ulaşılamadı" olarak kaydedilir.
- "Yapıldı" yazılan her denetimin çıktısı çalışma klasöründe bulunur.
