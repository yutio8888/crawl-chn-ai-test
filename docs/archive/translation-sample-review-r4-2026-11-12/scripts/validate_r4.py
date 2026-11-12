#!/usr/bin/env python3
"""Check inventory integrity/reproducibility; this is not a game rendering test."""
import argparse,json,pathlib,hashlib,collections,re
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--record-hashes',action='store_true');a=p.parse_args();out=pathlib.Path(a.out);d=json.loads((out/'samples_r4.json').read_text());log=json.loads((out/'selection_log_r4.json').read_text());xs=d['samples'];assert len(xs)==70;assert len({x['sample_id'] for x in xs})==70;assert len({x['key'].casefold() for x in xs})==70;assert len({x['english'] for x in xs})==70
for c,s in d['selection'].items():
 subset=[x for x in xs if x['category']==c];assert len(subset)==10
 assert collections.Counter(x['risk_stratum'] for x in subset)=={'high_risk':s['high_risk'],'static_control':s['static_control']}
 assert len(log['reserves'][c])==5;assert not set(log['reserves'][c])&{x['key'] for x in subset}
 pool=json.loads((out/f'pool_{c}.json').read_text());assert len(pool['candidates'])==s['pool_count']
for x in xs:
 assert x['consumers']['stable'];assert x['key'] not in log['excluded_keys']
 for l in d['refs']:
  for r in x['reconstructions'][l]:
   if r['method'] in ['静态模板，无参数','参数文本还原']:assert r['full_zh_display'] is not None
  for z in x['consumers'][l]:assert z['path'].startswith('crawl-ref/source/') and z['line']>0 and z['snippet']
for lane in [1,2]:
 text=(out/f'review_input_lane{lane}.md').read_text()
 for x in xs:assert text.count('## '+x['sample_id']+' ·')==1
for item in d['exclusion_provenance']:
 assert hashlib.sha256((out/'inputs'/(item['label']+'.json')).read_bytes()).hexdigest()==item['sha256']
assert {m['pr'] for m in log['merges']}==set(range(299,317))
files=['samples_r4.json','coverage_r4.md','selection_log_r4.json','review_input_lane1.md','review_input_lane2.md']+[f'pool_R4-{i}.json' for i in range(1,8)];hashes={f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in files};target=out/'verification_r4.json'
if a.record_hashes:target.write_text(json.dumps({'integrity_passed':True,'sample_count':70,'reserve_count':35,'game_rendering_tests_run':False,'artifact_sha256':hashes},ensure_ascii=False,indent=2)+'\n')
else:assert hashes==json.loads(target.read_text())['artifact_sha256'],'reproduction differs'
print('Inventory integrity passed; '+('hashes recorded.' if a.record_hashes else 'reproduction hashes identical.'))
