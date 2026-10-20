# Toprak bilimi: çeviri tuzakları

Bu dosya yeni terim kararı içermez. Her madde kullanıcının sözlüğünden (`kaynak/sozluk.md`) ya da öneri listelerinden (`kaynak/terim_onerileri_A.md`, `kaynak/terim_onerileri_B.md`) alınmıştır; satır numarası `oneriler.json` içindeki kimliktir. Öneri listeleri bağlayıcı değildir; bağlayıcı sözlük önce gelir.

## Bağlayıcı sözlükteki yalancı eşdeğerler

| Kavram | Doğru | Kullanılmayacak | Kaynak |
|---|---|---|---|
| bulk density | hacim ağırlığı | volume weight | sozluk.md |
| kireç içeriği | calcium carbonate content / calcareousness | lime content | sozluk.md |
| arazi bozulumu, toprak bozulumu | land degradation, soil degradation | deterioration (hiçbir bağlamda) | sozluk.md |
| organik madde bozunması | organic matter decomposition | degradation ile karıştırılmaz | sozluk.md |
| toprak verimliliği | soil fertility | productivity (arazi üretkenliği = land productivity) | sozluk.md |
| ıslah | reclamation / amelioration | improvement | sozluk.md |
| toprak kalitesi, toprak sağlığı | soil quality, soil health | ikisi birleştirilmez | sozluk.md |

Bağlayıcı sözlükte iki biçimi de geçerli olan ve bir metinde tek biçimle korunacak çiftler: tekstür / bünye, strüktür / yapı, silt / mil, KDK / KEK, kriging / krigleme. `qa_checks.py` aynı metinde iki biçimin birlikte kullanılmasını bildirir.

## Aynı sözcüğün alan içinde iki anlamı

- **verimlilik**: sözlükte fertility karşılığıdır. Nash-Sutcliffe efficiency için önerilen "Nash-Sutcliffe verimlilik katsayısı" biçiminde efficiency anlamındadır; ilk geçişte İngilizcesi verilir (A-078).
- **duyarlılık**: makine öğrenmesinde recall; erozyon ve heyelan çalışmalarında susceptibility (A-052).
- **artıklar**: tarım yayınlarında bitkisel atık anlamında da geçer. Residuals için "artık değerler" ya da "regresyon artıkları"; "kalıntı" kullanılmaz (A-093).
- **torbalama**: tarım yayınlarında meyve ve salkım torbalama. Bagging için kullanılmaz (A-050).
- **etmen**: tarım yayınlarında hastalık etmeni ve faktör. Dil modeli bağlamında agent için "ajan" (A-107).
- **covariate**: sayısal toprak haritalamada sözlükteki "yardımcı / çevresel değişken"; kovaryans analizinde "ortak değişken" (A-080).
- **uç değer**: extreme value karşılığıdır; outlier için "aykırı değer" (A-089).
- **veri sızıntısı**: Türkçe yayınlarda çoğunlukla bilgi güvenliği ihlali. Model doğrulama anlamında ilk geçişte tanımlanır (A-055).
- **aşırı öğrenme**: extreme learning machine yönteminin adıyla karışır; overfitting için "aşırı uyum" (A-044).

## İstatistik ve deneme dili

- **statistically significant**: tarım bilimlerinde "istatistiksel olarak önemli", sağlık ve sosyal bilimlerde "anlamlı". Bir metinde tek biçim; "önemli" seçilirse "istatistiksel olarak" nitelemesi atlanmaz (A-087).
- **estimation / prediction**: toprak metninde "tahmin"; "kestirim" ile dönüşümlü kullanılmaz (A-035).
- **replication / replicate**: "tekerrür". Tekerrür bağımsız deneme ünitesidir; aynı üniteden alınan alt örnek ya da laboratuvar yinelemesi tekerrür değildir (A-083, B-095). Çeviri, kaynağın analiz birimini değiştirmemelidir.
- **pseudoreplication**: yerleşik Türkçe karşılık yok; İngilizce terim açıklanarak kullanılır (A-084).

## Sınıflandırma adları

- Soil Taxonomy ordo adları özgün yazımla kalır: Entisol, Inceptisol, Vertisol (B-045).
- Tanı horizonu adları özgün yazımla kalır: argillic horizon; bir metinde iki yazım karıştırılmaz (B-041).
- WRB: tam adı bir kez verilir, sonra WRB (B-038).
- 1938 sisteminin büyük toprak grubu adları (kırmızı Akdeniz toprakları, kahverengi orman toprakları) Toprak Taksonomisi ya da WRB sınıfının çevirisi gibi sunulmaz (B-049).
- 5403 sayılı Kanun'daki tarım arazisi sınıfları yasal sınıflardır. İngilizce metinde başka ülkelerin sınıf adlarıyla eşleştirilmez; Türkçe ad korunur ve açıklanır (B-062).

## Sıfat tutarlılığı

- **plant-available**: sözlük fosfor için "alınabilir" der; öteki elementlerde de aynı sıfat kullanılır (B-090).
- **spatial**: bütün bileşiklerde "mekânsal" (mekânsal dağılım, mekânsal değişkenlik, mekânsal bağımlılık). Aynı makalede "konumsal", "alansal" ve "uzaysal" karıştırılmaz (A-030, B-032).

## Karşılığı yerleşmemiş kavramlar

Öneri listelerinde "yerleşmemiş" durumundaki terimler için Türkçe ad uydurulmaz. İngilizce terim ilk geçişte bir cümleyle açıklanır. Örnek: "önceki etütlerden kalan toprak verileri (legacy soil data)" (A-014). Bu terimlerin tam listesi `oneriler.json` içinde `"status": "yerleşmemiş"` olan girdilerdir. Kaynak listeler, yerleşmemiş terimlerin nottaki açıklamalarının ayrı bir kaynakla doğrulanmadığını belirtir (terim_onerileri_B.md, Yöntem ve sınırlar, madde 9).
