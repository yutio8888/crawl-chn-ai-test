#!/usr/bin/env python3
"""Run production cache rules/helpers in temporary repositories without compiling."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "crawl-ref/source"


class BuildCacheHelpersTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.repo = self.directory / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.source = self.repo / "crawl-ref/source"
        (self.source / "util").mkdir(parents=True)
        # Exercise the real Makefile cache block, without unrelated library,
        # generated-header, or compiler discovery performed by the full file.
        text = (SOURCE / "Makefile").read_text()
        start = text.index("# Share persistent caches")
        block = text[start:text.index("ifdef USE_ICC", start)]
        (self.source / "Makefile").write_text("GCC := gcc\nGXX := g++\n" + block)
        for target in ("console", "tiles", "android"):
            (self.source / f"util/build-{target}.sh").write_text((SOURCE / f"util/build-{target}.sh").read_text())
        (self.repo / ".gitignore").write_text(".worktrees/\n.ccache/\ncrawl-ref/source/android-project/app/build/\ncrawl-ref/source/android-project/local.properties\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.binary = self.directory / "bin"
        self.binary.mkdir()
        (self.binary / "ccache").write_text("#!/bin/sh\nexit 0\n")
        (self.binary / "ccache").chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.binary) + os.pathsep + os.environ["PATH"])

    def git(self, *args, root=None):
        return subprocess.check_output(["git", "-C", str(root or self.repo), *args], text=True, stderr=subprocess.DEVNULL).strip()

    def cache(self, *args, root=None):
        result = subprocess.run(["/usr/bin/make", "--no-print-directory", "ccache-config", *args],
                                cwd=root or self.source, env=self.env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return {key: value.strip() for key, value in
                (line.split(": ", 1) for line in result.stdout.splitlines() if ": " in line)}

    def test_profiles_are_separate_and_android_variants_retain_host_suffix(self):
        cases = [((), "console"), (("WEBTILES=y",), "webtiles"), (("TILES=y",), "native-tiles"),
                 (("CROSSHOST=x86_64-w64-mingw32", "TILES=y"), "mingw-tiles"),
                 (("ANDROID=1",), "android-tiles/buildTest/host"),
                 (("ANDROID=1", "ANDROID_VARIANT=release"), "android-tiles/release/host"),
                 (("ANDROID=1", "ANDROID_VARIANT=debug"), "android-tiles/debug/host")]
        for args, profile in cases:
            with self.subTest(profile=profile):
                state = self.cache(*args)
                self.assertEqual(state["ccache profile"], profile)
                self.assertEqual(state["ccache mode"], "read-write")
                self.assertEqual(state["ccache dir"], str(self.repo / ".ccache" / profile))
        self.assertEqual(self.cache("CROSSHOST=unknown-cross")["ccache mode"], "disabled")

    def test_only_main_and_dedicated_build_worktrees_can_write(self):
        for name, writable in (("developer", False), ("linux-console", True), ("mingw-tiles", True), ("android-tiles", True)):
            self.git("worktree", "add", "--detach", f".worktrees/{name}", "HEAD")
            state = self.cache(root=self.repo / ".worktrees" / name / "crawl-ref/source")
            self.assertEqual(state["ccache mode"], "read-write" if writable else "read-only")
            self.assertEqual(state["ccache dir"], str(self.repo / ".ccache/console"))

    def fake_make(self):
        self.log = self.directory / "commands.jsonl"
        script = f'''#!{sys.executable}
import json,os,pathlib,subprocess,sys
with open(os.environ['HELPER_TEST_LOG'],'a') as handle:
    handle.write(json.dumps({{'tool':'make','args':sys.argv[1:],'cwd':os.getcwd(),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'cache':os.environ.get('CCACHE_DIR')}})+'\\n')
'''
        (self.binary / "make").write_text(script)
        (self.binary / "make").chmod(0o755)
        self.env["HELPER_TEST_LOG"] = str(self.log)

    def test_windows_helper_builds_caller_head_and_caps_parallelism(self):
        self.fake_make()
        main_head = self.git("rev-parse", "HEAD")
        self.git("worktree", "add", "--detach", ".worktrees/mingw-tiles", "HEAD")
        self.git("worktree", "add", "-b", "feature", ".worktrees/feature", "HEAD")
        caller = self.repo / ".worktrees/feature"
        (caller / "new-file").write_text("new\n")
        self.git("add", ".", root=caller)
        self.git("commit", "-qm", "caller", root=caller)
        script = caller / "crawl-ref/source/util/build-tiles.sh"
        subprocess.run(["bash", str(script), "-j99", "NPROC=99"], env=self.env, check=True, stdout=subprocess.DEVNULL)
        record = json.loads(self.log.read_text().splitlines()[0])
        self.assertEqual(record["head"], self.git("rev-parse", "HEAD", root=caller))
        self.assertEqual(self.git("rev-parse", "HEAD"), main_head)
        self.assertEqual(record["args"][-2:], ["-j4", "NPROC=4"])
        self.assertEqual(record["cache"], str(self.repo / ".ccache/mingw-tiles"))
        build = self.repo / ".worktrees/mingw-tiles"
        (build / "unsafe.h").write_text("preserve\n")
        result = subprocess.run(["bash", str(script)], env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((build / "unsafe.h").exists())
        self.assertEqual(len(self.log.read_text().splitlines()), 1)

    def test_android_helper_uses_tracked_wrapper_and_separate_host_ndk_caches(self):
        self.fake_make()
        project = self.source / "android-project"
        project.mkdir()
        wrapper = project / "gradlew"
        wrapper.write_text(f'''#!{sys.executable}
import json,os,pathlib,sys
with open(os.environ['HELPER_TEST_LOG'],'a') as handle:
    handle.write(json.dumps({{'tool':'gradle','args':sys.argv[1:],'cwd':os.getcwd(),'cache':os.environ.get('CCACHE_DIR')}})+'\\n')
p=pathlib.Path('app/build/outputs/apk/buildTest/app-buildTest.apk')
p.parent.mkdir(parents=True,exist_ok=True)
p.write_bytes(b'fixture')
''')
        wrapper.chmod(0o755)
        self.git("add", ".")
        self.git("commit", "-qm", "wrapper")
        self.git("worktree", "add", "--detach", ".worktrees/android-tiles", "HEAD")
        sdk = self.directory / "Android SDK"
        sdk.mkdir()
        keystore = self.directory / "debug.keystore"
        keystore.write_text("fixture")
        self.env.update(ANDROID_SDK_ROOT=str(sdk), ANDROID_KEYSTORE=str(keystore))
        subprocess.run(["bash", str(self.source / "util/build-android.sh"), "123"], env=self.env, check=True, stdout=subprocess.DEVNULL)
        records = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(records[0]["cache"], str(self.repo / ".ccache/android-tiles/buildTest/host"))
        self.assertEqual(records[1]["cache"], str(self.repo / ".ccache/android-tiles/buildTest/ndk"))
        self.assertIn("NPROC=4", records[0]["args"])
        self.assertIn("ANDROID_VARIANT=buildTest", records[0]["args"])
        self.assertEqual(records[1]["args"], ["--no-daemon", "--max-workers=4", ":app:assembleBuildTest"])
        self.assertNotIn("wrapper", records[1]["args"])


if __name__ == "__main__":
    unittest.main()
