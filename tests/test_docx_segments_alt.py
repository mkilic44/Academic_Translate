"""docx_segments.py: şekil alternatif metninin çevrilmesi."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import docx_segments as ds  # noqa: E402

WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


class AltTextTests(unittest.TestCase):
    def test_alt_text_matching_caption_is_translated(self):
        caption = "<b>Şekil 4.</b> Ortak alanda toprak tuzluluğu değişimi: 100 m ızgara, 16869 ha."
        alt_map = {ds._alt_key(caption): ds._plain("<b>Figure 4.</b> Change in soil salinity: 100 m grid, 16869 ha.")}
        root = etree.fromstring(
            f'<r xmlns:wp="{WP}"><wp:docPr id="1" name="p" '
            'descr="Şekil 4. Ortak alanda toprak tuzluluğu değişimi: 100 m ızgara, 16.869 ha."/></r>'.encode("utf-8")
        )
        report = {"alt_text_replaced": 0, "alt_text_untranslated": []}
        ds._translate_alt_text(root, alt_map, report)
        self.assertEqual(report["alt_text_replaced"], 1)
        self.assertEqual(root[0].get("descr"), "Figure 4. Change in soil salinity: 100 m grid, 16869 ha.")

    def test_unmatched_alt_text_is_reported(self):
        root = etree.fromstring(f'<r xmlns:wp="{WP}"><wp:docPr id="1" name="p" descr="Logo"/></r>'.encode("utf-8"))
        report = {"alt_text_replaced": 0, "alt_text_untranslated": []}
        ds._translate_alt_text(root, {}, report)
        self.assertEqual(report["alt_text_untranslated"], ["Logo"])


if __name__ == "__main__":
    unittest.main()
