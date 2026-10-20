#!/usr/bin/env python3
"""Son çeviriyi (Markdown) biçimlendirilmiş .docx dosyasına, isteğe bağlı .pdf'e çevirir.

Kullanım:
    python scripts/export_docx.py WS/final-translation.md --out CIKTI.docx --lang tr [--template DERGI.docx] [--pdf]

- --template verilirse derginin Word şablonu pandoc başvuru belgesi
  (--reference-doc) olarak kullanılır ve biçim ondan gelir. Dergi şablonu
  her zaman bu betiğin varsayılanlarından önce gelir.
- Şablon yoksa pandoc'un varsayılan başvuru belgesi python-docx ile
  references/typesetting-rules.md kurallarına göre düzenlenir: Times New Roman,
  gövde 12 pt, 1,25 satır aralığı, başlıklar kalın 16/14/12 pt.
  python-docx yoksa pandoc varsayılan biçemi kullanılır ve uyarı verilir.
- --pdf: LibreOffice (soffice) varsa .docx dosyasından PDF üretir.
- --lang belge dilini Word'e bildirir (tr -> tr-TR, en -> en-US);
  yazım denetimi ve Türkçe büyük harf dönüşümü buna göre çalışır.
Gereksinim: pandoc. İsteğe bağlı: python-docx, LibreOffice.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LANGS = {"tr": "tr-TR", "en": "en-US"}


def build_reference(path: Path) -> bool:
    """Varsayılan pandoc başvuru belgesini üretir ve biçemleri düzenler."""
    res = subprocess.run(["pandoc", "-o", str(path), "--print-default-data-file", "reference.docx"], check=False)
    if res.returncode != 0 or not path.exists() or path.stat().st_size == 0:
        return False
    try:
        from docx import Document  # type: ignore
        from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore
        from docx.oxml.ns import qn  # type: ignore
        from docx.shared import Pt, RGBColor  # type: ignore
    except ImportError:
        print("UYARI: python-docx yok; pandoc varsayılan biçemi kullanılacak (pip install python-docx).")
        return True

    doc = Document(str(path))

    # Biçem adına göre arama yapılır; python-docx'in ad çevirisi pandoc
    # şablonundaki "Heading 1" gibi adlarda doğrudan erişimi bozabiliyor.
    by_name = {s.name: s for s in doc.styles}

    def font(style, size, bold=None, italic=None, center=False, before=None, after=None, line=None):
        st = by_name[style]
        f = st.font
        f.name = "Times New Roman"
        f.size = Pt(size)
        f.color.rgb = RGBColor(0, 0, 0)
        if bold is not None:
            f.bold = bold
        if italic is not None:
            f.italic = italic
        rpr = st.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = rpr.makeelement(qn("w:rFonts"), {})
            rpr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), "Times New Roman")
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]
        pf = st.paragraph_format
        if center:
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if before is not None:
            pf.space_before = Pt(before)
        if after is not None:
            pf.space_after = Pt(after)
        if line is not None:
            pf.line_spacing = line

    names = set(by_name)
    for body in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if body in names:
            font(body, 12, after=6, line=1.25)
    if "Title" in names:
        font("Title", 16, bold=True, center=True, after=18)
    for lvl, size, before, after in ((1, 14, 18, 12), (2, 12, 14, 8), (3, 12, 10, 6)):
        name = f"Heading {lvl}"
        if name in names:
            font(name, size, bold=True, italic=False, before=before, after=after)
    for cap in ("Caption", "Table Caption", "Image Caption"):
        if cap in names:
            font(cap, 10, italic=False, after=6)
    doc.save(str(path))
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--lang", choices=sorted(LANGS), required=True)
    ap.add_argument("--template", type=Path, help="Derginin Word şablonu (.docx)")
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args(argv)
    if not shutil.which("pandoc"):
        print("pandoc bulunamadı: https://pandoc.org/installing.html")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        ref = a.template
        if ref is None:
            ref = Path(tmp) / "reference.docx"
            if not build_reference(ref):
                ref = None
        cmd = ["pandoc", str(a.markdown), "-f", "gfm+tex_math_dollars", "-o", str(a.out), "-M", f"lang={LANGS[a.lang]}"]
        if ref is not None:
            cmd += ["--reference-doc", str(ref)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            print(res.stderr)
            return res.returncode
    print(f"DOCX: {a.out}")
    if a.pdf:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            print("UYARI: LibreOffice yok; PDF üretilmedi. Word'de 'Farklı kaydet > PDF' kullanılabilir.")
            return 0
        res = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(a.out.parent), str(a.out)],
                             capture_output=True, text=True, check=False)
        pdf = a.out.with_suffix(".pdf")
        print(f"PDF: {pdf}" if pdf.exists() else f"UYARI: PDF üretilemedi: {res.stderr.strip()[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
