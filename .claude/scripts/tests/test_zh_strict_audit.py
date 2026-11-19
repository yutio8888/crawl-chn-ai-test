import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


AUDIT = Path(__file__).resolve().parents[1] / 'zh_strict_audit.py'


class StrictAuditTest(unittest.TestCase):
    def test_key_names_need_a_shortcut_context(self):
        sys.path.insert(0, str(AUDIT.parent))
        self.addCleanup(sys.path.remove, str(AUDIT.parent))
        from zh_strict_audit import strict_mixed_cn_en

        examples = {
            '你必须 escape。': ['escape'],
            '回到 home。': ['home'],
            '到了 end。': ['end'],
            'home - 家的意思。': ['home'],
            '正文 tab、del、backspace。': ['tab', 'del', 'backspace'],
            '<w>go home</w> 和 <input>the end</input>': ['home', 'the', 'end'],
            '[ctrl-p] 日志': [],
            '<w>Home</w>：本页': [],
            '<input>Shift+Tab</input> 切换': [],
            '按 ESC 或 Ctrl+Shift-X，ESC退出': [],
            'Bksp - 返回，切换 NumLock': [],
            '[Tab] 后的 tab 仍要检查': ['tab'],
        }
        for value, expected in examples.items():
            with self.subTest(value=value):
                self.assertEqual(strict_mixed_cn_en(value, actionable_only=True),
                                 expected)

    def test_actionable_cli_preserves_candidates_and_default_report(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.txt'
            descriptions = root / 'descript'
            descriptions.mkdir()
            source.write_text(
                '%%%%\nkeys\n按 Esc/Tab/Ctrl/Shift/Del/Home/End/pgup/pgdn/NumLock\n'
                '%%%%\nconfig\n设置 CMD_SAVE_GAME auto_pickup .crawlrc init.txt morgue\n'
                '%%%%\nmouse\n按<input>Shift-right-click</input>或<input>Return</input>继续\n'
                '%%%%\nleak\n按 Tab 查看 <input>broken shortcut</input>，'
                'rFire∞/rCold∞/rElec∞ 或 rElec\n', encoding='utf-8')
            (descriptions / 'quotes.txt').write_text(
                '%%%%\ncredit\n「引文。」\n    -Jane Doe, _Wrapped\nBook_.\n'
                '   trans. John Smith.\n'
                '%%%%\nbody\n「引文。」\n    ——Jane Doe\n\n「残余 English。」\n'
                '%%%%\nenglish body\nUntranslated line\n    -中文作者\n',
                encoding='utf-8')
            command = [sys.executable, str(AUDIT), '--source-txt', str(source),
                       '--descript-dir', str(descriptions), '--json']

            def report(*options):
                output = subprocess.check_output(command + list(options), text=True)
                return {row['key']: row['english']
                        for row in json.loads(output)['candidates']}

            default = report()
            self.assertIn('Esc', default['keys'])
            self.assertIn('CMD', default['config'])
            self.assertIn('click', default['mouse'])
            self.assertIn('Smith', default['credit'])
            self.assertNotIn('rElec', default['leak'])
            self.assertEqual(report('--actionable-only'), {
                'leak': ['broken', 'rCold', 'rElec', 'rFire', 'shortcut'],
                'body': ['English'],
                'english body': ['Untranslated', 'line'],
            })


if __name__ == '__main__':
    unittest.main()
