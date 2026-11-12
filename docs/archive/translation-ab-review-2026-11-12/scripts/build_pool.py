"""Build a verified, layered A/B sample from frozen refs.

Usage: python3 -I build_pool.py <outdir> <seed>
Writes <outdir>/samples_private.json (with identities) and selection log.
"""
import json, os, random, re, subprocess, sys, collections

OURS_GIT = '$OURS_REPO'
OURS_REF = 'd8aef52fb44e939139b3c1fa3b94e8edfc993f62'
UP_REF = '1eebc1a289'  # upstream 0.34.1, shared base, no translation wrappers
THEIRS_GIT = '$WORKDIR/theirs.git'
THEIRS_REF = 'f34d100d027d25d0024023cc4a7c420c6c335647'
OUT, SEED = sys.argv[1], int(sys.argv[2])
os.makedirs(OUT, exist_ok=True)
exec(open('$WORKDIR/scripts/compare.py').read().split('po = parse_po')[0])

def git(repo, *a):
    return subprocess.run(['git', '-C', repo, *a], capture_output=True, text=True).stdout

def show(repo, ref, path):
    return git(repo, 'show', f'{ref}:{path}')

SRC_PATHS = ['crawl-ref/source/*.cc', 'crawl-ref/source/*.h', 'crawl-ref/source/dat/dlua/*.lua',
             'crawl-ref/source/dat/des/*.des']

def grep_sites(repo, ref, literal):
    out = git(repo, 'grep', '-n', '-F', '-e', literal, ref, '--', *SRC_PATHS)
    sites = []
    for line in out.splitlines():
        parts = line.split(':', 3)
        if len(parts) == 4:
            sites.append((parts[1], int(parts[2]), parts[3]))
    return sites

def snippet(repo, ref, path, line, before=4, after=4):
    lines = show(repo, ref, path).split('\n')
    lo, hi = max(0, line - 1 - before), min(len(lines), line + after)
    return '\n'.join(f'{i+1:5}  {lines[i]}' for i in range(lo, hi))

def c_literal(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

FMT = re.compile(r'%(\d+\$)?[-+ #0]*\d*(\.\d+)?[sdiufc%]')
def fmts(s):
    return sorted(m.group(0) for m in FMT.finditer(s) if m.group(0) != '%%')
TAGS = re.compile(r'</?[a-zA-Z]+>|@[a-z_]+@|\$[A-Z_]+')
def tags(s):
    return sorted(TAGS.findall(s))

# ---------------- UI catalogue candidates ----------------
po = parse_po('$WORKDIR/work/ui.po')
ours = parse_source('$WORKDIR/work/ours-stable-source.txt')
ours_plain = {k: v for k, v in ours.items() if not ('|' in k and not k.startswith('|'))}
by_en = collections.defaultdict(list)
for e in po:
    if e.get('msgstr'):
        by_en[e['msgid']].append(e)

LAYERS = {
    'L1': ('界面/状态', lambda c, en: c.startswith(('d.duration', 'm.ui', 'p.ui', 'i.reason', 'help.', 'w.ui', 's.ui'))),
    'L2': ('战斗及动态消息', lambda c, en: ('log' in c) and '%' in en),
    'L3': ('法术/技能/变异', lambda c, en: c.startswith(('display.spell', 'd.skill.title', 'm.mutation', 'a.mutation', 'display.ability'))),
    'L4': ('物品/怪物名称及短说明', lambda c, en: c.startswith(('display.item', 'display.monster', 'd.monster.state', 'd.feature.name'))),
    'L5': ('神明/角色语气', lambda c, en: c.startswith(('d.god', 'g.message', 'g.', 'r.power'))),
}

def ui_candidates(layer_pred):
    out = []
    for en, entries in by_en.items():
        if len(entries) != 1:          # same English with several contexts: skip (ambiguous)
            continue
        e = entries[0]
        if not layer_pred(e.get('msgctxt', ''), en):
            continue
        if en not in ours_plain:       # exact-case, context-free key on our side only
            continue
        if len(en) < 3 or len(en) > 220:
            continue
        out.append((en, e['msgctxt'], e['msgstr'], ours_plain[en]))
    out.sort()
    return out

log = collections.defaultdict(list)

def verify_ui(en, ctx, t, o):
    if fmts(en) != fmts(t) or fmts(en) != fmts(o):
        return None, 'placeholder mismatch'
    if tags(en) != tags(t) or tags(en) != tags(o):
        return None, 'markup mismatch'
    lit = c_literal(en)
    up = grep_sites(OURS_GIT, UP_REF, f'"{lit}"')
    if not up:
        return None, 'no upstream literal site'
    if len({s[0] for s in up}) > 2 or len(up) > 3:
        return None, f'literal used at {len(up)} sites (ambiguous usage)'
    th = grep_sites(THEIRS_GIT, THEIRS_REF, f'"{lit}"')
    th_ctx = [s for s in th if f'"{ctx}"' in s[2]]
    if not th_ctx:
        # context may sit on a neighbouring line
        for path, line, _ in th:
            near = show(THEIRS_GIT, THEIRS_REF, path).split('\n')[max(0, line-4):line+3]
            if any(f'"{ctx}"' in x for x in near):
                th_ctx.append((path, line, ''))
                break
    if not th_ctx and CURRENT_LAYER == 'L3' and up[0][0].endswith('-data.h') and len(up) == 1 \
            and git(THEIRS_GIT, 'grep', '-c', '-F', f'"{ctx}"', THEIRS_REF, '--', 'crawl-ref/source/*.cc').strip():
        th_ctx = [('generic-lookup:' + ctx, 0, '')]
    if not th_ctx:
        return None, 'their msgctxt not found at a call site'
    ou = grep_sites(OURS_GIT, OURS_REF, f'"{lit}"')
    if not ou:
        return None, 'our stable call site missing'
    path, line, _ = up[0]
    return {
        'usage_sites': [f'{p}:{l}' for p, l, _ in up],
        'context_snippet': snippet(OURS_GIT, UP_REF, path, line),
        'theirs_site': f'{th_ctx[0][0]}:{th_ctx[0][1]}', 'ours_site': f'{ou[0][0]}:{ou[0][1]}',
        'their_msgctxt': ctx,
    }, 'ok'

# ---------------- long-text candidates (descript) ----------------
def load_db(text):
    d = {}
    for b in text.split('%%%%\n'):
        l = b.strip('\n').split('\n')
        if l and l[0] and not l[0].startswith('#'):
            d[l[0].strip()] = '\n'.join(l[1:]).strip()
    return d

def descript_candidates(files, maxlen):
    out = []
    for f in files:
        en = load_db(show(OURS_GIT, UP_REF, f'crawl-ref/source/dat/descript/{f}'))
        o = load_db(show(OURS_GIT, OURS_REF, f'crawl-ref/source/dat/descript/zh/{f}'))
        t = load_db(show(THEIRS_GIT, THEIRS_REF, f'crawl-ref/source/dat/descript/zh/{f}'))
        for k in sorted(set(en) & set(o) & set(t)):
            if not en[k] or '{{' in en[k] or len(en[k]) > maxlen or len(en[k]) < 80:
                continue
            out.append((f, k, en[k], t[k], o[k]))
    return out

rng = random.Random(SEED)
CURRENT_LAYER = None
samples = []

def pick(layer, name, cands, verify, n_diff=7, n_same=1):
    global CURRENT_LAYER
    CURRENT_LAYER = layer
    rng.shuffle(cands)
    diff, same = [], []
    for c in cands:
        if len(diff) >= n_diff and len(same) >= n_same:
            break
        is_same = c[-2] == c[-1]
        if is_same and len(same) >= n_same:
            continue
        if not is_same and len(diff) >= n_diff:
            continue
        info, why = verify(*c)
        log[layer].append({'candidate': c[0] if layer != 'L6' else f'{c[0]}::{c[1]}', 'result': why})
        if info is None:
            continue
        (same if is_same else diff).append((c, info))
    for c, info in diff + same:
        samples.append((layer, name, c, info))
    return len(diff), len(same)

counts = {}
for layer, (name, pred) in LAYERS.items():
    counts[layer] = pick(layer, name, ui_candidates(pred), verify_ui)

def verify_descript(f, k, en, t, o):
    if tags(en) != tags(t) or tags(en) != tags(o):
        return None, 'markup mismatch'
    return {'usage_sites': [f'crawl-ref/source/dat/descript/{f} [{k}]'],
            'context_snippet': f'(数据文件 {f}，条目键 "{k}"；在游戏内查看对应对象说明时整段显示)',
            'theirs_site': f'dat/descript/zh/{f}', 'ours_site': f'dat/descript/zh/{f}',
            'their_msgctxt': None}, 'ok'

l6 = descript_candidates(['spells.txt', 'items.txt', 'monsters.txt', 'features.txt', 'gods.txt', 'mutations.txt'], 700)
counts['L6'] = pick('L6', '对话/长篇说明', [(f'{a}::{b}', c, d, e) for a, b, c, d, e in l6],
                    lambda key, en, t, o: verify_descript(key.split('::')[0], key.split('::')[1], en, t, o))

private = []
for i, (layer, name, c, info) in enumerate(samples):
    if layer == 'L6':
        key, en, t, o = c
    else:
        en, _ctx, t, o = c
        key = en
    private.append({'sample_id': f'S{i+1:02d}', 'layer': layer, 'layer_name': name, 'key': key,
                    'english': en, 'theirs': t, 'ours': o, 'identical': t == o, **info})
json.dump({'seed': SEED, 'refs': {'theirs': THEIRS_REF, 'ours': OURS_REF, 'upstream_context': UP_REF},
           'counts': counts, 'samples': private}, open(f'{OUT}/samples_private.json', 'w'), ensure_ascii=False, indent=1)
json.dump(log, open(f'{OUT}/selection_log.json', 'w'), ensure_ascii=False, indent=1)
print(counts, len(private))
