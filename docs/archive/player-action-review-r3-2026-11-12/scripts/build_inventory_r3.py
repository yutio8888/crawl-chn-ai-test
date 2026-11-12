#!/usr/bin/env python3
"""Read fixed git objects, enumerate bounded output-call clusters, freeze r3 evidence."""
import argparse, pathlib, subprocess, tarfile, io, re, ast, json, random, hashlib, collections
p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--out',required=True);p.add_argument('--previous',required=True);a=p.parse_args();repo=pathlib.Path(a.repo);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
refs={'stable':'4af734c175cee41cfaf75142e04bf1a9aea9ee1c','trunk':'40a7b9976ad10aade1a703e510c68ed0667d3ca5'};seed=2026111203;src='crawl-ref/source/'
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
def dump(name,data):(out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
for l,r in refs.items():
 root=out/'snapshots'/l
 if not (root/src/'AppHdr.h').exists():
  data=git('archive',r,'crawl-ref/source');root.mkdir(parents=True,exist_ok=True)
  with tarfile.open(fileobj=io.BytesIO(data)) as t:t.extractall(root)
def read(l,p):return (out/'snapshots'/l/p).read_text(errors='replace')
def parse(s):
 d={};key=None;body=[];line=0;active=False
 def flush():
  if key is not None:d[key]={'text':'\n'.join(body).strip('\n'),'line':line}
 for n,raw in enumerate(s.splitlines(),1):
  if raw.startswith('#'):continue
  if raw.startswith('%%%%'):flush();key=None;body=[];active=True;continue
  if not active:continue
  if key is None:
   if raw:key=raw;line=n
  else:body.append(raw)
 flush();return d
catalog=src+'dat/i18n/zh/source.txt';cats={l:parse(read(l,catalog)) for l in refs}
def norm(s):return s.replace('\\n','\n').replace('\\t','\t').replace('\\r','\r')
km={l:{norm(k):k for k in cats[l]} for l in refs}
litpat=re.compile(r'"(?:\\.|[^"\\])*"(?:\s*"(?:\\.|[^"\\])*")*')
def decode(s):
 try:return ''.join(ast.literal_eval(x) for x in re.findall(r'"(?:\\.|[^"\\])*"',s))
 except (ValueError,SyntaxError):return ''
def clean(s):
 token=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
 s=token.sub(lambda m:m[0] if m[0].startswith('"') else re.sub(r'[^\n]',' ',m[0]),s)
 # Remove debug-only preprocessor blocks, preserving all line/character positions.
 stack=[];lines=[]
 for line in s.splitlines(keepends=True):
  if re.match(r'\s*#\s*(if|ifdef|ifndef)\b',line):stack.append(bool(re.search(r'DEBUG|WIZARD',line)) or (stack[-1] if stack else False))
  blocked=any(stack)
  if re.match(r'\s*#\s*endif\b',line) and stack:stack.pop()
  lines.append(re.sub(r'[^\n]',' ',line) if blocked else line)
 return ''.join(lines)

def balanced(s,start,open='(',close=')'):
 dep=0;i=start;quote=None
 while i<len(s):
  c=s[i]
  if quote:
   if c=='\\':i+=2;continue
   if c==quote:quote=None
  elif c in '\"\'':quote=c
  elif c==open:dep+=1
  elif c==close:
   dep-=1
   if dep==0:return i+1
  i+=1
 return start

def args(s):
 parts=[];depth=0;quote=None;start=0;i=0
 while i<len(s):
  c=s[i]
  if quote:
   if c=='\\':i+=2;continue
   if c==quote:quote=None
  elif c in '\"\'':quote=c
  elif c in '([{':depth+=1
  elif c in ')]}':depth-=1
  elif c==',' and depth==0:parts.append(s[start:i].strip());start=i+1
  i+=1
 return parts+[s[start:].strip()]

def snippet(s,n,end=None,pad=10):
 ls=s.splitlines();end=end or n;return '\n'.join(f'{i+1}: {ls[i]}' for i in range(max(0,n-pad-1),min(len(ls),end+pad)))
def lookup(l,text,context=None):
 key=(context+'|'+text) if context and (context+'|'+text) in cats[l] else km[l].get(text)
 if key is None:return {'english':text,'key':None,'zh':None,'asset':None}
 x=cats[l][key];return {'english':text,'key':key,'zh':norm(x['text']),'zh_raw':x['text'],'asset':{'path':catalog,'line':x['line']},'trailing_space_english':len(text)-len(text.rstrip(' ')),'trailing_space_zh':len(norm(x['text']))-len(norm(x['text']).rstrip(' '))}

# Freeze external exclusions; only git show is used for repository document content.
inputs=out/'inputs';inputs.mkdir(exist_ok=True);previous=inputs/'samples_r2.json'
if not previous.exists():previous.write_bytes(pathlib.Path(a.previous).read_bytes())
old=inputs/'earlier48.json'
if not old.exists():
 head=git('rev-parse','HEAD').decode().strip();old.write_bytes(git('show',head+':docs/archive/translation-ab-review-2026-11-12/samples_with_identity.json'))
excluded={}
def exwalk(x,why):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in ('key','english','msgid') and isinstance(v,str):excluded[norm(v)]=why
   else:exwalk(v,why)
 elif isinstance(x,list):
  for v in x:exwalk(v,why)
exwalk(json.loads(previous.read_text())['samples'],'r2 80');exwalk(json.loads(old.read_text())['samples'],'earlier 48')
scopes={'A':['movement.cc','stairs.cc','travel.cc'],'B':['melee-attack.cc','ranged-attack.cc','throw.cc','beam.cc'],'C':['items.cc','item-use.cc','player-equip.cc'],'D':['potion.cc','evoke.cc','item-use.cc'],'E':['spl-cast.cc','ability.cc'],'F':['delay.cc','player.cc','player-reacts.cc']}
# Identify ordinary file-level function starts; C++ class methods included.
funcpat=re.compile(r'(?m)^(?:[\w:<>,*&]+[ \t]+)+([\w:~]+)\s*\([^;{}]*\)(?:\s*const)?\s*\n\{')
callpat=re.compile(r'\b(mpr\w*|yesno\w*|simple_monster_message|canned_msg)\s*\(')
allcalls={l:{} for l in refs};functions={l:{} for l in refs}
for l in refs:
 for f in sorted(set(sum(scopes.values(),[]))):
  path=src+f;s=read(l,path);cs=clean(s);fs=[]
  for m in funcpat.finditer(cs):
   b=cs.index('{',m.start());end=balanced(cs,b,'{','}');fs.append({'name':m[1],'start':m.start(),'end':end,'line':s.count('\n',0,m.start())+1,'body':s[m.start():end]})
  functions[l][path]=fs;calls=[]
  for m in callpat.finditer(cs):
   op=cs.index('(',m.start());end=balanced(cs,op)
   if end<=op:continue
   fn=next((fn for fn in fs if fn['start']<=m.start()<fn['end']),None)
   if not fn or any(w in fn['name'].lower() for w in ['debug','wizard','test_']):continue
   literal=[]
   for q in litpat.finditer(cs,op+1,end):
    text=decode(q[0]);context=None;pre=cs[max(op,q.start()-120):q.start()]
    # C_(context,text): the second literal belongs to the context catalog key.
    ctx=re.search(r'C_\(\s*"([^"\\]*)"\s*,\s*$',pre)
    if ctx:context=ctx[1]
    if re.search(r'\b(?:C_|NC_)\(\s*$',pre) and re.match(r'\s*,',cs[q.end():end]):continue
    if text:literal.append(lookup(l,text,context))
   if not literal:continue
   # Exclude context identifiers and pure format-only forwarding wrappers.
   literal=[x for x in literal if x['key'] is not None or re.search(r'[A-Za-z]{3}',x['english'])]
   if not literal:continue
   if 'MSGCH_ERROR' in s[op:end] or any(re.search(r'Lua error|Lua not initialised|ch_force_autopickup failed|Invalid spell|not a player castable|item has been removed|the spell.*is gone|buggy spell',x['english'],re.I) for x in literal):continue
   n=s.count('\n',0,m.start())+1;en=s.count('\n',0,end)+1;expression=s[m.start():end]
   calls.append({'path':path,'line':n,'end_line':en,'function':fn['name'],'call':expression,'arguments':args(s[op+1:end-1]),'templates_and_fragments':literal,'snippet':snippet(s,n,en),'function_line':fn['line'],'local_parameter_context':snippet(s,n,en,25)})
  allcalls[l][path]=calls

# Dynamic high-risk and common-action static strata. Reject whole clusters on exclusions.
pools={c:[] for c in scopes};regression=[];rejects=[];seen=set()
for c,files in scopes.items():
 for f in files:
  path=src+f;calls=allcalls['stable'][path];clusters=[]
  for call in calls:
   name=call['function'].lower()
   # item-use.cc is shared: quaff/read/zap to D; all other equip/wield calls to C.
   if f=='item-use.cc':
    is_d=bool(re.search(r'quaff|potion|scroll|read|wand|zap|evok',name))
    if (c=='D')!=is_d:continue
   if c=='F' and f=='delay.cc' and not re.search(r'rest|run|recover|wait',name):continue
   if c=='B' and not (re.search(r'player|throw|shoot|fire|ranged_attack::|melee_attack::',name) or re.search(r'attacker->is_player|agent.*is_player|you\.',call['local_parameter_context'])):continue
   if c=='F' and f=='player.cc' and not re.search(r'rest|heal|hunger|hp|mp|confus|poison|slow|haste|dur|drain|disease|paraly|rot|stat|magic|burn|banish|torment',name):continue
   if clusters and clusters[-1][-1]['function']==call['function'] and call['line']-clusters[-1][-1]['end_line']<=8:clusters[-1].append(call)
   else:clusters.append([call])
  for cluster in clusters:
   texts=list(dict.fromkeys(x['english'] for call in cluster for x in call['templates_and_fragments']));keys=[x['key'] for call in cluster for x in call['templates_and_fragments'] if x['key']]
   overlap=[t for t in texts if t in excluded]+[k for k in keys if norm(k) in excluded]
   identity=(path,cluster[0]['function'],tuple(texts))
   if identity in seen:continue
   seen.add(identity)
   if overlap:
    regression.append({'category':c,'path':path,'function':cluster[0]['function'],'line':cluster[0]['line'],'excluded_keys':sorted(set(overlap)),'reason':'previous sample overlap; whole family excluded'});continue
   if not any(re.search(r'[A-Za-z]{3}',t) for t in texts):continue
   dynamic=any(re.search(r'%(?:\d+\$)?[-+ #0\d.*]*[sdifu]|@[^@]+@',t) for t in texts)
   # Format arguments beyond message-channel and template, or text concatenation.
   dynamic=dynamic or any(' + ' in call['call'] or call['call'].startswith('simple_monster_message') for call in cluster)
   co={'stable':cluster,'trunk':[]}
   # Match each complete template in the same source function, allowing branch regrouping.
   for tc in allcalls['trunk'][path]:
    if tc['function']==cluster[0]['function'] and set(texts)&{x['english'] for x in tc['templates_and_fragments']}:co['trunk'].append(tc)
   # Exact-key fallback handles production function renames/moves in the same file.
   if not co['trunk']:
    co['trunk']=[tc for tc in allcalls['trunk'][path] if set(texts)&{t['english'] for t in tc['templates_and_fragments']}]
   # Source-confirmed template changes in equivalent production consumers.
   alias_stems={'You %s towards %s!':'You %s towards %s%s!', '%s %s shatters into small pieces.':'shatters into small pieces.', "%s's hold on you weakens, but your attempt to escape fails.":'hold on you weakens, but your attempt to escape fails.'}
   for old,new in alias_stems.items():
    if old in texts:
     for tc in allcalls['trunk'][path]:
      if any(new in t['english'] for t in tc['templates_and_fragments']) and tc not in co['trunk']:co['trunk'].append(tc)
   x={'category':c,'family_identity':{'path':path,'function':cluster[0]['function'],'first_line':cluster[0]['line']},'stratum':'high_risk' if dynamic else 'common_static','calls':co,'english_templates':texts,'scope_reason':'Scoped production output in a player action / combat feedback / state update consumer; full branch/function evidence retained.','branch_evidence':{l:[{'path':v['path'],'line':v['line'],'code':v['local_parameter_context']} for v in co[l]] for l in refs}}
   pools[c].append(x)

# Exact template-group aliases count once, retaining all consumers.
for c,pool in pools.items():
 merged={}
 for x in pool:
  ident=tuple(x['english_templates'])
  if ident not in merged:merged[ident]=x
  else:
   target=merged[ident]
   for l in refs:
    target['calls'][l].extend(v for v in x['calls'][l] if (v['path'],v['line']) not in {(z['path'],z['line']) for z in target['calls'][l]})
    target['branch_evidence'][l].extend(x['branch_evidence'][l])
 pools[c]=list(merged.values())
selected=[];selection={}
for i,(c,pool) in enumerate(pools.items(),1):
 pool.sort(key=lambda x:(x['family_identity']['path'],x['family_identity']['first_line']))
 rng=random.Random(seed+i);chosen=[];counts={}
 for st in ['high_risk','common_static']:
  subset=[x for x in pool if x['stratum']==st];counts[st]=len(subset);assert len(subset)>=6,(c,counts)
  rng.shuffle(subset);chosen+=subset[:6]
 selection[c]={'subseed':seed+i,'pool_count':len(pool),'strata_counts':counts,'selected_high_risk':6,'selected_common_static':6}
 for n,x in enumerate(chosen,1):x['family_id']=f'{c}-{n:02}';selected.append(x)
 dump('pool_'+c+'.json',{'seed':seed+i,'count':len(pool),'families':pool})

# Conservative source-only reconstruction. Unsupported value generators are explicitly runtime-needed.
def reconstruction(call,l):
 result=[]
 for t in call['templates_and_fragments']:
  en=t['english'];zh=t['zh'];formats=list(re.finditer(r'%(?:\d+\$)?[-+ #0\d.*]*[sdifu]',en))
  if zh is not None and not formats and not re.search('@[^@]+@',en) and not call['call'].startswith('simple_monster_message'):
   kind='静态模板，无参数';complete=zh
   if re.search(r'\+|\bformat|make_stringf',call['call']) and len(call['templates_and_fragments'])>1:kind='需要运行时输出才能确定的';complete=None
   result.append({'english':en,'zh_template':zh,'method':kind,'full_zh_display':complete,'source_call':{'path':call['path'],'line':call['line']},'parameters':call['arguments'],'conditions':call['local_parameter_context'],'note':'完整调用及其外部格式化/拼接若存在，以代码为准；模板本身不等同完整渲染。' if complete is None else '按catalog原样展开\\n/\\t，保留空格与标点。'});continue
  result.append({'english':en,'zh_template':zh,'method':'需要运行时输出才能确定的','full_zh_display':None,'parameters':call['arguments'],'parameter_sources':call['local_parameter_context'],'source_call':{'path':call['path'],'line':call['line']},'conditions':call['local_parameter_context'],'reason':'源码调用和局部赋值/条件完整保留；尚未为此实参生成器建立可执行状态，不能把任意中文名称当作实际显示。'})
 return result

def finish(x):
 x['catalog_entries']={l:[t for call in x['calls'][l] for t in call['templates_and_fragments']] for l in refs};x['reconstructions']={l:[r for call in x['calls'][l] for r in reconstruction(call,l)] for l in refs}
 st=sorted(set((t['english'],t['zh']) for t in x['catalog_entries']['stable']),key=str);tr=sorted(set((t['english'],t['zh']) for t in x['catalog_entries']['trunk']),key=str)
 x['applicability']='只在 stable' if not x['calls']['trunk'] else '只在 trunk' if not x['calls']['stable'] else '相同' if st==tr else '分化'
for x in selected:finish(x)

# Directed inventory: every catalog key with an English word 'here' and every C++ literal consumer.
here={};directsites={l:collections.defaultdict(list) for l in refs}
for l in refs:
 for path in sorted((out/'snapshots'/l/src).rglob('*')):
  if path.suffix not in ('.cc','.h','.lua','.des') or re.search(r'wiz-|debug|test|/util/|/catch2',str(path)):continue
  rel=str(path.relative_to(out/'snapshots'/l))
  if '/dat/' in rel and not any(part in rel for part in ['/dat/des/','/dat/clua/','/dat/dlua/','/dat/lua/']):continue
  rel=rel;s=path.read_text(errors='replace');cs=clean(s)
  for m in litpat.finditer(cs):
   text=decode(m[0])
   if not re.search(r'\bhere\b',text,re.I):continue
   pre=cs[max(0,m.start()-120):m.start()]
   if not re.search(r'\b(T_|C_|N_|t_|mpr\w*|yesno\w*|formatted_string|make_stringf)\s*\([^;{}]*$',pre) and text not in km[l]:continue
   if re.search(r'Error:|debug|wizard',text,re.I):continue
   n=s.count('\n',0,m.start())+1;start=max(s.rfind(';',0,m.start()),s.rfind('{',0,m.start()),s.rfind('}',0,m.start()))+1;end=s.find(';',m.end());end=end+1 if end>=0 else m.end();expr=s[start:end]
   if path.suffix in ('.des','.lua'):
    start=s.rfind('\n',0,m.start())+1;end=s.find('\n',m.end());end=end if end>=0 else m.end();expr=s[start:end]
   ctxmatch=re.search(r'(?:C_|NC_)\(\s*"([^"\\]*)"\s*,\s*$',pre)
   t=lookup(l,text,ctxmatch[1] if ctxmatch else None);key=t['key'] or text;here.setdefault(text,key)
   directsites[l][text].append({'path':rel,'line':n,'end_line':s.count('\n',0,end)+1,'function':'directed consumer; function/branch in code','call':expr,'arguments':[expr.strip()],'templates_and_fragments':[t],'snippet':snippet(s,n,s.count('\n',0,end)+1),'local_parameter_context':snippet(s,n,s.count('\n',0,end)+1,22)})
# Vault DSL and Lua may contain map glyphs / long strings that are not C++
# tokens. Locate their exact catalog literal keys independently, without
# allowing an unmatched quote in map text to hide later production callbacks.
for l in refs:
 for path in sorted((out/'snapshots'/l/src/'dat').rglob('*')):
  if path.suffix not in ('.lua','.des') or '/test' in str(path):continue
  rel=str(path.relative_to(out/'snapshots'/l));s=path.read_text(errors='replace')
  for text,key in km[l].items():
   if not re.search(r'\bhere\b',text,re.I):continue
   escaped=text.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
   for m in re.finditer(re.escape('"'+escaped+'"'),s):
    n=s.count('\n',0,m.start())+1
    if any(z['path']==rel and z['line']==n for z in directsites[l].get(text,[])):continue
    begin=s.rfind('\n',0,m.start())+1;end=s.find('\n',m.end());end=end if end>=0 else m.end();line=s[begin:end]
    if line.lstrip().startswith(('--','#')):continue
    here.setdefault(text,key);t=lookup(l,text)
    directsites[l][text].append({'path':rel,'line':n,'end_line':n,'function':'Lua/vault callback or message table (see code)','call':line,'arguments':[line.strip()],'templates_and_fragments':[t],'snippet':snippet(s,n),'local_parameter_context':snippet(s,n,pad=22)})
# Recover literal-only Lua concatenation passed to crawl.t_.
for l in refs:
 for path in sorted((out/'snapshots'/l/src/'dat').rglob('*')):
  if path.suffix not in ('.lua','.des') or '/test' in str(path):continue
  rel=str(path.relative_to(out/'snapshots'/l));s=path.read_text(errors='replace')
  for callmatch in re.finditer(r'crawl\.t_\s*\(',s):
   op=s.index('(',callmatch.start());end=balanced(s,op);inner=s[op+1:end-1]
   tokens=list(litpat.finditer(inner))
   if not tokens or not re.fullmatch(r'[\s.]*',litpat.sub('',inner)):continue
   text=''.join(decode(m[0]) for m in tokens)
   if not re.search(r'\bhere\b',text,re.I) or len(tokens)<2:continue
   n=s.count('\n',0,callmatch.start())+1;en=s.count('\n',0,end)+1;t=lookup(l,text);key=t['key'] or text
   for fragment in list(here):
    if fragment!=text:
     directsites[l][fragment]=[z for z in directsites[l].get(fragment,[]) if not (z['path']==rel and z['line']==n)]
   here[text]=key
   directsites[l][text].append({'path':rel,'line':n,'end_line':en,'function':'Lua literal concatenation in crawl.t_ / crawl.mpr','call':s[callmatch.start():end],'arguments':[inner],'templates_and_fragments':[t],'snippet':snippet(s,n,en),'local_parameter_context':snippet(s,n,en,22)})
here={text:key for text,key in here.items() if any(directsites[l].get(text) for l in refs)}
directed=[]
for n,text in enumerate(sorted(here),1):
 key=here[text];co={l:directsites[l].get(text,[]) for l in refs};paths=' '.join(z['path'] for l in refs for z in co[l]);lower=text.lower()
 if 'you see here' in lower:use='脚下单个物品';role='普通提示'
 elif any(w in lower for w in ['items here','things that are here','many items here']):use='脚下多个物品／物品列表';role='列表或枚举标题' if ':' in text else '普通提示'
 elif re.search(r'there is .*here',lower):use='地形或特征';role='普通提示'
 elif 'travel.cc' in paths:use='自动探索或旅行';role='普通提示'
 else:use='其他相近用途';role='列表或枚举标题' if text.rstrip().endswith(':') else '普通提示'
 x={'family_id':f'D-HERE-{n:02}','category':'directed','use_group':use,'presentation_role':role,'role_reason':'含冒号的列表引导文字，后续枚举见调用代码。' if role=='列表或枚举标题' else '随动作、位置查看或反馈输出的提示；场景与条件见消费者代码。','english_templates':[text],'calls':co,'regression_control':text in excluded,'excluded_random_reason':excluded.get(text),'key':key};finish(x);directed.append(x)

# Freeze now; enrich_reconstruction_r3.py adds only source-backed concrete examples.
data={'seed':seed,'refs':refs,'selection':selection,'families':selected,'directed':directed,'exclusion_inputs_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs.glob('*.json')},'regression_controls':regression,'method':'function-local output-call clusters with gaps <=8 source lines, containing all directly literal templates/conditionals in each selected cluster; variable-only output calls outside these clusters remain uncovered'}
dump('families_r3.json',data);dump('selection_log_r3.json',{'selection':selection,'regression_controls':regression,'invalidated':[],'replacements':[]})
print(json.dumps({'selection':selection,'selected':len(selected),'directed':len(directed)},ensure_ascii=False))
subprocess.run(['python3',str(pathlib.Path(__file__).with_name('enrich_r3.py')),'--out',str(out)],check=True)
subprocess.run(['python3',str(pathlib.Path(__file__).with_name('render_r3.py')),'--out',str(out)],check=True)
