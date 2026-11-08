#!/usr/bin/env python3
"""Word belgesinde izlenen değişiklikle (track changes) düzeltme yapar.

Kaynak metindeki hataları yazarın görebileceği biçimde düzeltmek için kullanılır.
Paragraflar docx_segments.py extract çıktısındaki kimliklerle (p0042) bulunur.

Kullanım:
    python scripts/docx_tracked.py apply GIRDI.docx --segments SEG/segments.json \
        --edits duzeltmeler.json --out IZLENEN.docx [--author Claude] [--date 2026-10-20T00:00:00Z]
    python scripts/docx_tracked.py accept IZLENEN.docx --out TEMIZ.docx

duzeltmeler.json bir liste ya da {"edits": [...]} nesnesidir. İşlemler:
    {"op": "replace", "pid": "p0005", "old": "14 bağlı grup", "new": "14 bağımlılık grubu", "note": "..."}
        old paragrafta tam bir kez geçmelidir. Ortak baş ve son sözcükler ayıklanır;
        izlenen değişiklik yalnız farklı sözcükleri gösterir.
    {"op": "insert_paragraph", "before_pid": "p0003", "text": "...", "style_like_pid": "p0023"}
        ya da "before_table": 0 (gövdedeki kaçıncı çizelgenin önüne). Yeni paragraf,
        style_like_pid paragrafının biçimini alır.
    {"op": "format_paragraph", "pid": "p0426", "like_pid": "p0425"}
        Paragraf biçimini (girinti, aralık) ve satır yazı boyutunu örnek paragraftan alır;
        eski biçim pPrChange ve rPrChange ile kaydedilir.
    {"op": "delete_paragraph", "pid": "p0424"}
        Paragrafı (metni ve paragraf işaretiyle) silinmiş olarak işaretler.
    {"op": "run_size", "pid": "p0421", "sz": 20}
        Yazı boyutu farklı satırları (ör. bağlantı satırları) verilen boyuta getirir (yarım punto).
    {"op": "italic", "pid": "p0422", "text": "Genetic Resources and Crop Evolution", "occurrence": 0}
        Verilen parçayı italik yapar; eski biçim rPrChange ile kaydedilir. Parça birden çok
        kez geçiyorsa occurrence (0'dan başlar) hangisi olduğunu seçer.

accept, bu betiğin ürettiği izlenen değişiklikleri kabul eder (w:del silinir, w:ins açılır,
biçim değişikliği kayıtları kaldırılır). Başka kaynaktan gelen izlenen değişiklikleri de
aynı kuralla kabul eder.
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
from pathlib import Path

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline",
    "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing",
    "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText",
    "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath", "rPrChange",
]


class EditError(Exception):
    pass


class Tracker:
    def __init__(self, root: etree._Element, author: str, date: str):
        self.root = root
        self.author = author
        self.date = date
        ids = [int(v) for v in root.xpath("//@w:id", namespaces={"w": W_NS}) if str(v).lstrip("-").isdigit()]
        self.next_id = max([0] + ids) + 1000

    def mark(self, tag: str) -> etree._Element:
        el = etree.Element(W + tag)
        el.set(W + "id", str(self.next_id))
        el.set(W + "author", self.author)
        el.set(W + "date", self.date)
        self.next_id += 1
        return el


# ---------------------------------------------------------------------------
# Paragraf ve satır yardımcıları
# ---------------------------------------------------------------------------


def body_paragraphs(root) -> list:
    body = root.find(W + "body")
    return list(body.iter(W + "p"))


def text_runs(p) -> list:
    """Paragraftaki metin taşıyan satırlar (w:del içindekiler hariç)."""
    out = []
    for r in p.iter(W + "r"):
        anc = r.getparent()
        skip = False
        while anc is not None and anc is not p:
            if anc.tag == W + "del":
                skip = True
                break
            anc = anc.getparent()
        if not skip:
            out.append(r)
    return out


def run_text(r) -> str:
    return "".join(t.text or "" for t in r.findall(W + "t"))


def para_text(p) -> str:
    return "".join(run_text(r) for r in text_runs(p))


def _set_t(t, text: str) -> None:
    t.text = text
    if text != text.strip() or "  " in text:
        t.set(XML_SPACE, "preserve")
    else:
        t.attrib.pop(XML_SPACE, None)


def drop_render_hints(root) -> int:
    """Word'ün sayfa kesme önbelleğini (w:lastRenderedPageBreak) siler ve yan yana kalan
    w:t öğelerini birleştirir. Öğe içerik taşımaz; Word belgeyi açınca yeniden üretir.
    Silinmezse bir satırda iki w:t kalır ve satır bölünemez."""
    n = 0
    for el in list(root.iter(W + "lastRenderedPageBreak")):
        el.getparent().remove(el)
        n += 1
    for r in root.iter(W + "r"):
        ts = r.findall(W + "t")
        if len(ts) < 2:
            continue
        kids = [k for k in r if k.tag != W + "rPr"]
        merged = []
        for k in kids:
            if k.tag == W + "t" and merged and merged[-1].tag == W + "t":
                _set_t(merged[-1], (merged[-1].text or "") + (k.text or ""))
                r.remove(k)
            else:
                merged.append(k)
    return n


def split_run(r, pos: int):
    """Satırı metin konumundan ikiye böler; (sol, sağ) döner. Satırda tek w:t olmalı."""
    ts = r.findall(W + "t")
    if len(ts) != 1:
        raise EditError(f"Satırda {len(ts)} metin öğesi var; bölünemiyor: {run_text(r)[:40]!r}")
    text = ts[0].text or ""
    if pos <= 0 or pos >= len(text):
        raise EditError("Bölme konumu satır sınırında")
    left = r
    right = copy.deepcopy(r)
    # Sağ kopyada metin dışı öğeleri (sekme, sayfa sonu) yalnız uygun tarafta bırak.
    for ch in list(right):
        if ch.tag not in (W + "rPr", W + "t"):
            right.remove(ch)
    _set_t(ts[0], text[:pos])
    _set_t(right.find(W + "t"), text[pos:])
    left.addnext(right)
    return left, right


def isolate(p, start: int, end: int) -> list:
    """[start, end) aralığını tam satırlara ayırır ve bu satırları döner."""
    def locate():
        spans, off = [], 0
        for r in text_runs(p):
            n = len(run_text(r))
            spans.append((r, off, off + n))
            off += n
        return spans

    for r, a, b in locate():
        if a < start < b:
            split_run(r, start - a)
            break
    for r, a, b in locate():
        if a < end < b:
            split_run(r, end - a)
            break
    return [r for r, a, b in locate() if a >= start and b <= end and b > a]


def _tokens(s: str) -> list[str]:
    return re.findall(r"\s+|[^\s]+", s)


def minimal_span(old: str, new: str) -> tuple[int, int, str]:
    """Ortak baş ve son sözcükleri ayıklar. (old içindeki başlangıç, bitiş, yeni orta) döner."""
    a, b = _tokens(old), _tokens(new)
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    start = len("".join(a[:i]))
    end = len(old) - len("".join(a[len(a) - j:])) if j else len(old)
    mid_new = "".join(b[i:len(b) - j] if j else b[i:])
    return start, end, mid_new


def _new_run(like_run, text: str):
    r = etree.Element(W + "r")
    rpr = like_run.find(W + "rPr") if like_run is not None else None
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    t = etree.SubElement(r, W + "t")
    _set_t(t, text)
    return r


# ---------------------------------------------------------------------------
# İşlemler
# ---------------------------------------------------------------------------


def op_replace(tr: Tracker, p, old: str, new: str) -> None:
    full = para_text(p)
    n = full.count(old)
    if n != 1:
        raise EditError(f"'{old[:60]}' paragrafta {n} kez geçiyor (1 olmalı). Paragraf: {full[:120]!r}")
    base = full.index(old)
    s, e, mid_new = minimal_span(old, new)
    start, end = base + s, base + e
    if start == end and not mid_new:
        return
    if start == end:
        # Yalnız ekleme: konumdan önceki satırın sonuna eklenir.
        runs_before = [r for r in isolate(p, 0, start)] if start > 0 else []
        anchor = runs_before[-1] if runs_before else None
        ins = tr.mark("ins")
        ins.append(_new_run(anchor if anchor is not None else text_runs(p)[0], mid_new))
        if anchor is not None:
            anchor.addnext(ins)
        else:
            first = text_runs(p)[0]
            first.addprevious(ins)
        return
    pieces = isolate(p, start, end)
    if not pieces:
        raise EditError("Silinecek parça bulunamadı")
    like = pieces[0]
    # Ardışık parçaları aynı ebeveyn içinde w:del ile sar.
    groups: list[list] = []
    for r in pieces:
        if groups and groups[-1][-1].getnext() is r:
            groups[-1].append(r)
        else:
            groups.append([r])
    last_del = None
    for g in groups:
        d = tr.mark("del")
        g[0].addprevious(d)
        for r in g:
            d.append(r)
            for t in r.findall(W + "t"):
                t.tag = W + "delText"
        last_del = d
    if mid_new:
        ins = tr.mark("ins")
        ins.append(_new_run(like, mid_new))
        last_del.addnext(ins)


def _ppr_core_copy(ppr):
    """pPrChange içine konacak eski pPr: rPr, sectPr ve pPrChange dışındaki öğeler."""
    old = etree.Element(W + "pPr")
    if ppr is not None:
        for ch in ppr:
            if ch.tag in (W + "rPr", W + "sectPr", W + "pPrChange"):
                continue
            old.append(copy.deepcopy(ch))
    return old


def _ordered_insert(rpr, el) -> None:
    name = etree.QName(el).localname
    idx = RPR_ORDER.index(name)
    for i, ch in enumerate(rpr):
        cname = etree.QName(ch).localname
        if cname in RPR_ORDER and RPR_ORDER.index(cname) > idx:
            rpr.insert(i, el)
            return
    rpr.append(el)


def _track_rpr(tr: Tracker, run, mutate) -> None:
    rpr = run.find(W + "rPr")
    if rpr is None:
        rpr = etree.Element(W + "rPr")
        run.insert(0, rpr)
    if rpr.find(W + "rPrChange") is not None:
        # Satırda zaten izlenen biçim değişikliği var: ilk (özgün) biçim kaydı korunur.
        mutate(rpr)
        return
    old = copy.deepcopy(rpr)
    mutate(rpr)
    for ch in rpr.findall(W + "rPrChange"):
        rpr.remove(ch)
    chg = tr.mark("rPrChange")
    chg.append(old)
    rpr.append(chg)


def op_format_paragraph(tr: Tracker, p, like) -> None:
    ppr = p.find(W + "pPr")
    like_ppr = like.find(W + "pPr")
    new_ppr = copy.deepcopy(like_ppr) if like_ppr is not None else etree.Element(W + "pPr")
    for ch in new_ppr.findall(W + "pPrChange") + new_ppr.findall(W + "rPr") + new_ppr.findall(W + "sectPr"):
        new_ppr.remove(ch)
    if ppr is not None:
        for keep in ("rPr", "sectPr"):
            el = ppr.find(W + keep)
            if el is not None:
                new_ppr.append(copy.deepcopy(el))
    chg = tr.mark("pPrChange")
    chg.append(_ppr_core_copy(ppr))
    new_ppr.append(chg)
    if ppr is not None:
        p.replace(ppr, new_ppr)
    else:
        p.insert(0, new_ppr)
    like_runs = text_runs(like)
    like_sz = None
    if like_runs:
        lr = like_runs[0].find(W + "rPr")
        if lr is not None and lr.find(W + "sz") is not None:
            like_sz = lr.find(W + "sz").get(W + "val")
    if like_sz is None:
        return
    for r in text_runs(p):
        def mutate(rpr, v=like_sz):
            for tag in ("sz", "szCs"):
                for ch in rpr.findall(W + tag):
                    rpr.remove(ch)
            el = etree.Element(W + "sz")
            el.set(W + "val", v)
            _ordered_insert(rpr, el)
        _track_rpr(tr, r, mutate)


def op_run_size(tr: Tracker, p, sz: str) -> int:
    """Yazı boyutu sz olmayan satırları sz yapar (bağlantı satırları dahil). Değişen satır sayısını döner."""
    n = 0
    for r in text_runs(p):
        if not run_text(r):
            continue
        rpr = r.find(W + "rPr")
        cur = rpr.find(W + "sz").get(W + "val") if rpr is not None and rpr.find(W + "sz") is not None else None
        if cur == sz:
            continue
        def mutate(rpr, v=sz):
            for tag in ("sz", "szCs"):
                for ch in rpr.findall(W + tag):
                    rpr.remove(ch)
            el = etree.Element(W + "sz")
            el.set(W + "val", v)
            _ordered_insert(rpr, el)
        _track_rpr(tr, r, mutate)
        n += 1
    return n


def op_italic(tr: Tracker, p, text: str, occurrence: int | None = None) -> None:
    full = para_text(p)
    hits = [m.start() for m in re.finditer(re.escape(text), full)]
    if occurrence is None:
        if len(hits) != 1:
            raise EditError(f"'{text[:60]}' paragrafta {len(hits)} kez geçiyor (1 olmalı; ya da occurrence ver)")
        start = hits[0]
    else:
        if occurrence >= len(hits):
            raise EditError(f"'{text[:60]}' için {occurrence}. geçiş yok")
        start = hits[occurrence]
    for r in isolate(p, start, start + len(text)):
        def mutate(rpr):
            if rpr.find(W + "i") is None:
                _ordered_insert(rpr, etree.Element(W + "i"))
        _track_rpr(tr, r, mutate)


def op_delete_paragraph(tr: Tracker, p) -> None:
    """Paragrafın bütün metnini ve paragraf işaretini silinmiş olarak işaretler."""
    for r in text_runs(p):
        d = tr.mark("del")
        r.addprevious(d)
        d.append(r)
        for t in r.findall(W + "t"):
            t.tag = W + "delText"
    ppr = p.find(W + "pPr")
    if ppr is None:
        ppr = etree.Element(W + "pPr")
        p.insert(0, ppr)
    rpr = ppr.find(W + "rPr")
    if rpr is None:
        rpr = etree.Element(W + "rPr")
        after = [ppr.find(W + "sectPr"), ppr.find(W + "pPrChange")]
        after = [a for a in after if a is not None]
        if after:
            after[0].addprevious(rpr)
        else:
            ppr.append(rpr)
    rpr.insert(0, tr.mark("del"))


def op_insert_paragraph(tr: Tracker, root, anchor, text: str, like) -> None:
    p = etree.Element(W + "p")
    like_ppr = like.find(W + "pPr")
    ppr = copy.deepcopy(like_ppr) if like_ppr is not None else etree.Element(W + "pPr")
    for ch in ppr.findall(W + "pPrChange"):
        ppr.remove(ch)
    prpr = ppr.find(W + "rPr")
    if prpr is None:
        prpr = etree.SubElement(ppr, W + "rPr")
    prpr.insert(0, tr.mark("ins"))
    p.append(ppr)
    ins = tr.mark("ins")
    like_runs = text_runs(like)
    ins.append(_new_run(like_runs[0] if like_runs else None, text))
    p.append(ins)
    anchor.addprevious(p)


# ---------------------------------------------------------------------------
# Kabul
# ---------------------------------------------------------------------------


def accept_tree(root) -> int:
    n = 0
    for d in root.xpath("//w:del[not(ancestor::w:rPr)]", namespaces={"w": W_NS}):
        d.getparent().remove(d)
        n += 1
    for ins in root.xpath("//w:ins[not(ancestor::w:rPr)]", namespaces={"w": W_NS}):
        parent = ins.getparent()
        idx = parent.index(ins)
        for ch in list(ins):
            parent.insert(idx, ch)
            idx += 1
        parent.remove(ins)
        n += 1
    for tag in ("pPrChange", "rPrChange"):
        for el in list(root.iter(W + tag)):
            el.getparent().remove(el)
            n += 1
    # Paragraf işareti silinmiş ve metni kalmamış paragraf kaldırılır. Metni kalan paragrafı
    # sonrakiyle birleştirmek bu betiğin işi değildir; o durumda yalnız işaret kaldırılır.
    for p in root.xpath("//w:p[w:pPr/w:rPr/w:del]", namespaces={"w": W_NS}):
        if not "".join(t.text or "" for t in p.iter(W + "t")).strip():
            p.getparent().remove(p)
            n += 1
    for el in root.xpath("//w:rPr/w:ins | //w:rPr/w:del", namespaces={"w": W_NS}):
        el.getparent().remove(el)
        n += 1
    return n


# ---------------------------------------------------------------------------
# Dosya işlemleri
# ---------------------------------------------------------------------------


def _rewrite(docx: Path, out: Path, fn) -> object:
    with zipfile.ZipFile(docx) as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    res = None
    tmp = Path(tempfile.mkstemp(suffix=".docx")[1])
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in items:
            if info.filename == "word/document.xml":
                root = etree.fromstring(data)
                res = fn(root)
                data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
            zout.writestr(info, data)
    shutil.move(str(tmp), out)
    return res


def apply_edits(docx: Path, segments: Path, edits: list, out: Path, author: str, date: str) -> list[str]:
    segs = {s["id"]: s for s in json.loads(segments.read_text(encoding="utf-8"))}
    log: list[str] = []

    def fn(root):
        drop_render_hints(root)
        tr = Tracker(root, author, date)
        paras = body_paragraphs(root)
        body = root.find(W + "body")
        tables = [ch for ch in body if ch.tag == W + "tbl"]

        def para(pid):
            s = segs.get(pid)
            if s is None or s.get("part", "word/document.xml") != "word/document.xml":
                raise EditError(f"{pid} gövde paragrafı değil ya da yok")
            p = paras[s["index"]]
            want = re.sub(r"</?[a-z]+\d*>|\{[A-Z]+\d*\}", "", s.get("text", ""))
            want = re.sub(r"\s+", " ", want).strip()[:30]
            got = re.sub(r"\s+", " ", para_text(p)).strip()
            if want and want[:20] not in got:
                raise EditError(f"{pid} kimliği beklenen paragrafı göstermiyor: {got[:60]!r}")
            return p

        # Paragraf eklemeleri dizinleri bozmasın diye önce bütün hedefler çözülür.
        resolved = []
        for e in edits:
            op = e["op"]
            if op == "insert_paragraph":
                anchor = para(e["before_pid"]) if "before_pid" in e else tables[e["before_table"]]
                resolved.append((e, anchor, para(e["style_like_pid"])))
            elif op == "format_paragraph":
                resolved.append((e, para(e["pid"]), para(e["like_pid"])))
            else:
                resolved.append((e, para(e["pid"]), None))
        for e, target, aux in resolved:
            op = e["op"]
            if op == "replace":
                op_replace(tr, target, e["old"], e["new"])
                log.append(f"{e['pid']}: '{e['old']}' -> '{e['new']}'")
            elif op == "italic":
                op_italic(tr, target, e["text"], e.get("occurrence"))
                log.append(f"{e['pid']}: italik '{e['text']}'")
            elif op == "run_size":
                k = op_run_size(tr, target, str(e["sz"]))
                log.append(f"{e['pid']}: {k} satırın yazı boyutu {e['sz']} yarım punto")
            elif op == "format_paragraph":
                op_format_paragraph(tr, target, aux)
                log.append(f"{e['pid']}: biçim {e['like_pid']} gibi")
            elif op == "delete_paragraph":
                op_delete_paragraph(tr, target)
                log.append(f"{e['pid']}: paragraf silindi")
            elif op == "insert_paragraph":
                op_insert_paragraph(tr, root, target, e["text"], aux)
                where = e.get("before_pid") or f"çizelge {e['before_table']}"
                log.append(f"yeni paragraf ({where} önüne): '{e['text']}'")
            else:
                raise EditError(f"Bilinmeyen işlem: {op}")
        # Bölünen satırların kopyaları aynı rPrChange kimliğini taşıyabilir; bu betiğin
        # eklediği bütün değişiklik öğelerine yeni ve tekil kimlik verilir.
        for el in root.iter(W + "ins", W + "del", W + "rPrChange", W + "pPrChange"):
            if el.get(W + "author") == tr.author and el.get(W + "date") == tr.date:
                el.set(W + "id", str(tr.next_id))
                tr.next_id += 1
        return log

    _rewrite(docx, out, fn)
    return log


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply")
    a.add_argument("docx", type=Path)
    a.add_argument("--segments", required=True, type=Path)
    a.add_argument("--edits", required=True, type=Path)
    a.add_argument("--out", required=True, type=Path)
    a.add_argument("--author", default="Claude")
    a.add_argument("--date", default="2026-10-20T00:00:00Z")
    c = sub.add_parser("accept")
    c.add_argument("docx", type=Path)
    c.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "apply":
        data = json.loads(args.edits.read_text(encoding="utf-8"))
        edits = data["edits"] if isinstance(data, dict) else data
        try:
            log = apply_edits(args.docx, args.segments, edits, args.out, args.author, args.date)
        except EditError as ex:
            print(f"HATA: {ex}", file=sys.stderr)
            return 1
        print("\n".join(log))
        print(f"{len(log)} işlem uygulandı -> {args.out}")
    else:
        n = _rewrite(args.docx, args.out, accept_tree)
        print(f"{n} izlenen değişiklik öğesi kabul edildi -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
