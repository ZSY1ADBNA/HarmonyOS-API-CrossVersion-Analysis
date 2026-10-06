import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from retrieve import Retriever, load, gate

TS = json.load(open(HERE / 'testset.json', encoding='utf-8'))['questions']
docs = load(HERE / 'data' / 'corpus_versions.jsonl')
base=Retriever(docs,mode='zh'); cache={}
print(f"{'ID':5}{'应无匹配':>8}{'实际弃答':>8}{'弃答理由 / top1':60}")
ok=0; bad=[]
for q in TS:
    v=q.get('version'); r=base
    if v:
        if v not in cache: cache[v]=Retriever(docs,mode='zh',version=v)
        r=cache[v]
    c=r.rank(q['query'],deep=200)
    ab,why=gate(q["query"],c,version=v)
    exp=bool(q.get('no_match'))
    mark='✓' if ab==exp else '✗'
    if ab==exp: ok+=1
    else: bad.append(q['id'])
    show = why if ab else f"top1={c[0][1]['file']}::{c[0][1]['name']} ({c[0][0]:.2f})"
    print(f"{q['id']:5}{str(exp):>8}{str(ab):>8}  {mark} {show[:56]}")
print()
print(f"弃答判定正确率: {ok}/{len(TS)}   判错: {bad}")
