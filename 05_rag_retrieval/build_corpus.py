#!/usr/bin/env python3
"""把 03_extracted_json/ 的节点摊平成检索语料，并生成数据缺口清单。

只读仓库数据，输出到本目录的 data/ 下（不入库）。
用法：
    python build_corpus.py
"""
import json
import os
import glob
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ROOT = REPO / '03_extracted_json'
OUT = HERE / 'data'

VERSIONS = ['API4.1', 'API5.0', 'API5.1', 'API6.0']
FULL_DATASET = 'API'          # 来源待确认的第五个数据集

# 只有这些类型参与检索；module 头结点和"无类型"孤儿节点排除
SEARCHABLE = ('class', 'interface', 'enum', 'namespace', 'method',
              'property', 'type_alias', 'enum_member', 'struct', 'call_signature')
OFFICIAL_PREFIX = ('@ohos.', '@system.', '@kit.')


def norm(x):
    if x is None:
        return ''
    if isinstance(x, str):
        return x.strip()
    if isinstance(x, (list, tuple)):
        return ' '.join(norm(i) for i in x if i)
    if isinstance(x, dict):
        return ' '.join(norm(v) for v in x.values())
    return str(x)


def params_text(ps):
    if not isinstance(ps, list):
        return ''
    out = []
    for p in ps:
        if isinstance(p, dict):
            out.append(' '.join([norm(p.get('名称')), norm(p.get('类型')), norm(p.get('说明'))]))
    return ' | '.join(out)


def build(dataset, skip_dup_js=True):
    """把一个数据集目录下的 JSON 摊平成文档列表。"""
    docs = []
    files = sorted(glob.glob(str(ROOT / dataset / '**' / '*.json'), recursive=True))
    for f in files:
        # API/ 的 ets 与 js 子目录内容相同（617/621 个文件字节一致），去重
        if skip_dup_js and os.sep + 'js' + os.sep in f:
            continue
        base = os.path.basename(f)[:-5]
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        for n in d.get('节点', []):
            t = n.get('类型')
            name = (n.get('名称') or n.get('签名') or '').strip()
            if t not in SEARCHABLE or not name:
                continue
            docs.append({
                'ds': dataset,
                'ver': n.get('版本') or dataset,
                'file': base,
                'name': name,
                'type': t,
                'parent': (n.get('上级') or '').strip(),
                'module': (n.get('所属模块') or '').strip(),
                'desc': norm(n.get('功能描述')),
                'comments': norm(n.get('注释信息')),
                'params': params_text(n.get('parameters')),
                'ret_type': norm(n.get('返回值') or n.get('属性类型')),
                'ret_desc': norm(n.get('return_description')),
                'errs': norm(n.get('error_codes')),
                'since': norm(n.get('since_version')),
                'syscap': norm(n.get('system_capability')),
            })
    return docs


def build_inventory():
    """每个 .d.ts 文件 × 每个版本的可用节点数。空文件也要记，用来识别数据缺口。"""
    inv = {}
    for dataset in VERSIONS:
        for f in glob.glob(str(ROOT / dataset / 'ets' / '*.json')):
            base = os.path.basename(f)[:-5]
            try:
                d = json.load(open(f, encoding='utf-8'))
            except Exception:
                inv.setdefault(base, {})[dataset] = 0
                continue
            n = sum(1 for x in d.get('节点', []) if x.get('类型') in SEARCHABLE)
            inv.setdefault(base, {})[dataset] = n
    return inv


def main():
    OUT.mkdir(exist_ok=True)

    tgt = OUT / 'corpus_versions.jsonl'
    docs = []
    for v in VERSIONS:
        docs += build(v)
    with open(tgt, 'w', encoding='utf-8') as fh:
        for d in docs:
            fh.write(json.dumps(d, ensure_ascii=False) + '\n')
    print(f'{tgt}  {len(docs)} 条')

    tgt = OUT / 'corpus_complete.jsonl'
    docs_full = build(FULL_DATASET)
    with open(tgt, 'w', encoding='utf-8') as fh:
        for d in docs_full:
            fh.write(json.dumps(d, ensure_ascii=False) + '\n')
    print(f'{tgt}  {len(docs_full)} 条')

    inv = build_inventory()
    inv_path = OUT / 'file_inventory.json'
    json.dump(inv, open(inv_path, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'{inv_path}  {len(inv)} 个文件')

    print()
    print('各版本 .d.ts 文件的可用节点情况：')
    print(f"{'版本':10}{'文件数':>8}{'0 可用节点':>12}{'占比':>8}")
    for v in VERSIONS:
        tot = sum(1 for f, p in inv.items() if v in p)
        empty = sum(1 for f, p in inv.items() if p.get(v) == 0)
        print(f'{v:10}{tot:>8}{empty:>12}{100*empty/tot:>7.0f}%')


if __name__ == '__main__':
    main()
