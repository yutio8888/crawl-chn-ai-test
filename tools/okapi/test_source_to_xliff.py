#!/usr/bin/env python3
import unittest

from source_to_xliff import build_xliff, entries


class SourceToXliffTest(unittest.TestCase):
    def test_namespace_prefix_is_removed_but_ui_pipes_are_preserved(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            output = Path(directory) / "out.xlf"
            source.write_text(
                "%%%%\nstatus|Fire\n火焰\n%%%%\nCorona\nweirdly glowing ball\n怪异发光球\n%%%%\n<w>Cast</w>|Describe|Hide|Show\n施放|描述|隐藏|显示\n",
                encoding="utf-8",
            )
            rows = list(entries(source))
            self.assertEqual(rows[0][1], "Fire")
            self.assertEqual(rows[0][3], "status")
            self.assertEqual(rows[1][0:2], ("Corona", "weirdly glowing ball"))
            self.assertEqual(rows[2][1], "<w>Cast</w>|Describe|Hide|Show")
            self.assertEqual(rows[2][3], "")
            output.write_text(build_xliff(source, "en", "zh"), encoding="utf-8")
            text = output.read_text(encoding="utf-8")
            self.assertIn("<source>Fire</source>", text)
            self.assertIn("key-prefix=status", text)
            self.assertIn("<source>&lt;w&gt;Cast&lt;/w&gt;|Describe|Hide|Show</source>", text)

    def test_inline_separator_token_is_not_a_record_boundary(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_text(
                "%%%%\nYou need %d%%%% to reach level %d.\n你距离升级到 %d 级还有 %d%%。\n%%%%\n",
                encoding="utf-8",
            )
            rows = list(entries(source))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][1], "You need %d%%%% to reach level %d.")
            self.assertEqual(rows[0][2], "你距离升级到 %d 级还有 %d%%。")


if __name__ == "__main__":
    unittest.main()
