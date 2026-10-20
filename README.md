# Bilimsel çeviri skill'i: Türkçe ve İngilizce

Türkçe ile İngilizce arasında, iki yönde, bilimsel araştırma makalesi çevirmek için bir [Claude Code](https://claude.com/claude-code) skill'i. [senshinji/claude-translation-skill](https://github.com/senshinji/claude-translation-skill) (MIT) temel alınarak yeniden kuruldu. Kaynak skill'in çözümlemesi ve uyarlama kararları: [docs/tersine-muhendislik-raporu.md](docs/tersine-muhendislik-raporu.md).

## Ne yapar

1. Kaynağı (.docx, .tex, .md, .pdf) Markdown'a çevirir ve yapı envanterini çıkarır.
2. Alan paketindeki bağlayıcı sözlükten ve kanıtlı öneri listelerinden bir tohum terim sözlüğü üretir.
3. Çevirmen ajan ile terim araştırmacısı ajanı paralel çalıştırır.
4. Çeviriyi kural tabanlı betikle denetler: sayılar (ondalık ayırıcı dönüşümüyle), atıflar, DOI, kaynakça, başlık ve çizelge yapısı, denklemler, onaylı terimler, yasak biçimler, Türkçe yazım kuralları, çözülmemiş çevirmen işaretleri, uzun cümleler.
5. Ayrı bağlamda bir denetçi ajana uydurma, eksiltme ve anlam kayması (savın kesinlik düzeyi, olumsuzluk, nedensellik) denetimi yaptırır.
6. Bulguları düzelttirir, otomatik denetimi yineler, çeviri raporu ve .docx (isteğe bağlı .pdf) çıktısı üretir.

Kaynak skill'den farkı kısaca: macOS bağımlılığı kalktı; sayı, atıf ve terim denetimi elle yapılan işten betiğe geçti; anlam kayması ayrı bulgu türü oldu; terimler genel web araması yerine kullanıcının kanıtlı alan sözlüğüyle başlıyor; denetçinin bağımsız uzman olmadığı raporda açıkça yazılıyor.

## Kurulum

```bash
git clone https://github.com/mkilic44/claude-scientific-translation-tr-en.git
# Linux / macOS
ln -s "$(pwd)/claude-scientific-translation-tr-en" ~/.claude/skills/bilimsel-ceviri-tr-en
```

Windows (yönetici olarak açılmış komut isteminde):

```bat
mklink /D "%USERPROFILE%\.claude\skills\bilimsel-ceviri-tr-en" "C:\yol\claude-scientific-translation-tr-en"
```

Gereksinimler:

| Araç | Zorunlu mu | Ne için |
|---|---|---|
| Python 3.9+ | evet | betikler; yalnız standart kitaplık |
| pandoc | evet | .docx, .tex, .odt kaynak ve .docx çıktı |
| python-docx | hayır | çıktı biçemleri (Times New Roman, başlık boyutları) |
| pdftotext (poppler) ya da PyMuPDF | hayır | PDF kaynak |
| LibreOffice | hayır | PDF çıktı |

## Kullanım

Claude Code içinde:

```
Bu makaleyi Türkçeye çevir: makale.docx
Özeti İngilizceye çevir, hedef dergi Geoderma
Çeviriyi denetle: kaynak.md ve ceviri.md
```

Betikler tek başına da çalışır:

```bash
python scripts/prepare_source.py prepare makale.docx --direction en-tr
python scripts/seed_glossary.py --source ceviri-makale/source.md --direction en-tr --out ceviri-makale/seed-glossary.json
python scripts/qa_checks.py --source ceviri-makale/source.md --target ceviri.md --direction en-tr \
  --glossary ceviri-makale/seed-glossary.json --params ceviri-makale/params.json --out-md qa-report.md
python scripts/export_docx.py ceviri.md --out makale.tr.docx --lang tr --pdf
```

`qa_checks.py` bulguları adaydır: kural tabanlı eşleşme yanlış alarm verebilir (örnek: kaynakta yazıyla, çeviride rakamla yazılmış sayı) ve anlam kaymasını göremez. Akış içinde her adayı denetçi doğrular ya da reddeder.

## Depo yapısı

```
SKILL.md                         skill tanımı ve ajan istemleri
references/
  bilimsel-ceviri-kurallari.md   sayı, yüzde, atıf, bölüm adları, kısaltma, kesinlik düzeyi
  glossary-schema.md             terim sözlüğü şeması
  review-feedback-schema.md      denetçi bulgu biçimi
  uydurma-onleme.md              uydurma, eksiltme, anlam kayması
  olcekleme.md                   mod eşikleri, parçalama, birleştirme
  dizgi-kurallari.md             .docx ve .pdf biçimi
  ceviri-raporu-sablonu.md       çeviri raporu ve model kullanım kaydı
scripts/
  trtext.py                      Türkçe harf dönüşümü, terim eşleşmesi, sayı ayıklama
  prepare_source.py              kaynak hazırlama, parçalama, birleştirme
  seed_glossary.py               tohum terim sözlüğü
  merge_glossaries.py            tohum ve araştırma sözlüklerini birleştirir
  qa_checks.py                   kural tabanlı denetim
  export_docx.py                 .docx ve .pdf çıktı
  build_domain_glossary.py       öneri listelerini JSON'a çevirir
domains/toprak-bilimi/
  kaynak/                        kullanıcının sözlüğü ve öneri listeleri (değiştirilmeden)
  baglayici.json, oneriler.json  makinece okunur sözlük
  alan-notlari.md                alanın çeviri tuzakları
tests/                           davranış ve bütünlük sınamaları, sentetik sınama metinleri
docs/tersine-muhendislik-raporu.md
docs/ornek-calisma/              uçtan uca sınama çalıştırmasının çıktıları
```

## Sınamalar

```bash
python -m unittest discover -s tests -v
```

Sınamalar sentetik bir İngilizce kaynak, doğru bir Türkçe çeviri ve bilinçli hatalar yerleştirilmiş bir Türkçe çeviriyle çalışır. Doğru çeviri iki yönde de bulgu vermez. Hatalı çevirideki değişmiş sayı, ondalık nokta, düşürülmüş atıf, eksik çizelge satırı, yanlış terim, en dash, "et al.", yüzde işareti yeri, "GIRIŞ" büyük harf hatası, çevrilmemiş çizelge etiketi ve uzun cümle yakalanır. Savın kesinlik düzeyinin değiştirilmesi ("düşündürmektedir" yerine "göstermektedir") kural tabanlı betikle yakalanmaz; bu hata denetçi ajanın işidir ve sınama bunu açıkça kaydeder.

GitHub Actions her itmede sınamaları çalıştırır.

Ajanlı akışın tamamı sentetik kaynak üzerinde bir kez uçtan uca çalıştırıldı. Ara dosyalar, denetçi bulguları ve çeviri raporu: [docs/ornek-calisma](docs/ornek-calisma/README.md). Gerçek bir makaleyle henüz çalıştırılmadı.

## Alan paketi

`domains/toprak-bilimi` paketi kullanıcının toprak bilimi terminoloji sözlüğünü (sürüm 1.2, bağlayıcı) ve 220 terimlik iki öneri listesini içerir. Ayrıntı: [domains/toprak-bilimi/README.md](domains/toprak-bilimi/README.md). Yeni alan için aynı yapıda `domains/<alan>/` klasörü açılır.

Depo herkese açık yapılırsa bu sözlük dosyaları da açık olur.

## Sınırlar

- Denetçi ve çevirmen aynı model ailesindendir. Denetçi okuması bağımsız uzman gözlemi değildir.
- Türkçe terim eşleşmesi sezgiseldir (ek ve ünsüz yumuşaması kuralları); seyrek biçimlerde kaçırma ya da yanlış alarm olabilir.
- PDF kaynakta çizelge, üst simge ve iki sütun düzeni bozulabilir; .docx ya da LaTeX kaynağı tercih edilir.
- Mod eşikleri (300 ve 6000 sözcük) ölçülmüş değil, varsayılandır.
- Türkçe ondalık virgül ve yüzde işareti kuralları bu depo hazırlanırken birincil kaynaktan (TDK) doğrulanamadı; `params.json` ile değiştirilebilir.

## Lisans

MIT. Kaynak skill'in telif bildirimi [LICENSE](LICENSE) dosyasında korunmuştur.
