#!/usr/bin/env python3
"""Source-only sentence examples; no translation quality decisions."""
import argparse,json,pathlib,re,itertools,collections
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=pathlib.Path(a.out);data=json.loads((out/'families_r3.json').read_text());src='crawl-ref/source/'
def read(l,f):return (out/'snapshots'/l/src/f).read_text()
def parse(s):
 d={};key=None;body=[];ln=0
 def flush():
  if key is not None:d[key]={'text':'\n'.join(body).strip('\n'),'line':ln}
 for n,line in enumerate(s.splitlines(),1):
  if line.startswith('#'):continue
  if line.startswith('%%%%'):flush();key=None;body=[];continue
  if key is None:
   if line:key=line;ln=n
  else:body.append(line)
 flush();return d
cats={l:parse(read(l,'dat/i18n/zh/source.txt')) for l in data['refs']}
def norm(s):return s.replace('\\n','\n').replace('\\t','\t')
def tr(l,k):
 actual=k if k in cats[l] else next((q for q in cats[l] if norm(q)==k),None)
 return norm(cats[l][actual]['text']) if actual is not None else None
def asset(l,k):return {'path':src+'dat/i18n/zh/source.txt','line':cats[l][k]['line'],'key':k,'zh':tr(l,k)} if k in cats[l] else {'key':k,'zh':None}
def ev(l,f,needle,pad=8):
 s=read(l,f);ls=s.splitlines();r=[]
 for i,line in enumerate(ls):
  if needle in line:r.append({'path':src+f,'line':i+1,'code':'\n'.join(f'{j+1}: {ls[j]}' for j in range(max(0,i-pad),min(len(ls),i+pad+1)))})
 return r
fmtpat=re.compile(r'%(?:(\d+)\$)?[-+ #0\d.*]*([sdifu])')
def fmt(s,values):
 i=0
 def sub(m):
  nonlocal i
  index=int(m[1])-1 if m[1] else i
  if not m[1]:i+=1
  return str(values[index])
 return fmtpat.sub(sub,s).replace('%%','%')

def sample_name(l,expr):
 if 'ancestor->' in expr:return []
 if 'DESC_ITS' in expr:return [(fmt(tr(l,"%s's"),[tr(l,'orc')]),'可见兽人；DESC_ITS 经 apostrophise(name)，使用 %s\'s 的中文模板。')]
 if 'DESC_YOUR' in expr:return [((tr(l,'your ') or '')+(tr(l,'dagger') or ''),'物品匕首；DESC_YOUR 在 name_aux 前加 T_("your ")；铭文、附魔等额外后缀关闭。')]
 if re.search(r'(mon|victim|attacker|defender|ancestor|target|targ).*name\(',expr) or 'defender_name(' in expr or 'targ_name' in expr:return [(tr(l,'orc'),'示例状态：可见普通兽人，名称来自 catalog orc；DESC_A/DESC_THE 的中文冠词规则及不可见分支见源代码。')]
 return []

def choices(l,expr,context):
 # Actual expressions rather than guessed surface labels.
 if expr.strip() in ('""',"''"):return [('', '空字符串分支')]
 if re.search(r'\?\s*T_\("',expr) or ('?' in expr and ': ' in expr):
  lits=re.findall(r'T_\("((?:\\.|[^"\\])*)"\)|(?<![\w])"((?:\\.|[^"\\])*)"',expr);vals=[]
  for wrapped,raw in lits:
   k=wrapped if wrapped else raw;v=tr(l,k) if wrapped else norm(k)
   if v is not None:vals.append((v,'按实参三元条件分支选择：'+expr))
  if vals:return list(dict.fromkeys(vals))
 if 'innate_stat(' in expr:return [(10,'示例玩家基础属性为10；实参原式 '+expr)]
 if 'hand_name(' in expr:
  k='hands' if 'true' in expr else 'hand';v=tr(l,k)
  return [(v,'示例为有普通手部的角色；you.hand_name('+('true' if k=='hands' else 'false')+')；其余种族/变形需运行时。')] if v else []
 if 'attack_strength_punctuation' in expr:return [(tr(l,'.'),'dmg < HIT_WEAK'),(tr(l,'!'),'HIT_WEAK <= dmg < HIT_MED'),((tr(l,'!') or '')*2,'HIT_MED <= dmg < HIT_STRONG')]
 if 'spell_title(' in expr:
  k='Searing Ray' if 'Without enough magic' in context else 'Magic Dart'
  v=tr(l,k);return [(v,'示例法术 '+k+'；从对应catalog取真实名称；持续引导分支使用可引导的灼热射线。')] if v else []
 if 'held_status()' in expr:
  vals=[]
  for k in ['held in a net','stuck in a web']:
   if tr(l,k):vals.append((tr(l,k),'held_status 的网/蛛网状态分支，英文键 '+k))
  return vals
 if 'runmode_name()' in expr:
  vals=[]
  for k in ['explore','travel','run','rest']:
   if tr(l,k):vals.append((tr(l,k),'runmode_name 的运行模式；英文键 '+k))
  return vals
 if expr.strip()=='adj' and 'You feel %s sick.' in context:
  return [('', 'dmg<=2'),(tr(l,'very '),'2<dmg<=6'),(tr(l,'extremely '),'dmg>6')]
 if 'feature_description_at(' in expr:return [(tr(l,'closed door'),'示例目标格是关闭的门；DESC_THE的中文冠词省略，特征名来自catalog closed door。')]
 if 'potion.name(DESC_QUALNAME)' in expr:
  k='curing';v=tr(l,k)
  if v and tr(l,'potion'):return [(v+tr(l,'potion'),'示例已鉴定治疗药水；ZH name_aux=type_name+potion，article_a在ZH直接返回name。')]
 name=[] if 'MONS_MUTANT_BEAST' in context else sample_name(l,expr)
 if name and name[0][0] is not None:return name
 return []

# Capture all assignments to variables passed at each selected call, not only its immediate snippet.
for x in data['families']:
 x['parameter_generation_evidence']={};x['source_function_evidence']={}
 for l in data['refs']:
  x['parameter_generation_evidence'][l]=[];x['source_function_evidence'][l]=[]
  for call in x['calls'][l]:
   path=call['path'];s=read(l,path.removeprefix(src));ls=s.splitlines()
   variables=set(re.findall(r'\b([a-zA-Z_]\w*)\b',','.join(call['arguments'][1:])))
   for i,line in enumerate(ls):
    if any(re.search(r'\b'+re.escape(v)+r'\b\s*(?:=|\[)',line) for v in variables if len(v)>2 and v not in ['true','false','c_str','DESC_THE','DESC_A']):
     # Only retain local-to-call assignments to avoid confusing another function's same local.
     if abs(i+1-call['line'])<=90:x['parameter_generation_evidence'][l].append({'path':path,'line':i+1,'code':'\n'.join(f'{j+1}: {ls[j]}' for j in range(max(0,i-5),min(len(ls),i+8)))})
  for r in x['reconstructions'][l]:
   call=next((c for c in x['calls'][l] if c['path']==r['source_call']['path'] and c['line']==r['source_call']['line']),None)
   if not call:continue
   en=r['english'];zh=r['zh_template']
   if call['call'].startswith('simple_monster_message') and zh is not None:
    name=tr(l,'orc') or ''
    poss=len(call['arguments'])>2 and call['arguments'][2].strip()=='true'
    if poss:name=fmt(tr(l,"%s's"),[name])
    r.update({'method':'参数文本还原','full_zh_display':name+zh,'example_state':'可见普通兽人；simple_monster_message默认DESC_THE；第三参数true时先apostrophise再拼接。','reconstruction_method':'catalog orc 的名称 + 当前片段；未运行游戏。','name_asset':asset(l,'orc')});continue
   if zh is None or not fmtpat.search(en):continue
   # Identify the output template argument, then its following format values.
   aa=call['arguments'];idx=next((i for i,arg in enumerate(aa) if '"'+en.split('\n')[0][:15] in arg or (re.search(r'T_\(',arg) and any(t['english']==en for t in call['templates_and_fragments']))),None)
   if idx is None:continue
   actual=aa[idx+1:]
   count=max([int(m[1]) for m in fmtpat.finditer(en) if m[1]] or [len(list(fmtpat.finditer(en)))])
   if len(actual)!=count:continue
   opts=[choices(l,e,call['local_parameter_context']) for e in actual]
   if not all(opts):
    r['resolved_parameter_examples']=[{'source_expression':e,'examples':v} for e,v in zip(actual,opts)];continue
   examples=[]
   for combo in itertools.islice(itertools.product(*opts),32):
    vals=[v[0] for v in combo]
    try:sentence=fmt(zh,vals)
    except (IndexError,TypeError):continue
    examples.append({'parameters':[{'source_expression':e,'value':v[0],'state_and_source':v[1]} for e,v in zip(actual,combo)],'full_zh_display':sentence})
   if examples:r.update({'method':'参数文本还原','full_zh_display':examples[0]['full_zh_display'],'branch_examples':examples,'reconstruction_method':'按所列示例状态从catalog取参数，按原模板位置替换；保留模板标点和空格；不声称实际运行或自动化断言覆盖。'})

# A static fragment nested inside a formatted call is not a complete
# static sentence. Preserve its catalog value but defer the full rendering.
for x in data['families']+data['directed']:
 for l in data['refs']:
  for r in x['reconstructions'][l]:
   if r['method']!='静态模板，无参数':continue
   call=next((c for c in x['calls'][l] if c['path']==r['source_call']['path'] and c['line']==r['source_call']['line']),None)
   if call and any(fmtpat.search(t['english']) for t in call['templates_and_fragments']):
    r.update({'method':'需要运行时输出才能确定的','full_zh_display':None,'fragment_zh':r['zh_template'],'reason':'这是同一动态格式调用中的条件片段/参数，而非独立输出句；完整格式调用与分支见源码。'})
# The attunement family has identical catalogs but different parameter
# producers: stable uses raw "amulet"; trunk translates that slot name.
for x in data['families']:
 if x['family_identity']['function']=='_maybe_attune_regen_items':
  x['applicability']='分化'
  x['parameter_semantics_difference']='stable eq_list在SLOT_AMULET分支使用裸字符串amulet；trunk使用T_(amulet)。分隔符与动词参数生产代码也有差异，见参数证据。'
  for l in data['refs']:
   for r in x['reconstructions'][l]:
    if r['english']!='Your %1$s attune%2$s to your body, and you begin to %3$s.':continue
    eq='amulet' if l=='stable' else tr(l,'amulet');examples=[]
    for suffix,state in [('', '单个普通再生护符、gained_regen=true且gained_mana_regen=false'),(tr(l,' magic'),'单个普通法力再生护符、gained_regen=false且gained_mana_regen=true')]:
     msg=fmt(tr(l,'regenerate%s more quickly'),[suffix]);vals=[eq,'attunes itself' if l=='stable' else 's itself',msg]
     examples.append({'parameters':vals,'state':state,'full_zh_display':fmt(r['zh_template'],vals),'source':'eq_list的SLOT_AMULET分支；msgs使用regenerate%s more quickly；中文模板不引用%2$s。'})
    r.update({'method':'参数文本还原','full_zh_display':examples[0]['full_zh_display'],'branch_examples':examples,'remaining_runtime_branches':'多装备列表、artefact专名、化学护符及多个恢复效果组合仍需具体运行时状态。','reconstruction_method':'严格保留源参数；stable中裸amulet不自行翻译，trunk经T_查catalog。'})
# Add the prefix dependencies and full sentence variants for the reported floor scenes.
for x in data['directed']:
 text=x['english_templates'][0];x['directed_examples']={};x['parameter_generation_evidence']={}
 for l in data['refs']:
  if not x['calls'][l]:continue
  examples=[];dep=[]
  potion=(tr(l,'curing') or '')+(tr(l,'potion') or '')
  dagger=tr(l,'dagger') or '';stack='2 '+potion
  # These are literal source naming rules; no invented classifier "一把"/"两瓶".
  name_examples=[(potion,'quantity=1；已鉴定治疗药水；DESC_A，ZH省略a/an。'),(stack,'quantity=2；同一堆已鉴定治疗药水；name() 实际添加数字2及一个ASCII空格，不调用number_in_words。'),(dagger,'quantity=1；匕首；不显示附魔/铭文/品牌的示例name_aux。DESC_A 在ZH不自动添加“一把”。')]
  if text in ('You see here ','You see here %s.'):
   for name,state in name_examples:
    sentence=(tr(l,'You see here ') or '')+name+(tr(l,'.') or '') if text.endswith(' ') else fmt(tr(l,text) or text,[name])
    examples.append({'method':'参数文本还原','state':state,'parameter':name,'full_zh_display':sentence,'formula':'T_(You see here +尾空格) + item.name(DESC_A) + T_(.)' if text.endswith(' ') else 'T_(You see here %s.) % item.name(DESC_A)'})
   x['use_group']='脚下单个物品／单个堆叠';x['presentation_role']='普通提示';x['role_reason']='item_check 单栈分支或原地鉴定后直接报告一个物品全名；并非列表标题。'
  elif text in ('Items here: %s.','Things that are here:'):
   sep=tr(l,'; ') or '; ';listing=stack+sep+dagger
   if text.startswith('Items'):
    sentence=fmt(tr(l,text) or text,['<darkgrey>! )</darkgrey>']);formula='item_message摘要分支输出物品glyph而非物品全名；示例使用默认glyph !（药水）和 )（武器）、两堆均specialness=0，按glyph排序并由空格隔开；颜色/用户glyph设置可能改变运行时输出。'
   else:sentence=(tr(l,text) or text)+'\n'+listing;formula='列表标题单独mpr_nojoin；后续mprf_nocap输出item_message的名称列表，以T_(; )连接；具体屏幕折行由窗口宽度决定。例句略去菜单颜色标签。'
   examples.append({'method':'参数文本还原','state':'两个不同物品堆：2个治疗药水及1把匕首；名称表面按源码生成，不人为加量词。','full_zh_display':sentence,'formula':formula})
   x['use_group']='脚下多个物品／物品列表';x['presentation_role']='列表或枚举标题' if text.startswith('Things') else '列表摘要提示';x['role_reason']='根据 items.size、item_stack_summary_minimum、msgwin_lines 分流；Things...引导后续列表，Items...同行携带列表摘要。'
  elif text=='%s%s here.':
   for prefix_key,feat_key in [('There is ','closed door')]:
    pref=tr(l,prefix_key);feat=tr(l,feat_key)
    if pref is not None and feat is not None:examples.append({'method':'参数文本还原','branch':prefix_key,'parameters':[pref,feat],'full_zh_display':fmt(tr(l,text) or text,[pref,feat]),'formula':'describe_floor switch(grid) 选择prefix；feature_description_at(you.pos(),true,DESC_A)→feat；输出T_(%s%s here.)。'})
   dep=[asset(l,k) for k in ['There is ','There is an entrance to ',text,'closed door','shop']];x['unresolved_branches']={'shop':{'method':'需要运行时输出才能确定的','parameter_source':'feature_description_at(...,DESC_A)中的商店专有名称；prefix=T_(There is an entrance to )；需具体商店状态。'}};x['use_group']='地形或特征';x['presentation_role']='普通提示';x['role_reason']='describe_floor报告脚下非水/岩浆特征；商店与其他地形为switch条件分支，不是列表标题。'
  elif text in ('There is %s here.','There is an entrance to %s here.'):
   feat=tr(l,'closed door') if text=='There is %s here.' else None
   if feat is not None:examples.append({'method':'参数文本还原','parameter':feat,'full_zh_display':fmt(tr(l,text) or text,[feat]),'formula':'trunk describe_floor 依据DNGN_ENTER_SHOP选择完整模板；feat=feature_description_at(...,DESC_A)。'})
   x['use_group']='地形或特征';x['role_reason']='describe_floor的商店入口／其他地形报告分支。'
  elif text=='<cyan>Item%1$s here:</cyan> %2$s.':
   for suff,name in [('',potion),('s',stack+(tr(l,'; ') or '; ')+dagger)]:examples.append({'method':'参数文本还原','parameters':[suff,name],'full_zh_display':fmt(tr(l,text) or text,[suff,name]),'formula':'cell_items_description：s后缀由items.size()>1决定，中文模板如不引用%1$s则保留源码参数但不输出；item_message提供%2$s。'})
   x['use_group']='目标格物品列表';x['presentation_role']='列表摘要提示';x['role_reason']='方向选择器/悬浮信息中列出目标格物品，未必是玩家脚下。'
  elif text in ('<cyan>Here:</cyan>','<cyan>Here:</cyan> %s','<cyan>Here:</cyan> %s\n'):
   name=tr(l,'closed door') if text=='<cyan>Here:</cyan>' else tr(l,'orc') or ''
   sentence=(tr(l,text) or text)+' '+name if '%s' not in text else fmt(tr(l,text) or text,[name])
   examples.append({'method':'参数文本还原','parameter':name,'full_zh_display':sentence,'formula':'get_square_desc中怪物描述或地形描述的标题；无参Here标题后接地形描述；有参Here模板例示可见普通兽人。更多形容词由cell_monster_description生成。'})
   x['use_group']='目标格描述标题';x['presentation_role']='列表或枚举标题';x['role_reason']='get_square_desc/悬浮描述组合怪物、物品、地形和云；用于引导目标格描述。'
  if examples:
   x['directed_examples'][l]=examples
   x['parameter_generation_evidence'][l]=dep+[asset(l,k) for k in ['curing','potion','dagger','; ','your ','.']]+ev(l,'item-name.cc','string item_def::name(',6)+ev(l,'item-name.cc','// EN only: articles (a/an)',7)+ev(l,'item-name.cc','buff << quantity <<',5)+ev(l,'item-name.cc','potion_type_name(item_typ) << T_("potion")',5)
  if text=='%s%s here.':
   x['parameter_generation_evidence'][l]+=ev(l,'directn.cc','void describe_floor()',40)
# Shared generators needed to interpret names, possessives, articles,
# punctuation and implicit monster-message prefixes.
data['shared_generator_evidence']={}
for l in data['refs']:
 data['shared_generator_evidence'][l]={
  'possessive':ev(l,'english.cc','string apostrophise(',12)+ev(l,'mon-info.cc','if (desc == DESC_ITS)',5),
  'articles_and_quantity':ev(l,'english.cc','string article_a(',8)+ev(l,'item-name.cc','// EN only: articles (a/an)',9)+ev(l,'item-name.cc','buff << quantity <<',6),
  'implicit_monster_prefix':ev(l,'message.cc','bool simple_monster_message(',24),
  'damage_punctuation':ev(l,'attack.cc','string attack_strength_punctuation(',14),
  'runmode_and_held':ev(l,'travel.cc','string runrest::runmode_name()',20)+ev(l,'traps.cc','const char* held_status(',10)}
# List catalog-only here keys as an explicit dead/unresolved audit, rather than silently treating them as live.
live={norm(x['key']) for x in data['directed']};data['here_catalog_without_direct_consumer']={l:[{'key':k,**v} for k,v in cats[l].items() if re.search(r'\bhere\b',norm(k),re.I) and norm(k) not in live] for l in cats}
data['sentence_example_notes']={'quantity':'源码例：2+ASCII空格+药水名称；不把“两瓶”当成自动生成值。','article':'DESC_A与article_a在中文省略a/an，不自动产生“一把”。','colour':'示例句省略菜单颜色标签；源调用仍完整保留。','assertions':'未运行游戏或自动化测试；不标记为已有自动化断言覆盖。'}
(out/'families_r3.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
