#!/usr/bin/env python3
"""
audit_data_i18n.py — Check data-driven translation coverage.

Scans runtime-translated data sources that i18n_extract.py misses because
the T_() call uses a variable (not a string literal):

1. Monster names from dat/mons/*.yaml (translated via T_(en.c_str()) at runtime)
2. Duration strings from duration-data.h (translated via T_(endmsg) at runtime)
3. Feature names from feature-data.h (translated via T_(get_feature_def().name))
4. Custom shop type/suffix fields (exact C_() contexts, including finite Lua pools)
5. Species orc names (including compatibility entries and the Orc fallback)
"""

import re
import os
import sys
from pathlib import Path
import json

# Use shared parser for consistency with scan_i18n.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import parse_source_txt
from i18n_extract import _lua_tokens



def check_monster_names(source_dir: str, source_txt: str):
    """Check monster YAML names against source.txt + zh_monster_name() map."""
    mons_dir = os.path.join(source_dir, 'dat/mons')
    if not os.path.isdir(mons_dir):
        print("ERROR: Monster directory not found:", mons_dir)
        return 1

    yaml_names = set()
    for fn in os.listdir(mons_dir):
        if fn.endswith('.yaml'):
            fpath = os.path.join(mons_dir, fn)
            with open(fpath, 'r') as f:
                content = f.read()
            m = re.search(r'name:\s*"(.+)"', content)
            if m:
                yaml_names.add(m.group(1))

    # Parse source.txt
    src_entries = parse_source_txt(source_txt)

    # Parse zh_monster_name() static map from mon-util.cc
    mon_util_cc = os.path.join(source_dir, 'mon-util.cc')
    zh_map = {}
    if os.path.exists(mon_util_cc):
        with open(mon_util_cc, 'r') as f:
            mon_util = f.read()
        for m in re.finditer(r'\{\s*"([^"]+)",\s*"([^"]+)"\s*\}', mon_util):
            zh_map[m.group(1)] = m.group(2)

    covered = set()
    covered_by_src = set()
    covered_by_zh = set()
    missing = []

    for name in yaml_names:
        found = False
        if name.lower() in src_entries:
            covered_by_src.add(name)
            found = True
        if name in zh_map:
            covered_by_zh.add(name)
            found = True
        if found:
            covered.add(name)
        else:
            missing.append(name)

    print(f"\n--- Monster name translation coverage ---")
    print(f"Total monster YAML names: {len(yaml_names)}")
    print(f"  Covered (source.txt): {len(covered_by_src)}")
    print(f"  Covered (zh_map only): {len(covered_by_zh - covered_by_src)}")
    print(f"  Covered total: {len(covered)} ({100*len(covered)//len(yaml_names)}%)")
    print(f"  MISSING (no translation): {len(missing)}")
    if missing:
        print("  Missing entries:")
        for m in missing[:15]:
            print(f"    - {m}")
        if len(missing) > 15:
            print(f"    ... and {len(missing) - 15} more")

    return 0 if not missing else 1


def check_duration_strings(source_dir: str, source_txt: str):
    """Check duration-data.h string literals against source.txt."""
    dur_h = os.path.join(source_dir, 'duration-data.h')
    if not os.path.exists(dur_h):
        print("ERROR: duration-data.h not found:", dur_h)
        return 1

    with open(dur_h, 'r') as f:
        content = f.read()

    # Strip C++ comment lines to avoid matching example text in /// comments
    content = re.sub(r'^[ \t]*//.*$', '', content, flags=re.MULTILINE)
    # Also strip /* */ block comments that span lines
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    # Extract sentence-like strings (capital letter start, punctuation end)
    sentences = set(re.findall(r'"([A-Z][^"]{3,}?[.!?])"', content))

    src_entries = parse_source_txt(source_txt)
    missing = sorted(s for s in sentences if s.lower() not in src_entries)

    print(f"\n--- Duration string translation coverage ---")
    print(f"Total duration sentence strings: {len(sentences)}")
    print(f"  Covered (source.txt): {len(sentences) - len(missing)}")
    print(f"  MISSING: {len(missing)}")
    if missing:
        print("  Missing entries:")
        for m in missing[:10]:
            print(f"    - {m}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")

    return 0 if not missing else 1


def check_feature_names(source_dir: str, source_txt: str):
    """Check feature-data.h feature descriptions against source.txt."""
    feat_h = os.path.join(source_dir, 'feature-data.h')
    if not os.path.exists(feat_h):
        return 1

    with open(feat_h, 'r') as f:
        content = f.read()

    # Extract feature name strings
    feat_names = set(re.findall(r'"([a-z][^"]{3,}?[^"]*)"', content))
    # Filter out non-descriptive strings (short codes, internal)
    feat_names = {f for f in feat_names if ' ' in f and len(f) > 10}

    src_entries = parse_source_txt(source_txt)
    missing = sorted(f for f in feat_names if f.lower() not in src_entries)

    print(f"\n--- Feature name translation coverage ---")
    print(f"Total feature description strings: {len(feat_names)}")
    print(f"  Covered (source.txt): {len(feat_names) - len(missing)}")
    print(f"  MISSING: {len(missing)}")
    if missing:
        for m in missing[:10]:
            print(f"    - {m}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")

    return 0 if not missing else 1


def check_cloud_names(source_dir: str, source_txt: str):
    """Check cloud.cc static array terse/verbose names against source.txt."""
    cloud_cc = os.path.join(source_dir, 'cloud.cc')
    if not os.path.exists(cloud_cc):
        return 1

    with open(cloud_cc, 'r') as f:
        content = f.read()

    # Extract terse + verbose names from cloud_data array
    # Pattern: { "terse", "verbose", // comment
    names = set()
    for m in re.finditer(r'\{\s*"([^"]+)",\s*(?:"([^"]+)"|nullptr)', content):
        terse = m.group(1)
        verbose = m.group(2)
        names.add(terse)
        if verbose:
            names.add(verbose)

    src_entries = parse_source_txt(source_txt)
    missing = sorted(n for n in names if n.lower() not in src_entries
                     and n not in ('?', 'ink'))  # skip debug/empty entries

    print(f"\n--- Cloud name translation coverage ---")
    print(f"Total cloud terse+verbose names: {len(names)}")
    print(f"  Covered (source.txt): {len(names) - len(missing)}")
    print(f"  MISSING: {len(missing)}")
    if missing:
        for m in missing[:10]:
            print(f"    - {m}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")

    return 0 if not missing else 1


def check_corrosion_sources(source_dir: str, source_txt: str):
    """Check corrosion source strings against source.txt."""
    src_entries = parse_source_txt(source_txt)
    sources = set()
    missing = []

    # Scan for you.corrode(..., "SOURCE", ...) and act->corrode(..., "SOURCE", ...)
    for fn in ['beam.cc', 'cloud.cc', 'ouch.cc', 'traps.cc', 'god-wrath.cc']:
        fpath = os.path.join(source_dir, fn)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r') as f:
            content = f.read()
        for m in re.finditer(r'corrode\([^,)]*,\s*"([^"]+)"', content):
            sources.add(m.group(1))

    for s in sorted(sources):
        if s.lower() not in src_entries:
            missing.append(s)

    print(f"\n--- Corrosion source coverage ---")
    print(f"Total corrosion sources: {len(sources)}")
    print(f"  Covered: {len(sources) - len(missing)}")
    print(f"  MISSING: {len(missing)}")
    if missing:
        for m in missing:
            print(f"    - \"{m}\"")

    return 0 if not missing else 1



def _lua_multi_assignment_targets(text):
    """Find target owners, excluding table fields but retaining callback writes."""
    # The finite pool lives in a .des Lua block; map glyphs outside those
    # blocks are not Lua quotes. Standalone Lua is also used by the fixtures.
    lua_blocks = re.findall(
        r'(?ms)^[ \t]*(?:[A-Za-z_]\w*)?\{\{[ \t]*\n(.*?)^[ \t]*\}\}[ \t]*$',
        text)
    if lua_blocks:
        text = '\n'.join(lua_blocks)
    text = re.sub(r'(?m)^[ \t]*\#[^\n]*', '', text)
    tokens = list(_lua_tokens(text))
    delimiters, tables, blocks = [], [], []
    pairs, targets = {}, set()

    def target_start(index):
        # Walk just a Lua target's prefix chain backwards. Balanced index/call
        # arguments are opaque: reads inside them are not assignment targets.
        while index >= 0:
            kind = tokens[index][0]
            if kind in (']', ')', '}'):
                opening = pairs.get(index)
                if opening is None:
                    return None
                index = opening - 1
                if (tokens[opening][0] == '('
                        and (index < 0 or tokens[index][0] not in
                             ('IDENT', 'STRING', ')', ']', '}'))):
                    return opening  # parenthesized prefix, not a bare owner
            elif kind == 'STRING':  # Lua also allows f"argument".field
                index -= 1
            elif kind == 'IDENT':
                if index > 0 and tokens[index - 1][0] in ('.', ':'):
                    index -= 2
                else:
                    return index
            else:
                return None
        return None

    for index, (kind, value, _offset) in enumerate(tokens):
        if kind in ('(', '[', '{'):
            delimiters.append(index)
            if kind == '{':
                tables.append(index)
        elif kind in (')', ']', '}'):
            if delimiters and tokens[delimiters[-1]][0] == {')': '(', ']': '[', '}': '{'}[kind]:
                pairs[index] = delimiters.pop()
            if kind == '}' and tables:
                tables.pop()
        elif kind == 'IDENT':
            if value in ('function', 'if', 'do', 'repeat'):
                blocks.append((value, index))
            elif value in ('end', 'until') and blocks:
                blocks.pop()
        elif kind == '=':
            if ((index > 0 and tokens[index - 1][0] in ('=', '<', '>', '~'))
                    or (index + 1 < len(tokens) and tokens[index + 1][0] == '=')):
                continue  # comparison, not an assignment
            if tables and not any(block == 'function' and start > tables[-1]
                                  for block, start in blocks):
                continue  # constructor field; a callback body is a statement scope
            owners, count, cursor = set(), 0, index - 1
            while cursor >= 0:
                start = target_start(cursor)
                if start is None:
                    break
                count += 1
                if tokens[start][0] == 'IDENT':
                    owners.add(tokens[start][1])
                cursor = start - 1
                if cursor < 0 or tokens[cursor][0] != ',':
                    break
                cursor -= 1
            if count > 1:
                targets.update(owners)
    return targets


def collect_shop_fields(source_dir: str):
    """Return (context, key) identities from the current .des tag grammar.

    Literal fields can occur in Lua continuation/conditional strings, so scan
    all non-comment lines, not just lines containing ``shop``. The only
    supported computed fields are finite local string arrays selected by the
    standard crawl.random2(#array) idiom. Other computations fail closed.
    Empty fields explicitly mean no custom word and need no translation.
    """
    des_dir = Path(source_dir) / 'dat/des'
    # pan.des contains the computed pool; its absence must not shrink coverage.
    if not des_dir.is_dir() or not (des_dir / 'branches/pan.des').is_file():
        raise ValueError('Required shop source dat/des/branches/pan.des is missing')
    paths = sorted(des_dir.rglob('*.des'))
    identities = set()
    tag = re.compile(r'(?<![\w_])(type|suffix):')
    for path in paths:
        raw_text = path.read_text(encoding='utf-8')
        text = '\n'.join('' if line.lstrip().startswith(('#', '--')) else line
                         for line in raw_text.splitlines())
        multi_targets = None
        for match in tag.finditer(text):
            context = 'shop name ' + match.group(1)
            tail = text[match.end():]
            literal = re.match(r'([^\s"\\]+)', tail)
            if literal:
                continuation = tail[literal.end():]
                if re.match(r'"\s*\.\.\s*(?:"[^\s;"]|[^"\s])', continuation):
                    raise ValueError(f'{path}: computed extension of literal shop field')
                identities.add((context, literal.group(1).replace('_', ' ')))
                continue
            # A closing quote followed by concatenation is a computed value;
            # do not confuse it with the deliberately empty ``suffix: ``.
            computed = re.match(r'"\s*\.\.\s*([A-Za-z_]\w*)', tail)
            if tail.startswith('"') and re.match(r'"\s*\.\.', tail):
                if not computed:
                    raise ValueError(f'{path}: unsupported computed shop field')
                variable = computed.group(1)
                if not re.match(r'\s*(?:\.\.\s*"[\s;]|[),])',
                                tail[computed.end():]):
                    raise ValueError(f'{path}: unsupported extension of computed shop field')
                assignments = list(re.finditer(
                    r'local\s+' + re.escape(variable) + r'\s*=\s*'
                    r'(\w+)\s*\[\s*crawl\.random2\(\s*#\s*\1\s*\)'
                    r'\s*\+\s*1\s*\]'
                    r'(?=[ \t]*(?:;[ \t]*)?(?:--[^\n]*)?(?:\n|$))', text))
                if len(assignments) != 1:
                    raise ValueError(f'{path}: unsupported shop field variable {variable}')
                selector = assignments[0]
                # Lua permits concatenation on the following line too. A
                # selector is only supported as a complete finite-pool lookup.
                after_selector = text[selector.end():]
                if re.match(r'[ \t]*(?:--[^\n]*)?\n'
                            r'(?:\s*--[^\n]*\n)*\s*'
                            r'(?:\.\.|[+*/%^<>=~-]|\b(?:and|or)\b)',
                            after_selector):
                    raise ValueError(f'{path}: extended shop field selector')
                pool = selector.group(1)
                if multi_targets is None:
                    multi_targets = _lua_multi_assignment_targets(raw_text)
                if (variable in multi_targets or pool in multi_targets
                        or len(re.findall(r'\b' + re.escape(variable) + r'\s*=', text)) != 1
                        or len(re.findall(r'\b' + re.escape(pool) + r'\s*=', text)) != 1
                        or re.search(r'\b' + re.escape(pool) + r'\s*\[[^\n]*\]\s*=', text)
                        or re.search(r'table\.(?:insert|remove)\s*\(\s*'
                                     + re.escape(pool) + r'\b', text)):
                    raise ValueError(f'{path}: mutated shop field pool or selector')
                arrays = re.findall(r'local\s+' + re.escape(pool)
                                    + r'\s*=\s*\{([^{}]*)\}', text, re.S)
                if len(arrays) != 1:
                    raise ValueError(f'{path}: missing/ambiguous shop field pool {pool}')
                values = re.findall(r'"([^"\\]*)"', arrays[0])
                residue = re.sub(r'"[^"\\]*"', '', arrays[0])
                if not values or residue.strip(' \t\r\n,'):
                    raise ValueError(f'{path}: nonliteral shop field pool {pool}')
                identities.update((context, value.replace('_', ' '))
                                  for value in values if value)
            elif tail.startswith('"'):
                # Empty field ending at a Lua string boundary is supported.
                continue
            elif not tail or tail[0].isspace():
                continue
            else:
                raise ValueError(f'{path}: unsupported shop field')
    if not identities:
        raise ValueError('No custom shop fields found')
    return identities


def collect_orc_names(source_dir: str):
    """Parse all generated species entries, including inactive compatibility.

    Validate the schema's five final pointer fields and each initializer tail
    together. This deliberately rejects an unfamiliar layout instead of silently
    reading the wrong field as an orc name.
    """
    root = Path(source_dir)
    schema = (root / 'species-def.h').read_text(encoding='utf-8')
    schema = re.sub(r'//[^\n]*|/\*.*?\*/', '', schema, flags=re.S)
    if not re.search(
            r'const char\* walking_verb;\s*const char\* altar_action;\s*'
            r'const char\* child_name;\s*const char\* orc_name;\s*'
            r'const char\* orcification_msg;\s*};', schema):
        raise ValueError('species_def final fields no longer match the orc-name schema')
    data = (root / 'species-data.h').read_text(encoding='utf-8')
    data = re.sub(r'//[^\n]*', '', data)
    # Enumerate every enum-headed initializer independently of accepted row
    # formatting. An indented/new-layout row must not disappear from both the
    # parser and its coverage comparison. Bind identities AND opening offsets.
    starts = [(match.group(1), match.start()) for match in
              re.finditer(r'\{\s*(SP_\w+)\s*,', data)]
    rows = list(re.finditer(r'^[ \t]*(\{)[ \t]*(SP_\w+),[^\n]*\n'
                            r'(.*?)^[ \t]*\},?', data, re.M | re.S))
    parsed_starts = [(row.group(2), row.start(1)) for row in rows]
    if (not rows or parsed_starts != starts
            or len({identity for identity, _ in starts}) != len(starts)):
        raise ValueError('Malformed, duplicate, or unsupported species initializers')
    names = {'Orc'}  # species::orc_name() uses this for nullptr.
    scalar = r'(nullptr|"(?:\\.|[^"\\])*")'
    tail = re.compile(r'\n    \{[^\n]*\},\n'
                      + ''.join('    ' + scalar + r',\n' for _ in range(5)) + r'\Z')
    for row in rows:
        if row.group(2) == 'SP_UNKNOWN':
            # The non-playable sentinel omits all remaining aggregate fields.
            if not re.search(r'\n    \{\},[ \t]*\n    nullptr,[ \t]*\n'
                             r'    nullptr,[ \t]*\n\Z', row.group(3)):
                raise ValueError('Unsupported SP_UNKNOWN initializer tail')
            continue
        fields = tail.search(row.group(3))
        if not fields:
            raise ValueError(f'{row.group(2)}: unsupported species initializer tail')
        if fields.group(4) != 'nullptr':
            names.add(json.loads(fields.group(4)))
    return names


def _check_collected_fields(title, collect, source_dir, source_txt, contextual=False):
    print(f"\n--- {title} translation coverage ---")
    try:
        identities = collect(source_dir)
        entries = parse_source_txt(source_txt)
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}')
        return 1
    keys = sorted(f'{context}|{key}' for context, key in identities) if contextual \
        else sorted(identities)
    missing = [key for key in keys if not entries.get(key.lower(), '').strip()]
    print(f'Total identities: {len(keys)}')
    print(f'  Covered: {len(keys) - len(missing)}')
    print(f'  MISSING: {len(missing)}')
    for key in missing:
        print(f'    - {key}')
    return int(bool(missing))


def check_shop_fields(source_dir: str, source_txt: str):
    return _check_collected_fields('Custom shop fields', collect_shop_fields,
                                   source_dir, source_txt, contextual=True)


def check_orc_names(source_dir: str, source_txt: str):
    return _check_collected_fields('Species orc names', collect_orc_names,
                                   source_dir, source_txt)


def main():
    if len(sys.argv) < 3:
        print("Usage: audit_data_i18n.py <source_dir> --source-txt <source.txt>")
        print("  Checks data-driven translation coverage (monsters, durations, features)")
        sys.exit(2)

    source_dir = sys.argv[1]
    if sys.argv[2] != '--source-txt' or len(sys.argv) < 4:
        print("ERROR: expected --source-txt <file>")
        sys.exit(2)
    source_txt = sys.argv[3]

    rc = 0
    rc |= check_monster_names(source_dir, source_txt)
    rc |= check_duration_strings(source_dir, source_txt)
    rc |= check_feature_names(source_dir, source_txt)
    rc |= check_cloud_names(source_dir, source_txt)
    rc |= check_corrosion_sources(source_dir, source_txt)
    rc |= check_shop_fields(source_dir, source_txt)
    rc |= check_orc_names(source_dir, source_txt)

    print(f"\n=== audit_data_i18n.py complete (exit {rc}) ===")
    return rc


if __name__ == '__main__':
    sys.exit(main())
