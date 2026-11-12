#!/usr/bin/env python3
"""Artifact integrity checks, not assertions about game rendering."""
import argparse,pathlib,json,collections,hashlib
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--record-hashes',action='store_true');a=p.parse_args();out=pathlib.Path(a.out);d=json.loads((out/'families_r3.json').read_text());xs=d['families'];assert len(xs)==72;assert len({x['family_id'] for x in xs})==72
for c in 'ABCDEF':
 rows=[x for x in xs if x['category']==c];assert len(rows)==12;assert collections.Counter(x['stratum'] for x in rows)=={'high_risk':6,'common_static':6}
excluded=set()
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in ('key','english','msgid') and isinstance(v,str):excluded.add(v.replace('\\n','\n').replace('\\t','\t'))
   else:walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
for f in (out/'inputs').glob('*.json'):walk(json.loads(f.read_text())['samples'])
for x in xs:
 assert x['calls']['stable']
 for text in x['english_templates']:assert text not in excluded,(x['family_id'],text)
for x in xs+d['directed']:
 assert x['calls']['stable'] or x['calls']['trunk']
 for l in ('stable','trunk'):
  for r in x['reconstructions'][l]:
   assert r['method'] in ['静态模板，无参数','参数文本还原','已有自动化断言覆盖的','需要运行时输出才能确定的']
   if r['method'] in ('静态模板，无参数','参数文本还原'):assert r['full_zh_display'] is not None
for lane in (1,2):
 s=(out/f'review_input_lane{lane}.md').read_text()
 for x in xs+d['directed']:assert s.count('## '+x['family_id']+' ·')==1
paths=['families_r3.json','selection_log_r3.json','coverage_r3.md','review_input_lane1.md','review_input_lane2.md']+[f'pool_{c}.json' for c in 'ABCDEF'];hashes={f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in paths}
path=out/'verification_r3.json'
if a.record_hashes:path.write_text(json.dumps({'integrity_passed':True,'random_family_count':72,'directed_count':len(d['directed']),'render_assertions_executed':False,'artifact_sha256':hashes},ensure_ascii=False,indent=2)+'\n')
else:assert hashes==json.loads(path.read_text())['artifact_sha256'],'reproduction hash mismatch'
print('Artifact checks passed; '+('hashes recorded.' if a.record_hashes else 'reproduction hashes identical.'))
