# Yapı raporu (ilk çeviri)

## Çizelgeler

- Çizelge 1: kaynak 3 x 3 -> çeviri 3 x 3 ; çok öğeli hücreler: yok (manifestte boş; çeviride de her hücrede tek öğe) / SINIR İHLALİ yok
  - Birleştirilmiş hücre (colspan/rowspan): yok, kaynakta ve çeviride 0
  - Çizelge başlığı: "Table 1." -> "Çizelge 1." (numara korundu)

## Başlıklar

- Kaynak: H1 1, H2 3 (manifest sayımı, Kaynakça başlığı hariç); Kaynakça başlığı ayrıca H2 olarak yazılı (toplam 4 satır `##`)
- Çeviri: H1 1, H2 3 + "## Kaynaklar" (toplam 4 satır `##`)
- Düzeyler ve sıra birebir korundu: Özet, 1. Giriş, 2. Materyal ve yöntem, Kaynaklar

## Paragraflar ve diğer yapı öğeleri

- Paragraf sayısı: kaynak 4 -> çeviri 4 (özet 1, giriş 1, materyal ve yöntem 1, çizelge başlığı 1); birleştirme, bölme ve sıra değişikliği yok
- Liste imi: kaynak 0 -> çeviri 0
- Ayrık denklem: kaynak 1 -> çeviri 1 (LaTeX satırı değiştirilmeden kopyalandı)
- Şekil gönderimi: "Figure 1" -> "Şekil 1" (1 gönderim; şeklin kendisi kaynakta yok)
- Kaynakça: 3 girdi, olduğu gibi kopyalandı; yalnız başlık çevrildi (translate_references = false)
- Kaynak dosyanın ilk satırındaki HTML yorum satırı (zaten Türkçe) olduğu gibi korundu
- Atıflar: yazar-yıl 3 (Smith ve ark., 2019; Brown ve Lee, 2020a; Yilmaz (2018)), numaralı 1 ([1, 3-5]); et al. -> ve ark., and -> ve; yıl ve harf eki (2020a) korundu
- U+2013, U+2014, U+2212 kullanılmadı; aralıklarda kısa çizgi (0-30, 3-5)

## İşaretlenen yerler ([?...?])

1. Özet, 2. cümle: `R2 [?tanımsız kısaltma: R2?]` (kaynakta R2 hiçbir yerde tanımlanmıyor; tohum sözlük de "tanımı yoksa eklenmez, raporda belirtilir" diyor; tanım eklenmedi)
2. 2. Materyal ve yöntem, 1. paragraf, 2. cümle: `10 kat [?terim: folds?]` (çapraz doğrulamada "fold" için tohum sözlükte karşılık yok; "10 kat" ifadesi "10 defa" okunabileceğinden terim araştırmacısına bırakıldı)

## Tohum sözlük uygulaması ve sözlükte olmayan seçimler

- Bağlayıcı karşılıklar (enforce=true) olduğu gibi kullanıldı: hacim ağırlığı, katyon değişim kapasitesi (KDK), toprak organik karbonu (TOK), kireç içeriği, alınabilir fosfor, sayısal toprak haritalama, yardımcı değişkenler, çapraz doğrulama, ortalama kare hatanın karekökü (root mean squared error, RMSE), rastgele orman
- "prediction" (sözlükte translation boş, enforce=false): kurallar 6.3 ve sözlük önerisi uyarınca "tahmin"; metinde "kestirim" kullanılmadı
- Kısaltma tanımları kaynaktaki yerinde verildi: TOK Özet'te, KDK Giriş'te, RMSE Özet'te (İngilizce açılımla birlikte). Çizelgedeki "SOC (%)" satır başlığı "TOK (%)" oldu (tanım Özet'te var)
- Sözlükte olmayan ama yerleşik sayılan karşılıklar işaretlenmedi: yarı kurak (semi-arid), havza (catchment), mekânsal (spatial), nokta (site), örnek (sample), ortalama (mean), standart sapma (standard deviation), özellik (property)
- Analiz birimi korundu: "120 sites" -> "120 noktada"; "120 samples" -> "120 örnek"
- Savın kesinlik düzeyi: "suggest" -> "düşündürmektedir"; "may control" -> "denetleyebileceğini"
- "RF" kısaltması kaynakta olmadığı için eklenmedi

## Sayı denetimi

- Ondalık ayırıcı nokta -> virgül (params.json: target_decimal ","); yüzde işareti sayıdan önce (%0,42; %25); değer, basamak ve sondaki sıfırlar korundu (1,35; 0,08; 1,21; 0,34; 7,5; 12,3; 38,9)
- Birimler çevrilmedi ve dönüştürülmedi (cm, mg kg-1, cmol(+) kg-1, g cm-3)

---

# Yapı raporu (düzeltme aşaması, final-translation.md)

## Çizelgeler

- Çizelge 1: kaynak 3 x 3 -> çeviri 3 x 3 ; çok öğeli hücreler: yok (her hücrede tek öğe) / SINIR İHLALİ yok
  - Birleştirilmiş hücre (colspan/rowspan): yok
  - Çizelge başlığı: "Çizelge 1. 120 örneğin özet istatistikleri." (numara ve ilişki korundu)

## Başlıklar ve diğer yapı

- Başlıklar: H1 1, H2 3 + "## Kaynaklar" (toplam 4 satır `##`); düzey ve sıra birebir aynı
- Paragraf sayısı: kaynak 4 -> çeviri 4; birleştirme, bölme ve sıra değişikliği yok
- Liste imi 0 -> 0; ayrık denklem 1 -> 1 (birebir aynı); kaynakça 3 girdi, kaynakla birebir aynı (diff boş)
- U+2013, U+2014, U+2212 yok; en uzun cümle 28 sözcük (sınır 30)

## Uygulanan düzeltmeler (review-feedback.md)

1. Büyük bulgu 1 (ABBREVIATION, Özet 2. cümle): `R2 [?tanımsız kısaltma: R2?] = 0,61` -> `R2 = 0,61`. İşaret kaldırıldı; tanım eklenmedi (sözlük: R2 korunur, kaynakta tanımı yoksa çeviride de eklenmez).
2. Büyük bulgu 2 (TERMINOLOGY, 2. Materyal ve yöntem 2. cümle): `Çapraz doğrulamada 10 kat [?terim: folds?] kullanılmış ve` -> `10 katlı çapraz doğrulama kullanılmış ve`. İşaret kaldırıldı; katların neyden oluştuğuna dair açılım eklenmedi.
3. Kritik bulgu: yok. Küçük bulgu: yok. Sözlük değişikliği (terminology-glossary.json): çeviriyle çelişen girdi yok; metinde başka değişiklik gerekmedi.
4. Denetçinin "değiştirilmesin" dediği 7 nokta (denetlenip bulgu yazılmayan noktalar) olduğu gibi bırakıldı.

## İşaretlenen yerler ([?...?])

Final çeviride [?...?] işareti kalmadı (0). Birinci çeviriden gelen iki işaret çözüldü (yukarıda 1 ve 2).

## Yazara sorular (metne eklenmedi)

- Özet'te "R2 = 0,61" ifadesindeki R2 kaynakta tanımsız. Korelasyon katsayısının karesi mi, model etkinliği ölçüsü mü hesaplandığı kaynaktan anlaşılmıyor (sözlük notu: ikisi aynı değildir). Çeviri kaynağa sadık kalıp tanım eklemedi; yazarın açıklaması gerekir.
- Yöntem'de "10 folds" ve "25% of the data were held out" cümlesi: katların bütün veriden mi yoksa ayrılan %25'in dışında kalan kısımdan mı oluştuğu kaynakta yazmıyor; çeviri bu ilişkiyi eklemedi.

## Uygulanmayan bulgular

Uygulanmayan kritik, büyük ya da küçük bulgu yok.

Bilgi için: denetçinin reddettiği otomatik aday (qa-report-1, READABILITY, minor: Özet 2. cümlede 31 sözcük) uygulanmadı. Gerekçe: sayımı aşıran şey çevirmen işaretinin 3 sözcüğüydü; işaret kaldırılınca cümle 28 sözcük oldu ve sınırın altında kaldı. Cümle bölünmedi, böylece cümle sonundaki atıfın (Smith ve ark., 2019; Brown ve Lee, 2020a) bağlandığı önerme değişmedi.
