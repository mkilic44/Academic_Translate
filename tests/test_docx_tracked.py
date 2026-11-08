"""docx_tracked.py birim testleri."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import docx_tracked as dt  # noqa: E402

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class RenderHintTests(unittest.TestCase):
    def test_last_rendered_page_break_is_dropped_and_text_merged(self):
        xml = (
            f'<w:document xmlns:w="{W_NS}"><w:body><w:p><w:r><w:t>Mekânsal tahmin </w:t>'
            "<w:lastRenderedPageBreak/><w:t>için sekiz aday</w:t></w:r></w:p></w:body></w:document>"
        )
        root = etree.fromstring(xml.encode("utf-8"))
        self.assertEqual(dt.drop_render_hints(root), 1)
        r = root.find(f".//{{{W_NS}}}r")
        ts = r.findall(f"{{{W_NS}}}t")
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0].text, "Mekânsal tahmin için sekiz aday")
        left, right = dt.split_run(r, 9)
        self.assertEqual(dt.run_text(left) + dt.run_text(right), "Mekânsal tahmin için sekiz aday")

    def test_tab_between_texts_is_kept(self):
        xml = (
            f'<w:document xmlns:w="{W_NS}"><w:body><w:p><w:r><w:t>a</w:t><w:tab/>'
            "<w:t>b</w:t></w:r></w:p></w:body></w:document>"
        )
        root = etree.fromstring(xml.encode("utf-8"))
        dt.drop_render_hints(root)
        r = root.find(f".//{{{W_NS}}}r")
        self.assertEqual(len(r.findall(f"{{{W_NS}}}t")), 2)
        self.assertIsNotNone(r.find(f"{{{W_NS}}}tab"))


if __name__ == "__main__":
    unittest.main()
