#!/usr/bin/env python3
"""Coverage regressions for data-driven shop fields and species orc names."""

import contextlib
import io
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

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
        text = audit._generate_species_data(str(SOURCE))
        self.human = re.search(r'^\{\s+SP_HUMAN,\n.*?^\},', text, re.M | re.S).group()
        self.elf = re.search(r'^\{\s+SP_HIGH_ELF,\n.*?^\},', text, re.M | re.S).group()
        (self.source / 'species-def.h').write_text(
            (SOURCE / 'species-def.h').read_text(encoding='utf-8'), encoding='utf-8')
        self.data = self.source / 'species-data.h'
        self.data.write_text(self.human + '\n#if TAG_MAJOR_VERSION == 34\n'
                             + self.elf + '\n#endif\n', encoding='utf-8')
        # Only replace the generation boundary for malformed-output mutations;
        # schema validation and initializer parsing still use production code.
        generation = mock.patch.object(audit, '_generate_species_data',
            side_effect=lambda _source: self.data.read_text(encoding='utf-8'))
        generation.start()
        self.addCleanup(generation.stop)
        self.write_translations(['Orc', 'High Orc'])

    def clean_species_source(self):
        source = self.source / 'clean-source'
        (source / 'util').mkdir(parents=True)
        for name in ('species-gen.py', 'genutil.py'):
            shutil.copy2(SOURCE / 'util' / name, source / 'util' / name)
        shutil.copytree(SOURCE / 'util/species-gen', source / 'util/species-gen')
        shutil.copytree(SOURCE / 'dat/species', source / 'dat/species')
        shutil.copy2(SOURCE / 'species-def.h', source / 'species-def.h')
        return source

    def test_orc_clean_checkout_uses_production_generator(self):
        source = self.clean_species_source()
        self.assertFalse((source / 'species-data.h').exists())
        names = audit.collect_orc_names(str(source))
        self.assertEqual(len(names), 47)
        self.assertTrue({'Orc', 'High Orc'} <= names)
        self.assertFalse((source / 'species-data.h').exists())
        # A stale build product must neither mask missing source nor set names.
        (source / 'species-data.h').write_text('invalid stale header')
        self.assertEqual(audit.collect_orc_names(str(source)), names)

    def test_orc_generator_failure_rejected(self):
        source = self.clean_species_source()
        (source / 'dat/species/broken.yaml').write_text('name: [unterminated')
        (source / 'species-data.h').write_text('stale generated data')
        with self.assertRaisesRegex(ValueError, 'Species generation failed'):
            audit.collect_orc_names(str(source))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit.check_orc_names(str(source), str(self.translations)), 1)

    def test_orc_missing_generator_input_rejected(self):
        source = self.clean_species_source()
        shutil.rmtree(source / 'dat/species')
        with self.assertRaisesRegex(ValueError, 'Species generation failed'):
            audit.collect_orc_names(str(source))

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
                         'shopsuffix = computed_suffix()',
                         'shopsuffix, ignored = "Uncovered_Suffix", nil',
                         'ignored, shopsuffix = nil, "Uncovered_Suffix"',
                         'first, shopsuffix, last = nil, "Uncovered_Suffix", nil',
                         'shops, ignored = { "Other" }, nil',
                         'ignored, shops = nil, { "Other" }',
                         'first, shops, last = nil, { "Other" }, nil',
                         'shopsuffix,\n ignored = "Other", nil',
                         'ignored, -- continued target list\n shopsuffix = nil, "Other"',
                         'first,\n shops,\n last = nil, { "Other" }, nil',
                         'local shopsuffix, ignored = "Other", nil',
                         'shopsuffix, target[1] = "Other", nil',
                         'target[1], shopsuffix, target.last = nil, "Other", nil',
                         'target.first, shops = nil, { "Other" }',
                         'shops, target[other[index]] = { "Other" }, nil',
                         'shopsuffix, get_target().value = "Uncovered_Suffix", nil',
                         'shops, get_target()[1] = { "Other" }, nil',
                         'shopsuffix, (get_target()).value = "Other", nil',
                         'shopsuffix, get_target():choose()[1] = "Other", nil',
                         'consume(function() shopsuffix, get_target().value = "Other", nil end)',
                         'local note = { callback = function() shopsuffix, other = "Other", nil end }',
                         'local note = { callback = function() if first then other, shops = nil, {} end end }',
                         'shopsuffix, (function() return {} end)().value = "Other", nil']:
            with self.subTest(mutation=mutation):
                self.pan.write_text(SHOP_FIXTURE.replace(
                    'if first then', mutation + '\nif first then'))
                self.assertEqual(self.check_shop(), 1)

    def test_unrelated_multiple_assignment_and_quoted_targets_supported(self):
        self.pan.write_text(SHOP_FIXTURE + '''
local first, last = shopsuffix, shops
first, -- unrelated targets
 last = last, first
first, target[shopsuffix] = shopsuffix, shops
first, target[other[index]] = shopsuffix, shops
get_target(shopsuffix).value, last = shopsuffix, shops
get_target(shops):choose()[1], last = shopsuffix, shops
-- shopsuffix, ignored = "Not a write", nil
--[[
 shops, ignored = {}, nil
]]
--[=[ shopsuffix,
 ignored = "not a write", nil ]=]
local note = "shopsuffix, ignored = not an assignment"
local other_note = 'shops, ignored = also not an assignment'
local note = {shopsuffix, other = nil}
local note = {shops, other = nil}
local note = {nested = {shopsuffix, other = nil}, shops, other = nil}
local note = { callback = function() end, shopsuffix, other = nil }
local note = { callback = function() if first then return shops end end,
               shops, other = nil }
local note = { callback = function() return {shopsuffix, other = nil} end }
''')
        self.assertEqual(audit.collect_shop_fields(str(self.source)), EXPECTED_SHOPS)
        self.assertEqual(self.check_shop(), 0)

    def test_des_lua_block_targets_ignore_map_quote_glyphs(self):
        for mutation, expected in [('', 0),
                                   ('shopsuffix, get_target().value = "Other", nil', 1)]:
            with self.subTest(mutation=mutation):
                body = SHOP_FIXTURE.replace('if first then', mutation + '\nif first then')
                self.pan.write_text("MAP\n.'...\nENDMAP\n{{\n" + body + "\n}}\n")
                self.assertEqual(self.check_shop(), expected)

    def test_des_mixed_block_and_main_lines_keep_all_assignment_targets(self):
        for lua_line, expected in [
                ('local note = {shopsuffix, other = nil}', 0),
                ('local first, last = shopsuffix, shops', 0),
                ('shopsuffix, ignored = "Uncovered_Suffix", nil', 1),
                ('shops, get_target()[1] = {"Other"}, nil', 1)]:
            with self.subTest(lua_line=lua_line):
                self.pan.write_text(
                    'MAP\n: shopsuffix, ignored = "Map glyphs", nil\nENDMAP\n'
                    '{{\n' + SHOP_FIXTURE + '\n}}\n: ' + lua_line + '\n'
                    ': kfeat("shop suffix:" .. shopsuffix .. " ; any")\n'
                    '{{\nlocal final_note = "second block"\n}}\n')
                self.assertEqual(self.check_shop(), expected)

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
