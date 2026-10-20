# Toprak bilimi alan paketi

Bu klasör, `seed_glossary.py` ve `qa_checks.py` betiklerinin okuduğu terim verisini ve çevirmenin okuyacağı alan notlarını içerir.

## Dosyalar

| Dosya | İçerik | Statü |
|---|---|---|
| `kaynak/sozluk.md` | Kullanıcının ortak terminoloji sözlüğü, sürüm 1.2 (17 Eylül 2026) | Bağlayıcı. Değiştirilmeden kopyalandı |
| `kaynak/terim_onerileri_A.md` | 110 terim önerisi: sayısal toprak haritalama, jeoistatistik, makine öğrenmesi, derin öğrenme, istatistik, büyük dil modelleri | Bağlayıcı değil. Değiştirilmeden kopyalandı |
| `kaynak/terim_onerileri_B.md` | 110 terim önerisi: spektroskopi, etüt, sınıflandırma, arazi değerlendirme, koruma, bitki besleme, laboratuvar yöntemleri | Bağlayıcı değil. Değiştirilmeden kopyalandı |
| `baglayici.json` | `sozluk.md` maddelerinin makinece okunur biçimi (84 girdi; 10 tanesi kısa ya da çok anlamlı olduğu için otomatik denetim dışında), yasak biçimler ve değişken çiftler | Elle aktarıldı; her girdinin `kaynak` alanı `sozluk.md` içindeki satır parçasıdır |
| `oneriler.json` | A ve B listelerinin satır satır JSON biçimi (220 girdi) | `scripts/build_domain_glossary.py` üretir |
| `alan-notlari.md` | Alanın çeviri tuzakları; her madde kaynak satırına bağlı | Yeni terim kararı içermez |

## Durum değerleri

- **bağlayıcı**: `sozluk.md` içindeki eşdeğer. Yakın anlamlısı kullanılmaz.
- **yerleşik**: öneri listesinde tek baskın biçim.
- **değişken**: birden çok yaygın biçim; listede biri önerilmiş. Bir el yazması içinde tek biçim korunur.
- **yerleşmemiş**: tutarlı Türkçe karşılık yok. İngilizce terim ilk geçişte bir cümleyle açıklanır; Türkçe ad uydurulmaz.

Öneri listelerinin kanıt sınırı listelerin kendi "Yöntem ve sınırlar" bölümündedir: kullanım taraması TR Dizin başlık ve özetleriyle yapılmıştır, DergiPark ve YÖK Tez taranamamıştır, "kanıt bulunamadı" terimin kullanılmadığını göstermez.

## `oneriler.json` dönüşüm kuralları

`build_domain_glossary.py` satırın anlamını değiştirmez; ham sütunları (`en_raw`, `tr_raw`, `note`) da saklar. Türetilen alanlar:

- `en_keys`: kaynak metinde aranacak İngilizce anahtarlar. "supervised / unsupervised classification" iki anahtara açılır. Parantez içi kısaltma ayrı anahtar olur.
- `tr_variants`: Türkçe sütundaki biçimler. "A / B C" biçimi yalnız İngilizce sütunda da koşut "/" varsa açılır.
- `preferred_tr`: nottaki "Öneri: ..." ifadesi Türkçe sütunda geçiyorsa o biçim; "yerleşik" ve tek biçimli satırda o biçim; aksi durumda boş. 220 satırın 119'unda belirlenir. Boş kalan satırlar çoğunlukla birden çok kavramı ya da bağlama göre değişen öneriyi içerir; kararı terim araştırmacısı notu okuyarak verir.
- `pairs`: çok kavramlı "yerleşik" satırda parça sayıları eşitse sırayla eşleme.

`tests/test_integrity.py` şunları denetler: `baglayici.json` içindeki her `kaynak` parçası `sozluk.md` içinde birebir geçer; `oneriler.json` satır sayıları ve durum dağılımı kaynak listelerin "Sayım" çizelgeleriyle aynıdır; `oneriler.json` güncel kaynak listelerden yeniden üretildiğinde değişmez.

## Sözlüğü güncelleme

1. Bağlayıcı karar `kaynak/sozluk.md` dosyasına yazılır ve sürüm numarası artırılır.
2. Aynı karar `baglayici.json` dosyasına, `kaynak` alanında `sozluk.md` satır parçasıyla eklenir.
3. Öneri listesi değiştiyse `python scripts/build_domain_glossary.py domains/toprak-bilimi` çalıştırılır.
4. `python -m unittest discover -s tests` çalıştırılır.

## Yeni alan paketi ekleme

`domains/<alan>/` altında aynı yapı kurulur: `kaynak/`, `baglayici.json`, isteğe bağlı `oneriler.json` ve `alan-notlari.md`. `seed_glossary.py --domain domains/<alan>` birden çok kez verilebilir; ilk verilen paket önceliklidir.
