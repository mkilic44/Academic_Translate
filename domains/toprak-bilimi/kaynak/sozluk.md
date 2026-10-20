# Ortak toprak bilimi terminoloji sözlüğü

Sürüm: 1.2. Tarih: 17 Eylül 2026.
Kaynak: MIRAC'ın bağlayıcı olarak verdiği eşdeğerler. Claude kalıcı belleğindeki `/topics/soil-terminology.md` dosyasından (sürüm ca5f922f8347, güncelleme 06.08.2026) dışa aktarıldı.

## Kullanım kuralı

1. Bu dosya, Claude, ChatGPT, Codex, Antigravity, Copilot ve diğer bütün araçlar için tek ortak terminoloji kaynağıdır. Bir terim burada varsa, yakın anlamlısı kullanılmaz.
2. Türkçeden İngilizceye ya da tersine yazarken birebir çeviri yapılmaz; buradaki karşılık kullanılır.
3. Yeni terim kararı alınırsa yalnızca bu dosyaya yazılır, sürüm numarası artırılır. Model belleğine, prompt'a ya da ayrı bir nota yazılmaz.
4. Metin yazıldıktan sonra son dosya bu sözlüğe karşı kontrol edilir. Yazım sırasında hatırlanmış olması yeterli sayılmaz.
5. Sözlükte olmayan bir terim için çalışmaya özgü bir ad üretiliyorsa, o ad metinde açıkça tanımlanır ve yerleşik bir terimmiş gibi sunulmaz.
6. Bu sözlükte bulunmayan terim için sırayla şuralara bakılır: `toprak-bilimi-uzmani` skill'indeki alan dosyalarının "Yerleşik terimler" bölümü, sonra aşağıdaki genişletme önerileri. Oralarda da yoksa ad uydurulmaz; kavram düz cümleyle anlatılır ve İngilizce terim parantez içinde verilir.

## Fiziksel özellikler

- toprak tekstürü = soil texture; tekstür sınıfı = textural class; kum / silt / kil = sand / silt / clay
- hacim ağırlığı = bulk density (asla "volume weight" değil); tane yoğunluğu = particle density
- toprak strüktürü = soil structure; agregat stabilitesi = aggregate stability
- gözeneklilik = porosity; hidrolik iletkenlik = hydraulic conductivity; infiltrasyon = infiltration
- tarla kapasitesi = field capacity; solma noktası = permanent wilting point; yarayışlı su tutma kapasitesi = available water capacity
- toprak sıkışması = soil compaction; penetrasyon direnci = penetration resistance; kabuk bağlama = surface crusting
- su tutma eğrisi = soil water retention curve; toprak nemi = soil moisture / soil water content

## Kimyasal özellikler

- katyon değişim kapasitesi (KDK) = cation exchange capacity (CEC); baz doygunluğu = base saturation
- toprak organik karbonu (TOK) = soil organic carbon (SOC); organik madde = soil organic matter
- elektriksel iletkenlik = electrical conductivity; tuzluluk = salinity; sodyumluluk = sodicity
- değişebilir sodyum yüzdesi = exchangeable sodium percentage; sodyum adsorpsiyon oranı = sodium adsorption ratio
- toprak reaksiyonu = soil reaction; kireç içeriği = calcium carbonate content / calcareousness (asla "lime content" değil)
- alınabilir fosfor = available phosphorus; değişebilir katyonlar = exchangeable cations; jips = gypsum

## Pedoloji ve morfoloji

- horizon = horizon; profil tanımlaması = profile description; solum = solum
- ana materyal = parent material; toprak oluşumu = pedogenesis / soil formation; toprak oluş faktörleri = soil-forming factors
- büyük toprak grubu (BTG) = great soil group; toprak serisi = soil series
- eluviasyon / illüviyasyon = eluviation / illuviation; kil zarfı (kutan) = clay coating (argillan)
- lekelenme = mottling / redoximorphic features; etkili kök derinliği = effective rooting depth
- taşlılık = rock fragment content / stoniness; drenaj = drainage

## Arazi, bozulum, yönetim

- arazi bozulumu (bozulması) = land degradation; toprak bozulumu = soil degradation. "deterioration" hiçbir bağlamda kullanılmaz.
- organik madde bozunması = organic matter decomposition (degradation ile karıştırılmaz)
- ayrışma = weathering; mineralizasyon = mineralization; çölleşme = desertification
- tuzlulaşma = salinization; sodyumlaşma = sodification; erozyon = erosion
- toprak verimliliği = soil fertility (productivity değil); arazi üretkenliği = land productivity
- toprak işleme = tillage; korumalı toprak işleme = conservation tillage; anız = crop residue / stubble
- ıslah = reclamation / amelioration ("improvement" değil); münavebe = crop rotation
- arazi kullanımı = land use; arazi örtüsü = land cover; arazi değerlendirme = land evaluation
- toprak etüdü ve haritalama = soil survey and mapping; arazi kullanım kabiliyet sınıfı = land capability class
- toprak kalitesi = soil quality; toprak sağlığı = soil health (ayrı kavramlar, birleştirilmez)

## Sayısal haritalama ve istatistik

- sayısal toprak haritalama = digital soil mapping; yardımcı / çevresel değişkenler = environmental covariates
- örnekleme deseni = sampling design; mekânsal otokorelasyon = spatial autocorrelation
- yarı-variogram = semivariogram; külçe etkisi = nugget; eşik = sill; etki mesafesi = range
- çapraz doğrulama = cross-validation; bağımsız doğrulama = independent validation; belirsizlik = uncertainty

## Türkçe literatürde gerçekten değişkenlik gösteren terimler

Bu çiftlerin her iki biçimi de literatürde geçiyor. Bir el yazması içinde biri seçilir ve sonuna kadar korunur.

- tekstür / bünye
- strüktür / yapı
- silt / mil
- KDK / KEK
- kriging / krigleme

## Genişletme önerileri (MIRAC onayı bekliyor)

17 Eylül 2026'da iki öneri listesi hazırlandı. Listeler 220 terim içerir ve her terim için Türkçe hakemli yayınlardan kullanım kanıtı verir.

- `D:/AI_CENTRE/incelemeler/005_sozluk_onerileri_A.md`: sayısal toprak haritalama, jeoistatistik, makine öğrenmesi, derin öğrenme, istatistik ve araştırma tasarımı, büyük dil modelleri.
- `D:/AI_CENTRE/incelemeler/005_sozluk_onerileri_B.md`: toprak spektroskopisi, toprak etüdü ve haritalama, sınıflandırma, arazi değerlendirme, toprak ve su koruma, toprak verimliliği ve bitki besleme, laboratuvar yöntemleri.

Bu listeler bağlayıcı değildir. Durumları şöyle okunur:

- "yerleşik": tek baskın kullanım vardır; o kullanılır.
- "değişken": birden fazla yaygın kullanım vardır. MIRAC aksini söyleyene kadar listede önerilen biçim kullanılır ve bir el yazması içinde tek biçim korunur.
- "yerleşmemiş": tutarlı Türkçe kullanım yoktur. İngilizce terim ilk geçtiği yerde bir cümleyle açıklanarak kullanılır; Türkçe ad uydurulmaz.

Kanıt sınırı: kullanım taraması TR Dizin kayıtlarının başlık ve özetleriyle yapıldı. DergiPark ve YÖK Tez taranamadı. "Kanıt bulunamadı" sonucu terimin kullanılmadığını göstermez. MIRAC'ın onayladığı terimler yukarıdaki bağlayıcı bölümlere taşınır ve öneri listesinden düşülür.

MIRAC kararı bekleyen örnekler: ortanca ya da medyan; kestirim ile tahmin ayrımı; "tasarım temelli çıkarım" ve "bileşimsel veri" karşılıkları; Nash-Sutcliffe katsayısı için "verimlilik" sözcüğünün toprak verimliliğiyle karışması.

## Kısaltma kuralı

1. Kısaltma bağımsız okunabilen bölümde ilk gerekli kullanımında tam terimle birlikte verilir: "toprak organik karbonu (TOK)", "katyon değişim kapasitesi (KDK)", "ortalama kare hatanın karekökü (root mean squared error, RMSE)". RMSE, tahmin ile gözlem arasındaki farkların karelerinin ortalamasının kareköküdür; hata bileşeni olmayan genel RMS işlemiyle karıştırılmaz. [Tanım kaynağı: scikit-learn, Mean squared error](https://scikit-learn.org/stable/modules/model_evaluation.html#mean-squared-error).
2. Tanımlanmadan kısaltma kullanılmaz.
3. Uydurma kısaltma üretilmez.
4. Özet ve ana metin ayrı okunabildiği için kısaltma her birinde gerektiğinde tanımlanır. Yeni alt başlık veya kod bloğu tek başına yeniden açma gerekçesi değildir; yeniden tanımlama bağımsız okunabilirlik ve hedef belgenin koşullarına göre yapılır.
5. Bir açıklamanın tamamı kısaltmalardan kurulmaz.

## Sürüm notu

1.1: Akademik skill düzenlemesi sırasında RMSE örneğine eksik hata bileşeni eklendi; kısaltmaları her bölüm ve kod bloğundan sonra yeniden açma zorunluluğu kaldırıldı. Diğer terim eşleştirmeleri bu değişiklikte yeniden doğrulanmadı.

1.2: Kullanım kuralına 6. madde ve "Genişletme önerileri" bölümü eklendi. Bağlayıcı terim eşleştirmeleri değiştirilmedi.
