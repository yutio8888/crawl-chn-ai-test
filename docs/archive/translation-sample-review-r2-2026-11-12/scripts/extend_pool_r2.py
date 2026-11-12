#!/usr/bin/env python3
"""Append C7/C8, preserving the frozen 60 objects and both original lane prefixes."""
import argparse, pathlib, json, re, random, hashlib, collections, subprocess, sys
ap=argparse.ArgumentParser();ap.add_argument('--repo',default='.');ap.add_argument('--out',default=str(pathlib.Path(__file__).resolve().parent.parent));a=ap.parse_args();out=pathlib.Path(a.out);repo=pathlib.Path(a.repo)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
frozen=out/'frozen60';frozen.mkdir(exist_ok=True)
for name in ['samples_r2.json','selection_log_r2.json','README_r2.md','review_input_lane1.md','review_input_lane2.md']:
 p=frozen/name
 if not p.exists():p.write_bytes((out/name).read_bytes())
base=json.loads((frozen/'samples_r2.json').read_text());assert len(base['samples'])==60
log=json.loads((frozen/'selection_log_r2.json').read_text());refs=base['refs'];seed=base['seed'];root={l:out/'snapshots'/l for l in refs};src='crawl-ref/source/'
def read(l,p):return (root[l]/p).read_text()
def parse(s):
 d={};key=None;body=[];line=0
 def flush():
  if key is not None:d[key.casefold()]={'key':key,'text':'\n'.join(body).strip('\n'),'line':line}
 active=False
 for n,raw in enumerate(s.splitlines(),1):
  if raw.startswith('#'):continue
  if raw.startswith('%%%%'):flush();key=None;body=[];active=True;continue
  if not active:continue
  if key is None:
   if raw.strip():key=raw.strip();line=n
  else:body.append(raw.rstrip())
 flush();return d
ex={k.casefold():v for k,v in log['exclusion_keys'].items()};extra_ex=[]
# Reparse changed TextDB entries using the actual comment-skipping/casefold grammar.
for merge in log['merges']:
 sha=merge['sha'];paths=subprocess.check_output(['git','-C',str(repo),'diff','--name-only',sha+'^1',sha,'--','crawl-ref/source/dat']).decode().splitlines()
 for p in paths:
  if '/zh/' not in p or not p.endswith('.txt'):continue
  versions=[]
  for rev in [sha+'^1',sha]:
   r=subprocess.run(['git','-C',str(repo),'show',rev+':'+p],capture_output=True);versions.append(parse(r.stdout.decode()) if r.returncode==0 else {})
  old,new=versions
  for k in set(old)|set(new):
   if old.get(k,{}).get('text')!=new.get(k,{}).get('text'):
    why='PR#'+str(merge['pr'])+' TextDB grammar diff';ex.setdefault(k,[]).append(why)

def snippets(l,p,needles):
 lines=read(l,p).splitlines();res=[]
 for i,line in enumerate(lines):
  if any(t in line for t in needles):res.append({'path':p,'line':i+1,'statement':line.strip(),'snippet':'\n'.join(f'{j+1}: {lines[j]}' for j in range(max(0,i-10),min(len(lines),i+11)))})
 return res

def names(l,kind):
 d={}
 for p in sorted((root[l]/src/'dat'/kind).glob('*.yaml')):
  s=p.read_text();m=re.search(r'^name:\s*[\'"]?([^\n\'"]+)',s,re.M)
  if m:d[m[1].strip().casefold()]={'path':str(p.relative_to(root[l])),'line':s.count('\n',0,m.start())+1,'statement':m[0]}
 return d
name_maps={l:{k:names(l,k) for k in ['species','jobs','mons']} for l in refs}
# Full raw key groups, plus all referenced SpeakDB groups, with weights intact.
dbs={l:{} for l in refs}
for l in refs:
 for area,f in [('descript',f) for f in ['species.txt','backgrounds.txt','ability.txt']]+[('database','monspeak.txt')]:
  for lang in ['','zh/']:
   p=src+'dat/'+area+'/'+lang+f; dbs[l][(f,lang)]=parse(read(l,p))

def group(l,key,lang):
 db=dbs[l][('monspeak.txt',lang)];en=dbs[l][('monspeak.txt','')];found=[];seen=set()
 def visit(k):
  if k in seen:return
  seen.add(k);entry=db.get(k) or en.get(k)
  if not entry:return
  origin=lang if k in db else '';found.append({'path':src+'dat/database/'+origin+'monspeak.txt',**entry,'fallback_english':bool(lang and not origin)})
  for sub in re.findall(r'@([^@\n]+)@',entry['text']):
   if sub.casefold() in en:visit(sub.casefold())
 visit(key);return found

def full(groups):
 if not groups:return None
 return '\n\n'.join((g['text'] if i==0 else '%%%%\n'+g['key']+'\n\n'+g['text']) for i,g in enumerate(groups))

used_keys={x['key'].casefold() for x in base['samples']};used_body={x['english'] for x in base['samples']};pools={'C7':[],'C8':[]}
for c,files in [('C7',['species.txt','backgrounds.txt','ability.txt']),('C8',['monspeak.txt'])]:
 for f in files:
  eng=dbs['stable'][(f,'')];zh=dbs['stable'][(f,'zh/')]
  for k in sorted(set(eng)&set(zh)):
   key=eng[k]['key'];why=None;cons={};generators={};groups={};lane_en={};lane_zh={};assets={};enassets={}
   if k in used_keys:why='duplicate frozen/sample key'
   elif k in ex:why='excluded English key'
   elif c=='C8' and k.startswith('_'):why='internal expansion key; retain only as dependency of root group'
   elif c=='C7' and k=='no ability ability':why='debug sentinel'
   for l in refs:
    present=k in dbs[l][(f,'')];e=dbs[l][(f,'')].get(k);z=dbs[l][(f,'zh/')].get(k)
    cons[l]=[];generators[l]=[]
    if c=='C7':
     if f in ('species.txt','backgrounds.txt'):
      kind='species' if f=='species.txt' else 'jobs';name_entry=name_maps[l][kind].get(k)
      if name_entry and present:
       generators[l]=[name_entry];cons[l]=snippets(l,src+'newgame.cc',['string db_key =','getGameStartDescription(db_key)'])+snippets(l,src+'database.cc',['string getGameStartDescription('])
     else:
      target=re.sub(r' ability$','',key);asrc=read(l,src+'ability.cc')
      matches=snippets(l,src+'ability.cc',['"'+target+'"'])
      matches=[m for m in matches if 'ABIL_NON_ABILITY' not in m['statement']]
      if matches and present:
       generators[l]=[{k:m[k] for k in ['path','line','statement']} for m in matches];cons[l]=matches+snippets(l,src+'ability.cc',['const string& name = ability_name(ability, true)','lookup = getLongDescription(name + " ability")'])+snippets(l,src+'describe.cc',['void describe_ability(','inf.body << get_ability_desc'])
     lane_en[l]=e['text'] if e else None;lane_zh[l]=z['text'] if z else None
     assets[l]={'path':src+'dat/descript/zh/'+f,**z} if z else None;enassets[l]={'path':src+'dat/descript/'+f,**e} if e else None
    else:
     # Restrict C8 to named monster roots with concrete monster-data generators.
     name_entry=name_maps[l]['mons'].get(k)
     if name_entry and present:
      generators[l]=[name_entry];cons[l]=snippets(l,src+'mon-speak.cc',['msg = getSpeakString(prefix + key)','msg = getSpeakString("default " + key)','mons->base_name(DESC_DBNAME)','? msg : do_mon_str_replacements'])+snippets(l,src+'database.cc',['string getSpeakString(','_getRandomisedStr(SpeakDB, key','_getRandomisedStr(lookup, marker, suffix'])
     groups[l]={'english':group(l,k,''),'zh':group(l,k,'zh/') if z else []}
     lane_en[l]=full(groups[l]['english']);lane_zh[l]=full(groups[l]['zh'])
     assets[l]={'path':src+'dat/database/zh/'+f,**z} if z else None;enassets[l]={'path':src+'dat/database/'+f,**e} if e else None
   if not cons['stable']:why=why or 'no concrete stable production name generator'
   if c=='C8':
    deps={g['key'].casefold() for l in groups for lang in groups[l] for g in groups[l][lang]}
    if deps & set(ex):why=why or 'excluded dependency key in full speech group'
    if not re.search('[A-Za-z]',re.sub(r'@[^@]+@|__NONE|__NEXT','',lane_en['stable'] or '')):why=why or 'no visible speech body'
   if lane_en['stable'] in used_body:why=why or 'duplicate full English body'
   if why:extra_ex.append({'category':c,'key':key,'reason':why});continue
   used_keys.add(k);used_body.add(lane_en['stable'])
   status='stable 特有' if not cons['trunk'] else '相同' if lane_en['stable']==lane_en['trunk'] and lane_zh['stable']==lane_zh['trunk'] else '分化'
   if c=='C7':
    dynamic={'species.txt':'种族枚举 id → species::name(id, species::SPNAME_PLAIN, true)，英文 name 来自 dat/species/*.yaml → getGameStartDescription(db_key)。','backgrounds.txt':'职业枚举 id → get_job_name_en(id)，英文 name 来自 dat/jobs/*.yaml → getGameStartDescription(db_key)。','ability.txt':'ability 枚举 → ability_name(ability, true)（英文能力名，含动态能力的 canonical 分支） + " ability" → getLongDescription；get_ability_desc 返回基础正文，可能再附加状态相关文字；本样本单位仅为 TextDB 正文。'}[f]
   else:dynamic='单位为一个根 key 的完整变体组，附递归引用的全部组（含 w: 权重；不抽单条变体）。怪物 dat/mons/*.yaml name → mons->base_name(DESC_DBNAME)；mon-speak.cc 从态度/逃跑/沉默/混乱/信仰/分支等生成 prefixes，先查 prefix + key，逐级退回裸 key / default key。database.cc _getRandomisedStr 在组内按权重取变体并递归展开 @子键@；剩余运行时占位符交给 do_mon_str_replacements(msg,*mons)。'
   x={'category':c,'subcategory':f,'key':key,'english':lane_en['stable'],'english_trunk':lane_en['trunk'],'stable_zh':lane_zh['stable'],'trunk_zh':lane_zh['trunk'],'trunk_applicability':status,'assets':assets,'english_assets':enassets,'catalog_presence':{l:assets[l] is not None for l in refs},'consumers':cons,'key_generators':generators,'dynamic_parameters':dynamic,'shared_key':{'note':'一个 lookup key 计一次；所有枚举/怪物实例共享此生产查找路径。','stable_consumers':len(cons['stable']),'trunk_consumers':len(cons['trunk'])}}
   if c=='C8':
    x['variant_groups']=groups;x['placeholder_evidence']={}
    for l in refs:
     tags=sorted(set(re.findall(r'@([^@\n]+)@',(lane_en[l] or '')+'\n'+(lane_zh[l] or ''))));evidence={}
     for tag in tags:
      if tag.casefold() in dbs[l][(f,'')]:evidence[tag]={'source':'SpeakDB recursive group expansion','groups':[g for g in groups[l]['english'] if g['key'].casefold()==tag.casefold()]};continue
      matches=snippets(l,src+'mon-util.cc',['@'+tag+'@'])
      if tag.startswith(('player','Player')):matches+=snippets(l,src+'mon-util.cc',['replace_all(msg, "@player",','replace_all(msg, "@Player",'])
      evidence[tag]={'source':'do_mon_str_replacements','code':matches}
     x['placeholder_evidence'][l]=evidence
   pools[c].append(x)
new=[];reserves={};pool_counts={}
for c,pool in pools.items():
 pool.sort(key=lambda x:(x['subcategory'],x['key'].casefold()));sub=seed+int(c[1:]);rng=random.Random(sub);chosen=[];backup=[]
 if c=='C7':
  for f,n,b in [('species.txt',3,1),('backgrounds.txt',3,2),('ability.txt',4,2)]:
   subset=[x for x in pool if x['subcategory']==f];assert len(subset)>=n+b,(f,len(subset));rng.shuffle(subset);chosen+=subset[:n];backup+=subset[n:n+b]
 else:
  order=list(pool);rng.shuffle(order);assert len(order)>=15;chosen=order[:10];backup=order[10:15]
 for i,x in enumerate(chosen,1):x=dict(x);x['sample_id']=f'{c}-{i:02}';new.append(x)
 reserves[c]=[x['key'] for x in backup];pool_counts[c]=len(pool);dump(out/f'pool_{c}.json',{'category':c,'seed':sub,'count':len(pool),'candidates':pool})
combined={**base,'subseeds':{**base['subseeds'],'C7':seed+7,'C8':seed+8},'samples':base['samples']+new};dump(out/'samples_r2.json',combined)
log['extension']={'subseeds':{'C7':seed+7,'C8':seed+8},'frozen60_sha256':hashlib.sha256((frozen/'samples_r2.json').read_bytes()).hexdigest(),'C7_quotas':{'species.txt':[3,1],'backgrounds.txt':[3,2],'ability.txt':[4,2]},'pre_draw_exclusions':extra_ex,'exclusion_keys_casefold':dict(sorted(ex.items())),'invalidated':[],'replacements':[],'original60_unchanged':True}
log['reserves'].update(reserves);dump(out/'selection_log_r2.json',log)
for lane,rseed in [(1,1201),(2,2302)]:
 order=list(new);random.Random(rseed).shuffle(order);buf=['\n\n# C7/C8 追加样本\n\n原60项内容与顺序不变；仅追加20项以原lane种子独立乱序。\n']
 for x in order:
  buf += [f"## {x['sample_id']} · {x['category']}\n",'英文全文：\n\n'+x['english'],'stable 中文全文：\n\n'+x['stable_zh']]
  if x['trunk_applicability']!='相同':buf+=['trunk（'+x['trunk_applicability']+'）英文全文：\n\n'+str(x['english_trunk']),'trunk 中文全文：\n\n'+str(x['trunk_zh'])]
  buf+=['动态参数与键生成：'+x['dynamic_parameters'],'键生成数据：\n```json\n'+json.dumps(x['key_generators'],ensure_ascii=False,indent=2)+'\n```']
  for l in refs:
   for z in x['consumers'][l]:buf += [f"{l} {z['path']}:{z['line']}\n```cpp\n{z['snippet']}\n```"]
  if 'placeholder_evidence' in x:buf+=['占位符来源（两线）：\n```json\n'+json.dumps(x['placeholder_evidence'],ensure_ascii=False,indent=2)+'\n```']
 (out/f'review_input_lane{lane}.md').write_bytes((frozen/f'review_input_lane{lane}.md').read_bytes()+('\n\n'.join(buf)+'\n').encode())
stats={c:dict(collections.Counter(x['trunk_applicability'] for x in new if x['category']==c)) for c in pools};counts7=dict(collections.Counter(x['subcategory'] for x in pools['C7']))
(out/'README_r2.md').write_text((frozen/'README_r2.md').read_text()+f'''\n## C7/C8追加（最终80项）

原60项字段、顺序与两份评审输入原始字节前缀保持不变。原文“共60”及未覆盖种族职业/怪物言语的限制描述对应首批；本节追加后共80项。

C7候选规模：{pool_counts['C7']}，分文件：{json.dumps(counts7)}。子种子2026111209。为覆盖三个领域采用固定分层配额：species 3、backgrounds 3、ability 4；备用分别1、2、2；不按总体比例。单个 Random(2026111209)，按species/backgrounds/ability顺序分别对按key排序的子池shuffle，每池先取正选再取备用。

C8候选规模：{pool_counts['C8']}。子种子2026111210。按key排序后 Random(2026111210).shuffle，先10再5。单位为一个怪物根key的完整变体组，保留全部权重与递归依赖组；内部组只作为正文依赖而非独立样本。候选框收窄到可由 dat/mons/*.yaml name 直接生成的怪物名根键，不含前缀专属键、glyph回退键和内部片段库。每个根key的生产消费者及参数替换代码均随样本提供。中文依赖缺项时保留英文回退，并在variant_groups标注 fallback_english。

两类均使用实际TextDB语法跳过#注释、空行，按大小写不敏感的lookup key配对；追加排除集从PR299–311的同一merge一父差分用该语法重新解析，同时保留上一轮及D-C-096排除集。依赖组命中排除集也排除整个C8根样本。与原60项按英文key和完整英文正文去重；两线适用性按生产键生成器存在性、英文全文及中文全文比较。C7只抽基础TextDB正文，运行时追加文字在调用证据中说明。

追加作废0、补抽0；各类备用5项。两线差异：{json.dumps(stats,ensure_ascii=False)}。每类候选完整资产、英文及中文全文、代码证据均在pool_C7/C8.json；追加排除记录在selection_log_r2.json的extension。两份lane保留原60项顺序，追加20项分别以1201、2302独立打乱。

重跑仍执行 scripts/build_pool_r2.py；已有frozen60时直接运行扩展脚本，避免重新抽取前60项。也可单独运行 scripts/extend_pool_r2.py --repo <仓库> --out <产出目录>。
''')
assert combined['samples'][:60]==base['samples'];assert len(combined['samples'])==80
print(json.dumps({'pool_counts':pool_counts,'C7_subpool_counts':counts7,'selected':{c:[x['key'] for x in new if x['category']==c] for c in pools},'differences':stats},ensure_ascii=False))
