#!/usr/bin/env python3
"""在同一批题上公平比较三个配置。

只用不带版本约束的 15 题，因为完整语料（API/ 目录）没有版本标签，
拿它跟版本化语料比全部 17 题会让版本约束题必然落空，数字不可比。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from retrieve import Retriever, load

TS = json.load(open(HERE / 'testset.json', encoding='utf-8'))['questions']
COMMON = [q for q in TS if q['retrievable'] and not q.get('version')]
KS = (1, 3, 5, 10)


def run(corpus, mode, label):
    r = Retriever(load(corpus), mode=mode)
    ranks = {}
    for q in COMMON:
        cand = r.rank(q['query'], deep=200)
        exp = [(f.lower(), n.lower()) for f, n in q['expect_any']]
        ranks[q['id']] = next((i for i, (_, d) in enumerate(cand, 1)
                               if (d['file'].lower(), d['name'].lower()) in exp), None)
    n = len(COMMON)
    line = f'{label:40}'
    for k in KS:
        h = sum(1 for v in ranks.values() if v and v <= k)
        line += f'  R@{k}={h}/{n}({100*h/n:.0f}%)'
    mrr = sum(1 / v for v in ranks.values() if v) / n
    print(line + f'  MRR={mrr:.3f}')
    return ranks


def main():
    print(f'共同题集: {len(COMMON)} 题（不含版本约束题）\n')
    d = HERE / 'data'
    r1 = run(d / 'corpus_versions.jsonl', 'naive', '① 版本化语料 · 基线英文 BM25')
    r2 = run(d / 'corpus_versions.jsonl', 'zh', '② 版本化语料 · 本目录检索器')
    r3 = run(d / 'corpus_complete.jsonl', 'zh', '③ 完整语料(API/) · 本目录检索器')
    print('\n逐题位次（①②③）:')
    for q in COMMON:
        i = q['id']

        def f(x):
            return f'@{x[i]}' if x[i] else '未命中'
        print(f'  {i:4} ①{f(r1):8} ②{f(r2):8} ③{f(r3):8}')


if __name__ == '__main__':
    main()
