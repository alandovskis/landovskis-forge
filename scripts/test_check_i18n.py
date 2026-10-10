import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import check_i18n
import tomlite

CONFIG_OK = """\
base_url = "https://example.test"

[translations]
hello = "Hello"
year = "© {year} Forge"

[languages.fr]
title = "Forge"

[languages.fr.translations]
hello = "Bonjour"
year = "© {year} Forge"
"""


class TomliteTests(unittest.TestCase):
    def test_parses_tables_and_top_level_keys(self):
        tables = tomlite.parse(CONFIG_OK, "config.toml")
        self.assertEqual(tables[""]["base_url"], '"https://example.test"')
        self.assertEqual(tables["translations"]["hello"], '"Hello"')
        self.assertEqual(tables["languages.fr.translations"]["hello"], '"Bonjour"')

    def test_rejects_multiline_strings(self):
        with self.assertRaises(ValueError):
            tomlite.parse('a = """x\ny"""\n', "f")

    def test_rejects_unparsable_lines(self):
        with self.assertRaises(ValueError):
            tomlite.parse("[t]\n  \"orphan\",\n", "f")

    def test_front_matter_extracts_plus_delimited_block(self):
        text = '+++\ntitle = "T"\n[extra]\nk = "v"\n+++\nbody\n'
        tables = tomlite.front_matter(text, "p.md")
        self.assertEqual(tables["extra"]["k"], '"v"')

    def test_front_matter_requires_block(self):
        with self.assertRaises(ValueError):
            tomlite.front_matter("no front matter", "p.md")


class TranslationTests(unittest.TestCase):
    def test_matching_tables_pass(self):
        self.assertEqual(check_i18n.check_translations(CONFIG_OK), [])

    def test_key_missing_in_french(self):
        text = CONFIG_OK.replace('hello = "Bonjour"\n', "")
        problems = check_i18n.check_translations(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("hello", problems[0])
        self.assertIn("missing in fr", problems[0])

    def test_key_missing_in_english(self):
        text = CONFIG_OK.replace('[translations]\nhello = "Hello"\n', "[translations]\n")
        problems = check_i18n.check_translations(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing in en", problems[0])

    def test_placeholder_mismatch(self):
        head, _, tail = CONFIG_OK.rpartition('year = "© {year} Forge"')
        text = head + 'year = "© {annee} Forge"' + tail
        problems = check_i18n.check_translations(text)
        self.assertEqual(len(problems), 1)
        self.assertIn("placeholders", problems[0])

    def test_no_translation_table_is_a_problem(self):
        problems = check_i18n.check_translations('base_url = "x"\n')
        self.assertTrue(any("[translations]" in p for p in problems))


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


PAGE = '+++\ntitle = "T"\n[extra]\nk = "v"\n+++\n'


class ContentTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_paired_content_passes(self):
        write(self.root, "_index.md", PAGE)
        write(self.root, "_index.fr.md", PAGE)
        write(self.root, "projects/a.md", PAGE)
        write(self.root, "projects/a.fr.md", PAGE)
        self.assertEqual(check_i18n.check_content(self.root), [])

    def test_missing_french_counterpart(self):
        write(self.root, "a.md", PAGE)
        problems = check_i18n.check_content(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("no French counterpart", problems[0])

    def test_missing_english_counterpart(self):
        write(self.root, "a.fr.md", PAGE)
        problems = check_i18n.check_content(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("no English counterpart", problems[0])

    def test_front_matter_key_mismatch(self):
        write(self.root, "a.md", PAGE)
        write(self.root, "a.fr.md", PAGE.replace('k = "v"\n', ""))
        problems = check_i18n.check_content(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("extra", problems[0])
        self.assertIn("k", problems[0])


class MainTests(unittest.TestCase):
    def test_main_reports_and_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "config.toml", CONFIG_OK.replace('hello = "Bonjour"\n', ""))
            write(root, "content/a.md", PAGE)
            self.assertEqual(check_i18n.main(root), 1)

    def test_main_returns_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "config.toml", CONFIG_OK)
            write(root, "content/a.md", PAGE)
            write(root, "content/a.fr.md", PAGE)
            self.assertEqual(check_i18n.main(root), 0)


if __name__ == "__main__":
    unittest.main()
