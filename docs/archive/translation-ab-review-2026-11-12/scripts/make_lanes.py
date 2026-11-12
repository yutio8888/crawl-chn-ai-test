"""Create anonymised reviewer inputs with independent A/B assignment per lane.
Usage: python3 -I make_lanes.py <private samples json> <outroot> <seed1> <seed2>
"""
import json, os, random, re, sys

CJK = r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]'
def norm_zh(t):
    paras = re.split(r'\n\s*\n', t.strip())
    out = []
    for p in paras:
        p = re.sub(r'\s*\n\s*', '', p)
        p = re.sub(rf'(?<={CJK})\s+|\s+(?={CJK})', '', p)
        out.append(p)
    return '\n\n'.join(out)


src, root = sys.argv[1], sys.argv[2]
seeds = {'lane1': int(sys.argv[3]), 'lane2': int(sys.argv[4])}
data = json.load(open(src))
mapping = {}
GUIDE = """# 中文译文 A/B 盲评输入

你是中文游戏本地化评审。下面是一款英文 roguelike 游戏（Dungeon Crawl Stone Soup 0.34.1）的 48 条英文原文，每条有两份独立的中文译文 A 与 B。

## 评审规则
- 只依据本文件内容评审；不要查找、打开或推断任何译文仓库、提交或作者，不要上网搜索这些译文。可以凭你对游戏机制的公共知识理解原文。
- 源码摘录来自上游英文版，只用于说明这句英文在何时、以何种参数显示。
- `%s`、`%d` 等占位符在运行时由程序填入（英文版填入什么见摘录）。两份译文所在的程序可能以不同形式填充参数（例如参数本身是否已带"的"或量词）。若你的判断依赖参数的具体填充形式，请标 `validation_gap`，不要据此判定错误。
- 专有名词、怪物/法术/神祇名称可能来自两套不同的既定术语表。只有在含义错误、与原文机制不符或同一译文内部自相矛盾时才算错误；仅仅"与你习惯的译名不同"属于偏好。
- 长段说明的两份译文已统一做过换行/空格规整（段内合并、保留段落），本轮不评价排版格式。
- 不要修改或重写译文；如需说明问题，可引用关键片段。

## 每项请评价
1. faithfulness：忠实/完整（有无漏译、增译、误译）
2. mechanics：机制、数字、条件是否与原文一致
3. terminology：术语是否贴切（注意上面的偏好规则）
4. invariants：占位符、标记（如 `<w>`、`@x@`）、行首空格等是否保持
5. readability：中文可读性、语法
6. tone：语气是否贴合原文（神明、怪物、讽刺等）

## 输出
把结果写入与本文件同目录的 `review_output.json`，格式为 JSON 数组，每项：
```
{"sample_id": "...",
 "verdict": "A" | "B" | "tie" | "insufficient_evidence",
 "reason": "一两句理由",
 "scores": {"A": {"faithfulness":1-5,"mechanics":1-5,"terminology":1-5,"invariants":1-5,"readability":1-5,"tone":1-5},
            "B": {...}},   // 可选；1=严重错误，3=可接受但有明显瑕疵，5=无可挑剔
 "findings": [{"side":"A"|"B","type":"objective_error"|"internal_consistency"|"preference"|"validation_gap",
               "category":"mistranslation|omission|addition|mechanics|placeholder|markup|grammar|terminology|tone|format",
               "quote":"关键原文/译文片段","evidence":"依据（引用原文或摘录）","impact":"对玩家的影响"}]}
```
客观错误、内部一致性问题与纯偏好请分开标注。没有充分证据的判断标 `validation_gap`。
最后在回复中给出：A 胜/B 胜/平局/证据不足的数量，以及你认为最重要的 5 条发现。

## 样本
"""

for lane, seed in seeds.items():
    rng = random.Random(seed)
    order = list(range(len(data['samples'])))
    rng.shuffle(order)
    mapping[lane] = {}
    parts = [GUIDE]
    for n, idx in enumerate(order):
        s = data['samples'][idx]
        aid = f'{lane[-1]}-{n+1:02d}'
        a_is_theirs = rng.random() < 0.5
        T, O = s['theirs'], s['ours']
        if s['layer'] == 'L6':
            T, O = norm_zh(T), norm_zh(O)
        A, B = (T, O) if a_is_theirs else (O, T)
        mapping[lane][aid] = {'sample_id': s['sample_id'], 'A': 'theirs' if a_is_theirs else 'ours',
                              'B': 'ours' if a_is_theirs else 'theirs'}
        usage = ', '.join(s['usage_sites'])
        parts.append(f"### {aid}（类别：{s['layer_name']}）\n\n**英文原文**\n```\n{s['english']}\n```\n"
                     f"**用途/位置**：{usage}\n\n**上下文（上游英文源码或数据说明）**\n```\n{s['context_snippet']}\n```\n"
                     f"**译文 A**\n```\n{A}\n```\n**译文 B**\n```\n{B}\n```\n")
    os.makedirs(f'{root}/{lane}', exist_ok=True)
    open(f'{root}/{lane}/review_input.md', 'w').write('\n'.join(parts))
json.dump({'seeds': seeds, 'mapping': mapping}, open(f'{root}/private/lane_mapping.json', 'w'), ensure_ascii=False, indent=1)
print({k: len(v) for k, v in mapping.items()})
