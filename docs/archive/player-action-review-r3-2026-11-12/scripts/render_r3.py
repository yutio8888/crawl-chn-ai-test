#!/usr/bin/env python3
import argparse,json,pathlib,random,collections
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=pathlib.Path(a.out);d=json.loads((out/'families_r3.json').read_text())
for lane,seed in [(1,1301),(2,2402)]:
 order=list(d['families']);random.Random(seed).shuffle(order);buf=[f'# 第三轮评审输入 lane{lane}\n\n顺序seed={seed}；refs={json.dumps(d["refs"])}']
 def emit(x):
  buf.extend([f"## {x['family_id']} · {x['category']}",'英文完整模板／片段：\n```json\n'+json.dumps(x['english_templates'],ensure_ascii=False,indent=2)+'\n```'])
  if x['category']=='directed':buf.append('用途：'+x['use_group']+'；显示角色：'+x['presentation_role']+'；'+x['role_reason'])
  for l in ['stable','trunk']:
   buf.append('### '+l)
   for c in x['calls'][l]:buf.extend([f"{c['path']}:{c['line']}\n```cpp\n{c['local_parameter_context']}\n```",'完整调用与实参：\n```cpp\n'+c['call']+'\n```'])
   buf.append('中文模板、参数与还原：\n```json\n'+json.dumps(x['reconstructions'][l],ensure_ascii=False,indent=2)+'\n```')
  if 'parameter_semantics_difference' in x:buf.append('两线参数来源：'+x['parameter_semantics_difference'])
  if 'parameter_generation_evidence' in x:buf.append('参数生成及片段catalog证据：\n```json\n'+json.dumps(x['parameter_generation_evidence'],ensure_ascii=False,indent=2)+'\n```')
  if 'unresolved_branches' in x:buf.append('待运行时分支：\n```json\n'+json.dumps(x['unresolved_branches'],ensure_ascii=False,indent=2)+'\n```')
  if 'directed_examples' in x:buf.append('完整句参数示例：\n```json\n'+json.dumps(x['directed_examples'],ensure_ascii=False,indent=2)+'\n```')
 for x in order:emit(x)
 buf.append('# 共用参数生成器代码证据\n\n```json\n'+json.dumps(d.get('shared_generator_evidence',{}),ensure_ascii=False,indent=2)+'\n```')
 buf.append('# 定向 HERE 专项（不计入随机抽样）')
 for x in d['directed']:emit(x)
 (out/f'review_input_lane{lane}.md').write_text('\n\n'.join(buf)+'\n')
methods=collections.Counter(r['method'] for x in d['families'] for r in x['reconstructions']['stable']);diff=collections.Counter(x['applicability'] for x in d['families']);ddiff=collections.Counter(x['applicability'] for x in d['directed'])
lines=['# 第三轮玩家动作及反馈消息族覆盖','\nrefs：'+json.dumps(d['refs']),'\n本轮是有边界的首批清单，不是动作消息全审。消息族以同函数内相邻输出调用组成（调用间隔不超过8行）；保留各调用的完整模板、片段、实参及附近条件代码。相同模板不同参数值不拆样本。','\n每类选12族：高风险6族、常用动作静态对照6族。高频是按常用动作入口选定的源码区域代理，不是运行频率测量。高风险含格式参数或字符串拼接；每类独立 Random(seed+类别序号)，先shuffle高风险子池取6，再shuffle静态子池取6。以文件和首调用行号排序；seed=2026111203。','\n|类别|总体|高风险候选|静态候选|抽中|子种子|','|---|---:|---:|---:|---:|---:|']
for c,s in d['selection'].items():lines.append(f"|{c}|{s['pool_count']}|{s['strata_counts']['high_risk']}|{s['strata_counts']['common_static']}|12（6+6）|{s['subseed']}|")
lines+=['\n纳入：实际生产C++的mpr/mprf及变体、yesno、simple_monster_message等带直接字面量的输出；限定动作源码范围，排除测试、debug/wizard函数；item-use按函数名把读卷/喝药/魔杖分到D，其余归C。状态类delay只取休息/奔跑，player只取恢复和状态函数。','\n排除：前轮80项和更早48项的英文键；任一直接模板命中排除集时整族不计入新增。回归对照列表见文末及JSON。非字面量输出尚未自动追溯，未计入本候选总体。','\n还原计数（随机样本stable模板/片段级，同族可含多个分支）：'+json.dumps(dict(methods),ensure_ascii=False),'\n随机样本两线：'+json.dumps(dict(diff),ensure_ascii=False),'\nHERE定向两线：'+json.dumps(dict(ddiff),ensure_ascii=False),'\n具体名称/数量示例按源码：中文DESC_A和article_a不自动加“一把”；普通堆叠为数字+ASCII空格+名称。item_message达到摘要阈值时返回glyph列表，低于阈值时才返回物品名称列表；两种输出单独还原。'+json.dumps(d.get('sentence_example_notes',{}),ensure_ascii=False),'\n定向HERE：独立directed段，D-HERE-xx，不计入72随机消息族。穷举范围为两线生产C++、头文件消息表以及Lua/vault DSL中包含英文独立单词here的已定位字面量（宏、显示入口或有catalog配对的消息数据）；包括流式拼接片段。按用途分组、记录全部识别到的消费者。每个key含尾空格和中文尾空格计数；评审输入末尾保留独立节。','\n待查覆盖：HERE已额外枚举Lua/vault DSL和头文件消息表；仍未穷尽Lua长括号字符串及完全动态拼接、其他TextDB帮助/描述中的here。随机动作池未追溯Lua/地图脚本、变量化/函数返回字符串；未覆盖所有duration-data表驱动结束消息、所有canned_msg枚举和战斗动词生成器、怪物自主行为与玩家动作的全部可达性组合。局部代码证据不等于运行时每个状态可达性。句子无法从已确认参数完整确定时标为需要运行时输出，未执行游戏或构造测试。','\nHERE catalog中尚未找到直接消费者的键（不冒充生产消息）：'+json.dumps(d.get('here_catalog_without_direct_consumer',{}),ensure_ascii=False),'\n随机范围文件：\n```json\n'+json.dumps({'A':['movement.cc','stairs.cc','travel.cc'],'B':['melee-attack.cc','ranged-attack.cc','throw.cc','beam.cc'],'C':['items.cc','item-use.cc','player-equip.cc'],'D':['potion.cc','evoke.cc','item-use.cc'],'E':['spl-cast.cc','ability.cc'],'F':['delay.cc','player.cc','player-reacts.cc']},ensure_ascii=False,indent=2)+'\n```','\n回归对照（不计入新增）：']
for x in d['regression_controls']:lines.append(f"- {x['category']} {x['path']}:{x['line']} `{x['function']}`："+json.dumps(x['excluded_keys'],ensure_ascii=False))
lines+=['\n重跑：`python3 scripts/build_inventory_r3.py --repo <repo> --out <output> --previous <samples_r2.json>`。固定git对象以archive/show导出；排除资料首次冻结到inputs。不修改仓库，不运行编译或游戏。']
(out/'coverage_r3.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'methods':dict(methods),'differences':dict(diff),'directed_differences':dict(ddiff)},ensure_ascii=False))
