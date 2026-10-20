# Ölçekleme: mod eşikleri, parçalama, birleştirme

## Mod eşikleri

Eşik birimi ana metnin sözcük sayısıdır. Kaynakça sayılmaz. `prepare_source.py` bu sayıyı `structure-manifest.md` dosyasına yazar.

| Ana metin | Mod | Çevirmen | Terim araştırmacısı | Denetçi |
|---|---|---|---|---|
| < 300 sözcük | Hafif | yönetici | yok (tohum sözlük yeterli; eksik terimi yönetici arar) | yok; `qa_checks.py` çalışır |
| 300 - 6000 | Tam | 1 | 1 | 1 |
| 6000 - 12000 | Parçalı | 2 | 1 | 1 |
| 12000 - 30000 | Parçalı | 3 - 5 | 1 | 1 |
| > 30000 (tez, kitap) | Parçalı | 5+ | 1 | 2 (bölüm gruplarına ayrılır) |

Eşikler skill varsayılanıdır; ölçülmüş bir kalibrasyona dayanmaz. Kaynak skill sayfa ve paragraf sayısıyla çalışıyordu (yaklaşık 35 paragraf = 1 sayfa, 10 sayfa sınırı). Bilimsel makalede paragraf uzunluğu çok değiştiği için sözcük sayısı seçildi. 6000 sözcük, kaynakça hariç tipik bir araştırma makalesinin tek çevirmene verilebilecek üst sınırı olarak alındı. Kullanıcı sınırı `--chunk-words` ile değiştirebilir.

## Parçalama kuralları

`prepare_source.py prepare --chunk-words N` şu kurallarla böler:

1. Önce H1 ve H2 başlık sınırları kullanılır. IMRaD düzeninde (Giriş, Materyal ve yöntem, Bulgular, Tartışma) her bölüm genellikle bir parça olur.
2. Tek bölüm sınırı aşarsa paragraf sınırında bölünür.
3. Çizelge ve kod bloğu ortasından bölünmez; boş satırla ayrılmış blok bölünmez.
4. Parça başlıkla bitmez; başlık, ait olduğu metinle sonraki parçaya geçer.
5. Çevrilecek sözcüğü olmayan parça (yalnız yorum) sonraki parçaya katılır.
6. Kaynakça parçalara girmez; `references.md` dosyasına ayrılır ve birleştirmede sona eklenir.

## Neden tek terim araştırmacısı ve tek denetçi

- **Tek sözlük**: bütün çevirmenler aynı `terminology-glossary.json` dosyasını okur. Parça A ile parça B'nin aynı terimi farklı çevirmesi önlenir.
- **Tek denetçi**: birleştirilmiş metnin tamamını okur. Parçalar arası tutarsızlığı (üslup kayması, yinelenen içerik, kopuk geçiş, kısaltmanın iki kez tanımlanması) görebilir.
- **Tek düzeltici**: bütün bulguları bir çevirmen uygular; çelişen düzeltmeler önlenir.

Kaynak skill 50'den fazla terimde iki terim araştırmacısı açıyordu (adlar ve yerler ile kurumlar ve teknik terimler). Bilimsel makalede terimlerin çoğu alan paketinden tohumlandığı için araştırmacının yükü azalır; tek araştırmacı varsayılandır. Tohum sözlükte olmayan terim sayısı 60'ı geçerse yönetici ikinci araştırmacı açabilir: biri yöntem, istatistik ve teknik terimler; öteki kurum, yer, cihaz ve yazılım adları. Her biri kendi dosyasını yazar (`glossary-research-1.json`, `glossary-research-2.json`); birleştirmeyi yalnız yönetici yapar.

## Birleştirme (parçalı mod)

```bash
python scripts/prepare_source.py merge WS
```

1. `first-pass-chunk-1.md`, `first-pass-chunk-2.md` ... sırayla birleştirilir; `references.md` sona eklenir.
2. Betik parça sınırında yinelenen başlığı bildirir.
3. Yönetici elle denetler: liste ve denklem numarası sürekliliği, "yukarıda" ve "aşağıda" göndermeleri, aynı kısaltmanın iki parçada ayrı ayrı tanımlanması.
4. Sonra `qa_checks.py` bütün metin üzerinde çalışır; denetçi birleştirilmiş `first-pass.md` dosyasını okur.
