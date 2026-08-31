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


if __name__ == "__main__":
    unittest.main()
