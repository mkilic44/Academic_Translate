# Tersine mühendislik raporu: senshinji/claude-translation-skill

Bu rapor, kaynak skill'in nasıl çalıştığını kanıta bağlı olarak çözümler ve Türkçe-İngilizce bilimsel makale çevirisi için yapılan uyarlama kararlarını gerekçelendirir.

## 1. Kapsam ve yöntem

- **Hedef**: [github.com/senshinji/claude-translation-skill](https://github.com/senshinji/claude-translation-skill), commit `42d6c8a2a07b77f085d6cafe6d4102d36aeafd02` (12 Mart 2026, "Initial release"). 12 dosya: `SKILL.md` (493 satır), beş başvuru dosyası, iki kabuk betiği, CI dosyası, README, lisans.
- **İstenen araç**: `/reverse-engineer-anything`, yani [morluto/rea](https://github.com/morluto/rea) deposundaki REA skill'i (SKILL.md `metadata.version: "43"`). REA'nın kendi SKILL.md dosyası aracı derlenmiş ikili dosya, paket ve çalışma zamanı kanıtı için tanımlar. Tam kaynağı bulunan bir depo için şunu söyler: "For ordinary analysis of a complete source repository, use normal repository tools and do not run REA readiness or provider commands."
- **Uygulanan yöntem**: Hedef depo yalnız Markdown, iki kabuk betiği ve bir CI dosyasından oluşur; kaynağın tamamı okunabilir. Bu yüzden REA MCP sunucusu kurulmadı ve REA araçları çalıştırılmadı. REA'nın inceleme disiplini elle uygulandı: önce soru listesi, her sonucun kanıta bağlanması, gözlem, çıkarım ve bilinmeyen ayrımı, sonda soru listesinin yeniden denetlenmesi.
- **Kanıt türleri**: dosya okuma (satır numarasıyla) ve betik çalıştırma (komut ve sonuçla).

## 2. Soru listesi

1. Skill hangi rolleri, hangi sırayla, hangi sözleşmelerle çalıştırıyor?
2. Hangi kısımlar dil çiftinden ve belge türünden bağımsız?
3. Hangi kısımlar Çince kaynağa ve konferans belgesine özgü?
4. Sınamalar neyi sınıyor, neyi sınamıyor?
5. Bilimsel makale ve Türkçe-İngilizce çifti için ne eksik?

## 3. Gözlemler

Gözlem: dosyada okunan ya da çalıştırılarak görülen olgu. Satır numaraları kaynak commit içindir.

| No | Gözlem | Kanıt |
|---|---|---|
| G1 | Dört ajan rolü vardır: yönetici, çevirmen (Sonnet), terim araştırmacısı (Sonnet; 50'den fazla terimde "fast" ve "deep" diye ikiye ayrılır), denetçi (Opus) | SKILL.md:150-160 |
| G2 | Üç sözleşme tanımlanır: terim sözlüğü JSON şeması, denetçi bulgu biçimi, çalışma klasörü yolları. Her ajan yalnız kendi dosyasını yazar | SKILL.md:94-122; ajan istemlerindeki OWNERSHIP blokları |
| G3 | .doc ve .docx kaynak macOS'a özgü `textutil -convert html` ile çevrilir | SKILL.md:61; references/test-translation-structure.sh:30 |
| G4 | Agent Teams deneysel bayrağı (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`) ve `TeamCreate` gerekir | SKILL.md:45-46, 128 |
| G5 | Parçalama sayfa tahminine dayanır: yaklaşık 35 paragraf 1 sayfa, sınır 10 sayfa | SKILL.md:68; references/scaling-guidelines.md:8 |
| G6 | Terim sayısı Çince kurum ekleriyle (协会/委员会/公司) ve sayfa başına 8-10 özel ad varsayımıyla tahmin edilir | SKILL.md:130-132 |
| G7 | Güven düzeyi: high = 2 ya da daha çok kaynak, medium = 1 kaynak. Kaynakların bağımsızlığı tanımlanmaz | SKILL.md:100, 290 |
| G8 | Denetçi ileri geçiş (çeviriden kaynağa, uydurma) ve geri geçiş (kaynaktan çeviriye, eksiltme) yapar | SKILL.md:487; references/anti-fabrication-checklist.md |
| G9 | Bulgu türleri: FABRICATION, OMISSION, TERMINOLOGY, ACCURACY, STRUCTURE, REGISTER. Savın kesinlik düzeyi, olumsuzluk ya da nedensellik için ayrı tür yoktur | references/review-feedback-schema.md, "Issue Type Reference" |
| G10 | Dizgi: İngilizce Times New Roman, Çince SimSun; .docx ve .pdf ikisi de zorunlu | SKILL.md:466, 472 |
| G11 | Çinceye özgü kurallar ve örnekler: pinyin, 美泉宫厅 salon adı | SKILL.md:231-232; references/glossary-schema.md:95 |
| G12 | Yapı kuralları konferans programı hatalarından türetilmiştir: ulaşım çizelgesinin başlığa dönüşmesi, bir hücredeki 10 sunumun dışarı taşması, yemek bilgisinin çizelgeye dönüşmesi | SKILL.md:192-200 |
| G13 | `test-skill-integrity.sh` 32 dize varlık denetimi yapar (aşama adları, dosya adları, "WEB SEARCH FALLBACK" gibi). Çeviri davranışını sınamaz. Çalıştırıldı: 32 geçti, 0 kaldı | references/test-skill-integrity.sh |
| G14 | `test-translation-structure.sh` `set -euo pipefail` altında `((PASS++))` kullanır. PASS=0 iken bu aritmetik ifade 0 değerini verir ve komut 1 çıkış koduyla biter; `set -e` betiği durdurur. Çalıştırıldı: 1 çizelgeli eşleşen kaynak ve çeviriyle betik "[PASS] Table count" yazdı ve çıkış kodu 1 ile durdu; tablo karşılaştırmasına ve özete ulaşmadı | references/test-translation-structure.sh:5, 130 |
| G15 | "real failures" ve "13 structure failures" savları için depoda veri, kayıt ya da sınama dosyası yoktur | SKILL.md:192, 251 |
| G16 | Sayı denetimi denetçinin elle yaptığı iştir; betik yoktur. Ondalık ayırıcı dönüşümü tanımlı değildir | SKILL.md, "ACCURACY CHECK" bölümü; references/ dizini |

## 4. Çıkarımlar

Çıkarım: gözlemlerden türetilen, doğrudan görülmeyen yargı.

| No | Çıkarım | Dayandığı gözlem |
|---|---|---|
| Ç1 | Dil çiftinden bağımsız ve korunmaya değer çekirdek: dosya sahipliği, sözleşmeler, ileri ve geri geçiş, yapı envanteri ile çevirmenin yapı raporunun karşılaştırılması, düzeltmede yapıyı değiştirmeme kuralı | G1, G2, G8 |
| Ç2 | Skill bir konferans belgesi çevirisinden doğmuştur. Ağırlık yapısal hatalardadır; bilimsel anlam hataları (kesinlik düzeyi, nedensellik, istatistiksel önem ile eşdeğerlik) kapsanmaz | G9, G12 |
| Ç3 | Sonnet ve Opus ataması hız ile doğruluk dengesi içindir. İki model aynı ailedendir; denetçi okuması bağımsız uzman gözlemi sayılamaz | G1 |
| Ç4 | Terim doğrulaması genel web aramasına dayanır. Türkçe bilimsel terimde genel web araması makine çevirisi ve birbirini kopyalayan sayfalar getirir; "2 kaynak" ölçütü bu durumda güveni şişirir. Kanıtlı, kullanıcıya ait bir alan sözlüğü daha güçlü bir başlangıçtır | G7 |
| Ç5 | Türkçe-İngilizce çiftinde ondalık ayırıcı değiştiği için sayı hatası Çince-İngilizce çiftinden daha olasıdır. Bu yüzden sayı denetimi elle bırakılamaz | G16 |
| Ç6 | Kaynak sınamalar skill'in çeviri davranışını güvenceye almaz; yapı sınaması da G14 nedeniyle bugünkü haliyle kullanılamaz | G13, G14 |

## 5. Bilinmeyenler

| No | Bilinmeyen | Sonuç |
|---|---|---|
| B1 | Agent Teams araçlarının (`TeamCreate`, görev bağımlılıkları) bugünkü durumu. Depo Mart 2026 tarihlidir | Uyarlama her ortamda bulunan `Agent` aracını temel aldı; takım modu isteğe bağlı bırakıldı |
| B2 | 10 sayfa ve 50 terim eşiklerinin ölçülüp ölçülmediği | Depoda ölçüm kaydı yok. Uyarlamadaki 300 ve 6000 sözcük eşikleri de ölçülmüş değildir; skill varsayılanı olarak işaretlendi |
| B3 | Kaynak skill'in hangi model sürümleriyle sınandığı | Bilinmiyor |

## 6. Uyarlama kararları

| Öğe | Kaynak skill | Uyarlama | Gerekçe |
|---|---|---|---|
| Roller ve dosya sahipliği | 4 rol, sahiplik blokları | Korundu | Ç1 |
| Sözleşmeler | 3 sözleşme | Korundu; sözlük şemasına `status`, `enforce`, `forbidden`, `alternatives`, `abbreviation`, `consistency_groups` eklendi | Alan sözlüğünün durum değerleri ve otomatik denetim için |
| Kaynak dönüşümü | `textutil` (macOS) | pandoc, python-docx, pdftotext, PyMuPDF; `prepare_source.py` | G3; platform bağımsızlığı |
| Ajan altyapısı | Agent Teams zorunlu | `Agent` aracı varsayılan; takım isteğe bağlı | G4, B1 |
| Parçalama | Sayfa tahmini | Sözcük sayısı; H1/H2 sınırı; parça başlıkla bitmez; kaynakça ayrı | G5; bilimsel makalede paragraf uzunluğu çok değişir |
| Terim sayısı tahmini | Çince kurum ekleri | Alan paketinden tohum sözlük (`seed_glossary.py`) | G6 |
| Terim araştırmacısı | 1 ya da 2 (50 terim eşiği) | 1; tohumlanmayan terim 60'ı geçerse 2 | Tohum sözlük araştırma yükünü azaltır |
| Güven ölçütü | 2+ kaynak | Farklı yazar gruplarından 2+ hakemli yayın; kopya sayfa ve makine çevirisi kanıt değil | Ç4 |
| Bulgu türleri | 6 tür | + MEANING_SHIFT, NUMERIC, CITATION, ABBREVIATION, READABILITY, TYPOGRAPHY | Ç2, Ç5 |
| Sayı ve atıf denetimi | Elle | `qa_checks.py`: ondalık ayırıcıya duyarlı sayı karşılaştırması, yazar-yıl ve numaralı atıf, DOI, kaynakça | G16, Ç5 |
| Yapı sınaması | bash/awk, çıkış kodu hatalı | Python: Markdown ve HTML çizelge, başlık düzeyi, şekil ve çizelge numarası, denklem, liste, paragraf | G14 |
| Terim denetimi | Denetçi elle | `qa_checks.py`: Türkçe ek almış biçimleri yakalayan sezgisel eşleşme, yasak biçim, değişken çiftlerin karışımı | Kullanıcının bağlayıcı sözlüğünü denetlenebilir kılmak için |
| Dizgi | TNR + SimSun, .pdf zorunlu | TNR; dergi şablonu öncelikli; .pdf isteğe bağlı | G10 |
| Dil özgü örnekler | Çince | Türkçe-İngilizce bilimsel örnekler; Çince örnekler kaldırıldı | G11 |
| Rapor | Yok | Çeviri raporu; kapsam ayrımı; büyük dil modeli kullanım kaydı | Ç3; kullanıcı raporlama kuralı |
| Sınama | 32 dize varlık denetimi | Davranış sınamaları (sentetik iyi ve hatalı çeviriyle) ve bütünlük sınamaları | Ç6 |

## 7. Soru listesinin son denetimi

| Soru | Durum | Dayanak |
|---|---|---|
| 1. Roller, sıra, sözleşmeler | Yanıtlandı | G1, G2, G8 |
| 2. Dil çiftinden bağımsız kısımlar | Yanıtlandı | Ç1 |
| 3. Çinceye ve konferans belgesine özgü kısımlar | Yanıtlandı | G3, G5, G6, G10, G11, G12 |
| 4. Sınamaların kapsamı | Yanıtlandı | G13, G14 |
| 5. Bilimsel makale ve Türkçe-İngilizce için eksikler | Yanıtlandı | Bölüm 6 |

Sınama durumu:

- Betikler sentetik sınama metinleriyle sınandı (`tests/`).
- Çok ajanlı akışın tamamı sentetik kaynak üzerinde bir kez uçtan uca çalıştırıldı; çıktılar ve çeviri raporu [ornek-calisma](ornek-calisma/README.md) klasöründedir. Bu çalıştırma dört sorun ortaya çıkardı ve dördü giderildi: çevirmen isteminde aşamanın belirtilmemesi, çözülmemiş çevirmen işaretlerinin denetlenmemesi, yapı envanterinin bölüm numaralarını sayı sayması, sözlük birleştirmede araştırmacı kararının kaybolması.
- Gerçek bir makale üzerinde çalıştırılmadı. Gerçek bir makaleyle ilk çalıştırmada ajan istemlerinin davranışı, eşiklerin uygunluğu ve terim araştırmacısının ağ erişimli bir ortamda kaynak açabilmesi ayrıca değerlendirilmelidir.
