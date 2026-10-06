"""跑测试集，算召回率，并打印失败诊断。"""
import json, sys, argparse, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from retrieve import Retriever, load

TS = json.load(open(HERE / 'testset.json', encoding='utf-8'))['questions']
KS = (1, 3, 5, 10)


def evaluate(corpus_path, mode, label, deep=200, verbose=False):
    docs = load(corpus_path)
    res = []
    # 先建全量索引一次，再按版本复用（版本过滤在打分后做，省时间）
    base = Retriever(docs, mode=mode)
    ver_cache = {}
    for q in TS:
        ver = q.get('version')
        r = base
        if ver:
            if ver not in ver_cache:
                ver_cache[ver] = Retriever(docs, mode=mode, version=ver)   # 打分前就过滤
            r = ver_cache[ver]
        cand = r.rank(q["query"], deep=deep)
        exp = [(f.lower(), n.lower()) for f, n in (q.get('expect_any') or [])]
        rank = None
        for i, (s, d) in enumerate(cand, 1):
            if (d['file'].lower(), d['name'].lower()) in exp:
                rank = i
                break
        top1 = cand[0] if cand else (0, None)
        res.append({
            'id': q['id'], 'cat': q['category'], 'no_match': bool(q.get('no_match')),
            'retrievable': q['retrievable'], 'rank': rank,
            'top1': (top1[1]['file'] + '::' + top1[1]['name']) if top1[1] else None,
            'top1_score': round(top1[0], 2),
            'expected': ' / '.join(f'{f.split(".")[-1]}::{n}' for f, n in (q.get('expect_any') or [])) or '(应无匹配)',
        })

    # 该语料若没有这道题要求的版本，则这题在本语料上不可评估，剔除出分母
    corpus_vers = {d['ds'] for d in docs}
    for r in res:
        q = next(x for x in TS if x['id'] == r['id'])
        r['evaluable'] = r['retrievable'] and (not q.get('version') or q['version'] in corpus_vers)
    ans = [r for r in res if r['evaluable']]
    skipped = [r['id'] for r in res if r['retrievable'] and not r['evaluable']]
    if skipped:
        print(f'  （本语料无版本标签，以下版本约束题剔除出分母: {skipped}）')
    print(f'\n{"="*100}\n【{label}】语料={Path(corpus_path).name} 模式={mode}')
    print('=' * 100)
    hdr = f"{'ID':5}{'类别':15}{'期望答案':40}{'首个命中位次':>10}   {'Top1 实际返回'}"
    print(hdr)
    print('-' * 100)
    for r in res:
        if r['no_match'] or not r.get('evaluable'):
            continue
        rk = f"@{r['rank']}" if r['rank'] else '未进前%d' % deep
        print(f"{r['id']:5}{r['cat']:15}{r['expected'][:38]:40}{rk:>10}   {str(r['top1'])[:44]}")
    print('-' * 100)
    n = len(ans)
    line = f'  可召回题数 {n}'
    for k in KS:
        hit = sum(1 for r in ans if r['rank'] and r['rank'] <= k)
        line += f'   Recall@{k}={hit}/{n} ({100*hit/n:.0f}%)'
    mrr = sum(1 / r['rank'] for r in ans if r['rank']) / n if n else 0
    line += f'   MRR={mrr:.3f}'
    print(line)
    # 无匹配题的 top1 分数分布（用来定"检索不足"的阈值）
    nm = [r for r in res if r['no_match']]
    if nm:
        print('  应无匹配题的 top1 分数:', [f"{r['id']}={r['top1_score']}" for r in nm])
    hit_scores = [r['top1_score'] for r in ans if r['rank']]
    miss_scores = [r['top1_score'] for r in ans if not r['rank']]
    print(f"  可召回题 top1 分数 中位/最小: {sorted(hit_scores)[len(hit_scores)//2] if hit_scores else 0} / {min(hit_scores) if hit_scores else 0}"
          f"   未命中题 top1 分数: {sorted(miss_scores, reverse=True)[:5]}")
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', default=str(HERE / 'data' / 'corpus_versions.jsonl'))
    ap.add_argument('--mode', default='zh')
    ap.add_argument('--label', default='')
    a = ap.parse_args()
    evaluate(a.corpus, a.mode, a.label or a.mode)
