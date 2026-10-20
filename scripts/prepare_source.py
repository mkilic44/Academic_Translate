#!/usr/bin/env python3
"""Kaynak belgeyi çeviri çalışma klasörüne hazırlar ve parçaları birleştirir.

Kullanım:
    python scripts/prepare_source.py prepare MAKALE.docx --direction en-tr [--workspace KLASOR] [--chunk-words 6000]
    python scripts/prepare_source.py merge KLASOR

prepare:
  1. Özgün dosyayı KLASOR/original.<uzantı> olarak kopyalar.
  2. Markdown'a çevirir ve KLASOR/source.md olarak yazar.
     - .md, .markdown, .txt: olduğu gibi kopyalanır.
     - .docx, .odt, .rtf, .html, .htm, .tex, .epub: pandoc ile GitHub Markdown'a
       (gfm) çevrilir; görseller KLASOR/media altına çıkarılır. pandoc yoksa
       .docx için python-docx ile yalın dönüşüm yapılır.
     - .pdf: pdftotext (poppler) ya da PyMuPDF ile metin çıkarılır; satır sonu
       tirelemesi birleştirilir, sayfa sınırları HTML yorumu olarak işaretlenir.
       PDF dönüşümü çizelgeleri, üst simgeleri (cm-3) ve iki sütun sırasını
       bozabilir; manifest bunu uyarı olarak yazar.
  3. KLASOR/structure-manifest.md: başlıklar, çizelgeler (satır x sütun),
     şekil ve çizelge numaraları, denklemler, sözcük, sayı ve atıf sayıları.
  4. Sözcük sayısı --chunk-words değerini aşarsa ana metin başlık sınırlarında
     parçalara bölünür (KLASOR/chunks/chunk-N.md). Kaynakça KLASOR/references.md
     dosyasına ayrılır. Çizelge ve kod bloğu ortasından bölünmez.
  5. KLASOR/params.json: yöne göre varsayılan çeviri parametreleri.

merge:
  KLASOR/first-pass-chunk-*.md dosyalarını sırayla birleştirir, varsa
  references.md'yi ekler ve KLASOR/first-pass.md yazar. Parça sınırlarında
  yinelenen başlıkları raporlar.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_checks import COMMON_DEFAULTS, DEFAULTS, extract_citations, extract_numbered, structure_stats  # noqa: E402
from trtext import DOI_RE, REFERENCE_HEADINGS, extract_numbers, normalize, split_references, strip_code_and_links  # noqa: E402

PANDOC_INPUTS = {".docx", ".odt", ".rtf", ".html", ".htm", ".tex", ".epub"}


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def convert(src: Path, ws: Path, warnings: list[str]) -> str:
    ext = src.suffix.lower()
    if ext in {".md", ".markdown", ".txt"}:
        return src.read_text(encoding="utf-8")
    if ext in PANDOC_INPUTS:
        if shutil.which("pandoc"):
            res = _run(["pandoc", str(src), "-t", "gfm", "--wrap=none", f"--extract-media={ws / 'media'}"])
            if res.returncode == 0:
                if "<table" in res.stdout:
                    warnings.append("Bazı çizelgeler HTML olarak kaldı (birleştirilmiş hücre olabilir). Çevirmen HTML yapısını korur.")
                return res.stdout
            warnings.append(f"pandoc hata verdi: {res.stderr.strip()[:200]}")
        if ext == ".docx":
            warnings.append("pandoc yok ya da çalışmadı; python-docx ile yalın dönüşüm yapıldı. Biçem başlıkları dışındaki biçimler kayboldu.")
            return _docx_fallback(src)
        raise SystemExit(f"{ext} dosyası için pandoc gerekli. Kurulum: https://pandoc.org/installing.html")
    if ext == ".pdf":
        warnings.append(
            "PDF kaynaktan metin çıkarıldı. Başlık düzeyleri kaybolur; çizelgeler düz metne döner; "
            "denklemler tamamen düşebilir; üst ve alt simgeler (cm-3, R2) düzleşir; iki sütunlu düzende okuma sırası "
            "bozulabilir. Bu yüzden structure-manifest.md sayıları PDF'in değil, çıkarılan metnin sayılarıdır. "
            "Mümkünse yazardan .docx ya da LaTeX kaynağı iste; yoksa yönetici başlıkları, çizelgeleri ve denklemleri "
            "PDF sayfa görüntüsüne bakarak source.md içinde yeniden kurar ve bunu rapora yazar."
        )
        return _pdf_text(src, warnings)
    raise SystemExit(f"Desteklenmeyen uzantı: {ext}")


def _docx_fallback(src: Path) -> str:
    try:
        import docx  # type: ignore
    except ImportError as exc:
        raise SystemExit("python-docx kurulu değil: pip install python-docx") from exc
    d = docx.Document(str(src))
    out: list[str] = []
    body = d.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = docx.text.paragraph.Paragraph(child, d)
            text = p.text.strip()
            if not text:
                continue
            style = (p.style.name or "").lower() if p.style is not None else ""
            m = re.match(r"heading (\d)", style)
            if m:
                out.append("#" * int(m.group(1)) + " " + text)
            elif style == "title":
                out.append("# " + text)
            else:
                out.append(text)
        elif tag == "tbl":
            t = docx.table.Table(child, d)
            rows = [[c.text.strip().replace("\n", "<br>").replace("|", "\\|") for c in r.cells] for r in t.rows]
            if rows:
                ncol = max(len(r) for r in rows)
                rows = [r + [""] * (ncol - len(r)) for r in rows]
                out.append("| " + " | ".join(rows[0]) + " |")
                out.append("|" + "---|" * ncol)
                out.extend("| " + " | ".join(r) + " |" for r in rows[1:])
    return "\n\n".join(out) + "\n"


def _pdf_text(src: Path, warnings: list[str]) -> str:
    pages: list[str] = []
    if shutil.which("pdftotext"):
        res = _run(["pdftotext", "-enc", "UTF-8", str(src), "-"])
        if res.returncode == 0:
            pages = res.stdout.split("\f")
    if not pages:
        try:
            import fitz  # type: ignore

            with fitz.open(str(src)) as doc:
                pages = [pg.get_text() for pg in doc]
        except ImportError as exc:
            raise SystemExit("PDF için pdftotext (poppler-utils) ya da PyMuPDF gerekli.") from exc
    out: list[str] = []
    for i, page in enumerate(pages, start=1):
        if not page.strip():
            continue
        text = normalize(page)
        text = re.sub(r"([a-zçğıöşü])-\n([a-zçğıöşü])", r"\1\2", text)
        paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text) if p.strip()]
        out.append(f"<!-- sayfa {i} -->")
        out.extend(paras)
    return "\n\n".join(out) + "\n"


def word_total(text: str) -> int:
    return len(re.findall(r"\S+", strip_code_and_links(text)))


def _blocks(text: str) -> list[str]:
    """Metni boş satırlarla ayrılmış bloklara böler; çizelge ve kod bloğu bölünmez."""
    blocks, buf, in_code = [], [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        if not line.strip() and not in_code:
            if buf:
                blocks.append("\n".join(buf))
                buf = []
            continue
        buf.append(line)
    if buf:
        blocks.append("\n".join(buf))
    return blocks


def chunk(body: str, limit: int) -> list[str]:
    blocks = _blocks(body)
    sections: list[list[str]] = []
    for b in blocks:
        if re.match(r"^#{1,2}\s", b) or not sections:
            sections.append([b])
        else:
            sections[-1].append(b)
    chunks: list[list[str]] = [[]]
    count = 0

    def new_chunk() -> None:
        nonlocal count
        # Parça bir başlıkla bitmesin: başlık, ait olduğu metinle birlikte sonraki parçaya geçer.
        carry = []
        while chunks[-1] and re.match(r"^#{1,6}\s", chunks[-1][-1]):
            carry.insert(0, chunks[-1].pop())
        chunks.append(carry)
        count = sum(word_total(b) for b in carry)

    for sec in sections:
        sec_words = sum(word_total(b) for b in sec)
        if count and count + sec_words > limit:
            new_chunk()
        if sec_words > limit:
            for b in sec:
                w = word_total(b)
                if count and count + w > limit and not all(re.match(r"^#{1,6}\s", x) for x in chunks[-1]):
                    new_chunk()
                chunks[-1].append(b)
                count += w
        else:
            chunks[-1].extend(sec)
            count += sec_words
    # Çevrilecek sözcüğü olmayan parça (yalnız yorum ya da boşluk) sonrakine katılır.
    merged: list[list[str]] = []
    pending: list[str] = []
    for c in chunks:
        if not c:
            continue
        if sum(word_total(b) for b in c) == 0:
            pending.extend(c)
            continue
        merged.append(pending + c)
        pending = []
    if pending:
        if merged:
            merged[-1].extend(pending)
        else:
            merged.append(pending)
    return ["\n\n".join(c) + "\n" for c in merged]


def manifest(text: str, direction: str | None, warnings: list[str]) -> str:
    st = structure_stats(text)
    body, refs = split_references(text)
    dec = DEFAULTS[direction]["source_decimal"] if direction else "."
    nums = extract_numbers(strip_code_and_links(body), dec)
    cites = extract_citations(strip_code_and_links(body))
    numbered = extract_numbered(strip_code_and_links(body))
    headings = re.findall(r"^(#{1,6})\s+(.+)$", re.sub(r"```.*?```", "", body, flags=re.DOTALL), re.MULTILINE)
    lines = [
        "# Yapı envanteri (structure-manifest.md)",
        "",
        f"- Ana metin sözcük sayısı: {word_total(body)}",
        f"- Kaynakça: {'var' if refs.strip() else 'bulunamadı'} ({len(refs.splitlines())} satır)",
        f"- Başlıklar (kaynakça başlığı hariç): {st['headings']}",
        f"- Paragraflar: {st['paragraphs']}; liste imleri: {st['list_items']}",
        f"- Çizelgeler: {len(st['tables'])}",
    ]
    for i, (r, c) in enumerate(st["tables"], start=1):
        lines.append(f"  - Çizelge {i}: {r} satır x {c} sütun")
    lines += [
        f"- Şekil numaraları: {st['figure_numbers']}; çizelge numaraları: {st['table_numbers']}",
        f"- Ayrık denklem: {st['display_equations']}; satır içi matematik: {st['inline_math']}",
        f"- Birleştirilmiş hücre (colspan/rowspan): {st['colspan_rowspan']}",
        f"- Sayı adedi (ana metin, ondalık ayırıcı '{dec}'): {len(nums)}",
        f"- Yazar-yıl atıfı: {sum(cites.values())}; numaralı atıf: {sum(numbered.values())}",
        f"- DOI: {len(set(DOI_RE.findall(text)))}",
        "",
        "## Başlık listesi",
        "",
    ]
    lines += [f"- {'  ' * (len(h) - 1)}{h} {t.strip()}" for h, t in headings]
    lines += ["", "## Uyarılar", ""]
    lines += [f"- {w}" for w in warnings] or ["- Yok"]
    lines += [
        "",
        "## Yöneticinin elle dolduracağı bölüm",
        "",
        "- Çok öğeli hücreler (bir hücrede birden çok madde): ",
        "- Şekil içindeki metin (çevrilmeyecek, ayrı listelenecek): ",
        "- Ek materyal ve dipnotlar: ",
    ]
    return "\n".join(lines) + "\n"


def cmd_prepare(a: argparse.Namespace) -> int:
    src: Path = a.input.resolve()
    ws: Path = (a.workspace or src.parent / f"ceviri-{src.stem}").resolve()
    ws.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, ws / f"original{src.suffix.lower()}")
    warnings: list[str] = []
    text = convert(src, ws, warnings)
    (ws / "source.md").write_text(text, encoding="utf-8")
    body, refs = split_references(text)
    words = word_total(body)
    if words > a.chunk_words:
        cdir = ws / "chunks"
        cdir.mkdir(exist_ok=True)
        parts = chunk(body, a.chunk_words)
        rows = ["# Parça listesi (chunk-manifest.md)", "", f"Kaynak: {src.name}; ana metin {words} sözcük; sınır {a.chunk_words}", "",
                "| Parça | Dosya | İlk başlık | Sözcük |", "|---|---|---|---|"]
        for i, part in enumerate(parts, start=1):
            (cdir / f"chunk-{i}.md").write_text(part, encoding="utf-8")
            first = next((ln for ln in part.splitlines() if ln.startswith("#")), "(başlıksız)")
            rows.append(f"| {i} | chunks/chunk-{i}.md | {first.lstrip('#').strip()} | {word_total(part)} |")
        if refs.strip():
            heading = REFERENCE_HEADINGS.search(text)
            (ws / "references.md").write_text(heading.group(0) + "\n" + refs, encoding="utf-8")
            rows += ["", "Kaynakça references.md dosyasına ayrıldı; birleştirmede sona eklenir."]
        (ws / "chunk-manifest.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
        warnings.append(f"Metin {len(parts)} parçaya bölündü (chunk-manifest.md).")
    (ws / "structure-manifest.md").write_text(manifest(text, a.direction, warnings), encoding="utf-8")
    if a.direction:
        params = dict(COMMON_DEFAULTS)
        params.update(DEFAULTS[a.direction])
        params["direction"] = a.direction
        p = ws / "params.json"
        if not p.exists():
            p.write_text(json.dumps(params, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Çalışma klasörü: {ws}")
    print(f"source.md: {words} sözcük (ana metin)")
    for w in warnings:
        print(f"UYARI: {w}")
    return 0


def cmd_merge(a: argparse.Namespace) -> int:
    ws: Path = a.workspace.resolve()
    parts = sorted(ws.glob("first-pass-chunk-*.md"), key=lambda p: int(re.search(r"(\d+)", p.stem.split("chunk-")[-1]).group(1)))
    if not parts:
        print("first-pass-chunk-*.md bulunamadı")
        return 1
    texts = [p.read_text(encoding="utf-8").strip() + "\n" for p in parts]
    issues = []
    for i in range(len(texts) - 1):
        last = [ln for ln in texts[i].splitlines() if ln.startswith("#")][-1:]
        first = [ln for ln in texts[i + 1].splitlines() if ln.startswith("#")][:1]
        if last and first and last[0].strip() == first[0].strip():
            issues.append(f"Parça {i + 1} ile {i + 2} sınırında yinelenen başlık: {first[0].strip()}")
    merged = "\n".join(texts)
    refs = ws / "references.md"
    if refs.exists():
        merged += "\n" + refs.read_text(encoding="utf-8")
    (ws / "first-pass.md").write_text(merged, encoding="utf-8")
    print(f"{len(parts)} parça birleştirildi: {ws / 'first-pass.md'}")
    for x in issues:
        print(f"UYARI: {x}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("input", type=Path)
    p.add_argument("--workspace", type=Path)
    p.add_argument("--direction", choices=["en-tr", "tr-en"])
    p.add_argument("--chunk-words", type=int, default=6000)
    p.set_defaults(func=cmd_prepare)
    m = sub.add_parser("merge")
    m.add_argument("workspace", type=Path)
    m.set_defaults(func=cmd_merge)
    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
