#!/usr/bin/env python3
import argparse, subprocess, pathlib, re, json, random, tarfile, io, collections, ast, hashlib
P=argparse.ArgumentParser(); P.add_argument('--repo',default='.'); P.add_argument('--out',default=str(pathlib.Path(__file__).resolve().parent.parent)); a=P.parse_args(); repo=pathlib.Path(a.repo); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
# An extension rerun must never redraw the frozen first sixty samples.
if (out/'frozen60'/'samples_r2.json').exists():
 import sys
 subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('extend_pool_r2.py')),'--repo',str(repo),'--out',str(out)],check=True)
 raise SystemExit(0)
refs={'stable':'83af93c8bdbbaf1b66aeac0af3eaa6ff58cebc57','trunk':'302ecba316bee8be19b73d06c3697cf82bd5bc3e'}; seed=2026111202

def git(*args): return subprocess.check_output(['git','-C',str(repo),*args])
def show(ref,p):
 try:return git('show',ref+':'+p).decode()
 except subprocess.CalledProcessError:return ''
def dump(p,x): (out/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def entries(s,cat=False):
 d={}; lines=s.splitlines(); i=0
 while i<len(lines):
  if lines[i].strip()!='%%%%': i+=1;continue
  i+=1
  if i>=len(lines):break
  key=lines[i]; line=i+1;i+=1; body=[]
  while i<len(lines) and lines[i].strip()!='%%%%':body.append(lines[i]);i+=1
  d[key]={'text':'\n'.join(body).strip('\n'),'line':line}
 return d
src='crawl-ref/source/'; catalog=src+'dat/i18n/zh/source.txt'
# Export only the two fixed snapshots, never inspect mutable source files.
snap={}
for lane,sha in refs.items():
 root=out/'snapshots'/lane
 if not (root/src/'AppHdr.h').exists():
  data=git('archive',sha,'crawl-ref/source'); root.mkdir(parents=True,exist_ok=True)
  with tarfile.open(fileobj=io.BytesIO(data)) as t:t.extractall(root)
 snap[lane]={str(p.relative_to(root)):p.read_text(errors='replace') for p in (root/src).rglob('*') if p.is_file() and p.suffix in ('.cc','.h','.txt')}
cat={l:entries(s[catalog],True) for l,s in snap.items()}
ex=collections.defaultdict(list)
def walk(x,reason):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in ('key','english','msgid') and isinstance(v,str):ex[v].append(reason)
   else:walk(v,reason)
 elif isinstance(x,list):
  for v in x:walk(v,reason)
for p in ['docs/archive/translation-ab-review-2026-11-12/samples_with_identity.json','docs/archive/dc096-anchoring-review-2026-11-12/anchoring-B-inventory.json']:

 frozen=out/'exclusion_inputs'/pathlib.Path(p).name; frozen.parent.mkdir(exist_ok=True)
 if not frozen.exists(): frozen.write_bytes((repo/p).read_bytes())
 walk(json.loads(frozen.read_text()),p)
merges=[]
for row in git('log','--all','--merges','--format=%H %s').decode().splitlines():
 m=re.search(r'Merge pull request #(\d+) from yutio8888/',row)
 if not m or not 299<=int(m[1])<=311:continue
 sha=row.split()[0]; merges.append({'pr':int(m[1]),'sha':sha})
 for p in git('diff','--name-only',sha+'^1',sha,'--','crawl-ref/source/dat').decode().splitlines():
  if '/zh/' not in p or not p.endswith('.txt'):continue
  before=entries(show(sha+'^1',p)); after=entries(show(sha,p))
  for k in set(before)|set(after):
   if before.get(k,{}).get('text')!=after.get(k,{}).get('text'):ex[k].append('PR#'+m[1])
assert set(x['pr'] for x in merges)==set(range(299,312))
# C/C++ adjacent literal groups, excluding comments before scanning.
pat=re.compile(r'"(?:\\.|[^"\\])*"(?:\s*"(?:\\.|[^"\\])*")*')
def dec(s):
 try:return ''.join(ast.literal_eval(x) for x in re.findall(r'"(?:\\.|[^"\\])*"',s))
 except (ValueError,SyntaxError):return ''
def norm(s):return s.replace('\\n','\n').replace('\\t','\t').replace('\\r','\r')
keymap={norm(k):k for l in cat.values() for k in l}
sites={l:collections.defaultdict(list) for l in refs}
for lane,files in snap.items():
 for p,s in sorted(files.items()):
  if not p.endswith(('.cc','.h')) or '/catch2' in p or any(x in pathlib.Path(p).name for x in ['wiz','debug','test']):continue
  clean=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/',lambda m:re.sub(r'[^\n]',' ',m[0]),s)
  for m in pat.finditer(clean):
   text=dec(m[0]); k=keymap.get(text)
   if not k:continue
   pre=clean[max(0,m.start()-100):m.start()]
   # Restrict the frame to proven translation/display entry points.
   if not re.search(r'\b(T_|C_|N_|mpr|mprf|canned_msg|yesno|formatted_string|make_stringf|prompt)\s*\([^;{}]*$',pre):continue
   n=s.count('\n',0,m.start())+1; lines=s.splitlines(); lo=max(0,n-11); hi=min(len(lines),n+10)
   # Capture complete enclosing statement to retain format argument expressions.
   start=max(s.rfind(';',0,m.start()),s.rfind('{',0,m.start()),s.rfind('}',0,m.start()))+1
   end=s.find(';',m.end()); statement=s[start:end+1] if end!=-1 else s[start:m.end()]
   sites[lane][k].append({'path':p,'line':n,'snippet':'\n'.join(f'{i+1}: {lines[i]}' for i in range(lo,hi)), 'statement':statement.strip()})
pools={f'C{i}':[] for i in range(1,7)}; excluded=[]
def add(k,c,en=None,asset=None,cons=None,dynamic=None):
 if k in ex:excluded.append({'key':k,'reason':ex[k]});return
 if len(k.strip())<4 or not re.search('[a-zA-Z]{2}',k):return
 st=cat['stable'].get(k); tr=cat['trunk'].get(k)
 if asset:
  st=asset['stable'];tr=asset['trunk']
 else:asset={l:({'path':catalog,**cat[l][k]} if k in cat[l] else None) for l in refs}
 co=cons or {l:sites[l].get(k,[]) for l in refs}
 if not co['stable']:return
 diff='stable 特有' if not co['trunk'] else 'trunk 特有' if not co['stable'] else '相同' if st and tr and st['text']==tr['text'] and (not en or en['stable']==en['trunk']) else '分化'
 pools[c].append({'category':c,'key':k,'english':en['stable'] if en else norm(k),'english_trunk':en['trunk'] if en else norm(k),'stable_zh':st['text'] if st else None,'trunk_zh':tr['text'] if tr else None,'trunk_applicability':diff,'assets':asset,'english_assets':({l:{'path':src+'dat/descript/skills.txt','line':ensk[l].get(k,{}).get('line')} for l in refs} if en else {l:[{'path':z['path'],'line':z['line']} for z in co[l]] for l in refs}),'catalog_presence':{l:asset[l] is not None for l in refs},'consumers':co,'dynamic_argument_evidence':{l:[z['statement'] for z in co[l]] for l in refs},'dynamic_parameters':dynamic or ('无格式占位符；条件及拼接上下文见消费者完整 statement 与 snippet。' if not re.search(r'%[-+\d.*]*[sdifu]',k) else '格式实参的真实生成表达式见各消费者 statement（保留完整调用，包括嵌套名称/数值表达式）。'),'shared_key':{'stable_consumers':len(co['stable']),'trunk_consumers':len(co['trunk']),'note':'同一英文键合为一项；列出快照中所有通过本候选规则识别的直接翻译/显示消费者。'}})
for k in sorted(sites['stable']):
 if k not in cat['stable']:continue
 paths=' '.join(x['path'] for x in sites['stable'][k]); c=None
 # Priority makes strata disjoint; condition/failure messages belong to C6.
 if re.search(r"can't|cannot|too .+ to |fail|unable|not enough|while|prevent",k,re.I) and (re.search(r'%[-+\d.*]*[sdifu]',k) or any(re.search(r'\b(if|case|else)\b',x['snippet']) for x in sites['stable'][k])):c='C6'
 elif re.search(r'/(command|menu|initfile|macro|options)[^/]*\.cc',paths):c='C1'
 elif re.search(r'/(potion|item-use|evoke|player-equip|wand)[^/]*\.cc',paths):c='C2'
 elif re.search(r'/(traps|terrain|branch[^/]*|stairs)\.cc',paths):c='C4'
 elif re.search(r'/(hints|tutorial)\.cc',paths):c='C5'
 if c:add(k,c)
# Skill descriptions form the C3 subcategory, via the production computed lookup.
for lane in refs:
 assert 'getLongDescription(skill_name_en(skill))' in snap[lane][src+'describe.cc']
ensk={l:entries(snap[l][src+'dat/descript/skills.txt']) for l in refs}; zhsk={l:entries(snap[l][src+'dat/descript/zh/skills.txt']) for l in refs}
for k in sorted(ensk['stable']):
 if k not in zhsk['stable']:continue
 co={}
 for l in refs:
  co[l]=[]
  for p in [src+'describe.cc',src+'hints.cc',src+'tilereg-skl.cc']:
   s=snap[l].get(p,''); lines=s.splitlines()
   for i,line in enumerate(lines):
    if 'getLongDescription(skill_name_en(skill))' in line or ('get_skill_description(' in line and not line.startswith('string get_')):
     co[l].append({'path':p,'line':i+1,'snippet':'\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-10),min(len(lines),i+11))),'statement':line.strip()})
 add(k,'C3',en={l:ensk[l].get(k,{}).get('text') for l in refs},asset={l:({'path':src+'dat/descript/zh/skills.txt',**zhsk[l][k]} if k in zhsk[l] else None) for l in refs},cons=co,dynamic='lookup key = skill_name_en(skill)，skill 为技能枚举；正文由 get_skill_description 返回，describe_skill / hints / tiles UI 消费。无格式实参。')
# Deduplicate both English identities and full bodies before drawing.
seen=set()
for c,pool in pools.items():
 dedup=[]
 for x in pool:
  if x['key'] in seen or x['english'] in seen:excluded.append({'key':x['key'],'reason':['duplicate key/body']});continue
  seen.update([x['key'],x['english']]);dedup.append(x)
 pools[c]=dedup
# Scope validation precedes the actual frozen draw; no Chinese wording is judged.
validation_exclusions=[]
def eligible(c,x):
 k=x['key']
 if re.search(r'debug|diagnostic|wizard',k,re.I):return False
 if c=='C6':
  # Limit this stratum to player restriction/failure output, excluding monster
  # descriptions, successful traversal advice, and failure-rate UI labels.
  if re.search(r"(?:Something |you |You )can't see|risk of failure|While standing| cannot move",k):return False
  if not re.search(r"(?:You|you|Your|your) (?:can't|cannot|are too|do not|don't|have no|lack|fail|are unable)|(?:prevents? (?:you|your)|not enough|This spell cannot)",k):return False
 return True
for c,pool in pools.items():
 kept=[]
 for x in pool:
  if eligible(c,x):kept.append(x)
  else:validation_exclusions.append({'category':c,'key':x['key'],'reason':'pre-draw scope check: debug/diagnostics or not a player restriction/failure message'})
 pools[c]=kept
samples=[]; reserve={}; counts={}
for i,(c,pool) in enumerate(pools.items(),1):
 assert len(pool)>=15,(c,len(pool))
 sub=seed+i; order=list(range(len(pool)));random.Random(sub).shuffle(order)
 reserve[c]=[pool[j]['key'] for j in order[10:15]]
 for n,j in enumerate(order[:10],1):
  x=dict(pool[j]);x['sample_id']=f'{c}-{n:02}';samples.append(x)
 counts[c]=len(pool);dump('pool_'+c+'.json',{'category':c,'seed':sub,'count':len(pool),'candidates':pool})
dump('samples_r2.json',{'seed':seed,'refs':refs,'subseeds':{c:seed+i for i,c in enumerate(pools,1)},'samples':samples})
dump('selection_log_r2.json',{'seed':seed,'merges':merges,'exclusion_input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'exclusion_inputs').glob('*.json')},'exclusion_key_count':len(ex),'exclusion_keys':dict(sorted(ex.items())),'pre_draw_exclusions':excluded+validation_exclusions,'invalidated':[],'replacements':[],'reserves':reserve})
for lane,rseed in [(1,1201),(2,2302)]:
 order=list(samples);random.Random(rseed).shuffle(order); buf=[f'# 第二轮抽样评审输入 lane{lane}\n\n顺序种子：{rseed}；快照：{json.dumps(refs)}\n']
 for x in order:
  buf += [f"## {x['sample_id']} · {x['category']}\n",'英文全文：\n\n'+x['english'],'\nstable 中文全文：\n\n'+x['stable_zh']]
  if x['trunk_applicability']!='相同':buf+=['\ntrunk（'+x['trunk_applicability']+'）中文全文：\n\n'+(x['trunk_zh'] if x['trunk_zh'] is not None else '（此快照无对应中文条目；见 catalog_presence 和消费者证据）'),'\ntrunk 英文全文：\n\n'+str(x['english_trunk'])]
  buf+=['\n动态参数说明：'+x['dynamic_parameters']]
  for l in refs:
   for z in x['consumers'][l]:buf += [f"\n{l} {z['path']}:{z['line']}\n```cpp\n{z['snippet']}\n```\n完整调用/语句：\n```cpp\n{z['statement']}\n```"]
 (out/f'review_input_lane{lane}.md').write_text('\n\n'.join(buf)+'\n')
stats=dict(collections.Counter(x['trunk_applicability'] for x in samples))
(out/'README_r2.md').write_text(f'''# 第二轮冻结样本

固定快照：{json.dumps(refs)}。seed={seed}；每类独立 Random(seed+类别序号)，候选按英文 key 排序；先取10，再取5作为有序备用。

候选总体规模：{json.dumps(counts)}。最终每类10，共60。作废0，补抽0。两线统计：{json.dumps(stats,ensure_ascii=False)}。

类别：C1命令帮助设置；C2消耗品装备操作；C3技能说明；C4地形机关分支；C5教程提示；C6条件与失败动态句。

范围明确收窄为可机械证明的直接显示/翻译调用；C3使用 skills.txt 中生产技能 lookup 正文，C5使用 hints/tutorial 直接翻译文字。没有穷尽动态构造的其他 TextDB lookup、怪物言语、种族职业说明；这是一套可复现的抽样框，不是整个类别资产总量。分类依次优先 C6/C1/C2/C4/C5，C3独立技能正文，避免重复。C6必须有格式占位符或调用附近有条件分支，并有失败/限制英文触发词。

纳入：stable 中文 catalog 对应键，固定快照生产 C++ 中有 T_/C_/N_ 或显示函数直接调用；或技能正文通过 skill_name_en(skill) 配对。每个样本保留完整正文、两线资产行号、所有被规则识别的直接消费者及上下10行、完整实参语句。共享键合并计数。候选抽取先仅按键与代码判定，不做译文质量评价。中文仅用于机械配对和两线相等比较。

排除：上一轮样本键、D-C-096探针键及PR299–311一父差分修改中文条目的键；排除测试、wiz/debug文件、短符号、无法证明显示调用的字面量。排除键与理由、merge SHAs 见 selection_log_r2.json。相同正文/英文键全局去重；冻结前进行了英文键和调用语境的范围验证，移除诊断帮助及不属于玩家行动限制的句子；记录于 pre_draw_exclusions。冻结抽样未作废或补抽。

两线适用性优先按生产消费者是否存在判定专属；两线均有消费者时再比较正文与中文。中文缺项单独记录 catalog_presence，仍有消费者的缺项计为分化。source 类显示消费者以两线分别记录。宏条件和角色状态见代码片段；不把版本专属执行分支当作文本差异。格式实参按原始完整语句保留，便于评审检查真实生成方式。

重跑：`python3 scripts/build_pool_r2.py --repo <仓库路径> --out <产出目录>`。源文件导出仅用 git archive/show，不改变仓库或检出。排除清单不在固定基线中，首次从任务指定的工作区文档复制到 exclusion_inputs，后续复跑使用该冻结副本；其 SHA-256 记录在 selection_log 中。脚本无外部依赖；两份评审输入分别用1201/2302打乱。
''')
print(json.dumps({'counts':counts,'samples':len(samples),'differences':stats},ensure_ascii=False))

import sys
subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('extend_pool_r2.py')),'--repo',str(repo),'--out',str(out)],check=True)
