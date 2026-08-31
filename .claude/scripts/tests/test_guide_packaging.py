#!/usr/bin/env python3

from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "crawl-ref/source"
GUIDES = ("crawl_manual.txt", "quickstart.txt", "macros_guide.txt",
          "options_guide.txt", "tiles_help.txt")


class GuidePackagingTest(unittest.TestCase):
    @staticmethod
    def _assert_complete_web_scroller_snapshots(source: str):
        marker = 'tiles.ui_state_change("formatted-scroller", 0);'
        positions = []
        offset = 0
        while (position := source.find(marker, offset)) != -1:
            positions.append(position)
            offset = position + len(marker)
        if not positions:
            raise AssertionError("no durable formatted-scroller update found")
        for position in positions:
            start = source.rfind("tiles.json_open_object();", 0, position)
            if start == -1:
                raise AssertionError("formatted-scroller update has no payload")
            payload = source[start:position]
            for field in ('"title"', '"text"', '"highlight"'):
                if f"tiles.json_write_string({field}" not in payload:
                    raise AssertionError(
                        f"formatted-scroller snapshot is missing {field}")

    def _assert_install(self, android: bool):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / ("assets" if android else "share")
            command = ["make", "-s", "install-guide-docs",
                       f"datadir_fp={destination}", f"DESTDIR={directory}"]
            if android:
                command.append("ANDROID=test")
            subprocess.run(command, cwd=SOURCE, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for guide in GUIDES:
                self.assertTrue((destination / "docs" / guide).is_file(), guide)
                self.assertTrue((destination / "docs" / "zh" / guide).is_file(),
                                "zh/" + guide)

    def test_desktop_install_contains_both_languages(self):
        self._assert_install(False)

    def test_android_assets_contain_both_languages(self):
        self._assert_install(True)

    def test_web_scroller_durable_update_binds_title_and_body(self):
        source = (SOURCE / "scroller.cc").read_text(encoding="utf-8")
        self._assert_complete_web_scroller_snapshots(source)

        for field in ("title", "text", "highlight"):
            mutated = source.replace(
                f'tiles.json_write_string("{field}"',
                f'tiles.json_write_string("lost_{field}"', 1)
            with self.subTest(missing_field=field):
                with self.assertRaises(AssertionError):
                    self._assert_complete_web_scroller_snapshots(mutated)


if __name__ == "__main__":
    unittest.main()
