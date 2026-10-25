#!/usr/bin/env python3
"""Coverage regressions for data-driven shop fields and species orc names."""

import contextlib
import io
from pathlib import Path
import re
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import audit_data_i18n as audit

ROOT = SCRIPTS.parents[1]
SOURCE = ROOT / 'crawl-ref/source'

SHOP_FIXTURE = '''
# kfeat("shop type:Comment suffix:Ignored")
-- kfeat("shop suffix:Lua_comment")
local shops = { "Tomes", "Deal" }
local shopsuffix = shops[ crawl.random2(#shops) + 1 ]
if first then
  kfeat("Z = general shop type:Range suffix:"
        .. shopsuffix .. " ; any")
else
  kfeat("Z = general shop " ..
        "type:Timeless suffix:Fine_Books ; any")
end
kfeat("S = general shop type:Store suffix: count:11")
weight_type:Internal
'''
EXPECTED_SHOPS = {('shop name type', value)
                  for value in ('Range', 'Timeless', 'Store')} | {
                      ('shop name suffix', value)
                      for value in ('Tomes', 'Deal', 'Fine Books')}


class DataDrivenCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name)
        self.pan = self.source / 'dat/des/branches/pan.des'
        self.pan.parent.mkdir(parents=True)
        self.pan.write_text(SHOP_FIXTURE, encoding='utf-8')
        self.translations = self.source / 'source.txt'
        self.write_translations(f'{context}|{key}' for context, key in EXPECTED_SHOPS)

    def write_translations(self, keys):
        self.translations.write_text(''.join(f'%%%%\n{key}\n译文\n' for key in keys),
                                     encoding='utf-8')

    def check_shop(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return audit.check_shop_fields(str(self.source), str(self.translations))

    def check_orc(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return audit.check_orc_names(str(self.source), str(self.translations))

    def species_fixture(self):
        # Real generated initializers preserve nested lists and #if legacy data;
        # no independently reconstructed interpretation of field positions.
        text = (SOURCE / 'species-data.h').read_text(encoding='utf-8')
        self.human = re.search(r'^\{\s+SP_HUMAN,\n.*?^\},', text, re.M | re.S).group()
        self.elf = re.search(r'^\{\s+SP_HIGH_ELF,\n.*?^\},', text, re.M | re.S).group()
        (self.source / 'species-def.h').write_text(
            (SOURCE / 'species-def.h').read_text(encoding='utf-8'), encoding='utf-8')
        self.data = self.source / 'species-data.h'
        self.data.write_text(self.human + '\n#if TAG_MAJOR_VERSION == 34\n'
                             + self.elf + '\n#endif\n', encoding='utf-8')
        self.write_translations(['Orc', 'High Orc'])

    def test_shop_membership_includes_continuations_pools_and_all_branches(self):
        self.assertEqual(audit.collect_shop_fields(str(self.source)), EXPECTED_SHOPS)
        self.assertEqual(self.check_shop(), 0)

    def test_generic_translation_cannot_cover_contextual_shop_word(self):
        for missing in [('shop name suffix', 'Deal'), ('shop name type', 'Range'),
                        ('shop name type', 'Timeless')]:
            with self.subTest(missing=missing):
                self.write_translations([f'{context}|{key}' for context, key
                                         in EXPECTED_SHOPS - {missing}] + [missing[1]])
                self.assertEqual(self.check_shop(), 1)

    def test_wrong_shop_context_does_not_cover(self):
        self.write_translations([f'{context}|{key}' for context, key
                                 in EXPECTED_SHOPS - {('shop name suffix', 'Deal')}]
                                + ['shop name type|Deal'])
        self.assertEqual(self.check_shop(), 1)

    def test_added_pool_value_needs_translation(self):
        self.pan.write_text(SHOP_FIXTURE.replace('"Tomes", "Deal"',
                                                '"Tomes", "Deal", "New shelf"'))
        self.assertEqual(self.check_shop(), 1)
        self.write_translations([f'{c}|{k}' for c, k in EXPECTED_SHOPS]
                                + ['shop name suffix|New shelf'])
        self.assertEqual(self.check_shop(), 0)

    def test_new_literal_branch_needs_translation(self):
        self.pan.write_text(SHOP_FIXTURE + '\nkfeat("shop suffix:New_Stock")\n')
        self.assertEqual(self.check_shop(), 1)

    def test_unknown_computed_variable_rejected(self):
        self.pan.write_text(SHOP_FIXTURE.replace('.. shopsuffix ..', '.. other_suffix ..'))
        self.assertEqual(self.check_shop(), 1)

    def test_nonliteral_pool_rejected(self):
        self.pan.write_text(SHOP_FIXTURE.replace('"Tomes", "Deal"', '"Tomes", make_suffix()'))
        self.assertEqual(self.check_shop(), 1)

    def test_computed_extension_of_literal_is_not_silently_ignored(self):
        for suffix in ['fragment', '"Stock"']:
            with self.subTest(suffix=suffix):
                self.pan.write_text(SHOP_FIXTURE
                                    + f'\nkfeat("shop suffix:New" .. {suffix})\n')
                self.assertEqual(self.check_shop(), 1)

    def test_extension_of_computed_value_rejected(self):
        self.pan.write_text(SHOP_FIXTURE.replace('.. shopsuffix .. " ; any"',
                                                '.. shopsuffix .. "Stock ; any"'))
        self.assertEqual(self.check_shop(), 1)

    def test_selector_expression_extension_rejected(self):
        for extension in [' .. "Stock"', '\n  .. "Stock"',
                          ' -- selector comment\n  .. "Stock"',
                          '\n  and "Stock"']:
            with self.subTest(extension=extension):
                self.pan.write_text(SHOP_FIXTURE.replace(
                    'local shopsuffix = shops[ crawl.random2(#shops) + 1 ]',
                    'local shopsuffix = shops[ crawl.random2(#shops) + 1 ]' + extension))
                self.assertEqual(self.check_shop(), 1)

    def test_selector_comment_or_statement_terminator_supported(self):
        for terminator in [' -- finite selector', ';', '; -- finite selector']:
            with self.subTest(terminator=terminator):
                self.pan.write_text(SHOP_FIXTURE.replace(
                    'local shopsuffix = shops[ crawl.random2(#shops) + 1 ]',
                    'local shopsuffix = shops[ crawl.random2(#shops) + 1 ]' + terminator))
                self.assertEqual(self.check_shop(), 0)

    def test_mutated_finite_pool_rejected(self):
        for mutation in ['shops[3] = "Other"', 'table.insert(shops, "Other")',
                         'shopsuffix = computed_suffix()']:
            with self.subTest(mutation=mutation):
                self.pan.write_text(SHOP_FIXTURE + '\n' + mutation + '\n')
                self.assertEqual(self.check_shop(), 1)

    def test_missing_dynamic_shop_source_rejected(self):
        self.pan.unlink()
        self.assertEqual(self.check_shop(), 1)

    def test_missing_translation_file_rejected(self):
        self.translations.unlink()
        self.assertEqual(self.check_shop(), 1)

    def test_orc_compatibility_and_fallback_covered(self):
        self.species_fixture()
        self.assertEqual(audit.collect_orc_names(str(self.source)), {'Orc', 'High Orc'})
        self.assertEqual(self.check_orc(), 0)

    def test_orc_missing_compatibility_name_rejected(self):
        self.species_fixture()
        self.write_translations(['Orc'])
        self.assertEqual(self.check_orc(), 1)

    def test_indented_orc_initializer_cannot_escape_coverage(self):
        self.species_fixture()
        self.data.write_text(self.human + '\n  '
                             + self.elf.replace('"High Orc"', '"Uncovered Orc"') + '\n')
        self.assertEqual(audit.collect_orc_names(str(self.source)),
                         {'Orc', 'Uncovered Orc'})
        self.assertEqual(self.check_orc(), 1)

    def test_unknown_orc_row_layout_rejected(self):
        self.species_fixture()
        # Inline layout is outside the supported generated grammar, but the
        # independent enum-headed initializer discovery must still see it.
        self.data.write_text(self.human + '\n' + ' '.join(self.elf.splitlines())
                             .replace('"High Orc"', '"Uncovered Orc"') + '\n')
        with self.assertRaises(ValueError):
            audit.collect_orc_names(str(self.source))
        self.assertEqual(self.check_orc(), 1)

    def test_duplicate_species_identity_rejected(self):
        self.species_fixture()
        self.data.write_text(self.data.read_text() + '\n' + self.human + '\n')
        self.assertEqual(self.check_orc(), 1)

    def test_orc_missing_fallback_rejected(self):
        self.species_fixture()
        self.write_translations(['High Orc'])
        self.assertEqual(self.check_orc(), 1)

    def test_orc_schema_tail_change_rejected(self):
        self.species_fixture()
        schema = self.source / 'species-def.h'
        schema.write_text(schema.read_text().replace('const char* orc_name;',
                                                     'const char* renamed_name;'))
        self.assertEqual(self.check_orc(), 1)

    def test_orc_initializer_missing_tail_field_rejected(self):
        self.species_fixture()
        self.data.write_text(self.data.read_text().replace('    "High Orc",\n', ''))
        self.assertEqual(self.check_orc(), 1)

    def test_orc_unrecognised_initializer_rejected(self):
        self.species_fixture()
        self.data.write_text(self.data.read_text().replace('"High Orc",', 'make_name(),'))
        self.assertEqual(self.check_orc(), 1)

    def test_orc_missing_source_file_rejected(self):
        self.species_fixture()
        self.data.unlink()
        self.assertEqual(self.check_orc(), 1)


if __name__ == '__main__':
    unittest.main()
