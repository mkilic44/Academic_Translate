# Otomatik denetim raporu (qa_checks.py)

Kaynak: `WS/source.md`  
Çeviri: `WS/first-pass.md`  
Yön: en-tr

Bu bulgular kural tabanlı adaylardır. Denetçi her adayı kaynakla karşılaştırıp doğrular ya da reddeder.

| Önem | Sayı |
|---|---|
| critical | 0 |
| major | 2 |
| minor | 1 |
| info | 0 |

## İstatistikler

```json
{
 "numbers": {
  "source": 31,
  "target": 31,
  "missing": 0,
  "extra": 0
 },
 "citations": {
  "author_year_source": 3,
  "author_year_target": 3,
  "numbered_source": 4,
  "numbered_target": 4,
  "ids_source": 4,
  "ids_target": 4
 },
 "references": {
  "source_chars": 306,
  "target_chars": 306
 },
 "structure": {
  "source": {
   "headings": {
    "H1": 1,
    "H2": 3
   },
   "tables": [
    [
     3,
     3
    ]
   ],
   "figure_numbers": [
    1
   ],
   "table_numbers": [
    1
   ],
   "display_equations": 1,
   "inline_math": 0,
   "list_items": 0,
   "paragraphs": 4,
   "colspan_rowspan": 0
  },
  "target": {
   "headings": {
    "H1": 1,
    "H2": 3
   },
   "tables": [
    [
     3,
     3
    ]
   ],
   "figure_numbers": [
    1
   ],
   "table_numbers": [
    1
   ],
   "display_equations": 1,
   "inline_math": 0,
   "list_items": 0,
   "paragraphs": 4,
   "colspan_rowspan": 0
  }
 },
 "glossary": {
  "checked": 16,
  "compliant": 16
 },
 "sentences": {
  "total": 10,
  "over_limit": 1,
  "limit": 30
 }
}
```

## major

1. TYPOGRAPHY (typography) [hedef satır 7]: Çözülmemiş çevirmen işareti | [?tanımsız kısaltma: R2?]
2. TYPOGRAPHY (typography) [hedef satır 15]: Çözülmemiş çevirmen işareti | [?terim: folds?]

## minor

1. READABILITY (sentences) [hedef paragraf satır 7]: 31 sözcüklü cümle (sınır 30) | Rastgele orman, TOK'u ortalama kare hatanın karekökü (root mean squared error, RMSE) %0,42 ve R2 [?tanımsız kısaltma: R2?] = 0,61 değerleriyle tahmin etmiştir (

