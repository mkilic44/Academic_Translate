#!/usr/bin/env python3
"""Word belgesini biçimi koruyarak çevirmek için paragraf parçaları çıkarır ve geri yazar.

Markdown yolu (prepare_source.py + export_docx.py) şekil, denklem, biçem ve
çizelge biçimini kaybeder. Bu betik çeviriyi özgün .docx paketinin içine yazar:
şekiller, Word denklemleri, bağlantılar, çizelgeler, üst ve alt bilgiler,
sayfa düzeni olduğu gibi kalır; yalnız paragraf metni değişir.

Kullanım:
    python scripts/docx_segments.py extract KAYNAK.docx --out WS/segments
    python scripts/docx_segments.py apply KAYNAK.docx --segments WS/segments \
        --translations WS/ceviri.txt --out HEDEF.docx [--lang en-GB] \
        [--math-map WS/notation.json] [--core-title "..."]
    python scripts/docx_segments.py check WS/chunks/K1.txt WS/out/K1.txt
    python scripts/docx_segments.py render HEDEF.docx --out WS/hedef.md

extract çıktısı:
    segments.json   paragraf kimliği, dosya, biçem, metin, biçim etiketleri,
                    yer tutucular (geri yazmada kullanılır; elle düzenlenmez)
    source.txt      çevirmen için düz metin: her paragraf tek satır,
                    "[[p0042|Balk2]] metin" biçiminde
    tags.md         etiket ve yer tutucu açıklaması

Satır içi gösterim:
    <i>..</i> <b>..</b> <u>..</u> <sub>..</sub> <sup>..</sup>
              paragrafın temel biçiminden farklı parçalar (iç içe olabilir)
    <x1>..</x1>
              başka bir biçim farkı (yazı tipi, renk, boyut); özgün biçim korunur
    {M1}      Word denklemi (m:oMath); içi çevrilmez, --math-map ile alt simgeler değişir
    {IMG1}    görsel; {H1} bağlantı (DOI, adres); {TAB} sekme; {BR} satır sonu
Çevirmen etiketleri ve yer tutucuları korur. Yer tutucu sırası cümle yapısına
göre değişebilir; sayısı ve kimliği değişemez. apply bunu denetler.

apply çeviri dosyası biçimi: source.txt ile aynı; "[[kimlik]] çeviri" satırları.
Kimliği bulunmayan paragraf özgün haliyle kalır ve raporlanır.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W = "{%s}" % W_NS
M = "{%s}" % M_NS
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

PARTS = ["word/document.xml", "word/header1.xml", "word/header2.xml", "word/header3.xml",
         "word/footer1.xml", "word/footer2.xml", "word/footer3.xml", "word/footnotes.xml", "word/endnotes.xml"]
SIMPLE_FLAGS = {"b": W + "b", "i": W + "i", "u": W + "u"}
DROP = {W + "proofErr", W + "lastRenderedPageBreak"}
KEEP_AT_EDGES = {W + "bookmarkStart", W + "bookmarkEnd", W + "permStart", W + "permEnd"}
LINE_RE = re.compile(r"^\[\[([a-z0-9]+)(?:\|[^\]]*)?\]\]\s?(.*)$")
TOKEN_RE = re.compile(r"(\{(?:M|IMG|H|X)\d+\}|\{TAB\}|\{BR\}|</?(?:i|b|u|sub|sup|x\d+)>)")


def _flag_on(rpr, tag) -> bool:
    if rpr is None:
        return False
    el = rpr.find(tag)
    if el is None:
        return False
    return el.get(W + "val") not in ("0", "false", "none")


def _vert(rpr) -> str:
    if rpr is None:
        return ""
    v = rpr.find(W + "vertAlign")
    return v.get(W + "val") if v is not None else ""


def _canon(rpr) -> str:
    """Biçim özelliklerinin ad alanı bildirimlerinden bağımsız, sıralı gösterimi.

    Yazı tipi, dil ve karmaşık betik (cs) özellikleri karşılaştırmaya girmez.
    """
    if rpr is None:
        return ""
    skip = {W + "rFonts", W + "lang", W + "noProof", W + "rtl", W + "cs", W + "bCs", W + "iCs", W + "szCs"}

    def enc(el):
        attrs = ",".join(f"{k}={v}" for k, v in sorted(el.attrib.items()))
        kids = "".join(enc(c) for c in el if c.tag not in skip)
        return f"<{el.tag}|{attrs}>{kids}</>"

    return "".join(sorted(enc(c) for c in rpr if c.tag not in skip))


def _strip(rpr, *tags):
    r = copy.deepcopy(rpr) if rpr is not None else etree.Element(W + "rPr")
    for t in tags:
        for el in r.findall(t):
            r.remove(el)
    return r


def _describe(base, rpr) -> list[str]:
    """Bir çalışmanın biçimini temel biçime göre basit etiketlere çevirir; çözülemezse boş liste."""
    tags = []
    for name, t in SIMPLE_FLAGS.items():
        if _flag_on(rpr, t) != _flag_on(base, t):
            if not _flag_on(rpr, t):
                return []
            tags.append(name)
    vb, vr = _vert(base), _vert(rpr)
    if vr != vb:
        if vb:
            return []
        tags.append({"subscript": "sub", "superscript": "sup"}.get(vr, "?"))
        if "?" in tags:
            return []
    a = _canon(_strip(rpr, W + "b", W + "i", W + "u", W + "vertAlign"))
    b = _canon(_strip(base, W + "b", W + "i", W + "u", W + "vertAlign"))
    return tags if a == b else []


def _parts_iter(root):
    for p in root.iter(W + "p"):
        yield p


def _run_kind(r):
    kinds = set()
    for ch in r:
        if ch.tag == W + "t" or ch.tag == W + "delText":
            kinds.add("t")
        elif ch.tag == W + "drawing" or ch.tag == W + "pict" or ch.tag == W + "object":
            kinds.add("img")
        elif ch.tag == W + "tab":
            kinds.add("tab")
        elif ch.tag == W + "br" or ch.tag == W + "cr":
            kinds.add("br")
        elif ch.tag in (W + "rPr",) or ch.tag in DROP:
            continue
        else:
            kinds.add("other")
    return kinds


def analyse_paragraph(p, counters):
    """Paragrafı (metin, etiket haritası, yer tutucular) olarak çözümler."""
    items = []  # ("text", rpr, str) | ("ph", name, element)
    for ch in p:
        if ch.tag == W + "pPr" or ch.tag in DROP or ch.tag in KEEP_AT_EDGES:
            continue
        if ch.tag == W + "r":
            kinds = _run_kind(ch)
            rpr = ch.find(W + "rPr")
            if kinds == {"t"} or kinds == set():
                text = "".join(t.text or "" for t in ch if t.tag == W + "t")
                if text:
                    items.append(("text", rpr, text))
                continue
            if kinds == {"tab"}:
                items.append(("ph", "{TAB}", ch))
                continue
            if kinds == {"br"}:
                items.append(("ph", "{BR}", ch))
                continue
            if "img" in kinds and "t" not in kinds:
                counters["IMG"] += 1
                items.append(("ph", "{IMG%d}" % counters["IMG"], ch))
                continue
            counters["X"] += 1
            items.append(("ph", "{X%d}" % counters["X"], ch))
            continue
        if ch.tag in (M + "oMath", M + "oMathPara"):
            counters["M"] += 1
            items.append(("ph", "{M%d}" % counters["M"], ch))
            continue
        if ch.tag == W + "hyperlink":
            counters["H"] += 1
            items.append(("ph", "{H%d}" % counters["H"], ch))
            continue
        counters["X"] += 1
        items.append(("ph", "{X%d}" % counters["X"], ch))

    chars = Counter()
    rprs = {}
    for it in items:
        if it[0] == "text":
            key = _canon(it[1])
            chars[key] += len(it[2])
            rprs.setdefault(key, it[1])
    base_key = chars.most_common(1)[0][0] if chars else ""
    base = rprs.get(base_key)
    tag_map = {"": base_key}
    custom = {}
    out = []
    xn = 0
    for it in items:
        if it[0] == "ph":
            out.append(it[1])
            continue
        _, rpr, text = it
        key = _canon(rpr)
        if key == base_key:
            out.append(text)
            continue
        tags = _describe(base, rpr)
        if not tags:
            if key not in custom:
                xn += 1
                custom[key] = "x%d" % xn
            tags = [custom[key]]
        opened = "".join("<%s>" % t for t in tags)
        closed = "".join("</%s>" % t for t in reversed(tags))
        out.append(opened + text + closed)
        tag_map["+".join(tags)] = key
    text = "".join(out)
    # Bitişik aynı etiketleri birleştir: </i><i>
    for t in ["i", "b", "u", "sub", "sup"] + sorted(set(custom.values())):
        text = text.replace("</%s><%s>" % (t, t), "")
    return text, base_key, {v: k for k, v in custom.items()}, rprs, items


def extract(docx: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    segs = []
    counters = Counter()
    with zipfile.ZipFile(docx) as z:
        names = set(z.namelist())
        styles = {}
        if "word/styles.xml" in names:
            st = etree.fromstring(z.read("word/styles.xml"))
            for s in st.iter(W + "style"):
                n = s.find(W + "name")
                styles[s.get(W + "styleId")] = n.get(W + "val") if n is not None else s.get(W + "styleId")
        for part in PARTS:
            if part not in names:
                continue
            root = etree.fromstring(z.read(part))
            prefix = "p" if part == "word/document.xml" else re.sub(r"[^a-z0-9]", "", Path(part).stem)
            for idx, p in enumerate(_parts_iter(root)):
                text, base_key, custom, rprs, items = analyse_paragraph(p, counters)
                plain = re.sub(r"<[^>]+>|\{[^}]+\}", "", text).strip()
                ps = p.find(W + "pPr/" + W + "pStyle")
                style_id = ps.get(W + "val") if ps is not None else ""
                in_table = any(a.tag == W + "tc" for a in p.iterancestors())
                segs.append({
                    "id": f"{prefix}{idx:04d}",
                    "part": part,
                    "index": idx,
                    "style": styles.get(style_id, style_id),
                    "in_table": in_table,
                    "text": text,
                    "translate": bool(re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", plain)),
                    "custom_tags": custom,
                })
    (out / "segments.json").write_text(json.dumps(segs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = []
    for s in segs:
        if s["translate"]:
            label = s["style"] + ("|tablo" if s["in_table"] else "")
            lines.append(f"[[{s['id']}|{label}]] {s['text']}")
    (out / "source.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "tags.md").write_text(__doc__.split("Satır içi gösterim:")[1].split("apply çeviri")[0], encoding="utf-8")
    return {"segments": len(segs), "translatable": sum(1 for s in segs if s["translate"]), "placeholders": dict(counters)}


def parse_translations(path: Path) -> dict[str, str]:
    out = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        m = LINE_RE.match(ln.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def check_segment(src: str, tgt: str) -> list[str]:
    """Yer tutucuların ve etiketlerin korunduğunu denetler."""
    problems = []
    ph = lambda s: Counter(re.findall(r"\{(?:M|IMG|H|X)\d+\}|\{TAB\}|\{BR\}", s))  # noqa: E731
    if ph(src) != ph(tgt):
        problems.append(f"yer tutucu farkı: kaynak {dict(ph(src))}, çeviri {dict(ph(tgt))}")
    depth = []
    for tok in re.findall(r"</?(?:i|b|u|sub|sup|x\d+)>", tgt):
        name = tok.strip("</>")
        if tok.startswith("</"):
            if not depth or depth[-1] != name:
                problems.append(f"etiket dengesi bozuk: {tok}")
                break
            depth.pop()
        else:
            depth.append(name)
    if depth:
        problems.append(f"kapanmamış etiket: {depth}")
    for t in set(re.findall(r"<(x\d+)>", tgt)) - set(re.findall(r"<(x\d+)>", src)):
        problems.append(f"kaynakta olmayan özel etiket: {t}")
    return problems


def _new_run(rpr, text):
    r = etree.Element(W + "r")
    if rpr is not None and len(rpr):
        r.append(copy.deepcopy(rpr))
    t = etree.SubElement(r, W + "t")
    t.text = text
    t.set(XML_SPACE, "preserve")
    return r


def _rpr_with(base, tags):
    r = copy.deepcopy(base) if base is not None else etree.Element(W + "rPr")
    for tg in tags:
        if tg in SIMPLE_FLAGS:
            el = r.find(SIMPLE_FLAGS[tg])
            if el is None:
                el = etree.SubElement(r, SIMPLE_FLAGS[tg])
            el.attrib.pop(W + "val", None)
            if tg == "u":
                el.set(W + "val", "single")
        elif tg in ("sub", "sup"):
            el = r.find(W + "vertAlign")
            if el is None:
                el = etree.SubElement(r, W + "vertAlign")
            el.set(W + "val", "subscript" if tg == "sub" else "superscript")
    return r


def rebuild_paragraph(p, new_text: str, counters_before: Counter):
    text_src, base_key, custom, rprs, items = analyse_paragraph(p, counters_before)
    ph_elements = {it[1]: it[2] for it in items if it[0] == "ph"}
    base = rprs.get(base_key)
    custom_rpr = {name: rprs[key] for name, key in custom.items()}
    edges_start = []
    edges_end = []
    seen_content = False
    for ch in list(p):
        if ch.tag == W + "pPr":
            continue
        if ch.tag in KEEP_AT_EDGES:
            (edges_end if seen_content else edges_start).append(ch)
        elif ch.tag not in DROP:
            seen_content = True
        p.remove(ch)
    for e in edges_start:
        p.append(e)
    stack = []
    for tok in TOKEN_RE.split(new_text):
        if not tok:
            continue
        if TOKEN_RE.fullmatch(tok):
            if tok.startswith("{"):
                if tok in ("{TAB}", "{BR}"):
                    el = ph_elements.get(tok)
                    p.append(copy.deepcopy(el) if el is not None else _special_run(base, tok))
                else:
                    p.append(ph_elements.pop(tok))
            elif tok.startswith("</"):
                stack.pop()
            else:
                stack.append(tok.strip("<>"))
            continue
        customs = [t for t in stack if t.startswith("x")]
        if customs:
            rpr = _rpr_with(custom_rpr[customs[-1]], [t for t in stack if not t.startswith("x")])
        else:
            rpr = _rpr_with(base, stack)
        p.append(_new_run(rpr, tok))
    for e in edges_end:
        p.append(e)


def _special_run(base, tok):
    r = etree.Element(W + "r")
    if base is not None:
        r.append(copy.deepcopy(base))
    etree.SubElement(r, W + ("tab" if tok == "{TAB}" else "br"))
    return r


def apply(docx: Path, segdir: Path, translations: Path, out: Path, lang: str | None,
          math_map: dict | None, core_title: str | None, core_subject: str | None) -> dict:
    segs = json.loads((segdir / "segments.json").read_text(encoding="utf-8"))
    tr = parse_translations(translations)
    report = {"applied": 0, "missing": [], "problems": {}, "math_replacements": 0}
    by_part: dict[str, dict[int, dict]] = {}
    for s in segs:
        by_part.setdefault(s["part"], {})[s["index"]] = s
    for s in segs:
        if s["translate"] and s["id"] not in tr:
            report["missing"].append(s["id"])
        if s["id"] in tr:
            pr = check_segment(s["text"], tr[s["id"]])
            if pr:
                report["problems"][s["id"]] = pr
    if report["problems"]:
        return report
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(docx) as z:
        z.extractall(tmp)
    counters = Counter()
    for part in PARTS:
        f = tmp / part
        if not f.exists():
            continue
        tree = etree.parse(str(f))
        for idx, p in enumerate(_parts_iter(tree.getroot())):
            s = by_part.get(part, {}).get(idx)
            if s and s["id"] in tr:
                rebuild_paragraph(p, tr[s["id"]], counters)
                report["applied"] += 1
            else:
                analyse_paragraph(p, counters)
        if math_map:
            for t in tree.getroot().iter(M + "t"):
                if t.text in math_map:
                    t.text = math_map[t.text]
                    report["math_replacements"] += 1
        tree.write(str(f), xml_declaration=True, encoding="UTF-8", standalone=True)
    if lang:
        for name in ("word/styles.xml", "word/settings.xml", "word/document.xml"):
            f = tmp / name
            if f.exists():
                s = f.read_text(encoding="utf-8")
                s = re.sub(r'(<w:lang\b[^>]*\bw:val=")tr-TR(")', r"\g<1>%s\2" % lang, s)
                s = re.sub(r'(<w:themeFontLang\b[^>]*\bw:val=")tr-TR(")', r"\g<1>%s\2" % lang, s)
                f.write_text(s, encoding="utf-8")
    core = tmp / "docProps/core.xml"
    if core.exists() and (core_title or core_subject):
        s = core.read_text(encoding="utf-8")
        if core_title:
            s = re.sub(r"<dc:title>.*?</dc:title>", "<dc:title>%s</dc:title>" % _xml_escape(core_title), s, flags=re.S)
        if core_subject:
            s = re.sub(r"<dc:subject>.*?</dc:subject>", "<dc:subject>%s</dc:subject>" % _xml_escape(core_subject), s, flags=re.S)
        core.write_text(s, encoding="utf-8")
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(docx) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = (tmp / info.filename).read_bytes() if (tmp / info.filename).is_file() else zin.read(info.filename)
            zout.writestr(info, data)
    shutil.rmtree(tmp, ignore_errors=True)
    return report


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(docx: Path, out: Path) -> None:
    """Çevrilmiş belgeden denetim için düz metin üretir (qa_checks.py girdisi)."""
    tmpdir = Path(tempfile.mkdtemp())
    extract(docx, tmpdir)
    segs = json.loads((tmpdir / "segments.json").read_text(encoding="utf-8"))
    lines = []
    for s in segs:
        if s["part"] != "word/document.xml":
            continue
        t = re.sub(r"</?(?:i|b|u|x\d+)>", "", s["text"])
        t = re.sub(r"<sub>(.*?)</sub>", r"\1", t)
        t = re.sub(r"<sup>(.*?)</sup>", r"\1", t)
        style = (s["style"] or "").lower()
        if style.startswith(("heading 1", "balk1")) or style in ("başlık 1",):
            t = "# " + t
        elif style.startswith(("heading 2", "balk2")) or style in ("başlık 2",):
            t = "## " + t
        lines.append(t)
    out.write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    shutil.rmtree(tmpdir, ignore_errors=True)


def check_files(src: Path, tgt: Path) -> list[str]:
    """Kaynak parça ile çeviri parçasını satır kimliği, yer tutucu ve etiket bakımından karşılaştırır."""
    s = parse_translations(src)
    t = parse_translations(tgt)
    out = []
    for k in s:
        if k not in t:
            out.append(f"{k}: çeviride yok")
        elif not t[k].strip():
            out.append(f"{k}: çeviri boş")
        else:
            out.extend(f"{k}: {p}" for p in check_segment(s[k], t[k]))
    for k in t:
        if k not in s:
            out.append(f"{k}: kaynakta olmayan kimlik")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("docx", type=Path)
    e.add_argument("--out", required=True, type=Path)
    a = sub.add_parser("apply")
    a.add_argument("docx", type=Path)
    a.add_argument("--segments", required=True, type=Path)
    a.add_argument("--translations", required=True, type=Path)
    a.add_argument("--out", required=True, type=Path)
    a.add_argument("--lang", help="tr-TR dil etiketlerinin yerine yazılacak dil, örnek en-GB")
    a.add_argument("--math-map", type=Path, help="Denklem içi metin eşlemesi (JSON: {\"gece\": \"night\"})")
    a.add_argument("--core-title")
    a.add_argument("--core-subject")
    c = sub.add_parser("check")
    c.add_argument("source_chunk", type=Path)
    c.add_argument("translated_chunk", type=Path)
    r = sub.add_parser("render")
    r.add_argument("docx", type=Path)
    r.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "extract":
        print(json.dumps(extract(args.docx, args.out), ensure_ascii=False))
        return 0
    if args.cmd == "check":
        probs = check_files(args.source_chunk, args.translated_chunk)
        print("\n".join(probs) if probs else "TAMAM: kimlikler, yer tutucular ve etiketler uyuşuyor")
        return 1 if probs else 0
    if args.cmd == "render":
        render(args.docx, args.out)
        print(args.out)
        return 0
    mm = json.loads(args.math_map.read_text(encoding="utf-8")) if args.math_map else None
    rep = apply(args.docx, args.segments, args.translations, args.out, args.lang, mm, args.core_title, args.core_subject)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 1 if rep["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
