---
name: bilimsel-ceviri-tr-en
description: "Türkçe ile İngilizce arasında, iki yönde, bilimsel araştırma makalesi çevirisi için çok ajanlı iş akışı. Alan sözlüğüyle tohumlanan terim sözlüğü, yapı korumalı çeviri, kural tabanlı otomatik denetim (sayı ve ondalık ayırıcı, atıf, DOI, çizelge, denklem, terim, yazım), ayrı bağlamda denetçi okuması, düzeltme ve .docx/.pdf çıktı üretir. Makale, özet, tez bölümü, proje metni ya da hakem yanıtı çevirisinde kullan. Tetikleyiciler: 'makaleyi çevir', 'bilimsel çeviri', 'özeti İngilizceye çevir', 'Türkçeye çevir', 'çeviriyi denetle', 'translate this paper into Turkish', 'translate this manuscript into English'. Toprak bilimi alan paketiyle gelir; başka alan paketi eklenebilir."
---

# Bilimsel çeviri: Türkçe ve İngilizce

Bu skill, bilimsel bir metni Türkçeden İngilizceye ya da İngilizceden Türkçeye çevirir. Çeviriyi tek geçişle bitirmez. Terimleri önce sabitler, çeviriyi kural tabanlı betiklerle ve ayrı bir denetçi okumasıyla sınar, bulguları düzelttirir ve ne yapıldığını raporlar.

Kaynak: [senshinji/claude-translation-skill](https://github.com/senshinji/claude-translation-skill) (MIT). Neyin alındığı ve neyin değiştirildiği [docs/tersine-muhendislik-raporu.md](docs/tersine-muhendislik-raporu.md) dosyasındadır.

## Ne zaman hangi mod

| Durum | Mod | Ne çalışır |
|---|---|---|
| 300 sözcükten kısa metin (özet, başlık, birkaç cümle) | Hafif | Yönetici tek başına çevirir; tohum sözlük ve `qa_checks.py` çalışır; denetçi ajan yoktur |
| 300 ile 6000 sözcük arası | Tam | Çevirmen + terim araştırmacısı paralel; sonra otomatik denetim, denetçi, düzeltme |
| 6000 sözcükten uzun | Parçalı | Parça başına bir çevirmen; tek terim araştırmacısı, tek denetçi, tek düzeltici |

Kullanıcı yalnız terim ya da tek cümle sorarsa bu akışı başlatma. Bağlayıcı sözlüğe bak ve doğrudan yanıt ver.

## Mimari

```
Kullanıcı: "Bu makaleyi Türkçeye çevir"
        |
Yönetici (bu oturum)
  Aşama 0: kaynağı oku, parametreleri belirle,
           prepare_source.py -> source.md, structure-manifest.md, params.json
           seed_glossary.py  -> seed-glossary.json
        |
  +-----+---------------------------+
  |                                 |
Çevirmen(ler)                Terim araştırmacısı
Aşama 1A: ilk çeviri         Aşama 1B: tohum sözlükte olmayan
(tohum sözlükle)             terimleri kaynakla sabitler
  |                                 |
  +-----------+---------------------+
              |
  Aşama 1.5: yönetici sözlüğü birleştirir -> terminology-glossary.json
  Aşama 2:   qa_checks.py -> qa-report.md ; denetçi -> review-feedback.md
  Aşama 3:   çevirmen düzeltir -> final-translation.md ; qa_checks.py yeniden
  Aşama 4:   yönetici doğrular -> çeviri raporu + .md + .docx (+ .pdf)
```

Roller ve dosya sahipliği:

| Rol | Önerilen model | Yazdığı dosya |
|---|---|---|
| Yönetici | bu oturum | params.json, structure-manifest.md (elle tamamlanan bölüm), terminology-glossary.json, qa-report*.md, ceviri-raporu.md, çıktı dosyaları |
| Çevirmen | sonnet | first-pass.md ya da first-pass-chunk-N.md, structure-report.md, final-translation.md |
| Terim araştırmacısı | sonnet | glossary-research.json |
| Denetçi | opus (erişilebilen en güçlü model) | review-feedback.md |

Hiçbir ajan başkasının dosyasını değiştirmez.

Bağımsızlık sınırı: denetçi ve çevirmen aynı model ailesindendir. Denetçinin okuması ayrı bağlamda yapılan ikinci okumadır, bağımsız uzman gözlemi değildir. Bağımsız denetim yalnız kural tabanlı betiklerdir ve yalnız kapsadıkları alanlarda geçerlidir. Çeviri raporu bu ayrımı açıkça yazar.

## Kurulum ön koşulları

- Python 3.9 ya da üstü. Betikler yalnız standart kitaplığı kullanır.
- pandoc: .docx, .odt, .tex, .html kaynak ve .docx çıktı için.
- İsteğe bağlı: python-docx (çıktı biçemi), pdftotext ya da PyMuPDF (PDF kaynak), LibreOffice (PDF çıktı).
- Alt ajanlar `Agent` aracıyla açılır. Agent Teams (`TeamCreate`, `SendMessage`) etkinse aynı akış takım olarak da yürütülebilir; dosya sözleşmeleri değişmez.

Aşağıda `SKILL_DIR` bu dosyanın bulunduğu klasördür. Claude Code skill'i yüklerken bu klasörü "Base directory for this skill" satırında verir; alt ajan istemlerine bu mutlak yol yazılır.

---

## Aşama 0: Yönetici hazırlığı

### 0.1 Kaynağı gerçekten oku

Kaynağın tamamını oku. Özet, arama parçası ya da önceki bir okuma yerine geçmez. Şunları belirle:

- Yön: `en-tr` ya da `tr-en`.
- Belge türü: araştırma makalesi, derleme, kısa bildiri, tez bölümü, proje metni, hakem yanıtı.
- Alan ve alan paketi: şimdilik `domains/toprak-bilimi`.
- Hedef dergi ya da kurum. Biliniyorsa yazım kurallarını oku; dergi kuralı bu skill'in varsayılanlarından önce gelir.

### 0.2 Kaynağı hazırla

```bash
python "$SKILL_DIR/scripts/prepare_source.py" prepare MAKALE.docx --direction en-tr
```

Betik `MAKALE` dosyasının yanına `ceviri-MAKALE/` çalışma klasörü (WS) açar. İçine `original.*`, `source.md`, `structure-manifest.md` ve `params.json` yazar. Metin 6000 sözcüğü aşarsa `chunks/chunk-N.md`, `chunk-manifest.md` ve `references.md` de oluşur.

Kaynak biçimi kuralları:

- .docx, .odt, .tex en iyi kaynaktır. Çizelge ve başlık yapısı korunur.
- PDF yalnız başka kaynak yoksa kullanılır. Başlık düzeyleri kaybolur, çizelgeler düz metne döner, Word denklemleri tamamen düşebilir, üst simgeler düzleşir (cm-3 ile cm3 karışır), iki sütunlu düzende okuma sırası bozulabilir. Bu skill'in sınamasında DOCX'ten üretilen bir PDF'te başlıklar, çizelge yapısı ve denklem kayboldu. PDF kullanıldıysa başlıkları, her çizelgeyi ve denklemi PDF sayfasıyla karşılaştır ve `source.md` dosyasında yeniden kur. Bunu rapora yaz.
- LaTeX kaynağı varsa komutlar, `\cite{}` anahtarları ve denklem ortamları olduğu gibi kalır; yalnız metin çevrilir.

### 0.2b Word kaynağında biçimi koruyan yol (çıktı .docx isteniyorsa önerilir)

Markdown yolu şekil, Word denklemi, çizelge biçimi ve sayfa düzenini kaybeder. Kaynak .docx ise ve çıktı .docx isteniyorsa çeviri özgün paketin içine yazılır:

```bash
python "$DOCX_SKILL/scripts/merge_runs.py" MAKALE.docx -o WS/kaynak_merged.docx   # docx skill'i varsa
python "$SKILL_DIR/scripts/docx_segments.py" extract WS/kaynak_merged.docx --out WS/seg
python "$SKILL_DIR/scripts/docx_segments.py" render WS/kaynak_merged.docx --out WS/source.md
```

`WS/seg/source.txt` her Word paragrafını tek satır yapar: `[[p0042|biçem]] metin`. İtalik, alt ve üst simge `<i>`, `<sub>`, `<sup>` etiketiyle; denklem, görsel ve bağlantı `{M1}`, `{IMG1}`, `{H1}` yer tutucusuyla gösterilir. Çevirmen satır sayısını, etiketleri ve yer tutucuları korur ve çıktısını `docx_segments.py check` ile denetler. Bitince:

```bash
python "$SKILL_DIR/scripts/docx_segments.py" apply WS/kaynak_merged.docx --segments WS/seg \
  --translations WS/ceviri.txt --out MAKALE.en.docx --lang en-GB --math-map WS/notation.json
python "$SKILL_DIR/scripts/docx_segments.py" render MAKALE.en.docx --out WS/hedef.md   # qa_checks.py girdisi
```

`--math-map` denklem içindeki Türkçe alt simgeleri değiştirir (örnek: `{"gece": "night"}`); aynı eşleme çevirmenlere notasyon çizelgesi olarak verilir. Görselin içindeki yazı çevrilmez; yönetici şekilleri açıp okur. Şekiller hedef dilde ise içlerindeki terimler proje sözlüğüne "yazar-şekil" olarak girer ve metin onlarla tutarlı çevrilir.

**Kaynak metindeki hatalar.** Çeviri sırasında bulunan kaynak sorunu (tutarsız sayı, eksik çizelge başlığı, aynı birime birden çok ad, kaynakça biçimi) yazara bildirilir. Yazar düzeltmeyi istediğinde düzeltme Türkçe belgeye izlenen değişiklikle yazılır; böylece yazar her değişikliği görüp kabul ya da ret edebilir:

```bash
python "$SKILL_DIR/scripts/docx_tracked.py" apply MAKALE.docx --segments WS/seg/segments.json \
  --edits WS/duzeltmeler.json --out MAKALE.izlenen.docx --author Claude
python "$SKILL_DIR/scripts/docx_tracked.py" accept MAKALE.izlenen.docx --out MAKALE.duzeltilmis.docx
```

İşlemler: `replace` (yalnız farklı sözcükler izlenir), `insert_paragraph`, `format_paragraph`, `run_size`, `italic`. Her eski ifade paragrafta tam bir kez geçmelidir; geçmezse betik durur. Kabul edilmiş temiz belge yeniden `extract` edilir ve İngilizce çeviri bu tabana yazılır. Paragraf eklenirse kimlikler kayar; bu yüzden düzeltme çeviriden önce yapılır ya da kimlikler yeniden eşlenir. Anlamı yoruma dayanan düzeltme (belirsiz ifadenin açılması) raporda "yorumla düzeltildi" diye ayrı gösterilir.

### 0.3 Parametreleri belirle

`WS/params.json` yöne göre varsayılanlarla gelir. Hedef dergi kuralı farklıysa dosyayı düzenle.

| Parametre | en-tr varsayılanı | tr-en varsayılanı | Not |
|---|---|---|---|
| source_decimal / target_decimal | "." / "," | "," / "." | Türkçe gelenek: ondalık virgül, binlik nokta (birincil kaynakla doğrulanmadı; bkz. kurallar dosyası, bölüm 1). Dergi nokta istiyorsa değiştir |
| target_percent | "prefix" (%25) | "suffix" (25%) | |
| etal_target | "ve ark." | "et al." | Dergiye göre "vd." olabilir |
| table_label_target / figure_label_target | "Çizelge" / "Şekil" | "Table" / "Figure" | Bazı dergiler "Tablo" ister |
| translate_references | false | false | Kaynakça girdileri çevrilmez |
| forbid_dashes | true | true | U+2013, U+2014, U+2212 yerine kısa çizgi |
| max_sentence_words | 30 | 35 | Okunabilirlik sınırı |

Kullanıcıya yalnız bilimsel anlamı etkileyen eksik bilgiyi sor: yön belirsizse ya da kaynakta okunamayan kısım varsa. Dergi bilinmiyorsa varsayılanları kullan ve raporda belirt.

Ayrıntılı yazım kuralları: [references/bilimsel-ceviri-kurallari.md](references/bilimsel-ceviri-kurallari.md).

### 0.4 Tohum sözlüğü üret

```bash
python "$SKILL_DIR/scripts/seed_glossary.py" --source WS/source.md --direction en-tr \
  --domain "$SKILL_DIR/domains/toprak-bilimi" --out WS/seed-glossary.json
```

Betik alan paketindeki bağlayıcı sözlüğü ve öneri listelerini kaynak metinde arar. Bulduğu terimleri onaylı karşılıklarıyla yazar. Web araması yapmaz. Şema: [references/glossary-schema.md](references/glossary-schema.md). Alan paketi: [domains/toprak-bilimi/README.md](domains/toprak-bilimi/README.md).

### 0.5 Yapı envanterini tamamla

`structure-manifest.md` sayılarını betik üretir. Yönetici şu bölümü elle doldurur:

- Bir hücrede birden çok madde taşıyan çizelge hücreleri.
- Şekil içindeki metin. Görsel çevrilmez; şekil içi metin raporda ayrı listelenir.
- Dipnotlar, ek materyal, kutu metinleri.

---

## Aşama 1: Paralel çalışma

Tam modda çevirmeni ve terim araştırmacısını aynı mesajda iki `Agent` çağrısıyla başlat. Parçalı modda her parça için bir çevirmen aç. Yer tutucuları doldur: [WS], [YÖN], [KAYNAK_DİL], [HEDEF_DİL], [SKILL_DIR], [AŞAMA]. Yer tutucusu kalmış istem gönderilmez.

### Çevirmen istemi

```
Sen bu ekibin çevirmenisin. [KAYNAK_DİL] dilinden [HEDEF_DİL] diline bilimsel makale çeviriyorsun.
Bu çağrıda yapılacak aşama: [AŞAMA]  (İLK ÇEVİRİ ya da DÜZELTME; yalnız bu aşamayı yap ve dur)

SAHİPLİK: Yalnız [WS]/first-pass.md, [WS]/structure-report.md ve sonra [WS]/final-translation.md
dosyalarını yazarsın. Başka dosyayı değiştirmezsin.

OKU:
1. [WS]/structure-manifest.md
2. [WS]/params.json
3. [WS]/seed-glossary.json  (translation alanı dolu ve enforce=true olan karşılıklar bağlayıcıdır)
4. [SKILL_DIR]/references/bilimsel-ceviri-kurallari.md
5. [WS]/source.md  (tamamını oku, sonra çevir)

ÇEVİRİ KURALLARI:
- Paragraf paragraf çevir. Paragraf birleştirme, bölme, sıra değiştirme yok.
- Uzun cümleyi aynı paragraf içinde bölebilirsin; bağlaçların mantıksal ilişkisi (neden, karşıtlık, koşul) korunur.
- Başlık düzeyi, liste türü, çizelge satır ve sütunları birebir korunur. Hücre içindeki madde hücrede kalır.
- Savın kesinlik düzeyi korunur: "suggest" "göstermektedir" olmaz; "may" "-ebilir" olur.
- Olumsuzluk, karşılaştırma yönü, nicelik sözcükleri (en az, en çok, yaklaşık) ve "sırasıyla" eşlemesi korunur.
- Sayılar params.json'daki ayırıcıyla yazılır; değer, basamak ve sondaki sıfırlar değişmez. Birim çevrilmez, dönüştürülmez.
- Atıflar, DOI'ler, adresler, kod, denklem, kimyasal formül, Latince tür adı ve toprak takson adları değişmez.
  Yalnız atıf bağlacı değişir: "et al." <-> params.json'daki etal_target, "and" <-> "ve".
- Kaynakça bölümünü olduğu gibi kopyala, yalnız başlığını çevir.
- Kısaltma: kaynak nerede tanımlıyorsa orada tanımla. Kaynakta tanımsız kısaltmaya tanım ekleme; [?tanımsız kısaltma: X?] diye işaretle.
  Türkçe kısaltma uydurma; yalnız sözlükte olanı kullan (TOK, KDK gibi).
- Tohum sözlükte olmayan, emin olmadığın terimi [?terim: kaynak terim?] diye işaretle ve devam et.
- Kaynakta okunamayan ya da anlamı belirsiz yeri [kaynakta belirsiz: ...] diye işaretle. Tahminle doldurma.
- Kaynakta olmayan açıklama, değerlendirme, bağlantı cümlesi ekleme.

YAPI RAPORU: first-pass.md'yi kaydetmeden önce structure-report.md yaz:
  Çizelge N: kaynak R x C -> çeviri R x C ; çok öğeli hücreler: içeride / SINIR İHLALİ
  Başlık sayıları, paragraf sayısı, işaretlediğin [?...?] yerlerin listesi.
SINIR İHLALİ varsa kaydetmeden düzelt.

DÜZELTME AŞAMASI (yönetici çağırınca):
- [WS]/review-feedback.md ve [WS]/terminology-glossary.json dosyalarını oku.
- Kritik ve büyük bulguların hepsini, onaylanmış küçük bulguları uygula. Sözlük değişikliklerini uygula.
- Yalnız metni değiştir; yapıyı değiştirme. Terim değişikliğini yerinde, birebir değiştirme ile yap.
- Sonucu [WS]/final-translation.md olarak kaydet. Uygulamadığın bulguyu gerekçesiyle dosyanın sonuna değil,
  [WS]/structure-report.md içindeki "Uygulanmayan bulgular" bölümüne yaz.
```

Parçalı modda aynı istem şu farklarla kullanılır: kaynak `[WS]/chunks/chunk-N.md`, çıktı `[WS]/first-pass-chunk-N.md`, yapı raporu `[WS]/structure-report-chunk-N.md`. Çevirmen kendi parçasının dışındaki başlık numaralarını değiştirmez. Kaynakça `references.md` dosyasındadır ve parçalara dahil değildir.

**Yüksek doğruluk düzeni (bölüm bölüm).** Kullanıcı yüksek doğruluk isterse, metin 6000 sözcüğün altında olsa da bölüm sınırlarında 800-1200 sözcüklük parçalara bölünür. Gerekçe: her çevirmen kendi parçasını paragraf paragraf doğrulayabilecek kadar kısa bir işe odaklanır; eksiltme ve özetleme riski azalır. Tutarlılık için her çevirmen önce makalenin tamamını bağlam olarak okur ve hepsi aynı sözlüğü ve proje kurallarını kullanır. Denetim iki katmanlıdır: her parçaya ayrı denetçi, sonra bütün metni okuyan tek bir tutarlılık denetçisi (terim, kısaltma tanımı, notasyon, gönderme numaraları, yazım türü). Düzeltmeyi parçayı çeviren ajan yapar (`SendMessage` ile bağlamını koruyarak). Bu düzenin daha doğru olduğu ölçülerek gösterilmiş değildir; doğruluk, otomatik denetim ve denetçi bulgularıyla her çeviride ayrıca ölçülür ve raporlanır.

### Terim araştırmacısı istemi

```
Sen bu ekibin terim araştırmacısısın. Görevin, tohum sözlükte olmayan ya da karşılığı belirsiz kalan
terimleri kaynakla sabitlemek. Çeviri yönü: [YÖN] ([KAYNAK_DİL] -> [HEDEF_DİL]).

SAHİPLİK: Yalnız [WS]/glossary-research.json dosyasını yazarsın.

OKU: [WS]/source.md, [WS]/seed-glossary.json, [SKILL_DIR]/references/glossary-schema.md,
     [SKILL_DIR]/domains/toprak-bilimi/README.md

GÖREV:
1. Kaynakta tohum sözlükte olmayan teknik terimleri, yöntem ve istatistik adlarını, kısaltmaları,
   kurum ve fon kuruluşu adlarını, yer adlarını, cihaz ve yazılım adlarını çıkar.
2. Tohum sözlükte translation=null olan ya da status="değişken" olup notunda bağlam ayrımı bulunan
   girdileri de ele al. Notu oku; bağlama uyan biçimi seç ve gerekçesini yaz.
3. Her yeni terim için kaynak ara. Sıra:
   Türkçe karşılık için: Türkçe hakemli dergilerde kullanım (TR Dizin, DergiPark; alterlab-trdizin
   skill'i varsa onu kullan), YÖK Tez, TÜBA Türkçe Bilim Terimleri Sözlüğü, yazım için TDK Güncel
   Türkçe Sözlük.
   İngilizce karşılık için: alanın standart terim kaynakları (ISO toprak kalitesi sözlüğü, WRB,
   Soil Taxonomy anahtarları, SSSA terim sözlüğü) ve alanın uluslararası hakemli dergilerindeki kullanım.
   Kurum adları için kurumun kendi İngilizce ya da Türkçe sayfası.
4. Kanıt kuralı: aynı biçimi kullanan, farklı yazar gruplarından en az iki hakemli yayın = high.
   Tek yayın = medium. Kanıt yok = low. Birbirini kopyalayan sayfalar iki kaynak sayılmaz.
   Sözlük sitesindeki makine çevirisi kanıt değildir.
5. Yerleşik Türkçe karşılık yoksa ad UYDURMA. translation alanına İngilizce terimi yaz,
   notes alanına "ilk geçişte bir cümleyle açıkla" ve önerilen açıklamayı yaz, status="yerleşmemiş".
6. Her girdiye kaynak adresi ekle. Adresi açıp terimi gördüysen yaz; görmediysen yazma.
7. Sonucu şemaya uygun olarak [WS]/glossary-research.json olarak kaydet.

ARAMA SORUNU: Bir terim için iki arama başarısız olursa confidence="low", notes="web araması yapılamadı"
yaz ve devam et. Bütün aramalar başarısızsa metadata.web_search_failures alanına sayıyı yaz.
Başlangıç ve bitiş zamanını metadata alanına ISO 8601 biçiminde yaz.
```

---

## Aşama 1.5: Yönetici sözlüğü birleştirir

```bash
python "$SKILL_DIR/scripts/merge_glossaries.py" WS/seed-glossary.json WS/glossary-research.json \
  --out WS/terminology-glossary.json
```

1. Betik `terms` dizilerini `original` alanına göre birleştirir. Öncelik: bağlayıcı alan sözlüğü, sonra araştırmacının kaynaklı kararı, sonra öneri listesi.
2. Araştırmacının bağlayıcı bir girdiyle çelişen önerisi uygulanmaz; `metadata.conflicts` listesine yazılır. Yönetici bunu raporda "kullanıcı kararı gerekir" diye verir.
3. Metadata sayıları yeniden hesaplanır.
4. Yönetici düşük güvenli girdileri okur. Kaynaksız bir karşılık bağlayıcı gibi sunulmaz; gerekirse `enforce: false` yapılır.
5. Çevirmenin `[?terim: ...?]` işaretleri sözlükle karşılaştırılır; karşılanmayan işaret kalırsa araştırmacıya geri gönderilir.

Parçalı modda önce parçaları birleştir:

```bash
python "$SKILL_DIR/scripts/prepare_source.py" merge WS
```

Betik parça sınırındaki yinelenen başlıkları bildirir. Numara sürekliliğini ve "yukarıda", "aşağıda" göndermelerini elle denetle.

---

## Aşama 2: Otomatik denetim ve denetçi

### 2.1 Otomatik denetim

```bash
python "$SKILL_DIR/scripts/qa_checks.py" --source WS/source.md --target WS/first-pass.md \
  --direction en-tr --glossary WS/terminology-glossary.json --params WS/params.json \
  --out-md WS/qa-report-1.md --out-json WS/qa-report-1.json
```

Betik şunları denetler: sayılar (ondalık ayırıcı dönüşümünden sonra), yazar-yıl ve numaralı atıflar, DOI ve adresler, kaynakçanın değişmediği, başlık düzeyleri, çizelge satır ve sütunları, şekil ve çizelge numaraları, denklemler, liste imleri, paragraf sayısı, onaylı terimler, yasak biçimler, değişken terimde iki biçim karışımı, hedef dilin yazım kuralları, çözülmemiş çevirmen işaretleri (`[?...?]`, `[kaynakta belirsiz: ...]`) ve uzun cümleler. Kaynak ve hedefin paragraf sayısı eşitse onaylı terimler paragraf paragraf da denetlenir. Belge düzeyindeki denetim, onaylı karşılık belgenin bir yerinde geçince geçer; bir paragraftaki sapmayı ancak paragraf düzeyindeki denetim gösterir. Paragraf düzeyindeki aday küçük önemdedir ve elle okunur: gönderme sözcüğü ya da bağlama göre seçilen karşılık geçerli olabilir. Sözlük çeviri sırasında güncellenirse (yeni yönetici kararı) otomatik denetim yeni sözlükle yeniden çalıştırılır. Son çeviride çözülmemiş işaret kalmaz; kalan işaret raporun "Çözülmemiş noktalar" bölümüne taşınır ve metinden yönetici kararıyla kaldırılır.

Betiğin bulguları adaydır. Kaynakta yazıyla, çeviride rakamla yazılmış sayı gibi yanlış alarmlar olabilir. Betiğin göremediği hatalar da vardır: anlam kayması, savın kesinlik düzeyinin değişmesi, yanlış bağlamda doğru terim. Bunlar denetçinin işidir.

### 2.2 Denetçi istemi

```
Sen bu ekibin denetçisisin. Çeviriyi kaynakla karşılaştırıp bulguları yazarsın; çeviriyi değiştirmezsin.

SAHİPLİK: Yalnız [WS]/review-feedback.md dosyasını yazarsın.

OKU: [WS]/source.md, [WS]/first-pass.md, [WS]/terminology-glossary.json, [WS]/qa-report-1.md,
     [WS]/structure-manifest.md, [WS]/structure-report.md, [WS]/params.json,
     [SKILL_DIR]/references/review-feedback-schema.md, [SKILL_DIR]/references/uydurma-onleme.md,
     [SKILL_DIR]/references/bilimsel-ceviri-kurallari.md
ÖN KOŞUL: Sözlükte terim yoksa ya da sayı belge boyuna göre akla yatkın değilse yöneticiye bildir ve bekle.

DENETİM SIRASI (önem sırasıyla):
a. Otomatik bulgular: qa-report-1.md'deki her adayı kaynağa bakarak DOĞRULANDI ya da REDDEDİLDİ diye işaretle.
b. UYDURMA: çevirideki her paragrafın kaynakta karşılığı var mı? Fazla bilgi, değerlendirme, bağlantı cümlesi?
c. EKSİLTME: kaynaktaki her paragrafın, cümlenin, dipnotun çeviride karşılığı var mı?
d. ANLAM KAYMASI: savın kesinlik düzeyi (suggest/indicate/show; -ebilir/göstermiştir), olumsuzluk ve kapsamı,
   nedensellik (ilişkili ile neden olur), karşılaştırma yönü, nicelik sözcükleri, "sırasıyla" eşlemesi,
   oran, fark ve yüzde değişim ayrımı, istatistiksel önem ile eşdeğerlik ayrımı,
   örneklem ve tekrar sözcükleri (örnek, nokta, tekerrür, parsel).
e. SAYI: sayı, birim, işaret, sondaki sıfır, aralık ve eşitsizlik işaretleri.
f. ATIF: yazar, yıl, harf eki, sıra, numaralı atıf; kaynakça değişmemiş mi?
g. TERİM: sözlük uyumu; doğru terim doğru bağlamda mı; yerleşmemiş terim açıklanmış mı; kısaltma ilk geçişte tanımlı mı?
h. YAPI: structure-manifest.md ile karşılaştırma çizelgesi (her "HAYIR" kritik bulgudur).
i. ÜSLUP VE OKUNABİLİRLİK: hedef dilin bilimsel üslubu, uzun cümle, açılmamış ad zinciri, birebir çeviri kokan yapı.

İKİ GEÇİŞ: önce çeviriden kaynağa (uydurma), sonra kaynaktan çeviriye (eksiltme).
Bulguyu yazmadan önce iki metindeki tam cümleyi oku.

ÇIKTI: review-feedback-schema.md biçiminde [WS]/review-feedback.md. Her bulguda konum, tür, çevirideki metin,
kaynaktaki metin ve önerilen düzeltme olsun. Sonunda istatistik çizelgesi.
Yöneticiye kısa özet ver: kaç kritik, büyük, küçük bulgu; uydurma ya da eksiltme var mı.
```

---

## Aşama 3: Düzeltme ve yeniden denetim

1. Çevirmene düzeltme görevini ver (yeni `Agent` çağrısı ya da takım modunda `SendMessage`). Çevirmen `final-translation.md` yazar.
2. Otomatik denetimi `final-translation.md` üzerinde yeniden çalıştır: `--out-md WS/qa-report-2.md`.
3. Kritik bulgu kalırsa ikinci düzeltme turu yap. En çok iki tur. İkinci turdan sonra kalan kritik bulguyu raporda "çözülmedi" diye yaz; çeviriyi tamamlanmış gösterme.

## Aşama 4: Son doğrulama, rapor, çıktı

### 4.1 Yöneticinin son doğrulaması

- `qa-report-2.md` içinde kritik aday kalmadığını ya da kalanların gerekçeli olarak reddedildiğini doğrula.
- Rastgele 5 paragrafı kaynakla tam cümle düzeyinde karşılaştır. Paragraf sayısı `qa-report-2.json` içindeki `stats.structure.source.paragraphs` değeridir (N). Seçimi `python -c "import random; random.seed(20261020); print(sorted(random.sample(range(1, N + 1), 5)))"` ile yap; tohum değerini ve seçilen sıra numaralarını rapora yaz.
- Denetçinin "HAYIR" yazdığı yapı satırlarının düzeldiğini doğrula.
- Sözlükten 10 terimin son metindeki kullanımını oku.
- Her ana bölümün ilk ve son paragrafının çevrildiğini doğrula.
- Değişen her paragrafı baştan oku: eksik, yinelenen, bozuk sözcük, kaybolan atıf var mı?

### 4.2 Çeviri raporu

`WS/ceviri-raporu.md` dosyasını [references/ceviri-raporu-sablonu.md](references/ceviri-raporu-sablonu.md) şablonuyla yaz. Rapor şunları ayırır: otomatik denetimin kapsadığı alanlar, yalnız denetçinin okuduğu alanlar, çözülmemiş noktalar. Büyük dil modeli kullanımının yöntem bölümünde ya da dergi beyanında raporlanması için model, erişim tarihi, ayarlar ve istem kaydını da içerir.

### 4.3 Çıktı

```bash
python "$SKILL_DIR/scripts/export_docx.py" WS/final-translation.md --out MAKALE.tr.docx --lang tr [--template DERGI.docx] [--pdf]
```

- Çıktı dosyaları kaynak dosyanın yanına yazılır: `MAKALE.tr.md`, `MAKALE.tr.docx`, isteğe bağlı `MAKALE.tr.pdf`.
- Dergi şablonu varsa `--template` ile verilir; biçim şablondan gelir. Varsayılan biçim: [references/dizgi-kurallari.md](references/dizgi-kurallari.md).
- Kullanıcıya dosya yollarını, çözülmemiş noktaları ve raporun yerini bildir. Ulaşılan durumu ayır: çeviri yazıldı, denetlendi, son dosya yeniden okunarak doğrulandı.

---

## Çevrilmeyecek öğeler

- Kaynakça girdileri (dergi çevrilmiş başlık istemiyorsa), DOI, adres, e-posta, ORCID, proje ve fon numaraları.
- Kod, yazılım, paket ve işlev adları, değişken adları, Google Earth Engine koleksiyon kimlikleri.
- Denklemler, matematik simgeleri, kimyasal formüller, birim simgeleri.
- Latince tür adları (italik korunur), Soil Taxonomy ve WRB takson adları (özgün yazım).
- Kişi adları; kurumların resmî adları (resmî çevirisi varsa o kullanılır).
- Uydu, algılayıcı ve veri ürünü adları (Sentinel-2, Landsat 8 OLI, SoilGrids).

## Kesin kurallar

- Kaynakta olmayanı ekleme; kaynakta olanı atlama.
- Sayıyı, birimi, atfı, takson adını değiştirme. Yalnız ayırıcı ve atıf bağlacı hedef dile uyar.
- Savın kesinlik düzeyini koru.
- Yerleşik terim yoksa ad uydurma; İngilizce terimi açıklayarak kullan.
- Yapıyı koru: başlık, paragraf, liste, çizelge, hücre.
- Ayrıntılı önleme ve yakalama yöntemi: [references/uydurma-onleme.md](references/uydurma-onleme.md).

## Çalışma klasörü sözleşmesi

```
ceviri-MAKALE/                    (WS)
├── original.*                    özgün dosya
├── source.md                     Markdown kaynak
├── structure-manifest.md         yapı envanteri (betik + yönetici)
├── params.json                   çeviri parametreleri
├── seed-glossary.json            tohum sözlük (seed_glossary.py)
├── glossary-research.json        terim araştırmacısının girdileri
├── terminology-glossary.json     birleştirilmiş sözlük (yönetici)
├── chunks/chunk-N.md             yalnız parçalı modda
├── chunk-manifest.md, references.md
├── first-pass[-chunk-N].md       ilk çeviri
├── structure-report[-chunk-N].md çevirmenin yapı raporu
├── qa-report-1.md / .json        ilk otomatik denetim
├── review-feedback.md            denetçi bulguları
├── final-translation.md          düzeltilmiş çeviri
├── qa-report-2.md / .json        son otomatik denetim
└── ceviri-raporu.md              çeviri raporu
```

## Başvuru dosyaları

| Dosya | İçerik |
|---|---|
| [references/bilimsel-ceviri-kurallari.md](references/bilimsel-ceviri-kurallari.md) | Sayı, yüzde, birim, atıf, bölüm adları, kısaltma, kesinlik düzeyi, Türkçe harf kuralları |
| [references/glossary-schema.md](references/glossary-schema.md) | Terim sözlüğü JSON şeması |
| [references/review-feedback-schema.md](references/review-feedback-schema.md) | Denetçi bulgu biçimi ve bulgu türleri |
| [references/uydurma-onleme.md](references/uydurma-onleme.md) | Uydurma, eksiltme ve anlam kaymasını önleme ve yakalama |
| [references/olcekleme.md](references/olcekleme.md) | Mod eşikleri, parçalama ve birleştirme |
| [references/dizgi-kurallari.md](references/dizgi-kurallari.md) | .docx ve .pdf biçim kuralları |
| [references/ceviri-raporu-sablonu.md](references/ceviri-raporu-sablonu.md) | Çeviri raporu ve model kullanım kaydı |
| [domains/toprak-bilimi/README.md](domains/toprak-bilimi/README.md) | Toprak bilimi alan paketi |
| [domains/toprak-bilimi/alan-notlari.md](domains/toprak-bilimi/alan-notlari.md) | Alanın çeviri tuzakları |
