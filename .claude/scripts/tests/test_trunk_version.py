#!/usr/bin/env python3
"""Version regression tests; all tag writes stay in disposable /tmp repos."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENSURE = ROOT / '.claude/scripts/ensure_version_info.sh'
SOURCE = ROOT / 'crawl-ref/source'


class TrunkVersionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='trunk-version-', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.source = self.repo / 'crawl-ref/source'
        self.util = self.source / 'util'
        self.util.mkdir(parents=True)
        shutil.copy2(SOURCE / 'util/gen_ver.pl', self.util)
        shutil.copy2(SOURCE / 'Makefile', self.source)
        # Retain the actual version rules, without C++ build dependencies.
        (self.source / 'Makefile.obj').write_text('OBJECTS =\n')
        (self.source / 'main.cc').touch()
        (self.util / 'release_ver').write_text('0.34.1-zh5-1-001\n')
        self.env = os.environ.copy()
        for key in ('GITHUB_REF_TYPE', 'GITHUB_REF_NAME', 'GITHUB_SHA',
                    'GIT_DESCRIBE_FLAGS', 'GIT_DIR', 'GIT_WORK_TREE'):
            self.env.pop(key, None)
        self.env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Version test')
        self.git('config', 'user.email', 'version@example.invalid')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.alpha_commit = self.git('rev-parse', 'HEAD').strip()
        self.remote = self.root / 'origin.git'
        self.run_cmd(['git', 'init', '-q', '--bare', str(self.remote)])
        self.git('remote', 'add', 'origin', str(self.remote))

    def run_cmd(self, args, *, cwd=None, env=None, ok=True):
        result = subprocess.run(args, cwd=cwd or self.repo,
                                env=env or self.env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ok:
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        else:
            self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
        return result

    def git(self, *args):
        return self.run_cmd(['git', *args]).stdout

    def tag(self, name, *, annotated=True):
        args = ['tag', '-a', name, '-m', name] if annotated else ['tag', name]
        self.git(*args)
        self.git('push', '-q', 'origin', f'refs/tags/{name}')

    def commit(self):
        self.git('commit', '--allow-empty', '-qm', 'development')
        return self.git('rev-parse', 'HEAD').strip()

    def alpha(self):
        self.tag('0.35-a0')
        return self.commit()

    def ensure(self, tag=None, *, commit=None, ok=True, fetch=False):
        env = self.env.copy()
        env['GITHUB_REF_TYPE'] = 'tag' if tag else 'branch'
        if tag:
            env.update(GITHUB_REF_NAME=tag,
                       GITHUB_SHA=commit or self.git('rev-parse', 'HEAD').strip())
        result = self.run_cmd(['bash', str(ENSURE),
                               *(['--fetch-upstream-tags'] if fetch else [])],
                              env=env, ok=ok)
        return result

    def generate(self, *, ok=True):
        self.run_cmd(['perl', 'util/gen_ver.pl', 'build.h'], cwd=self.source, ok=ok)
        return (self.source / 'build.h').read_text() if ok else ''

    def assert_version(self, expected):
        self.ensure()
        self.assertEqual(expected, (self.util / 'release_ver').read_text().strip())
        header = self.generate()
        self.assertIn('#define CRAWL_VERSION_RELEASE VER_ALPHA', header)
        self.assertIn(f'#define CRAWL_VERSION_LONG "{expected}"', header)
        short = expected.split('-g')[0].rsplit('-', 1)[0] if '-g' in expected else expected
        self.assertIn(f'#define CRAWL_VERSION_SHORT "{short}"', header)

    def test_alpha_development_and_interfering_stable_tags(self):
        commit = self.alpha()
        self.tag('0.34.1-zh5-1-010')
        self.tag('0.35.0')
        expected = self.git('describe', '--match', '*-a[0-9]*').strip()
        self.assertRegex(expected, r'^0\.35-a0-1-g[0-9a-f]+$')
        self.assertTrue(commit.startswith(expected.split('-g')[1]))
        self.assert_version(expected)

    def test_exact_trunk_tag_restores_annotated_identity(self):
        commit = self.alpha()
        tag = '0.35-trunk-001'
        self.tag(tag)
        self.git('update-ref', f'refs/tags/{tag}', commit)
        self.ensure(tag)
        self.assertEqual('tag', self.git('cat-file', '-t', tag).strip())
        self.assert_version(tag)

    def test_trunk_followup_in_detached_checkout_and_recursive_make(self):
        self.alpha()
        self.tag('0.35-trunk-001')
        commit = self.commit()
        self.git('checkout', '--detach', '-q', commit)
        expected = self.git('describe', '--match', '*-trunk-*').strip()
        self.assertRegex(expected, r'^0\.35-trunk-001-1-g[0-9a-f]+$')
        self.assert_version(expected)
        (self.source / 'build.h').unlink()
        # Actual Makefile -> gen_ver.pl, and a recursive make reading the same
        # Makefile. No compile recipes are invoked.
        (self.source / 'probe.mk').write_text(
            'probe: build.h\n\t@echo SRC=$(SRC_VERSION) TAG=$(RECENT_TAG)\n'
            'recursive:\n\t+$(MAKE) -f Makefile -f probe.mk -o main.cc probe\n')
        result = self.run_cmd(['make', '-j4', '-f', 'Makefile', '-f', 'probe.mk',
                               'recursive', 'NO_PKGCONFIG=y', 'OBJECTS='], cwd=self.source)
        self.assertIn(f'SRC={expected} TAG=0.35-trunk-001', result.stdout)
        self.assertIn(f'CRAWL_VERSION_LONG "{expected}"',
                      (self.source / 'build.h').read_text())

    def test_android_build_parameters_and_version_identity(self):
        self.alpha()
        self.tag('0.35-trunk-001')
        header = self.generate()
        template = self.source / 'android-project/app/build.gradle.in'
        template.parent.mkdir(parents=True)
        shutil.copy2(SOURCE / 'android-project/app/build.gradle.in', template)
        self.run_cmd(['make', '-j4', 'ANDROID=147', 'TILES=y', 'NPROC=4',
                      'ANDROID_APPLICATION_ID=org.develz.crawl.trunk',
                      'ANDROID_APP_NAME=Dungeon Crawl Stone Soup Trunk',
                      'android-project/app/build.gradle'], cwd=self.source)
        config = template.with_suffix('').read_text()
        self.assertIn('applicationId = "org.develz.crawl.trunk"', config)
        self.assertIn('crawlAppName: "Dungeon Crawl Stone Soup Trunk"', config)
        self.assertIn("arguments '-j4'", config)
        self.assertIn('versionName = "0.35-trunk-001"', config)
        self.assertIn('CRAWL_VERSION_LONG "0.35-trunk-001"', header)
        self.assertIn('compileSdk = 36', config)
        self.assertIn('targetSdkVersion 36', config)
        self.assertIn('sourceCompatibility JavaVersion.VERSION_21', config)

    def test_trunk_major_mismatch_is_rejected(self):
        self.alpha()
        self.tag('0.36-trunk-001')
        result = self.ensure('0.36-trunk-001', ok=False)
        self.assertIn('differs from upstream 0.35-a0', result.stderr)

    def test_missing_alpha_fails_without_release_ver_fallback(self):
        self.tag('0.35-trunk-001')
        self.ensure('0.35-trunk-001', ok=False)
        self.ensure(ok=False)
        self.generate(ok=False)
        self.assertEqual('0.34.1-zh5-1-001\n',
                         (self.util / 'release_ver').read_text())

    def test_tag_validation_remains_strict(self):
        self.alpha()
        self.tag('0.35-trunk-001', annotated=False)
        self.assertIn('must be annotated', self.ensure('0.35-trunk-001', ok=False).stderr)
        for tag in ('0.35-trunk-000', '0.35-trunk-1', '0.35-trunk-1000'):
            with self.subTest(tag=tag):
                self.ensure(tag, ok=False)
        self.ensure('0.35-trunk-001', commit='0' * 40, ok=False)

    def test_ci_upstream_fetch_is_fail_closed_and_uses_exact_refs(self):
        self.alpha()
        # Re-route only this temporary repo's upstream URL to its local origin.
        self.git('config', f'url.{self.remote}.insteadOf', 'https://github.com/crawl/crawl')
        self.git('tag', '-d', '0.35-a0')
        self.ensure(fetch=True)
        self.assertEqual('tag', self.git('cat-file', '-t', '0.35-a0').strip())
        self.git('push', '-q', 'origin', ':refs/tags/0.35-a0')
        self.assertIn('alpha tag list is empty', self.ensure(fetch=True, ok=False).stderr)
        self.git('config', '--unset', f'url.{self.remote}.insteadOf')
        self.git('config', f'url.{self.root / "missing"}.insteadOf', 'https://github.com/crawl/crawl')
        self.assertIn('failed to list upstream', self.ensure(fetch=True, ok=False).stderr)

    def test_source_bundle_without_git_preserves_trunk_version(self):
        bundle = self.root / 'bundle'
        bundle.mkdir()
        shutil.copy2(self.util / 'gen_ver.pl', bundle)
        for version in ('0.35-trunk-001', '0.35-trunk-001-12-gabcdef0'):
            with self.subTest(version=version):
                (bundle / 'release_ver').write_text(version + '\n')
                self.run_cmd(['perl', './gen_ver.pl', 'build.h'], cwd=bundle)
                header = (bundle / 'build.h').read_text()
                self.assertIn('CRAWL_VERSION_RELEASE VER_ALPHA', header)
                self.assertIn('CRAWL_VERSION_SHORT "0.35-trunk-001"', header)
                self.assertIn(f'CRAWL_VERSION_LONG "{version}"', header)


if __name__ == '__main__':
    unittest.main()
