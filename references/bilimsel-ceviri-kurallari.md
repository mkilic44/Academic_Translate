# Türkçe ve İngilizce bilimsel çeviri kuralları

Bu dosya çevirmenin, denetçinin ve yöneticinin ortak kural kaynağıdır. Hedef derginin yazım kuralı bu dosyadan önce gelir. Dergi kuralı ile bu dosya çelişirse dergi kuralı uygulanır ve çeviri raporuna yazılır.

Kuralların statüsü her bölümde belirtilmiştir:

- **Kullanıcı tercihi**: skill sahibinin bağlayıcı yazım kuralı.
- **Yazım kuralı**: Türkçe ya da İngilizce yazım geleneği; kaynağı belirtilmiştir.
- **Skill varsayılanı**: dergi kuralı yoksa uygulanan seçim; gerekçesi yazılmıştır.

## 1. Sayılar

| Konu | Türkçe hedef | İngilizce hedef | Statü |
|---|---|---|---|
| Ondalık ayırıcı | virgül: 0,05 ; 1,35 | nokta: 0.05 ; 1.35 | Yazım kuralı (aşağıdaki not) |
| Binlik ayırıcı | nokta: 1.234 ya da ayırıcısız 1234 | virgül: 1,234 ya da ayırıcısız 1234 | Yazım kuralı |
| Yüzde | %25 ; %0,42 | 25% ; 0.42% | Yazım kuralı |
| Aralık | 10-20 cm (kısa çizgi) | 10-20 cm | Kullanıcı tercihi: en dash kullanılmaz |
| Negatif değer | -0,12 (kısa çizgi) | -0.12 | Kullanıcı tercihi: U+2212 kullanılmaz |
| Birim üssü | g cm-3, mg kg-1 kaynaktaki gösterimle | aynı | Skill varsayılanı: kaynak gösterimi korunur |

Kurallar:

1. Sayının değeri, basamak sayısı ve sondaki sıfırlar değişmez. "0.50" çeviride "0,50" olur, "0,5" olmaz; raporlanan duyarlık bilgidir.
2. Yazıyla yazılmış sayı yazıyla, rakamla yazılmış sayı rakamla kalır. Türkçede cümle başındaki rakam ("120 örnek ...") kaynakta öyleyse korunur.
3. Türkçe kaynakta "1.234" hem bin iki yüz otuz dört hem de yanlış yazılmış ondalık olabilir. Belirsizse bağlama bak; çözülmezse [kaynakta belirsiz: 1.234] diye işaretle.
4. Koordinatlar, tarih biçimleri ve saat dergi kuralına göre yazılır. Dergi kuralı yoksa kaynaktaki biçim korunur; yalnız ondalık ayırıcı değişir.
5. LaTeX denkleminde Türkçe ondalık virgül `{,}` biçiminde yazılır: `0{,}05`. Denklem içindeki değişken adları değişmez.
6. Birim dönüştürülmez. "ppm" kaynakta varsa "ppm" kalır; dönüşüm gerekiyorsa çevirmen önerir, yazar karar verir.

Kaynak notu: Türkçe ondalık virgül, binlik nokta ve yüzde işaretinin sayıdan önce yazılması Türk Dil Kurumu (TDK) Yazım Kılavuzu kuralı olarak bilinir. Bu skill hazırlanırken tdk.gov.tr ve ikincil kaynak sayfaları bu oturumun ağından açılamadı. Kural birincil kaynakla doğrulanmadı. Bu nedenle üç kural da `params.json` içinde değiştirilebilir parametredir. Bazı Türkçe dergiler ondalık nokta ister; dergi kuralı uygulanır.

## 2. Atıflar ve kaynakça

1. Yazar adı, yıl, harf eki (2020a), sıra ve sayfa değişmez.
2. Yalnız bağlaç ve kısaltma hedef dile uyar:
   - "et al." <-> "ve ark." ya da "vd." (params.json: `etal_target`)
   - "and" <-> "ve"; "&" kaynakçada korunur.
   - "e.g." <-> "örn."; "see" <-> "bkz."; "cited in" <-> "aktaran".
3. Türkçede atıfa ek gelirse iki biçim kullanılır: "Kılıç'a (2020) göre" ve "Kılıç (2020)'a göre". Dergi kuralı varsa o uygulanır; yoksa bir biçim seçilir ve metin boyunca korunur. Statü: skill varsayılanı.
4. Numaralı atıf köşeli parantezde aynı numarayla kalır: [1, 3-5].
5. Kaynakça girdileri çevrilmez. Yalnız bölüm başlığı çevrilir ("References" <-> "Kaynaklar"). Dergi çevrilmiş başlık istiyorsa params.json'da `translate_references: true` yapılır ve özgün başlık korunarak çeviri köşeli parantez içinde eklenir.
6. Türkçe atıf biçimi için `alterlab-tr-academic-style` skill'i varsa ona bakılır.

## 3. Bölüm ve öğe adları

Skill varsayılanı. Türkçe tarım ve toprak dergilerinde yaygın biçimler; dergi kuralı farklıysa o uygulanır.

| İngilizce | Türkçe |
|---|---|
| Abstract | Özet |
| Keywords | Anahtar kelimeler |
| Highlights | Öne çıkanlar |
| Introduction | Giriş |
| Materials and methods | Materyal ve yöntem |
| Results | Bulgular |
| Discussion | Tartışma |
| Results and discussion | Bulgular ve tartışma |
| Conclusion(s) | Sonuç(lar) |
| Acknowledgements | Teşekkür |
| Funding | Finansman |
| Conflict of interest | Çıkar çatışması |
| Author contributions | Yazar katkıları |
| Data availability | Veri erişilebilirliği |
| Supplementary material | Ek materyal |
| References | Kaynaklar |
| Figure 1 | Şekil 1 |
| Table 1 | Çizelge 1 (dergi isterse Tablo 1) |
| Equation (1) / Eq. (1) | Eşitlik (1) ya da Denklem (1); metin içinde tek biçim |

Başlık yazımında hedef dilin kuralı uygulanır. Türkçede büyük harfe çevirirken "i" harfinin büyüğü "İ", "ı" harfinin büyüğü "I" olur: GİRİŞ, BULGULAR. Python'da `str.upper()` bunu yanlış yapar; `scripts/trtext.py` içindeki `tr_upper()` kullanılır.

## 4. Kısaltmalar

1. Kaynak bir kısaltmayı nerede tanımlıyorsa çeviri de orada tanımlar. Özet ve ana metin ayrı okunduğu için ikisinde de tanım gerekebilir.
2. Kaynakta tanımsız kısaltmaya çevirmen tanım eklemez. [?tanımsız kısaltma: X?] diye işaretler; rapor bunu listeler.
3. Türkçe kısaltma yalnız alan sözlüğünde varsa kullanılır (TOK, KDK, BTG, YSA gibi). Türkçe baş harflerden yeni kısaltma üretilmez.
4. Türkçe hedefte yerleşik Türkçe kısaltma yoksa İngilizce kısaltma korunur ve ilk geçişte Türkçe tam ad ile İngilizce açılım birlikte verilir: "ortalama kare hatanın karekökü (root mean squared error, RMSE)".
5. İngilizce hedefte Türkçe kısaltma İngilizce karşılığıyla değişir: TOK -> SOC, KDK -> CEC.

## 5. Savın kesinlik düzeyi

Bilimsel çevirinin en sık anlam hatası, savı güçlendirmek ya da zayıflatmaktır. Çevirmen kaynaktaki düzeyi korur. Aşağıdaki eşlemeler yönlendiricidir; bağlam her zaman belirleyicidir.

| Düzey | İngilizce | Türkçe |
|---|---|---|
| Kesin | show, demonstrate, confirm, establish | göstermiştir, ortaya koymuştur, doğrulamıştır |
| Orta | indicate, suggest, imply, point to | işaret etmektedir, düşündürmektedir |
| Zayıf | may, might, could, possibly, appear, seem | -ebilir, olabilir, muhtemelen, görünmektedir |
| Olasılık | likely, unlikely | büyük olasılıkla, düşük olasılıkla |

Ayrıca korunacaklar:

- **Olumsuzluk ve kapsamı**: "not significantly different" -> "önemli (ya da anlamlı) düzeyde farklı değildir". "Aynıdır" ya da "eşdeğerdir" yazılmaz; istatistiksel fark bulunmaması eşdeğerlik kanıtı değildir.
- **Nedensellik**: "associated with", "correlated with" -> "ile ilişkili". "Neden olur", "etkiler" yazılmaz. Tersi de geçerlidir.
- **Karşılaştırma yönü**: "X was 20% higher than Y" ile "Y was 20% lower than X" aynı şey değildir. Yön korunur.
- **Oran, fark ve yüzde değişim**: "increased by 20%" (göreli artış) ile "increased by 20 percentage points" (yüzde puan farkı) ayrı büyüklüklerdir. "Two-fold" "iki kat" olur; "%200 artış" diye dönüştürülmez.
- **Nicelik sözcükleri**: at least (en az), up to (en çok, -e kadar), approximately (yaklaşık), more than (-den fazla).
- **"respectively" / "sırasıyla"**: eşlenen sıralar değişmez.
- **Örnekleme sözcükleri**: sample (örnek), site (nokta), plot (parsel), replicate (tekerrür), observation (gözlem). Analiz birimini değiştiren çeviri anlamı değiştirir.

## 6. İstatistik ve yöntem dili

1. Simgeler değişmez: p, R2 ya da R², RMSE, n, SD, CI. Kaynakta italikse çeviride de italiktir.
2. "Statistically significant" için tarım bilimlerinde "istatistiksel olarak önemli", sağlık bilimlerinde "anlamlı" geleneği vardır. Bir metinde tek biçim seçilir (alan paketi: A-087 satırı).
3. "Estimation" ve "prediction" toprak metninde "tahmin" diye çevrilir; aynı metinde "kestirim" ile dönüşümlü kullanılmaz (alan paketi: A-035 satırı).
4. "Validation" model doğrulamasıdır; "verification" ile karıştırılmaz.
5. Model geliştirme, bağımsız sınama ve modelin sonraki kullanımı kaynakta ayrı anlatılıyorsa çeviride de ayrı kalır. "Training", "validation", "test" kümeleri birbirine çevrilmez.

## 7. Okunabilirlik

Kullanıcı tercihi:

1. Türkçede 30, İngilizcede 35 sözcüğü geçen cümle anlamı koruyarak aynı paragraf içinde bölünür. Bağlacın taşıdığı mantık ilişkisi (neden, karşıtlık, koşul, amaç) korunur.
2. Yerleşik olmayan, üç ve daha fazla addan kurulu ad zinciri fiille açılır. Örnek: "soil organic carbon stock change prediction uncertainty" -> "toprak organik karbonu stokundaki değişim tahmin edilirken ortaya çıkan belirsizlik".
3. Türkçe bilimsel metinde edilgen yapı ("ölçülmüştür", "belirlenmiştir") yaygındır. İngilizce "we measured" Türkçede "ölçülmüştür" ya da "bu çalışmada ölçülmüştür" olabilir. Öznenin kim olduğu anlamı etkiliyorsa (örnek: önceki çalışma mı, bu çalışma mı) açıkça yazılır.
4. İki dil aynı cümlede karıştırılmaz. İngilizce terim yalnız ilk geçişte parantez içinde verilir.
5. U+2013 (en dash), U+2014 (em dash) ve U+2212 (eksi işareti) kullanılmaz. Yerine kısa çizgi, virgül ya da iki nokta.

## 8. Adlar

1. Kişi adları değişmez; Türkçe karakterler korunur (Kılıç, Öztürk).
2. Türkiye'deki yer adları Türkçe yazımla kalır: İzmir, Şanlıurfa, Doğu Anadolu. İngilizce hedefte bölge adı için yaygın İngilizce biçim kullanılabilir (Eastern Anatolia); dergi kuralına bakılır.
3. Ülke adı: İngilizce hedefte "Türkiye" (skill varsayılanı). Hedef dergi "Turkey" istiyorsa dergi kuralı uygulanır. Kaynak metinde geçen özgün ad, alıntı ve kaynakça girdisi değiştirilmez.
4. Kurum ve fon kuruluşu adlarında kurumun kendi sitesindeki resmî İngilizce ya da Türkçe ad kullanılır. Terim araştırmacısı adresi sözlüğe yazar.
5. Proje numarası, hibe numarası ve etik kurul karar numarası değişmez.

## 9. Şekil ve çizelge

1. Şekil ve çizelge başlıkları çevrilir; numaraları değişmez.
2. Görselin içindeki metin çevrilmez. Yönetici şekil içi metni raporda listeler; yazar isterse görseli yeniden üretir.
3. Çizelge hücresindeki sayı, birim ve kısaltma kuralları metindekiyle aynıdır.
4. Çizelge dipnot imleri (a, b, *, **) ve anlamları değişmez.
