# Denetçi bulgu biçimi

Denetçi `WS/review-feedback.md` dosyasını bu biçimde yazar. Çevirmen düzeltme aşamasında bu dosyayı okur.

## Bulgu türleri

Önem sırasıyla:

| Tür | Önem | Tanım |
|---|---|---|
| FABRICATION (uydurma) | Kritik | Çeviride kaynakta olmayan içerik: bilgi, sayı, değerlendirme, bağlantı cümlesi |
| OMISSION (eksiltme) | Kritik | Kaynaktaki içeriğin çeviride bulunmaması |
| MEANING_SHIFT (anlam kayması) | Kritik | Savın kesinlik düzeyi, olumsuzluk, nedensellik, karşılaştırma yönü, nicelik, "sırasıyla" eşlemesi, oran ile fark ayrımı değişmiş |
| NUMERIC (sayı) | Kritik | Sayı, işaret, birim, sondaki sıfır, aralık ya da eşitsizlik işareti değişmiş |
| CITATION (atıf) | Kritik | Yazar, yıl, harf eki, numara, DOI değişmiş ya da kaybolmuş; kaynakça değişmiş |
| STRUCTURE (yapı) | Kritik | Başlık, paragraf, liste, çizelge, hücre yapısı değişmiş |
| TERMINOLOGY (terim) | Büyük | Onaylı karşılık kullanılmamış; yasak biçim; aynı metinde iki biçim; terim yanlış bağlamda |
| ABBREVIATION (kısaltma) | Büyük | Kısaltma tanımsız, uydurma Türkçe kısaltma, tanım yeri kaynakla uyuşmuyor |
| REGISTER (üslup) | Küçük | Hedef dilin bilimsel üslubuna uymayan anlatım, birebir çeviri kokan yapı |
| READABILITY (okunabilirlik) | Küçük | Sınırı aşan cümle, açılmamış ad zinciri |
| TYPOGRAPHY (yazım) | Küçük | Ondalık ayırıcı, yüzde işareti, tire, atıf kısaltması, Türkçe büyük harf (Büyük: ondalık ayırıcı ve İ/I hatası) |

Önem düzeyleri: Kritik = yayımlanamaz, düzeltilmeli. Büyük = düzeltilmeli. Küçük = düzeltilmesi önerilir.

## Şablon

```markdown
## Denetim: [BELGE ADI]

**Kaynak**: [WS]/source.md
**Çeviri**: [WS]/first-pass.md
**Sözlük**: [WS]/terminology-glossary.json
**Otomatik denetim**: [WS]/qa-report-1.md
**Denetçi**: denetçi ajan ([model takma adı])
**Tarih**: [YYYY-AA-GG]

---

### Otomatik bulguların doğrulanması

| No | qa-report bulgusu | Karar | Gerekçe |
|---|---|---|---|
| 1 | NUMERIC: 0.42 eksik | DOĞRULANDI | Çeviride %0,24 yazılmış; kaynak 0.42% |
| 2 | NUMERIC: 3 fazla | REDDEDİLDİ | Kaynakta "three" yazıyla, çeviride "3"; değer aynı. Yine de yazıyla yazılmalı (bkz. küçük bulgu 2) |

### Kritik bulgular

1. [Konum: Özet, 2. cümle]
   **MEANING_SHIFT**: "denetlediğini göstermektedir"
   - Kaynak: "suggest that calcium carbonate content may control"
   - Düzeltme: "denetleyebileceğini düşündürmektedir"

### Büyük bulgular

1. [Konum: 2. Materyal ve yöntem, 1. paragraf]
   **TERMINOLOGY**: "yığın yoğunluğu"
   - Sözlük: "bulk density" -> "hacim ağırlığı" (bağlayıcı)
   - Düzeltme: "hacim ağırlığı"

### Küçük bulgular

1. [Konum: ...]
   **READABILITY**: 38 sözcüklü cümle
   - Öneri: "... kullanır [1, 3-5]. Yilmaz (2018) ..."

---

### Yapı karşılaştırma çizelgesi

| Öğe | Kaynak | Çeviri | Uyuşuyor mu? |
|---|---|---|---|
| H2 başlık sayısı | 3 | 3 | EVET |
| Çizelge 1 satır | 3 | 2 | HAYIR |
| Çizelge 1 sütun | 3 | 3 | EVET |
| Şekil numaraları | [1] | [1] | EVET |
| Ayrık denklem | 1 | 1 | EVET |
| Paragraf sayısı | 4 | 4 | EVET |

Her "HAYIR" satırı kritik bulgular bölümünde de yer alır.

---

### İstatistik

| Ölçüt | Değer |
|---|---|
| Kritik bulgu | N |
| Büyük bulgu | N |
| Küçük bulgu | N |
| Uydurma bulundu mu | evet/hayır |
| Eksiltme bulundu mu | evet/hayır |
| Anlam kayması bulundu mu | evet/hayır |
| Otomatik bulgu: doğrulanan / reddedilen | N / N |
| Terim uyumu | uyan terim / denetlenen terim (yüzde) |
| Yapı uyumu | uyuşan satır / toplam satır |
| Genel değerlendirme | geçti / düzeltmeyle geçer / geçmedi |
```

## Yazım kuralları

- Her bulguda konum, tür, çevirideki metin, kaynaktaki metin ve düzeltme bulunur.
- Bulgu yazmadan önce iki metnin tam cümlesi okunur. Bellekten bulgu yazılmaz.
- Terim uyumu yüzdesi "uyan terim sayısı / kaynakta geçen ve denetlenen terim sayısı" olarak hesaplanır. Pay ve payda ayrıca yazılır.
- Denetçi çeviriyi değiştirmez; yalnız bulgu yazar.
