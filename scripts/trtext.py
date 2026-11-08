"""Türkçe ve İngilizce bilimsel metin için ortak yardımcılar.

Bu modül yalnız Python standart kitaplığını kullanır. Öteki betikler
(qa_checks.py, seed_glossary.py, prepare_source.py) buradaki işlevleri çağırır.

İçerik:
- Türkçeye özgü büyük-küçük harf dönüşümü (I/ı, İ/i).
- Metin normalleştirme: bağlı harfler (fi, fl), yumuşak tire, tire türleri.
- Ek almış Türkçe terimi yakalayan düzenli ifade üretimi (sezgisel).
- Ondalık ayırıcıya duyarlı sayı ayıklama.
- Markdown içinde kod, bağlantı ve kaynakça bölümünü ayıklama.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

# ---------------------------------------------------------------------------
# Harf dönüşümü
# ---------------------------------------------------------------------------

_TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})
_TR_UPPER = str.maketrans({"i": "İ", "ı": "I"})

TR_LETTERS = "a-zçğıöşüâîû"
TR_WORD = rf"[{TR_LETTERS}0-9]"
VOWELS = set("aeıioöuüâîû")


def tr_lower(text: str) -> str:
    """Türkçe kurala göre küçük harfe çevirir: I -> ı, İ -> i."""
    return text.translate(_TR_LOWER).lower()


def tr_upper(text: str) -> str:
    """Türkçe kurala göre büyük harfe çevirir: i -> İ, ı -> I."""
    return text.translate(_TR_UPPER).upper()


# ---------------------------------------------------------------------------
# Normalleştirme
# ---------------------------------------------------------------------------

_LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
}

DASH_CHARS = {
    "\u2013": "en dash",
    "\u2014": "em dash",
    "\u2212": "eksi işareti",
}


def normalize(text: str) -> str:
    """Karşılaştırma için metni normalleştirir.

    Bağlı harfleri açar, yumuşak tireyi siler, bölünmez boşluğu boşluğa,
    U+2013, U+2014 ve U+2212 işaretlerini kısa çizgiye çevirir.
    Kaynak ya da hedef dosya değiştirilmez; yalnız denetim kopyası üretilir.
    """
    text = unicodedata.normalize("NFC", text)
    for lig, repl in _LIGATURES.items():
        text = text.replace(lig, repl)
    text = text.replace("\u00ad", "")
    text = text.replace("\u00a0", " ").replace("\u202f", " ").replace("\u2009", " ")
    for ch in DASH_CHARS:
        text = text.replace(ch, "-")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    return text


# ---------------------------------------------------------------------------
# Markdown ayıklama
# ---------------------------------------------------------------------------

REFERENCE_HEADINGS = re.compile(
    r"^(#{1,6})\s*(references|reference list|literature cited|bibliography|"
    r"kaynaklar|kaynakça|kaynakca|yararlanılan kaynaklar)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

URL_RE = re.compile(r"https?://[^\s)\]>]+")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>)\]]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def split_references(text: str) -> tuple[str, str]:
    """Metni ana metin ve kaynakça olarak ikiye ayırır.

    Kaynakça başlığından sonraki, aynı ya da üst düzey ilk başlığa kadar olan
    bölüm kaynakça sayılır. Başlık bulunmazsa kaynakça boş döner.
    """
    m = REFERENCE_HEADINGS.search(text)
    if not m:
        return text, ""
    level = len(m.group(1))
    rest = text[m.end():]
    # Kaynakça, aynı ya da üst düzey başlıkta ya da başlık biçemi taşımayan bir ek satırında biter
    # ("Ek 2. Yöntem ayrıntıları", "Appendix A", "Supplementary material").
    nxt = re.search(rf"^(?:#{{1,{level}}}\s+\S|(?:Ek|EK|Ekler|EKLER|Appendix|APPENDIX|Appendices|Supplementary)\b[ \t]*[A-Z0-9.:]*)", rest, re.MULTILINE)
    if nxt:
        refs = rest[: nxt.start()]
        body = text[: m.start()] + rest[nxt.start():]
    else:
        refs = rest
        body = text[: m.start()]
    return body, refs


def strip_code_and_links(text: str) -> str:
    """HTML yorumlarını, kod bloklarını, satır içi kodu, adresleri, DOI ve e-postaları boşlukla değiştirir.

    Satır sayısı korunur; böylece bulguların satır numaraları özgün dosyayla uyuşur.
    """
    text = HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = INLINE_CODE_RE.sub(" ", text)
    # pandoc'un Markdown kaçışlarını aç: \[1\] -> [1]
    text = re.sub(r"\\([\[\]()*_#<>])", r"\1", text)
    text = URL_RE.sub(" ", text)
    text = DOI_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    return text


_SECTION_PATTERNS = [
    # Başlık numarası: "## 2.1 Study area", "## 2.1. Çalışma alanı"
    re.compile(r"^(#{1,6}\s+)(\d+(?:\.\d+)*\.?)(?=\s)", re.MULTILINE),
    # "Section 2.3", "Sections 2.1 and 2.2", "Bölüm 2.3"
    re.compile(r"(?i)(\b(?:sections?|sect\.|subsections?|bölüm|bölümler|kısım|alt\s?bölüm)\s+)(\d+(?:\.\d+)+)"),
    # "2.3. bölümde", "2.3 numaralı bölüm"
    re.compile(r"(?i)()(\b\d+(?:\.\d+)+\.?)(?=\s+(?:numaralı\s+)?(?:bölüm|kısım|alt\s?bölüm))"),
    # Çok düzeyli numara: 2.3.1
    re.compile(r"()(\b\d+\.\d+\.\d+(?:\.\d+)*\b)"),
]


def mask_section_numbers(text: str) -> str:
    """Bölüm numaralarını ve bölüm göndermelerini sayı denetiminin dışına alır.

    Rakamlar "§" ile değiştirilir; satır ve karakter sayısı korunur.
    "2.1" Türkçe ondalık kuralıyla 2 ve 1 diye okunacağı için bu adım gereklidir.
    """
    for rx in _SECTION_PATTERNS:
        text = rx.sub(lambda m: m.group(1) + re.sub(r"\d", "§", m.group(2)), text)
    return text


# ---------------------------------------------------------------------------
# Terim yakalama
# ---------------------------------------------------------------------------

_SOFTEN = {
    "ğ": "[ğk]",
    "k": "[kğ]",
    "b": "[bp]",
    "p": "[pb]",
    "d": "[dt]",
    "t": "[td]",
    "c": "[cç]",
    "ç": "[çc]",
    "g": "[gk]",
}


def _tr_stem_pattern(word: str) -> str:
    """Bir Türkçe sözcüğün ek alabilen gövdesi için düzenli ifade üretir.

    Sezgisel kural: tamlama ekini (-sı/-si/-su/-sü ya da ünsüzden sonra
    -ı/-i/-u/-ü) atar, sondaki ünsüz yumuşamasına izin verir.
    Örnek: "ağırlığı" -> "ağırlı[ğk]" ve böylece "ağırlıkları" da yakalanır.
    """
    w = word
    if len(w) > 5 and w[-2] == "s" and w[-1] in "ıiuü" and w[-3] in VOWELS:
        w = w[:-2]
    elif len(w) > 4 and w[-1] in "ıiuü" and w[-2] not in VOWELS:
        w = w[:-1]
    if len(w) < 3:
        return re.escape(word)
    last = w[-1]
    return re.escape(w[:-1]) + _SOFTEN.get(last, re.escape(last))


def _clean_term(term: str) -> str:
    # Yalnız harfle başlayan parantez içi atılır (kısaltma ya da açıklama: "(SOC)").
    # Birim parçası olan "(+)" korunur: "cmol(+) kg-1".
    term = re.sub(r"\s*\([A-Za-zÇĞİÖŞÜçğıöşü][^)]*\)", " ", term)
    return " ".join(term.split())


def term_pattern(term: str, lang: str) -> re.Pattern[str]:
    """Terimi metinde arayan düzenli ifadeyi döndürür.

    lang="tr": metin tr_lower ile küçültülmüş olarak aranmalıdır. Son sözcük
    ek alabilir. lang="en": büyük-küçük harf duyarsız; son sözcük çoğul eki
    alabilir; sözcük arasında boşluk ya da kısa çizgi olabilir.
    Parantez içindeki kısaltma terimden çıkarılır.
    """
    clean = _clean_term(term)
    if lang == "tr" and " " not in clean and len(clean) <= 4:
        # Kısa tek sözcük (kil, kum, jips): en çok dört harflik ek kabul edilir,
        # böylece "kilin", "killi" yakalanır, "kilometre" yakalanmaz.
        w = re.escape(tr_lower(clean))
        return re.compile(rf"(?<![{TR_LETTERS}0-9]){w}[{TR_LETTERS}']{{0,4}}(?![{TR_LETTERS}0-9])")
    if lang == "tr":
        words = tr_lower(clean).split()
        parts = [re.escape(w) for w in words[:-1]]
        parts.append(_tr_stem_pattern(words[-1]) + rf"[{TR_LETTERS}']*")
        body = r"[\s-]+".join(parts)
        return re.compile(rf"(?<![{TR_LETTERS}0-9]){body}(?![{TR_LETTERS}0-9])")
    words = clean.lower().replace("-", " ").split()
    parts = [re.escape(w) for w in words[:-1]]
    last = words[-1]
    if len(last) > 2 and last.endswith("y") and last[-2] not in "aeiou":
        parts.append(re.escape(last[:-1]) + r"(?:y|ies)")
    else:
        parts.append(re.escape(last) + r"(?:s|es)?")
    body = r"[\s-]+".join(parts)
    return re.compile(rf"(?<![a-z0-9]){body}(?![a-z0-9])", re.IGNORECASE)


def find_spans(text: str, term: str, lang: str) -> list[tuple[int, int]]:
    """Terimin metindeki (başlangıç, bitiş) konumlarını döndürür.

    tr_lower karakter sayısını değiştirmez; konumlar özgün metne uyar.
    """
    hay = tr_lower(text) if lang == "tr" else text
    return [m.span() for m in term_pattern(term, lang).finditer(hay)]


def find_term(text: str, term: str, lang: str) -> list[int]:
    """Terimin metindeki başlangıç konumlarını döndürür."""
    return [a for a, _ in find_spans(text, term, lang)]


def abbreviation_pattern(abbr: str) -> re.Pattern[str]:
    """Kısaltmayı büyük-küçük harf duyarlı, tam sözcük olarak arar."""
    return re.compile(rf"(?<![\w]){re.escape(abbr)}(?![\w])")


# ---------------------------------------------------------------------------
# Sayı ayıklama
# ---------------------------------------------------------------------------

_NUM_POINT = re.compile(
    r"(?P<sign>(?<![\w)\]%])-)?(?<![\w])(?P<int>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<frac>\d+))?(?!\d)"
)
_VERSION_BEFORE = re.compile(r"(?i)(sürüm\w*|version|release|v)\s*$")
_VERSION_AFTER = re.compile(r"(?i)^\s*(sürüm|version)")
_DOTTED = re.compile(r"(?<![\w.,-])\d+(?:\.\d+)+(?![\w.,]\d)")
_NUM_COMMA = re.compile(
    r"(?P<sign>(?<![\w)\]%])-)?(?<![\w])(?P<int>\d{1,3}(?:\.\d{3})+|\d+)(?:,(?P<frac>\d+))?(?!\d)"
)


def extract_numbers(text: str, decimal: str) -> list[tuple[str, int]]:
    """Metindeki sayıları kanonik biçimde ve satır numarasıyla döndürür.

    decimal="." İngilizce gelenek (1,234.5); decimal="," Türkçe gelenek (1.234,5).
    Kanonik biçim: işaret + binlik ayırıcısız tam kısım + "." + ondalık kısım.
    Sondaki sıfırlar korunur; "0,50" ile "0.5" farklı sayılır, çünkü
    raporlanan duyarlık değişmiştir.
    Kod, adres, DOI ve e-posta önceden çıkarılmalıdır (strip_code_and_links).
    LaTeX'te Türkçe ondalık yazımı "{,}" virgüle çevrilir.
    """
    if decimal not in {".", ","}:
        raise ValueError("decimal '.' ya da ',' olmalı")
    text = normalize(text).replace("{,}", ",")
    rx = _NUM_POINT if decimal == "." else _NUM_COMMA
    sep = "," if decimal == "." else "."
    out: list[tuple[str, int]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        # Noktalı sürüm ve bölüm numaraları (6.1, 2.3.0) iki dilde de aynı yazılır; virgül
        # ondalıklı metinde binlik ayırıcı sanılmasın diye olduğu gibi alınır.
        def _literal(m):
            tok = m.group(0)
            groups = tok.split(".")
            if decimal == "," and all(len(g) == 3 for g in groups[1:]):
                return tok
            if len(groups) < 3:
                # İki parçalı noktalı sayı yalnız sürüm bağlamında olduğu gibi alınır;
                # öteki durumda virgül ondalıklı metindeki hatalı ondalık nokta yakalanmalı.
                before = line[max(0, m.start() - 16):m.start()]
                after = line[m.end():m.end() + 12]
                if not (_VERSION_BEFORE.search(before) or _VERSION_AFTER.match(after)):
                    return tok
                if decimal == ".":
                    return tok
            out.append((tok, lineno))
            return " " * len(tok)
        line = _DOTTED.sub(_literal, line)
        for m in rx.finditer(line):
            integer = m.group("int").replace(sep, "")
            frac = m.group("frac")
            canon = ("-" if m.group("sign") else "") + integer + ("." + frac if frac else "")
            out.append((canon, lineno))
    return out


# ---------------------------------------------------------------------------
# Cümle bölme
# ---------------------------------------------------------------------------

_ABBREVS = [
    "et al.", "e.g.", "i.e.", "Fig.", "Figs.", "Eq.", "Eqs.", "vs.", "cf.", "approx.",
    "No.", "Dr.", "Prof.", "ve ark.", "vd.", "vb.", "örn.", "bkz.", "yy.", "Doç.", "Dr.",
    "Şek.", "Çiz.", "s.", "ss.", "p.", "pp.", "ca.", "Sect.",
]


def split_sentences(paragraph: str) -> list[str]:
    """Paragrafı cümlelere böler. Yaygın kısaltmalardaki nokta cümle sonu sayılmaz."""
    protected = paragraph
    for i, ab in enumerate(_ABBREVS):
        # Kısaltma yalnız sözcük başında aranır: "s." kısaltması "days." sonunu yakalamamalı.
        rx = re.compile(r"(?<![\w])" + re.escape(ab))
        protected = rx.sub(lambda m, i=i: m.group(0).replace(".", "\u0000%d\u0000" % i), protected)
    # Ondalık noktayı koru: 0.05
    protected = re.sub(r"(\d)\.(\d)", "\\1\u0001\\2", protected)
    # Şekil başlıklarındaki panel etiketi ("(a, b) ...", "(c) ...") yeni cümle başlatır.
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-ZÇĞİÖŞÜ0-9]|\([a-z](?:,\s?[a-z])*\)\s)", protected)
    restored = []
    for p in parts:
        p = p.replace("\u0001", ".")
        p = re.sub(r"\u0000\d+\u0000", ".", p)
        if p.strip():
            restored.append(p.strip())
    return restored


def word_count(sentence: str) -> int:
    return len(re.findall(r"[^\s]+", sentence))


def iter_prose_paragraphs(text: str) -> Iterable[tuple[int, str]]:
    """Başlık, çizelge, liste imi, kod ve denklem dışındaki paragrafları verir.

    Döndürülen değer (başlangıç satırı, paragraf metni) çiftidir.
    """
    text = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = text.splitlines()
    buf: list[str] = []
    start = 0
    for i, line in enumerate(lines + [""], start=1):
        s = line.strip()
        is_break = (
            not s
            or s.startswith("#")
            or s.startswith("|")
            or s.startswith("<")
            or s.startswith("$$")
        )
        if is_break:
            if buf:
                yield start, " ".join(buf)
                buf = []
            continue
        if not buf:
            start = i
        s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
        buf.append(s)
