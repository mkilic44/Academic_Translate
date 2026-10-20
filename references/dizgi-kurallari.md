# Dizgi kuralları (.docx ve .pdf çıktı)

Öncelik sırası:

1. Hedef derginin Word şablonu: `export_docx.py --template DERGI.docx`. Biçim tamamen şablondan gelir.
2. Hedef derginin yazım kuralı (sayfa düzeni, satır aralığı, yazı tipi). Şablon yoksa yönetici aşağıdaki varsayılanları dergiye göre düzenler.
3. Bu dosyadaki varsayılanlar.

Bilimsel el yazmasında dizgi süs değildir. Dergiye gönderilecek metinde satır numarası ve çift satır aralığı gibi istekler dergiden gelir; bu skill onları uydurmaz.

## Varsayılanlar

| Öğe | Yazı tipi | Boyut | Biçim |
|---|---|---|---|
| Gövde metni | Times New Roman | 12 pt | 1,25 satır aralığı, paragraf sonrası 6 pt |
| Başlık 1 | Times New Roman | 14 pt | Kalın, önce 18 pt, sonra 12 pt |
| Başlık 2 | Times New Roman | 12 pt | Kalın, önce 14 pt, sonra 8 pt |
| Başlık 3 | Times New Roman | 12 pt | Kalın, önce 10 pt, sonra 6 pt |
| Belge başlığı (Title biçemi) | Times New Roman | 16 pt | Kalın, ortalı |
| Şekil ve çizelge başlığı | Times New Roman | 10 pt | Düz |

Times New Roman Türkçe karakterlerin hepsini (ç, ğ, ı, İ, ö, ş, ü) içerir. Kaynak skill'deki Çince yazı tipi kuralı (SimSun) kaldırıldı.

Times New Roman kurulu olmayan sistemde LibreOffice PDF üretirken ölçüleri aynı olan Liberation Serif yazı tipini kullanır. Bu skill'in sınamalarında PDF bu yolla üretildi. Dergiye gönderilecek PDF'i Word ya da Times New Roman kurulu bir sistem üretmelidir.

## Çizelgeler

pandoc, Markdown çizelgesini Word'ün "Table" biçemiyle yazar. Dergi şablonu yoksa:

- Başlık satırı kalın.
- Sayılar sağa, metin sola hizalı.
- Çizelge başlığı çizelgenin üstünde, şekil başlığı şeklin altında (dergi kuralı farklı değilse).
- Çizelge dipnot imleri (a, b, *, **) korunur.

## Türkçe belge dili

`export_docx.py --lang tr` belgeye `tr-TR` dil etiketini yazar. Word yazım denetimi ve büyük harf dönüşümü buna göre çalışır. İngilizce çıktı için `--lang en` (`en-US`).

## Uygulama

`scripts/export_docx.py` şunları yapar:

1. pandoc'un varsayılan başvuru belgesini üretir.
2. python-docx varsa yukarıdaki biçemleri bu belgeye yazar. Yoksa pandoc varsayılan biçemi kalır ve betik uyarı verir.
3. `pandoc final-translation.md -o CIKTI.docx --reference-doc ...` çalıştırır. Denklemler `$...$` ve `$$...$$` içinden Word denklemine çevrilir.
4. `--pdf` verilirse LibreOffice ile PDF üretir.

## Son kontrol listesi

- [ ] Bütün Türkçe karakterler doğru görünüyor (özellikle İ ve ı).
- [ ] Başlık düzeyleri görsel olarak ayrılıyor.
- [ ] Çizelge sayısı, satır ve sütunları Markdown çeviriyle aynı.
- [ ] Denklemler Word denklemi olarak açılıyor.
- [ ] Atıf numaraları ve köşeli parantezler bozulmamış.
- [ ] Sayfa kenar boşlukları ve satır aralığı dergi kuralına uyuyor (dergi kuralı varsa).
