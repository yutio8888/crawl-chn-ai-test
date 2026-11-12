#!/usr/bin/env python3
"""Add conservative source/canonical-catalog reconstruction and neutral review inputs."""
import argparse,pathlib,json,re,random,collections,itertools
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=pathlib.Path(a.out);d=json.loads((out/'samples_r4.json').read_text());log=json.loads((out/'selection_log_r4.json').read_text());src='crawl-ref/source/'
def read(l,f):return (out/'snapshots'/l/src/f).read_text(errors='replace')
def parse(s):
 d={};key=None;body=[];ln=0;active=False
 def flush():
  if key is not None:d[key]={'text':'\n'.join(body).strip('\n'),'line':ln}
 for n,line in enumerate(s.splitlines(),1):
  if line.startswith('#'):continue
  if line.startswith('%%%%'):flush();key=None;body=[];active=True;continue
  if not active:continue
  if key is None:
   if line:key=line;ln=n
  else:body.append(line)
 flush();return d

def norm(s):return s.replace('\\n','\n').replace('\\t','\t').replace('\\r','\r')
cats={l:parse(read(l,'dat/i18n/zh/source.txt')) for l in d['refs']}
def tr(l,k):
 actual=k if k in cats[l] else next((z for z in cats[l] if norm(z)==k),None)
 return norm(cats[l][actual]['text']) if actual is not None else None

def asset(l,k):return {'path':src+'dat/i18n/zh/source.txt','line':cats[l][k]['line'],'key':k,'zh':tr(l,k)} if k in cats[l] else {'key':k,'zh':None}
fp=re.compile(r'%(?:(\d+)\$)?[-+ #0\d.*]*([sdifu])')
def fmt(s,values):
 i=0
 def sub(m):
  nonlocal i
  idx=int(m[1])-1 if m[1] else i
  if not m[1]:i+=1
  return str(values[idx])
 return fp.sub(sub,s).replace('%%','%')

def choices(l,expression,call):
 e=expression.strip();context=call['snippet']
 if e=='""':return [('', '源码空后缀分支')]
 # Full type constraints / custom proper names require the real game state.
 if any(v in e for v in ['ancestor','apostle','get_name','your_name']):return []
 if 'attack_strength_punctuation' in e:return [(tr(l,'.'),'dmg < HIT_WEAK'),(tr(l,'!'),'HIT_WEAK <= dmg < HIT_MED')]
 if re.search(r'(?:mon|mons|caster|defender|attacker|victim|target|targ).*name\(',e):
  if re.search(r'MONS_|UNRAND_|create_monster',context):return []
  name=tr(l,'orc')
  if not name:return []
  if 'DESC_ITS' in e:name=fmt(tr(l,"%s's"),[name]);note='中文DESC_ITS经apostrophise；套用catalog %s\'s，未添加英文所有格。'
  elif 'DESC_YOUR' in e:name=(tr(l,'your ') or '')+name;note='友方可见兽人，DESC_YOUR由中文your前缀与兽人名称构成。'
  else:note='以可见普通兽人为参数文本示例；DESC_THE/DESC_A中文无英语冠词；未证明该实例在该分支中的游戏可达性。'
  return [(name,note)]
 if re.search(r'\?\s*(?:T_\()?"',e):
  # Only consume literal-only alternatives; other nested generators remain unresolved.
  branches=re.findall(r'T_\("([^"\\]*)"\)|(?<![\w])"([^"\\]*)"',e);out=[]
  for wrapped,raw in branches:
   val=tr(l,wrapped) if wrapped else raw
   if val is not None:out.append((val,'按实参条件分支选择；完整条件：'+e))
  return list(dict.fromkeys(out))
 return []

for x in d['samples']:
 x['reconstructions']={};x['catalog_fragments']={};x['branch_parameter_evidence']={};x['existing_test_coverage']=[]
 for l in d['refs']:
  x['reconstructions'][l]=[];x['catalog_fragments'][l]=[];x['branch_parameter_evidence'][l]=[]
  if not x['consumers'][l]:continue
  if x['kind']=='textdb':
   body=x['stable_zh'] if l=='stable' else x['trunk_zh'];en=x['english'] if l=='stable' else x['english_trunk']
   dynamic=bool(en and re.search(r'\{\{|\$cmd\[|@[A-Za-z_]+@|%(?:\d+\$)?[-+0\d.*]*[sdfiu]|\$[1-9]',en))
   if body is None or dynamic:
    x['reconstructions'][l].append({'method':'需要运行时或布局才能确定','full_zh_display':None,'zh_body':body,'reason':'TextDB正文含模板标记、命令键标签、Lua表达式或参数；保留完整正文，需相应角色状态/键位和布局。','parameter_source':x['parameter_sources'],'key_generation_evidence':x.get('key_generation_evidence',{}).get(l,[])})
   else:x['reconstructions'][l].append({'method':'静态模板，无参数','full_zh_display':body,'formula':'按相同lookup key读取完整ZH正文；不截断、不改写数值。颜色标记保留，终端折行不作断言。'})
   x['catalog_fragments'][l]=[x['assets'][l]];continue
  for call in x['consumers'][l]:
   ts=call['templates'];x['catalog_fragments'][l]+=ts
   x['branch_parameter_evidence'][l].append({'path':call['path'],'line':call['line'],'arguments':call['arguments'],'code':call['snippet']})
   for t in ts:
    en=t['english'];zh=t['zh'];base={'english':en,'zh_template':zh,'source':{'path':call['path'],'line':call['line']},'parameter_expressions':call['arguments'],'conditions_and_generation':call['snippet']}
    if call['call'].startswith('simple_monster_message'):
     has_params=bool(fp.search(en));poss=len(call['arguments'])>2 and call['arguments'][2].strip()=='true';name=tr(l,'orc');constraint=bool(re.search(r'MONS_|UNRAND_|ancestor',call['snippet']))
     if zh is not None and not has_params and name and not constraint:
      if poss:name=fmt(tr(l,"%s's"),[name])
      base.update({'method':'参数文本还原','full_zh_display':re.sub(r'(?<=[\u3400-\u9fff]) +(?=[\u3400-\u9fff])','',name+zh),'example_state':'指定可见普通兽人作为名称参数文本；不声称已在游戏中触发该状态。','formula':'mons.name(descrip)；need_possessive=true时apostrophise，再拼event片段；CJK-CJK空格归一见message.cc。','parameter_assets':[asset(l,'orc'),asset(l,"%s's")],'remaining_runtime':'其他怪物名、不可见分支、状态可达性和布局需运行时。'})
     else:base.update({'method':'需要运行时或布局才能确定','full_zh_display':None,'reason':'隐式怪物名称/所有格前缀与原模板或受类型限制的实例需要具体运行时状态。'})
    elif zh is not None and not fp.search(en) and not re.search(r'@[A-Za-z_]+@',en) and not any(fp.search(v['english']) for v in ts):base.update({'method':'静态模板，无参数','full_zh_display':zh,'formula':'catalog展开\\n/\\t，保留模板空格与标点；对应条件见源代码。'})
    else:
     base.update({'method':'需要运行时或布局才能确定','full_zh_display':None,'reason':'未建立该实参生成器的完整状态；保留表达式与全部已提取条件片段，不以假定名称代替真实生成路径。'})
     if zh is not None and fp.search(en):
      aa=call['arguments'];idx=next((i for i,arg in enumerate(aa) if '"'+en.split('\n')[0][:12] in arg or (re.search(r'T_\(',arg) and i==0)),None)
      actual=aa[idx+1:] if idx is not None else [];n=max([int(m[1]) for m in fp.finditer(en) if m[1]] or [len(list(fp.finditer(en)))])
      if len(actual)==n:
       opts=[choices(l,e,call) for e in actual];base['resolved_parameter_examples']=[{'expression':e,'examples':v} for e,v in zip(actual,opts)]
       if all(opts):
        examples=[]
        for combo in itertools.islice(itertools.product(*opts),32):
         try:sentence=fmt(zh,[v[0] for v in combo])
         except (IndexError,TypeError):continue
         examples.append({'parameters':[{'expression':e,'value':v[0],'source_and_state':v[1]} for e,v in zip(actual,combo)],'full_zh_display':sentence})
        if examples:base.update({'method':'参数文本还原','full_zh_display':examples[0]['full_zh_display'],'branch_examples':examples,'formula':'按所列原始参数表达式和catalog参数示例逐位置替换；不增加冠词、量词或修正文案。'})
    x['reconstructions'][l].append(base)
 methods={r['method'] for r in x['reconstructions']['stable']}
 x['reconstruction_method']='需要运行时或布局才能确定' if '需要运行时或布局才能确定' in methods else '参数文本还原' if '参数文本还原' in methods else '静态模板，无参数'
 x['applicability_basis']='生产消费者按相同TextDB key或同源调用中的模板定位；正文/catalog比较决定相同或分化；未确认的运行时参数/布局不据此断言相同。'

# Shared source evidence for implicit prefixes / possessives is kept neutral.
def excerpt(l,f,needle,pad=10):
 s=read(l,f);ls=s.splitlines();out=[]
 for i,line in enumerate(ls):
  if needle in line:out.append({'path':src+f,'line':i+1,'code':'\n'.join(f'{j+1}: {ls[j]}' for j in range(max(0,i-pad),min(len(ls),i+pad+1)))})
 return out
d['shared_generator_evidence']={l:{'possessive':excerpt(l,'english.cc','string apostrophise(',14),'implicit_monster_message':excerpt(l,'message.cc','bool simple_monster_message(',25),'item_name_article_quantity':excerpt(l,'item-name.cc','// EN only: articles (a/an)',9)+excerpt(l,'item-name.cc','buff << quantity <<',8)} for l in d['refs']}
(out/'samples_r4.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

for lane,rseed in [(1,1401),(2,2502)]:
 order=list(d['samples']);random.Random(rseed).shuffle(order);buf=[f'# 第四轮评审输入 lane{lane}\n\n顺序种子：{rseed}；固定refs：{json.dumps(d["refs"])}']
 for x in order:
  buf.extend([f"## {x['sample_id']} · {x['category']}",'英文全文：\n\n'+str(x['english']),'参数／键生成：'+x['parameter_sources']])
  for l in d['refs']:
   buf+=['### '+l,'中文全文：\n\n'+str(x['stable_zh'] if l=='stable' else x['trunk_zh'])]
   if l=='trunk' and x['english_trunk']!=x['english']:buf+=['trunk 英文全文：\n\n'+str(x['english_trunk'])]
   for z in x['consumers'][l]:buf.append(f"{z['path']}:{z['line']}\n```cpp\n{z['snippet']}\n```\n"+(('完整调用：\n```cpp\n'+z['call']+'\n```') if z.get('call') else ''))
   if x.get('key_generation_evidence'):buf+=['具体键生成证据：\n```json\n'+json.dumps(x['key_generation_evidence'][l],ensure_ascii=False,indent=2)+'\n```']
   buf+=['还原及参数来源：\n```json\n'+json.dumps(x['reconstructions'][l],ensure_ascii=False,indent=2)+'\n```']
 buf+=['# 共用名称和所有格生成器\n\n```json\n'+json.dumps(d['shared_generator_evidence'],ensure_ascii=False,indent=2)+'\n```']
 (out/f'review_input_lane{lane}.md').write_text('\n\n'.join(buf)+'\n')

names={'R4-1':'物品／神器长说明与物品属性行','R4-2':'法术正文与效果反馈','R4-3':'怪物正文与施法反馈','R4-4':'神祇交互与神祇正文','R4-5':'教程／帮助长段','R4-6':'环境及vault宣告','R4-7':'怪物动作及状态动态反馈'}
reasons={
 'R4-1':'R1仅抽样物品名/短说明，R2主要操作，R3为动作反馈；完整items/unrand及物品属性行仍有未覆盖单位。',
 'R4-2':'R1法术/技能层是小样本，R2技能及能力正文不等同spell正文，R3偏施法入口；保留未重叠的spell正文和效果调用。',
 'R4-3':'R1怪物名/短说明稀疏，R2怪物言语根key不等同monster正文，R3偏玩家动作；补怪物完整正文和mon-cast输出。',
 'R4-4':'既有神祇检查及探针/修复键全部排除，不把它们算新单位；正文powers/wrath/extra和其他剩余交互仍形成独立候选。C5-09宗教状态提示及归一同源模板不纳入。',
 'R4-5':'R2 C1/C5主要直接界面提示片段；R3未按整个HintsDB正文枚举。保留有具体事件/教程调用的完整未覆盖段落。',
 'R4-6':'R3移动/HERE覆盖部分楼层/位置反馈，不等同云、深渊和mainline vault公告；补实际crawl.mpr输出，排除用户自动战斗脚本与Sprint评分，并将stairs整体留给既有移动轮次而不再次计为新增。',
 'R4-7':'R3为玩家动作与反馈；剩余monster enchantment/行动事件/能力状态有独立动态模板。动态多、完整静态对照少，采用6+4配额。'}
methods=collections.Counter(x['reconstruction_method'] for x in d['samples']);branchmethods=collections.Counter(r['method'] for x in d['samples'] for r in x['reconstructions']['stable']);diff=collections.Counter(x['applicability'] for x in d['samples'])
lines=['# 第四轮覆盖与样本冻结','\n固定refs：'+json.dumps(d['refs']),'\n本轮是首批70项有边界抽检清单，不代表七类已审完。只做候选总体、抽样和源文本还原，不评价译文。','\n## 前轮覆盖矩阵','\n|前轮证据|规模／范围|本轮处理|','|---|---|---|','|R1 samples_with_identity|48项、6层小样本|排除key、英文正文及归一模板|','|D-C-096 inventory|46个spec探针|排除探针身份及PR修复键|','|R2 samples + selection log|80项、C1–C8|排除键和模板；C5-09宗教状态提示不作为新增|','|R3 index|72消息族 + 76 HERE定向|排除全部模板/catalog key；含function身份的已覆盖源族整体不计|','|PR #299–#316|18个merge的一父中文资产差分|解析修改／删除键；同样排除|','\n归档证据Git提交和SHA-256：\n```json\n'+json.dumps(d['exclusion_provenance'],ensure_ascii=False,indent=2)+'\n```','\n## 本轮类别及候选总体','\n|类别|候选总体|高风险候选|静态候选|抽中高风险+静态|子种子|备用|','|---|---:|---:|---:|---:|---:|---:|']
for c,s in d['selection'].items():lines.append(f"|{c} {names[c]}|{s['pool_count']}|{s['strata']['high_risk']}|{s['strata']['static_control']}|{s['high_risk']}+{s['static_control']}|{s['subseed']}|5|")
for c in names:lines.append('\n'+c+'：'+reasons[c])
lines+=['\n种子=2026111213，各类Random(seed+类别序号)；候选按英文key（casefold）及完整正文排序，分高风险/静态子池分别shuffle。先高风险正选、备用，再静态正选、备用；一般5+5正选、3+2备用。R4-6备用2+3；R4-7因静态总体少，正选6+4、备用4+1。备用按记录顺序使用。作废0、补抽0；范围验证发生于最终抽样前，未按中文质量选择。','\n高风险定义：格式参数/隐式怪物前缀、相邻条件调用组；长段正文长度至少650或含机制数字/半数/倍数/等级/回合/伤害/概率等英文信号。高风险长正文不因此虚构运行时变量；它可属于静态正文。静态对照是不含这些风险信号的候选，并非声称没有游戏条件。','\n## 纳入、排除与孤立候选','\nTextDB按英文lookup key配对完整中英文，并提供具体数据name/枚举/字面量生成证据和生产lookup。items限能从item-name/item-prop具体字面量证明的键；unrand匹配art-data NAME；spell匹配spl-data标题；monster匹配dat/mons name；god匹配canonical god name及后缀；hint匹配具体事件键和getHintString路径。纯别名正文不独立计数。','\n动态单元是同函数中调用间隔不超过8行的输出组，保留模板、片段、所有提取到的相邻条件和实参。同key或同完整英文正文全局只计一次。R4-1只取物品相关描述函数；其他C++动态候选要求真实mpr/yesno/simple_monster_message入口，不把内部make_stringf当显示消费者。环境Lua仅取mainline .des中的crawl.mpr，排除Sprint/教程/自动战斗用户脚本。','\n排除调试/巫师、错误诊断、内部键、既有key与归一模板；归一将格式位置/类型占位视为同一参数位置文本，防止仅更换占位符形式成为新增。含既有source path+function身份的已覆盖调用族整体排除；排除项及回归对照详见selection_log。','\n未取得具体生产生成器证据或为别名正文的候选数：'+str(len(log['unproven_or_isolated']))+'。单独逐项列于selection_log.unproven_or_isolated；这是未证明的排除集合，不把“没有在本抽样框中找到证据”一概断言为死键。','\n## 还原和两线适用性','\n样本级还原方式（只要含一个待运行分支，该样本计入待运行）：'+json.dumps(dict(methods),ensure_ascii=False),'\nstable模板/正文分支级统计：'+json.dumps(dict(branchmethods),ensure_ascii=False),'\n两线适用性：'+json.dumps(dict(diff),ensure_ascii=False),'\n没有执行游戏或新增渲染断言，因此“已有测试覆盖”计0。参数文本还原保留实际catalog名称及源码表达式；不自行补冠词、量词、所有格或标点。具体状态可达性、命令绑定、Lua占位和窗口折行仍需运行时/布局验证。','\n## 仍未查区域','\n此候选总体不等于仓库全部可见文本：未穷尽生成式物品DBNAME、TextDB所有别名链、所有spell文件、动态Lua/长括号文本、完全变量化输出与全部跨函数拼接。未测试角色/神祇/变形/可见性条件的全部组合；TextDB本体之外的运行时追加属性与语言分支保留调用证据但不声称已还原所有值。mon-cast lambda/table的近邻组可能仍需评审结合完整源文件细分；未开展游戏机制正确性评价。','\n## 回归对照（不计新增）']
for r in log['regression_controls']:lines.append('- '+r['category']+' '+json.dumps(r['key'],ensure_ascii=False)+'：'+json.dumps(r['consumers'],ensure_ascii=False))
lines+=['\n其他同源调用排除与全量修复键见selection_log_r4.json。','\n重跑：`python3 scripts/build_inventory_r4.py --repo <仓库> --out <产出目录>`。输入归档来自固定Git对象并冻结inputs；源文件只通过git archive/show读取。两份lane分别以1401/2502对70项独立乱序。']
(out/'coverage_r4.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'sample_methods':dict(methods),'stable_branch_methods':dict(branchmethods),'differences':dict(diff)},ensure_ascii=False))
