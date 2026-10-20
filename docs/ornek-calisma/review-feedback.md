## Denetim: Yarı kurak bir havzada toprak organik karbonunun mekânsal tahmini (ceviri-ornek-makale)

**Kaynak**: WS/source.md
**Çeviri**: WS/first-pass.md
**Sözlük**: WS/terminology-glossary.json
**Otomatik denetim**: WS/qa-report-1.md
**Denetçi**: denetçi ajan (opus)
**Tarih**: 2026-10-20

Ön koşul: sözlükte 22 terim var ve 22'si de kaynakta geçiyor. Ana metin 168 sözcük; özet ve yöntem ağırlıklı, terim yoğun bir metin için bu sayı akla yatkın. Yöneticiye bildirim gerekmedi.

Yön: en-tr. Parametreler (params.json): ondalık virgül, yüzde işareti önde, "ve ark.", "Şekil", "Çizelge", kaynakça çevrilmez, tire yasağı, cümle sınırı 30 sözcük.

---

### Otomatik bulguların doğrulanması

| No | qa-report bulgusu | Karar | Gerekçe |
|---|---|---|---|
| 1 | TYPOGRAPHY (major): hedef satır 7, çözülmemiş çevirmen işareti `[?tanımsız kısaltma: R2?]` | DOĞRULANDI | Kaynak satır 7: "and R2 = 0.61". R2 kaynağın hiçbir yerinde tanımlanmıyor; işaret çeviride duruyor. Sözlük kararı artık var (R2 korunur, tanım eklenmez). Bkz. Büyük bulgu 1. |
| 2 | TYPOGRAPHY (major): hedef satır 15, çözülmemiş çevirmen işareti `[?terim: folds?]` | DOĞRULANDI | Kaynak satır 15: "Cross-validation used 10 folds". Çeviride "10 kat [?terim: folds?] kullanılmış". Sözlük "kat" diyor ama enforce=false ve "denetçi bağlama bakar" notu var; bu bağlamda "10 kat kullanılmış" belirsiz. Bkz. Büyük bulgu 2. |
| 3 | READABILITY (minor): hedef satır 7, 31 sözcüklü cümle (sınır 30) | REDDEDİLDİ | Sayım doğru, ama sınırı aşan tek şey çevirmen işaretinin 3 sözcüğü. İşaret kaldırılınca cümle 28 sözcük oluyor ve sınırın altında kalıyor. Büyük bulgu 1 düzelince bu da kendiliğinden çözülür. Cümle bölünmesin: bölünürse cümle sonundaki atıfın (Smith ve ark., 2019; Brown ve Lee, 2020a) hangi önermeye bağlandığı değişebilir. |

Otomatik istatistiklerin elle sınanması:

- Sayılar (31 / 31, eksik 0, fazla 0): satır satır karşılaştırıldı; bütün değerler ve basamaklar aynı. Hedef satır 7'de görülen fazladan "2", işaretin içindeki "R2" yazısıdır; gerçek bir sayı değil.
- Manifestteki 33 ile otomatik denetimdeki 31 arasındaki fark, manifestin bölüm numaralarını ("1.", "2.") da saymasından geliyor. Çeviride iki bölüm numarası da korunmuş.
- Betiğin eşleştiremediği birim (sözlük notu): kaynak satır 11'deki "12.3 to 38.9 cmol(+) kg-1" çeviride "12,3 ile 38,9 cmol(+) kg-1" olmuş; simge ve yazımı aynı.
- Sözlük uyumu (15 / 15): enforce=true terimler için doğru. enforce=false 7 terim elle denetlendi (aşağıdaki terim uyumu satırına bakınız).

---

### Denetim adımları özeti

| Adım | Sonuç |
|---|---|
| a. Otomatik bulgular | 2 doğrulandı, 1 reddedildi |
| b. Uydurma (çeviriden kaynağa) | Çevirideki 10 cümlenin (başlık, 8 ana metin cümlesi, çizelge başlığı) ve çizelgenin hepsinin kaynakta karşılığı var. Fazladan bilgi, değerlendirme ya da bağlantı cümlesi yok. Kaynakta olmayan tek metin, iki çevirmen işareti (Büyük bulgu 1 ve 2). |
| c. Eksiltme (kaynaktan çeviriye) | Kaynaktaki her başlığın, cümlenin, çizelge hücresinin, denklemin ve kaynakça girdisinin çeviride karşılığı var. Kaynakta dipnot yok. "on average", "mean", "(0-30 cm)" gibi niteleyiciler korunmuş. |
| d. Anlam kayması | Yok. "suggest" -> "düşündürmektedir" ve "may control" -> "denetleyebileceğini": iki katmanlı kesinlik düzeyi korunmuş. "reported" -> "bildirmiştir", "ranged from ... to" -> "... ile ... arasında değişmiştir". Analiz birimleri ayrı tutulmuş: "120 sites" -> "120 noktada", "120 samples" -> "120 örneğin". Metinde olumsuzluk, karşılaştırma, "respectively" ya da istatistiksel önem ifadesi yok. |
| e. Sayı | Değer, basamak, işaret ve birim değişmemiş. Ondalık virgül 10 değerde de doğru (0,42; 0,61; 7,5; 12,3; 38,9; 1,35; 1,21; 0,34; 1,35; 0,08). Yüzde işareti önde (%0,42; %25'i). Aralıklarda kısa çizgi var (0-30; 3-5). Tek ilişki işareti "=" ve korunmuş. |
| f. Atıf | Yazar-yıl atıfları 3 / 3: sıra, yıl ve "2020a" harf eki korunmuş; "et al." -> "ve ark.", "and" -> "ve". Numaralı atıf [1, 3-5] aynı. Kaynakça 3 girdi, birebir aynı (306 / 306 karakter, diff boş); DOI 2 / 2. |
| g. Terim | 21 / 22 terim uyumlu. Uymayan tek terim "folds" (Büyük bulgu 2). Kısaltmalar kaynaktaki yerlerinde tanımlanmış: TOK ve RMSE Özet'te, KDK Giriş'te. Uydurma Türkçe kısaltma yok ("RF" ya da "RO" eklenmemiş). |
| h. Yapı | 22 / 22 satır uyuşuyor (çizelge aşağıda) |
| i. Üslup ve okunabilirlik | Sınırı aşan gerçek bir cümle yok. Açılmamış ad zinciri yok. Birebir çeviri kokan bir yapı bulunmadı. |

---

### Kritik bulgular

Yok.

Uydurma, eksiltme, anlam kayması, sayı, atıf ya da yapı hatası bulunmadı. İki yönlü geçiş tamamlandı: önce çeviriden kaynağa, sonra kaynaktan çeviriye. Her cümle iki metinde tam olarak okundu.

### Büyük bulgular

1. [Konum: Özet, 2. cümle (hedef satır 7)]
   **ABBREVIATION** (otomatik denetimde TYPOGRAPHY, çözülmemiş çevirmen işareti): "R2 [?tanımsız kısaltma: R2?] = 0,61"
   - Kaynak: "Random forest predicted SOC with a root mean squared error (RMSE) of 0.42% and R2 = 0.61 (Smith et al., 2019; Brown and Lee, 2020a)."
   - Çeviri: "Rastgele orman, TOK'u ortalama kare hatanın karekökü (root mean squared error, RMSE) %0,42 ve R2 [?tanımsız kısaltma: R2?] = 0,61 değerleriyle tahmin etmiştir (Smith ve ark., 2019; Brown ve Lee, 2020a)."
   - Sözlük: "R2" -> "R2" (kısaltma, enforce=true). Sözlük notu: "Kaynak belgede tanımı yoksa çeviride de eklenmez, raporda belirtilir." Ayrıca kurallar 4.2 ve 6.1: R2 bir simgedir ve değişmez.
   - Sorun: R2'nin tanımsız kalması kaynağa sadıktır, hata değildir. Hata, işaretin yayımlanacak metinde kalmasıdır: işaret kaynakta olmayan bir metindir.
   - Düzeltme: "Rastgele orman, TOK'u ortalama kare hatanın karekökü (root mean squared error, RMSE) %0,42 ve R2 = 0,61 değerleriyle tahmin etmiştir (Smith ve ark., 2019; Brown ve Lee, 2020a)."
   - Ek: "belirleme katsayısı" ya da başka bir açılım eklenmez. R2'nin kaynakta tanımsız olduğu çeviri raporuna yazara soru olarak yazılır: korelasyon katsayısının karesi mi, model etkinliği ölçüsü mü (sözlük notu).

2. [Konum: 2. Materyal ve yöntem, 1. paragraf, 2. cümle (hedef satır 15)]
   **TERMINOLOGY** (otomatik denetimde TYPOGRAPHY, çözülmemiş çevirmen işareti): "Çapraz doğrulamada 10 kat [?terim: folds?] kullanılmış"
   - Kaynak: "Cross-validation used 10 folds, and 25% of the data were held out (Figure 1)."
   - Çeviri: "Çapraz doğrulamada 10 kat [?terim: folds?] kullanılmış ve verilerin %25'i ayrı tutulmuştur (Şekil 1)."
   - Sözlük: "folds" -> "kat" (değişken, low, enforce=false). Notlarda iki biçim veriliyor: "'10 katlı çapraz doğrulama' ya da 'çapraz doğrulamada 10 kat'". Ayrıca şu uyarı var: "'Kat' tek başına çok anlamlı ... denetçi bağlama bakar." Tohum satırı A-054'e göre TR Dizin'de "katlı" 28, "kat" 26 kayıtta geçiyor.
   - Sorun: işaret çözülmemiş. Ayrıca "10 kat ... kullanılmış" Türkçede "on katı kadar" ya da "on kez kullanılmış" diye okunabilir; çevirmenin kaygısı yerinde.
   - Düzeltme: "10 katlı çapraz doğrulama kullanılmış ve verilerin %25'i ayrı tutulmuştur (Şekil 1)."
   - Kaçınılacak biçim: "veriler 10 kata bölünmüş" gibi bir açılım. Kaynak, katların bütün veriden mi yoksa ayrılan %25'in dışında kalan kısımdan mı oluştuğunu yazmıyor; çeviri bu ilişkiyi eklememeli.

### Küçük bulgular

Yok. Otomatik READABILITY adayı reddedildi (yukarıdaki çizelgede 3. satır).

### Denetlenip bulgu yazılmayan noktalar (düzeltmede değiştirilmesin)

1. Özet, 3. cümle: "Sonuçlar, kireç içeriğinin TOK depolanmasını denetleyebileceğini düşündürmektedir." Kaynak: "The results suggest that calcium carbonate content may control SOC storage." Sözlükteki "SOC storage" yan notu "belirleyebilir ya da etkileyebilir düşünülmeli" diyor. Karar: "denetleyebileceğini" kalsın. Bu biçim review-feedback-schema.md örneğindeki doğru biçimle de aynı. "etkileyebileceğini" yazılmasın: "control" savını (belirleyici etken olmak) "affect" düzeyine indirir ve savı zayıflatır. "belirleyebileceğini" eş değer bir seçenektir, ama değiştirmek zorunlu değil.
2. Yöntem, 2. cümle: "held out" -> "ayrı tutulmuştur". Sözlük bu terimi "yerleşmemiş" ve enforce=false olarak işaretliyor ve sıradan bir fiille karşılanmasına izin veriyor. Sözlükteki örnek açıklama ("model kurulumunda kullanılmamak üzere") eklenmesin, çünkü kaynak ayrılan payın amacını yazmıyor. Aynı nedenle "test kümesi" ya da "bağımsız doğrulama" da yazılmasın.
3. "120 sites" -> "120 noktada" (Özet) ve "120 samples" -> "120 örneğin" (Çizelge 1 başlığı): iki analiz birimi ayrı korunmuş. İkisi birleştirilmesin; "örneklem" sözcüğü de kullanılmasın.
4. Çizelge 1'deki "TOK (%)" için Materyal ve yöntem bölümünde ayrı bir tanım yok. Kaynakta da "SOC (%)" yalnız Özet'te tanımlı. Çeviri kaynağa sadık; tanım eklenmez.
5. "Yilmaz" adı kaynakta ve kaynakçada "i" ile yazılmış. "Yılmaz" diye düzeltilmesin (kural 8.1).
6. "environmental covariates" -> "yardımcı değişkenler": bu bağlayıcı alan sözlüğünün kararıdır. "Çevresel" sözcüğünün düşmesi bir bulgu değildir.
7. "Hacim ağırlığı ortalama 1,35 g cm-3 olmuştur": "olmuştur", Türkçe tarım yayınlarında ölçülen ortalama için yaygın bir kalıptır. Değiştirmeye gerek yok.

---

### Yapı karşılaştırma çizelgesi

| Öğe | Kaynak | Çeviri | Uyuşuyor mu? |
|---|---|---|---|
| H1 başlık sayısı | 1 | 1 | EVET |
| H2 başlık sayısı (kaynakça başlığı hariç) | 3 | 3 | EVET |
| Kaynakça başlığı | 1 (## References) | 1 (## Kaynaklar) | EVET |
| Başlık sırası ve düzeyi | Abstract, 1. Introduction, 2. Materials and methods, References | Özet, 1. Giriş, 2. Materyal ve yöntem, Kaynaklar | EVET |
| Bölüm numaraları | 1., 2. | 1., 2. | EVET |
| Paragraf sayısı | 4 | 4 | EVET |
| Ana metin cümle sayısı (Özet / Giriş / Yöntem) | 3 / 3 / 2 | 3 / 3 / 2 | EVET |
| Liste imi | 0 | 0 | EVET |
| Çizelge sayısı | 1 | 1 | EVET |
| Çizelge 1 satır | 3 | 3 | EVET |
| Çizelge 1 sütun | 3 | 3 | EVET |
| Çizelge 1 hücre değerleri | 1.21; 0.34; 1.35; 0.08 | 1,21; 0,34; 1,35; 0,08 | EVET |
| Birleştirilmiş hücre (colspan/rowspan) | 0 | 0 | EVET |
| Çizelge numaraları | [1] | [1] | EVET |
| Şekil numaraları | [1] | [1] | EVET |
| Ayrık denklem | 1 | 1 (birebir aynı) | EVET |
| Satır içi matematik | 0 | 0 | EVET |
| Sayı adedi (qa_checks, bölüm numaraları hariç) | 31 | 31 | EVET |
| Yazar-yıl atıfı | 3 | 3 | EVET |
| Numaralı atıf | 4 ([1, 3-5]) | 4 ([1, 3-5]) | EVET |
| DOI | 2 | 2 | EVET |
| Kaynakça girdileri | 3 (306 karakter) | 3 (306 karakter, birebir aynı) | EVET |

"HAYIR" satırı yok. Kaynakta dipnot ve ek materyal yok. İlk satırdaki HTML yorum satırı birebir korunmuş.

---

### İstatistik

| Ölçüt | Değer |
|---|---|
| Kritik bulgu | 0 |
| Büyük bulgu | 2 |
| Küçük bulgu | 0 |
| Uydurma bulundu mu | hayır (kaynakta olmayan tek metin, iki çevirmen işareti; Büyük bulgu 1 ve 2'de) |
| Eksiltme bulundu mu | hayır |
| Anlam kayması bulundu mu | hayır |
| Otomatik bulgu: doğrulanan / reddedilen | 2 / 1 |
| Terim uyumu | 21 / 22 (%95,5); uymayan: "folds". enforce=true terimler: 15 / 15 (%100) |
| Yapı uyumu | 22 / 22 |
| Genel değerlendirme | düzeltmeyle geçer (iki işaret kaldırılıp "10 katlı çapraz doğrulama" yazıldığında yayımlanabilir) |
