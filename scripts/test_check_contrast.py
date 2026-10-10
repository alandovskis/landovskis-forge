import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import check_contrast


class ContrastTests(unittest.TestCase):
    def test_black_on_white_is_21(self):
        self.assertAlmostEqual(check_contrast.contrast_ratio("#000000", "#ffffff"), 21.0, places=1)

    def test_same_colour_is_1(self):
        self.assertAlmostEqual(check_contrast.contrast_ratio("#336699", "#336699"), 1.0, places=2)

    def test_reads_tokens_and_flags_low_contrast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sass").mkdir()
            tokens = ":root {\n" + "".join(
                f"  --{name}: {value};\n"
                for name, value in {
                    "bg": "#0b0e13", "surface": "#11161d", "surface-2": "#171d26",
                    "text": "#e6eaf0", "muted": "#222222", "accent": "#ff8a3d",
                    "accent-ink": "#0b0e13",
                }.items()
            ) + "}\n"
            (root / "sass" / "_tokens.scss").write_text(tokens, encoding="utf-8")
            self.assertEqual(check_contrast.main(root), 1)


if __name__ == "__main__":
    unittest.main()
