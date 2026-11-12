"""Map lane verdicts to identities and aggregate.
Usage: python3 -I aggregate.py <abroot>
"""
import json, sys, collections
root = sys.argv[1]
priv = json.load(open(f'{root}/private/samples_private.json'))
mp = json.load(open(f'{root}/private/lane_mapping.json'))['mapping']
INVALID = {'S29'}
samples = {s['sample_id']: s for s in priv['samples']}
per = collections.defaultdict(dict)
findings = []
for lane in ('lane1', 'lane2'):
    out = json.load(open(f'{root}/{lane}/review_output.json'))
    for r in out:
        m = mp[lane][r['sample_id']]
        sid = m['sample_id']
        v = r['verdict']
        ident = m[v] if v in ('A', 'B') else v
        per[sid][lane] = {'verdict': ident, 'reason': r.get('reason', ''), 'lane_id': r['sample_id']}
        for f in r.get('findings', []):
            side = f.get('side')
            findings.append({'sample_id': sid, 'lane': lane, 'side': m.get(side, side) if side in ('A', 'B') else side,
                             **{k: f.get(k) for k in ('type', 'category', 'quote', 'evidence', 'impact')}})
rows, tally, agree = [], {l: collections.Counter() for l in ('lane1', 'lane2')}, collections.Counter()
for sid in sorted(per):
    if sid in INVALID:
        continue
    a, b = per[sid]['lane1']['verdict'], per[sid]['lane2']['verdict']
    tally['lane1'][a] += 1; tally['lane2'][b] += 1
    if a == b:
        agree['same'] += 1
    elif {a, b} & {'theirs', 'ours'} and {a, b} == {'theirs', 'ours'}:
        agree['opposite'] += 1
    else:
        agree['one_decisive_other_tie_or_gap'] += 1
    rows.append({'sample_id': sid, 'layer': samples[sid]['layer'], 'identical': samples[sid]['identical'],
                 'lane1': a, 'lane2': b, 'english': samples[sid]['english'][:80]})
layer = collections.defaultdict(collections.Counter)
for r in rows:
    if r['lane1'] == r['lane2']:
        layer[r['layer']][r['lane1']] += 1
    else:
        layer[r['layer']]['split'] += 1
res = {'invalid_samples': sorted(INVALID), 'valid': len(rows), 'tally': {k: dict(v) for k, v in tally.items()},
       'agreement': dict(agree), 'by_layer_consensus': {k: dict(v) for k, v in sorted(layer.items())},
       'rows': rows, 'findings': findings, 'per_sample': per}
json.dump(res, open(f'{root}/private/aggregate.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ('valid', 'tally', 'agreement', 'by_layer_consensus')}, ensure_ascii=False, indent=1))
for r in rows:
    if r['lane1'] != 'tie' or r['lane2'] != 'tie':
        print(r['sample_id'], r['layer'], 'L1=', r['lane1'], 'L2=', r['lane2'], '|', r['english'].replace('\n', ' ')[:60])
print('findings by side/type:', collections.Counter((f['side'], f['type']) for f in findings))
