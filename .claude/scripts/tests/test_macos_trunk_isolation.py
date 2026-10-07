#!/usr/bin/env python3
"""Linux checks for the production macOS save branches and bundle recipes."""

from __future__ import annotations

import json
import os
import plistlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'crawl-ref/source'
MAC = SOURCE / 'mac'
STABLE_APP = 'Dungeon Crawl Stone Soup'
TRUNK_APP = STABLE_APP + ' Trunk'


class MacosIsolationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='macos-isolation-', dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def command(self, args, **kwargs):
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kwargs)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout

    def test_save_defaults_override_and_runtime_tilde_resolution(self):
        compiler = shutil.which('c++')
        self.assertIsNotNone(compiler, 'C++ compiler required for save-path checks')
        init = (SOURCE / 'initfile.cc').read_text()
        files = (SOURCE / 'files.cc').read_text()
        catpath = files[files.index('string catpath('):files.index('// Given a relative path')]
        helpers = init[init.index('static string _user_home_dir()'):
                       init.index('\n#endif\n\nstatic string _get_save_path')]
        check_string = init[init.index('static string check_string('):
                            init.index('\nvoid get_system_environment()')]
        environment = init[init.index('void get_system_environment()'):
                           init.index('#ifdef __ANDROID__',
                                      init.index('void get_system_environment()'))] + '}\n'
        # Compile the actual production functions/conditionals, using only the
        # small environment structure and charset stub needed by this slice.
        (self.work / 'paths.cc').write_text(
            '#include <string>\n#include <cstdlib>\n#include <iostream>\n'
            'using std::string;\n#define FILE_SEPARATOR \'/\'\n'
            '#define CRAWL "Dungeon Crawl Stone Soup"\n'
            'struct { string crawl_name, crawl_dir; } SysEnv;\n'
            'string mb_to_utf8(const char *s) { return s; }\n'
            + catpath + helpers + check_string + environment
            + 'int main() { get_system_environment();\n'
              'std::cout << _resolve_dir(SysEnv.crawl_dir, "saves/"); }\n')
        (self.work / 'Makefile').write_text(
            'all: default-mac trunk-mac trunk-linux\n'
            'default-mac: paths.cc\n'
            '\t$(CXX) -std=c++17 -DTARGET_OS_MACOSX $< -o $@\n'
            'trunk-mac: paths.cc\n'
            '\t$(CXX) -std=c++17 -DTARGET_OS_MACOSX '
            '-DSAVE_DIR_PATH=\\\"~/.crawl-trunk\\\" $< -o $@\n'
            'trunk-linux: paths.cc\n'
            '\t$(CXX) -std=c++17 -DSAVE_DIR_PATH=\\\"~/.crawl-trunk\\\" $< -o $@\n')
        self.command(['make', '-j4', f'CXX={compiler}'], cwd=self.work)
        env = os.environ.copy()
        env.pop('CRAWL_DIR', None)
        user_home = env['HOME']
        for binary, expected in (
            ('default-mac', f'{user_home}/Library/Application Support/{STABLE_APP}/saves/'),
            ('trunk-mac', f'{user_home}/.crawl-trunk/saves/'),
            ('trunk-linux', f'{user_home}/.crawl-trunk/saves/'),
        ):
            with self.subTest(binary=binary):
                self.assertEqual(expected, self.command([str(self.work / binary)], env=env))
        env['CRAWL_DIR'] = str(self.work / 'explicit-user-path')
        for binary in ('default-mac', 'trunk-mac'):
            with self.subTest(binary=binary, override=True):
                self.assertEqual(env['CRAWL_DIR'] + '/saves/',
                                 self.command([str(self.work / binary)], env=env))

    def test_bundle_dry_run_and_generated_plist(self):
        probe = self.work / 'probe.mk'
        # The actual Makefile derives Tiles from MAKECMDGOALS. This empty goal
        # selects that branch while executing only the plist recipe on Linux.
        probe.write_text('.PHONY: identity-tiles\nidentity-tiles:\n')
        for label, app, identifier, extra in (
            ('stable', STABLE_APP, 'net.sourceforge.crawl-ref', []),
            ('trunk', TRUNK_APP, 'net.sourceforge.crawl-ref.trunk',
             [f'APP_NAME={TRUNK_APP}', 'BUNDLE_IDENTIFIER=net.sourceforge.crawl-ref.trunk']),
        ):
            with self.subTest(label=label):
                staging = self.work / label
                bundle = staging / f'{app} - Tiles.app'
                (bundle / 'Contents').mkdir(parents=True)
                args = ['make', '-j4', '-f', 'Makefile.app-bundle',
                        f'STAGING_DIR={staging}', 'SRC_VERSION=0.35-trunk-001', *extra]
                output = self.command([*args, '-n', 'tiles-dmg'], cwd=MAC)
                self.assertIn(f'{app} - Tiles.app', output)  # codesign quoted path
                self.assertIn(f'{app} Tiles', output)  # DMG volume name
                self.assertIn(f'{app.replace(" ", chr(92) + " ")}\\ -\\ Tiles', output)
                self.assertIn(identifier, output)
                self.command([*args, '-f', str(probe), 'copy-info-plist', 'identity-tiles'], cwd=MAC)
                plist = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())
                self.assertEqual(app, plist['CFBundleDisplayName'])
                self.assertEqual(identifier, plist['CFBundleIdentifier'])
                self.assertEqual(f'{app} - Tiles', plist['CFBundleExecutable'])
                self.assertEqual('0.35-trunk-001', plist['CFBundleVersion'])

    def test_ci_build_parameters_preserve_stable_tag_defaults(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text())
        steps = workflow['jobs']['build_macos_tiles']['steps']
        command = next(step['run'] for step in steps if step.get('name') == 'Build macOS tiles app')
        fake_bin = self.work / 'bin'
        fake_bin.mkdir()
        fake_make = fake_bin / 'make'
        fake_make.write_text(
            '#!/usr/bin/env python3\nimport json, os, sys\n'
            'open(os.environ["MAC_ARGS_OUTPUT"], "w").write(json.dumps(sys.argv[1:]))\n')
        fake_make.chmod(0o755)
        for ref, trunk in (
            ('refs/tags/0.34.1-zh5-1-001', False),
            ('refs/tags/0.35-trunk-001', True),
            ('refs/heads/chn-trunk', True),
        ):
            with self.subTest(ref=ref):
                env = dict(os.environ, GITHUB_REF=ref,
                           PATH=str(fake_bin) + os.pathsep + os.environ['PATH'],
                           MAC_ARGS_OUTPUT=str(self.work / 'args.json'))
                self.command(['bash', '-c', command], env=env)
                args = json.loads((self.work / 'args.json').read_text())
                for argument in ('SAVEDIR=~/.crawl-trunk', f'APP_NAME={TRUNK_APP}',
                                 'BUNDLE_IDENTIFIER=net.sourceforge.crawl-ref.trunk'):
                    self.assertEqual(trunk, argument in args)
                self.assertIn('-j4', args)


if __name__ == '__main__':
    unittest.main()
