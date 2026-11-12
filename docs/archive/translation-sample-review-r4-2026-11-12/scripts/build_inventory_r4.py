#!/usr/bin/env python3
"""Reproducible, source-only round-four sampling; repository is never written."""
import argparse,pathlib,subprocess,tarfile,io,json,re,ast,random,collections,hashlib,itertools
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--out',required=True);a=p.parse_args();repo=pathlib.Path(a.repo);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
seed=2026111213;refs={'stable':'ae5a420e78579a9433f4ffb127b7a9062a7d948c','trunk':'59aec6256f1824d8c5cd7de92b7c25691132cce9'};src='crawl-ref/source/';catalog=src+'dat/i18n/zh/source.txt'
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
def dump(f,x):(out/f).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def show(r,p):
 q=subprocess.run(['git','-C',str(repo),'show',r+':'+p],capture_output=True);return q.stdout.decode() if q.returncode==0 else ''
def read(l,p):return (out/'snapshots'/l/p).read_text(errors='replace')
for l,sha in refs.items():
 root=out/'snapshots'/l
 if not (root/src/'AppHdr.h').exists():
  root.mkdir(parents=True,exist_ok=True)
  with tarfile.open(fileobj=io.BytesIO(git('archive',sha,'crawl-ref/source'))) as t:t.extractall(root)

def parse(s,trim=True):
 d={};key=None;body=[];ln=0;active=False
 def flush():
  if key is not None:d[key]={'text':'\n'.join(body).strip('\n'),'line':ln}
 for n,line in enumerate(s.splitlines(),1):
  if line.startswith('#'):continue
  if line.startswith('%%%%'):flush();key=None;body=[];active=True;continue
  if not active:continue
  if key is None:
   if line.strip():key=line.strip() if trim else line;ln=n
  else:body.append(line)
 flush();return d

def norm(s):return s.replace('\\n','\n').replace('\\t','\t').replace('\\r','\r')
def sig(s):
 s=norm(s).casefold();s=re.sub(r'%(?:\d+\$)?[-+ #0\d.*]*[sdifu]','{param}',s);return re.sub(r'\s+',' ',s).strip()
inputs=out/'inputs';inputs.mkdir(exist_ok=True);provenance=[];ex=collections.defaultdict(set);prior_sources=set()
paths=[('r1','docs/archive/translation-ab-review-2026-11-12/samples_with_identity.json'),('dc096','docs/archive/dc096-anchoring-review-2026-11-12/anchoring-B-inventory.json'),('r2','docs/archive/translation-sample-review-r2-2026-11-12/samples_r2.json'),('r2log','docs/archive/translation-sample-review-r2-2026-11-12/selection_log_r2.json'),('r3','docs/archive/player-action-review-r3-2026-11-12/families_r3_index.json')]
def walk(x,why):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in ['key','english','msgid','english_template'] and isinstance(v,str):ex[norm(v)].add(why)
   elif k in ['english_templates','excluded_keys'] and isinstance(v,list):
    for text in v:
     if isinstance(text,str):ex[norm(text)].add(why)
   else:walk(v,why)
  if isinstance(x.get('path'),str) and isinstance(x.get('function'),str):prior_sources.add((x['path'],x['function']))
 elif isinstance(x,list):
  for v in x:walk(v,why)
for label,path in paths:
 frozen=inputs/(label+'.json');meta=inputs/(label+'.provenance.json')
 if not frozen.exists():
  text='';rev=None
  for ref in refs.values():
   text=show(ref,path)
   if text:rev=ref;break
  if not text:
   rev=git('log','--all','-1','--format=%H','--',path).decode().strip();text=show(rev,path)
  assert text,(label,path);frozen.write_text(text);meta.write_text(json.dumps({'path':path,'commit':rev}))
 obj=json.loads(frozen.read_text());walk(obj,label);provenance.append({'label':label,**json.loads(meta.read_text()),'sha256':hashlib.sha256(frozen.read_bytes()).hexdigest()})
merges=[]
for row in git('log','--all','--merges','--format=%H %s').decode().splitlines():
 m=re.search(r'Merge pull request #(\d+) from yutio8888/',row)
 if not m or not 299<=int(m[1])<=316:continue
 sha=row.split()[0];merges.append({'pr':int(m[1]),'sha':sha})
 for path in git('diff','--name-only',sha+'^1',sha,'--','crawl-ref/source/dat').decode().splitlines():
  if '/zh/' not in path or not path.endswith('.txt'):continue
  old=parse(show(sha+'^1',path),path!=catalog);new=parse(show(sha,path),path!=catalog)
  for k in sorted(set(old)|set(new)):
   if old.get(k,{}).get('text')!=new.get(k,{}).get('text'):ex[norm(k)].add('PR#'+m[1])
assert {m['pr'] for m in merges}==set(range(299,317))
exsig={sig(k) for k in ex};exfold={k.casefold() for k in ex}
cats={l:parse(read(l,catalog),False) for l in refs};cm={l:{norm(k):k for k in cats[l]} for l in refs}
def lookup(l,text,ctx=None):
 k=ctx+'|'+text if ctx and ctx+'|'+text in cats[l] else cm[l].get(text)
 if k is None:return {'english':text,'key':None,'zh':None,'asset':None}
 v=cats[l][k];return {'english':text,'key':k,'zh':norm(v['text']),'zh_raw':v['text'],'asset':{'path':catalog,'line':v['line']}}

def clean(s):
 token=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
 s=token.sub(lambda m:m[0] if m[0].startswith('"') else re.sub(r'[^\n]',' ',m[0]),s);stack=[];out=[]
 for line in s.splitlines(keepends=True):
  if re.match(r'\s*#\s*(if|ifdef|ifndef)\b',line):stack.append(bool(re.search(r'DEBUG|WIZARD',line)) or (stack[-1] if stack else False))
  blocked=any(stack)
  if re.match(r'\s*#\s*endif\b',line) and stack:stack.pop()
  out.append(re.sub(r'[^\n]',' ',line) if blocked else line)
 return ''.join(out)
litpat=re.compile(r'"(?:\\.|[^"\\])*"(?:\s*"(?:\\.|[^"\\])*")*')
def decode(s):
 try:return ''.join(ast.literal_eval(q) for q in re.findall(r'"(?:\\.|[^"\\])*"',s))
 except (ValueError,SyntaxError):return ''
def balanced(s,op,opening='(',closing=')'):
 depth=0;quote=None;i=op
 while i<len(s):
  ch=s[i]
  if quote:
   if ch=='\\':i+=2;continue
   if ch==quote:quote=None
  elif ch in '\"\'':quote=ch
  elif ch==opening:depth+=1
  elif ch==closing:
   depth-=1
   if depth==0:return i+1
  i+=1
 return op

def splitargs(s):
 dep=0;quote=None;start=0;out=[];i=0
 while i<len(s):
  ch=s[i]
  if quote:
   if ch=='\\':i+=2;continue
   if ch==quote:quote=None
  elif ch in '\"\'':quote=ch
  elif ch in '([{':dep+=1
  elif ch in ')]}':dep-=1
  elif ch==',' and dep==0:out.append(s[start:i].strip());start=i+1
  i+=1
 return out+[s[start:].strip()]

def snippet(s,n,end=None,pad=10):
 lines=s.splitlines();return '\n'.join(f'{i+1}: {lines[i]}' for i in range(max(0,n-pad-1),min(len(lines),(end or n)+pad)))
def find(l,path,needles):
 s=read(l,path);res=[]
 for i,line in enumerate(s.splitlines(),1):
  if any(v in line for v in needles):res.append({'path':path,'line':i,'statement':line.strip(),'snippet':snippet(s,i)})
 return res

# Frozen production token index, also used as concrete key-generator evidence.
literals={l:collections.defaultdict(list) for l in refs};source_text={l:{} for l in refs};functions={l:{} for l in refs}
funcpat=re.compile(r'(?m)^(?:[\w:<>,*&]+[ \t]+)+([\w:~]+)\s*\([^;{}]*\)(?:\s*const)?\s*\n\{')
for l in refs:
 for path in sorted((out/'snapshots'/l/src).rglob('*')):
  if path.suffix not in ['.cc','.h','.lua','.des'] or re.search(r'wiz-|/test|debug|/catch2|/util/',str(path)):continue
  rel=str(path.relative_to(out/'snapshots'/l))
  if '/dat/' in rel and not any(t in rel for t in ['/dat/des/','/dat/clua/','/dat/dlua/','/dat/lua/']):continue
  s=path.read_text(errors='replace');source_text[l][rel]=s;cs=clean(s);functions[l][rel]=[]
  if path.suffix in ['.cc','.h']:
   for fm in funcpat.finditer(cs):
    b=cs.index('{',fm.start());functions[l][rel].append({'name':fm[1],'start':fm.start(),'end':balanced(cs,b,'{','}')})
  for q in litpat.finditer(cs):
   text=decode(q[0]);n=s.count('\n',0,q.start())+1
   if text:literals[l][text.casefold()].append({'path':rel,'line':n,'statement':s.splitlines()[n-1].strip(),'snippet':snippet(s,n)})

# Direct display calls, grouped with nearby conditional alternatives in the same function.
scopes={
 'R4-1':['describe.cc'],
 'R4-2':['spl-damage.cc','spl-summoning.cc','spl-clouds.cc','spl-other.cc','spl-transloc.cc'],
 'R4-3':['mon-cast.cc'],
 'R4-4':['god-gift.cc','god-wrath.cc','god-abil.cc','religion.cc','god-prayer.cc','describe-god.cc'],
 'R4-5':['hints.cc','command.cc','tutorial.cc'],
 'R4-6':['cloud.cc','dungeon.cc','abyss.cc','timed-effects.cc','dgn-event.cc','orb.cc','branch.cc'],
 'R4-7':['mon-act.cc','mon-ench.cc','mon-abil.cc','spl-monench.cc']}
callregex=re.compile(r'\b(mpr\w*|yesno\w*|simple_monster_message|make_stringf\w*|formatted_string)\s*\(')
calls={l:{c:[] for c in scopes} for l in refs};unproven=[];excluded_rows=[{'category':'R4-1','reason':'pre-draw scope validation: monster/bane rows and internal inventory diagnostics excluded from item description frame'},{'category':'R4-6','reason':'pre-draw scope validation: stairs left to earlier movement rounds; diagnostic channels, Lua DEBUG callbacks, Sprint scoring and user automation excluded'}]
for l in refs:
 for category,files in scopes.items():
  for f in files:
   path=src+f
   if path not in source_text[l]:continue
   s=source_text[l][path];cs=clean(s);found=[]
   for m in callregex.finditer(cs):
    op=cs.index('(',m.start());end=balanced(cs,op)
    if end<=op:continue
    fn=next((v for v in functions[l][path] if v['start']<=m.start()<v['end']),None);name=fn['name'] if fn else 'file-scope lambda/table'
    if re.search(r'debug|wizard|test_',name,re.I):continue
    if (path,name) in prior_sources:excluded_rows.append({'category':category,'path':path,'function':name,'reason':'previous-source-family'});continue
    expression=s[m.start():end]
    if category!='R4-1' and not re.match(r'(?:mpr\w*|yesno\w*|simple_monster_message)\s*\(',expression):continue
    if category=='R4-1' and path==src+'describe.cc':
     if not fn or not (re.search(r'item|weapon|armour|artefact|randart|jewel|ammo|missile|talisman|equipment|training|lignify|orb',name,re.I) or 'item_def' in s[fn['start']:cs.index('{',fn['start'])]):continue
    if any(ch in expression for ch in ['MSGCH_ERROR','MSGCH_DIAGNOSTICS','MSGCH_DEBUG']) or re.search(r'buggy|Lua error|error:|invalid|illegal|no desc for|Failed to place prism',expression,re.I):continue
    templates=[]
    for q in litpat.finditer(cs,op+1,end):
     text=decode(q[0]);pre=cs[max(op,q.start()-120):q.start()];ctx=re.search(r'(?:C_|NC_)\(\s*"([^"\\]*)"\s*,\s*$',pre)
     if re.search(r'\b(?:C_|NC_)\(\s*$',pre) and re.match(r'\s*,',cs[q.end():end]):continue
     if text and (text in cm[l] or re.search(r'[a-zA-Z]{3}',text)):templates.append(lookup(l,text,ctx[1] if ctx else None))
    if not templates:continue
    main=templates[0]['english']
    # R4-5 direct units are paragraphs; R4-1 static controls are full sentences.
    if category=='R4-5' and len(main)<220:continue
    if category=='R4-1' and not re.search(r'%[-+ #0\d.*$]*[sdfiu]|[.!?]\s*$',main):continue
    n=s.count('\n',0,m.start())+1;en=s.count('\n',0,end)+1
    found.append({'path':path,'line':n,'end_line':en,'function':name,'call':expression,'arguments':splitargs(s[op+1:end-1]),'templates':templates,'snippet':snippet(s,n,en,18)})
   for call in found:
    if calls[l][category] and calls[l][category][-1]['path']==path and calls[l][category][-1]['function']==call['function'] and call['line']-calls[l][category][-1]['end_line']<=8:
     group=calls[l][category][-1];group['calls'].append(call);group['end_line']=call['end_line']
    else:calls[l][category].append({'path':path,'line':call['line'],'end_line':call['end_line'],'function':call['function'],'calls':[call]})

# Vault/Lua environmental announcements: scan actual crawl.mpr consumers,
# independent of map glyph quoting; preserve the complete Lua call and args.
for l in refs:
 for path,s in sorted(source_text[l].items()):
  if not path.endswith('.des') or any(v in path for v in ['/sprint/','/tutorial/','/test/']):continue
  for m in re.finditer(r'crawl\.mpr\s*\(',s):
   line_start=s.rfind('\n',0,m.start())+1
   if s[line_start:m.start()].lstrip().startswith('--'):continue
   op=s.index('(',m.start());end=balanced(s,op)
   if end<=op:continue
   expr=s[m.start():end];aa=splitargs(s[op+1:end-1]);text=None
   if not aa:continue
   first=aa[0]
   tm=re.search(r'crawl\.t_\s*\(',first)
   payload=first[first.index('(',tm.start())+1:balanced(first,first.index('(',tm.start()))-1] if tm else first
   matches=list(litpat.finditer(payload))
   if matches and re.fullmatch(r'[\s.]*',litpat.sub('',payload)):text=''.join(decode(q[0]) for q in matches)
   elif matches:text=decode(matches[0][0])
   if not text or not re.search(r'[A-Za-z]{5}',text):continue
   if re.search(r'Error|debug|[Ii]nvalid|veto|layout_|check_collision|cannot generate',text,re.I):continue
   local=s[max(0,line_start-300):m.start()]
   if re.search(r'if[^\n]*(?:DEBUG_|crawl\.wizard)',local):continue
   n=s.count('\n',0,m.start())+1;en=s.count('\n',0,end)+1;t=lookup(l,text)
   call={'path':path,'line':n,'end_line':en,'function':'environment vault/Lua callback','call':expr,'arguments':aa,'templates':[t],'snippet':snippet(s,n,en,16)}
   calls[l]['R4-6'].append({'path':path,'line':n,'end_line':en,'function':call['function'],'calls':[call]})

pools={c:[] for c in scopes};regressions=[];seen_keys=set();seen_bodies=set()
def excluded(k,en,templates=()):return k.casefold() in exfold or sig(k) in exsig or en.casefold() in exfold or sig(en) in exsig or any(t.casefold() in exfold or sig(t) in exsig for t in templates)
def add(category,key,english,zh,co,assets,kind,generator,extra=None):
 texts=english['stable'] or english['trunk'] or key
 if excluded(key,texts,[t['english'] for l in refs for z in co[l] for t in z.get('templates',[])]):regressions.append({'category':category,'key':key,'reason':'prior key, normalized source template, or repaired key','consumers':{l:[{'path':z['path'],'line':z['line']} for z in co[l]] for l in refs}});return
 if key.casefold() in seen_keys or texts in seen_bodies:excluded_rows.append({'category':category,'key':key,'reason':'global key/body duplicate'});return
 if not co['stable']:unproven.append({'category':category,'key':key,'reason':'no stable production consumer/generator'});return
 seen_keys.add(key.casefold());seen_bodies.add(texts)
 dynamic=kind=='dynamic' and (any(re.search(r'%(?:\d+\$)?[-+ #0\d.*]*[sdifu]|@[^@]+@',t['english']) for z in co['stable'] for t in z.get('templates',[])) or any(z.get('call','').startswith('simple_monster_message') for z in co['stable']) or len(co['stable'])>1)
 high=dynamic or (kind=='textdb' and (len(texts)>=650 or bool(re.search(r'\d|percent|\b(?:half|twice|double|level|turns|damage|resistan|chance)\b',texts,re.I))))
 stat='只在 stable' if not co['trunk'] else '相同' if english['stable']==english['trunk'] and zh['stable']==zh['trunk'] else '分化'
 x={'category':category,'key':key,'kind':kind,'risk_stratum':'high_risk' if high else 'static_control','english':english['stable'],'english_trunk':english['trunk'],'stable_zh':zh['stable'],'trunk_zh':zh['trunk'],'consumers':co,'assets':assets,'parameter_sources':generator,'applicability':stat}
 if extra:x.update(extra)
 pools[category].append(x)

# Concrete name lists for TextDB generators.
def yaml_names(l,folder):
 result={}
 for p in sorted((out/'snapshots'/l/src/'dat'/folder).glob('*.yaml')):
  s=p.read_text();m=re.search(r'^name:\s*[\'"]?([^\n\'"]+)',s,re.M)
  if m:result[m[1].strip().casefold()]={'path':str(p.relative_to(out/'snapshots'/l)),'line':s.count('\n',0,m.start())+1,'statement':m[0]}
 return result
monnames={l:yaml_names(l,'mons') for l in refs}
artnames={}
for l in refs:
 s=read(l,src+'art-data.txt');artnames[l]={m[1].strip().casefold():{'path':src+'art-data.txt','line':s.count('\n',0,m.start())+1,'statement':m[0]} for m in re.finditer(r'^NAME:\s*(.+)$',s,re.M) if 'DUMMY' not in m[1]}

filesets={'R4-1':['items.txt','unrand.txt'],'R4-2':['spells.txt'],'R4-3':['monsters.txt'],'R4-4':['gods.txt'],'R4-5':['hints.txt','tutorial.txt']}
for category,files in filesets.items():
 for f in files:
  paths={l:src+'dat/descript/'+f for l in refs};eng={l:parse(read(l,paths[l])) for l in refs};zhdb={l:parse(read(l,src+'dat/descript/zh/'+f)) for l in refs}
  ef={l:{k.casefold():k for k in eng[l]} for l in refs};zf={l:{k.casefold():k for k in zhdb[l]} for l in refs}
  for identity in sorted(set(ef['stable'])&set(zf['stable'])):
   key=ef['stable'][identity];en={};zh={};co={};assets={};gens={};eligible=True
   for l in refs:
    ek=ef[l].get(identity);zk=zf[l].get(identity);entry=eng[l].get(ek);ze=zhdb[l].get(zk);en[l]=entry['text'] if entry else None;zh[l]=ze['text'] if ze else None;co[l]=[];gens[l]=[]
    assets[l]={'english':{'path':paths[l],**entry} if entry else None,'zh':{'path':src+'dat/descript/zh/'+f,**ze} if ze else None}
    if not entry:continue
    if category=='R4-1':
     proof=artnames[l].get(identity) if f=='unrand.txt' else next((z for z in literals[l].get(identity,[]) if z['path'] in [src+'item-name.cc',src+'item-prop.cc']),None)
     if proof:
      gens[l]=[proof];co[l]=find(l,src+'describe.cc',['getLongDescription(get_unrand_name_en(item))'] if f=='unrand.txt' else ['getLongDescription(db_name)','getLongDescription(en_db_name)'])
    elif category=='R4-2':
     title=re.sub(r' spell$','',ek);proof=next((z for z in literals[l].get(title.casefold(),[]) if z['path']==src+'spl-data.h'),None)
     if proof:gens[l]=[proof];co[l]=find(l,src+'describe.cc',['getLongDescription(string(spell_english_name(spell))'])
    elif category=='R4-3':
     proof=None if identity in ['player ghost','player illusion','serpent of hell'] else monnames[l].get(identity)
     if proof:gens[l]=[proof];co[l]=[z for z in find(l,src+'describe.cc',['getLongDescription(db_name)']) if 'inf.body' in z['statement']]+find(l,src+'describe.cc',['db_name = mi.db_name()','string db_name = mi.db_name()'])
    elif category=='R4-4':
     base=re.sub(r' (?:powers|wrath|extra)$','',ek);proof=next((z for z in literals[l].get(base.casefold(),[]) if re.search(r'god|religion',z['path'])),None)
     if proof:
      gens[l]=[proof];suffix=re.search(r' (powers|wrath|extra)$',ek)
      co[l]=find(l,src+'describe-god.cc',['getLongDescription(string(_god_name_en(which_god)) + "'+' '+suffix[1]+'"'] if suffix else ['getLongDescription(_god_name_en(which_god))'])
    else:
     if len(entry['text'])<220:continue
     proofs=[z for z in literals[l].get(identity,[]) if re.search(r'hints.cc|tutorial|/dat/(des|clua|dlua)',z['path'])]
     if not proofs and re.fullmatch(r'HINT_[A-Z_]+',ek):
      for path in [src+'hints.cc',src+'hints.h']:
       proofs+=find(l,path,[ek])
     if proofs:
      gens[l]=proofs;co[l]=proofs+find(l,src+'hints.cc',['getHintString(key)','getHintString("welcome")'])
   if not co['stable']:unproven.append({'category':category,'key':key,'path':paths['stable'],'reason':'no concrete name/enum plus active production lookup proof (player ghosts/illusions and base Serpent of Hell keys bypass ordinary lookup)'});continue
   if re.fullmatch(r'\s*<[^>]+>\s*',en['stable']):unproven.append({'category':category,'key':key,'reason':'alias-only TextDB body; not counted independently'});continue
   gen={'R4-1':'已鉴定unrand：get_unrand_name_en(item)的canonical NAME；其他物品：item.name(DESC_DBNAME,true,false,false)，ZH失败时临时EN生成fallback键。','R4-2':'spell枚举→spl-data.h英文标题→spell_english_name(spell)+" spell"→getLongDescription。','R4-3':'monster种类→dat/mons/*.yaml name→monster_info.db_name→getLongDescription(db_name)。','R4-4':'god枚举→_god_name_en(which_god)，按基础说明或powers/wrath/extra后缀→getLongDescription。','R4-5':'具体提示键/事件枚举由所列生产调用传入_get_hint/tutorial_msg→getHintString→HintsDB。'}[category]
   add(category,key,en,zh,co,assets,'textdb',gen,{'subcategory':f,'key_generation_evidence':gens})

for category,groups in calls['stable'].items():
 for group in groups:
  texts=list(dict.fromkeys(t['english'] for z in group['calls'] for t in z['templates']));key=texts[0]
  co={'stable':group['calls'],'trunk':[]}
  for tg in calls['trunk'][category]:
   if tg['path']==group['path'] and (tg['function']==group['function'] or tg['function']=='file-scope lambda/table') and set(texts)&{t['english'] for z in tg['calls'] for t in z['templates']}:co['trunk']+=tg['calls']
  if not co['trunk']:
   for tg in calls['trunk'][category]:
    if tg['path']==group['path'] and set(texts)&{t['english'] for z in tg['calls'] for t in z['templates']}:co['trunk']+=tg['calls']
  english={};zh={};assets={}
  for l in refs:
   ts=list({(t['english'],t['zh']):t for z in co[l] for t in z['templates']}.values());english[l]='\n\n'.join(t['english'] for t in ts) if ts else None;zh[l]='\n\n'.join(t['zh'] if t['zh'] is not None else '[此模板无中文catalog条目：'+t['english']+']' for t in ts) if ts else None;assets[l]=ts
  add(category,key,english,zh,co,assets,'dynamic','每个模板的实参原式、DESC_*、条件分支及上下文保存在consumers.arguments/call/snippet；simple_monster_message隐式添加mons.name(descrip)，第三参数true时先apostrophise。',{'family_identity':{'path':group['path'],'function':group['function'],'line':group['line']},'english_templates':texts})

samples=[];selection={};reserves={}
for i,(category,pool) in enumerate(pools.items(),1):
 pool.sort(key=lambda x:(x['key'].casefold(),x['english'] or ''));rng=random.Random(seed+i);chosen=[];backup=[];counts={}
 quotas=[('high_risk',6,4),('static_control',4,1)] if category=='R4-7' else [('high_risk',5,2),('static_control',5,3)] if category=='R4-6' else [('high_risk',5,3),('static_control',5,2)]
 for st,n,b in quotas:
  subset=[x for x in pool if x['risk_stratum']==st];counts[st]=len(subset);assert len(subset)>=n+b,(category,counts)
  rng.shuffle(subset);chosen+=subset[:n];backup+=subset[n:n+b]
 for j,x in enumerate(chosen,1):x=dict(x);x['sample_id']=f'{category}-{j:02}';samples.append(x)
 reserves[category]=[x['key'] for x in backup];selection[category]={'pool_count':len(pool),'strata':counts,'selected':10,'high_risk':quotas[0][1],'static_control':quotas[1][1],'subseed':seed+i,'reserve_count':5}
 dump('pool_'+category+'.json',{'category':category,'subseed':seed+i,'count':len(pool),'candidates':pool})
dump('samples_r4.json',{'seed':seed,'refs':refs,'selection':selection,'samples':samples,'exclusion_provenance':provenance})
dump('selection_log_r4.json',{'seed':seed,'refs':refs,'selection':selection,'merges':merges,'exclusion_provenance':provenance,'excluded_keys':{k:sorted(v) for k,v in sorted(ex.items())},'prior_source_families':[list(x) for x in sorted(prior_sources)],'regression_controls':regressions,'pre_draw_exclusions':excluded_rows,'unproven_or_isolated':unproven,'invalidated':[],'replacements':[],'reserves':reserves})
print(json.dumps({'selection':selection,'sample_count':len(samples),'unproven_or_isolated':len(unproven)},ensure_ascii=False))
subprocess.run(['python3',str(pathlib.Path(__file__).with_name('finish_r4.py')),'--out',str(out)],check=True)
