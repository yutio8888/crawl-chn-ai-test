"""Compare their ui.po with our source.txt (exact English match, case-sensitive and
case-insensitive), report counts and dump matched pairs as JSON.
Usage: python3 -I compare.py <ui.po> <ours source.txt> <out.json>
"""
import json, re, sys, collections

def unq(s):
    s = s.strip()
    assert s.startswith('"') and s.endswith('"'), s
    body = s[1:-1]
    return bytes(body, 'utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8') if '\\' in body else body

def parse_po(path):
    entries, cur, field = [], {}, None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip():
            if cur.get('msgid') is not None:
                entries.append(cur)
            cur, field = {}, None
            continue
        if line.startswith('#'):
            continue
        m = re.match(r'(msgctxt|msgid|msgstr)\s+(".*")$', line)
        if m:
            field = m.group(1); cur[field] = unq(m.group(2)); continue
        if line.startswith('"') and field:
            cur[field] += unq(line)
    if cur.get('msgid') is not None:
        entries.append(cur)
    return [e for e in entries if e.get('msgid')]

def parse_source(path):
    text = open(path, encoding='utf-8').read()
    out = {}
    for block in text.split('%%%%\n'):
        lines = block.split('\n')
        if not lines or not lines[0].strip():
            continue
        key = lines[0]
        val = '\n'.join(l for l in lines[1:] if l != '').strip()
        if not val:
            continue
        # source.txt stores \n as literal backslash-n; normalise to real newline
        key = key.replace('\\n', '\n'); val = val.replace('\\n', '\n')
        out[key] = val
    return out

po = parse_po(sys.argv[1])
ours = parse_source(sys.argv[2])
ours_plain = {}
ours_ctx = collections.defaultdict(dict)
for k, v in ours.items():
    if '|' in k and not k.startswith('|'):
        c, e = k.split('|', 1)
        ours_ctx[e.lower()][c] = v
    ours_plain.setdefault(k.lower(), v)

their_untrans = sum(1 for e in po if not e.get('msgstr'))
their_ids = {e['msgid'] for e in po}
ctx_counts = collections.Counter(e.get('msgctxt', '').split('.')[0] for e in po)
matched, rows = set(), []
for e in po:
    en = e['msgid']
    o = ours_plain.get(en.lower())
    octx = ours_ctx.get(en.lower())
    if o is None and octx:
        o = next(iter(octx.values()))
    if o is not None and e.get('msgstr'):
        matched.add(en)
        rows.append({'ctx': e.get('msgctxt', ''), 'en': en, 'theirs': e['msgstr'], 'ours': o,
                     'ours_ctx': sorted(octx) if octx else []})
summary = {
    'their_entries': len(po), 'their_distinct_english': len(their_ids),
    'their_untranslated': their_untrans,
    'their_top_contexts': ctx_counts.most_common(15),
    'ours_entries': len(ours), 'ours_distinct_english_ci': len(set(k.split('|',1)[-1].lower() for k in ours)),
    'matched_distinct_english_ci': len(matched),
    'identical_translation': sum(1 for r in rows if r['theirs'] == r['ours']),
}
json.dump({'summary': summary, 'rows': rows}, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
