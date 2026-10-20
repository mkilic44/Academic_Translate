# Uydurma, eksiltme ve anlam kaymasını önleme

Bilimsel çeviride en büyük risk, kaynakta olmayan bir içeriğin çeviriye girmesi ya da kaynaktaki savın değişmesidir. Bu dosya çevirmenin önleme, denetçinin yakalama yöntemidir.

## Çevirmen: önleme

### Çeviriden önce

- [ ] Kaynağın tamamını oku; kapsamını ve sınırlarını not et.
- [ ] Belge türünü ve bölüm düzenini belirle.
- [ ] Okunamayan ya da belirsiz yerleri baştan işaretle.

### Çeviri sırasında

- [ ] Paragraf paragraf çevir; her paragraf için kaynağı yeniden oku, sonra yaz.
- [ ] Emin olmadığın terimi [?terim: kaynak terim?] diye işaretle.
- [ ] Belirsiz yeri [kaynakta belirsiz: ...] diye işaretle; tahminle doldurma.
- [ ] Açıklama, değerlendirme, geçiş cümlesi ekleme.
- [ ] Sayıyı yuvarlama; birimi dönüştürme.
- [ ] Belirli içeriğin yerine genel bir özet yazma.
- [ ] Savın kesinlik düzeyini koru (bkz. bilimsel-ceviri-kurallari.md, bölüm 5).

### Yüksek riskli alanlar

| Alan | Yanlış | Doğru |
|---|---|---|
| Kesinlik düzeyi | "suggest" -> "kanıtlamaktadır" | "düşündürmektedir" |
| Olumsuzluk | "not significantly different" -> "aynıdır" | "önemli düzeyde farklı değildir" |
| Nedensellik | "associated with" -> "neden olmuştur" | "ile ilişkilidir" |
| Karşılaştırma | "20% higher than" -> "%20'si kadar" | "%20 daha yüksek" |
| Yüzde puan | "increased by 5 percentage points" -> "%5 artmıştır" | "5 yüzde puan artmıştır" |
| Ondalık | "0.50" -> "0,5" | "0,50" |
| Ondalık ayırıcı | Türkçe metinde "1.35" | "1,35" |
| Atıf | "(Smith et al., 2019a)" -> "(Smith ve ark., 2019)" | "(Smith ve ark., 2019a)" |
| Örnekleme birimi | "120 samples from 40 sites" -> "120 noktadan örnek" | "40 noktadan 120 örnek" |
| Tekrar | "three replicates" -> "üç örnek" | "üç tekerrür" |
| Takson adı | "Typic Haploxerept" -> "Tipik Haploksereptler" | "Typic Haploxerept" |
| Kısaltma | Kaynakta tanımsız "BD" için tanım uydurmak | [?tanımsız kısaltma: BD?] |
| Kurum adı | Resmî adı aramadan çevirmek | Kurumun kendi sayfasındaki resmî ad |
| Eksik içerik | Okunamayan yeri akla yatkın içerikle doldurmak | [kaynakta belirsiz: ...] |

## Denetçi: yakalama

### Sistematik karşılaştırma

1. **İleri geçiş (çeviriden kaynağa)**: çevirideki her paragrafın kaynaktaki karşılığını bul. Karşılığı olmayan paragrafı ve kaynaktan fazlasını söyleyen cümleyi işaretle.
2. **Geri geçiş (kaynaktan çeviriye)**: kaynaktaki her paragrafın çevirideki karşılığını bul. Karşılığı olmayanı işaretle.
3. **Sayılar**: `qa_checks.py` sayı denetimini kullan. Her adayı kaynağa bakarak doğrula ya da reddet. Betiğin kapsamadığı yazıyla sayıları (three, üç) elle denetle.
4. **Atıflar**: `qa_checks.py` atıf denetimini kullan. Yazar sırasını ve "a, b" eklerini elle de denetle.
5. **Kesinlik düzeyi**: kaynakta her "may, might, could, suggest, indicate, likely, appear" ve Türkçe karşılıkları (-ebilir, olabilir, düşündürmektedir, işaret etmektedir) için çevirideki karşılığa bak.
6. **Terimler**: sözlükteki her terimi çeviride bul; doğru bağlamda kullanıldığını oku.

### Uydurma belirtileri

- Kaynakta belirsiz olan bir şeyin çeviride kesin ayrıntıyla anlatılması.
- Kaynakta olmayan değerlendirme: "önemli bir katkı", "ilk kez", "çarpıcı biçimde".
- Kaynakta olmayan bağlam: "bölgenin en verimli toprakları".
- Çıkarımın olgu gibi sunulması: "artma eğiliminde" -> "artmıştır".
- Çizelgede kaynakta olmayan satır ya da sütun.
- Listede fazladan madde.
- Yöntem bölümünde kaynakta olmayan ayar ya da adım (örnek: tohum değeri, katman sayısı).

### Önem sınıfları

| Uydurma türü | Önem | Örnek |
|---|---|---|
| Uydurma sayı, bulgu, yöntem adımı | Kritik | Kaynakta olmayan örnek sayısı |
| Uydurma ad, kurum, kaynak | Kritik | Kaynakta olmayan fon kuruluşu |
| Kesinlik düzeyini değiştirmek | Kritik | "suggest" -> "göstermiştir" |
| Değerlendirme ekleme | Büyük | "önemli bir katkı sağlamıştır" |
| Küçük süsleme | Küçük | "bildirmiştir" -> "özellikle vurgulamıştır" |
| Yapısal ekleme | Kritik | Fazladan çizelge satırı |

## Düzeltmeden sonra

- [ ] UYDURMA olarak işaretlenen her yer düzeldi mi?
- [ ] EKSİLTME olarak işaretlenen her yer geri geldi mi?
- [ ] ANLAM KAYMASI olarak işaretlenen her yer kaynağın düzeyine döndü mü?
- [ ] `qa_checks.py` yeniden çalıştı mı ve kritik aday kaldı mı?
- [ ] Rastgele 5 paragraf yeniden karşılaştırıldı mı?
- [ ] Başlık, paragraf ve çizelge sayıları kaynakla uyuşuyor mu?
