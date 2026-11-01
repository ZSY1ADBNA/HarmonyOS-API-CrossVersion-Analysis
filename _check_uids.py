"""UID 碰撞预检：按 _run_import.py 的新算法计算全部 JSON 的 uid，报告全局重复与未知模块残留。

用法：python _check_uids.py
只读 JSON，不连数据库。完整碰撞清单写入 06_logs/uid_collisions_full.json。
"""
import json
import sys
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _run_import import JSON_ROOT, make_uid, resolve_module_of, file_tag_for, disambiguate_uid


def compute_uid(version, node, resolve_module, uid_counts, file_tag):
    node_type = node.get("类型", "Unknown")
    name = node.get("名称") or node.get("签名", "unnamed")
    parent = node.get("上级", "")
    module = name if node_type == "module" else resolve_module(node)
    base = make_uid(node_type, name, version, module, parent)
    n = uid_counts.get(base, 0) + 1
    uid_counts[base] = n
    plain = base if n == 1 else f"{base}#{n}"
    return disambiguate_uid(plain, node_type, name, file_tag), plain, base


def main():
    uid_files = collections.defaultdict(list)
    uid_types = {}
    total = 0
    unknown_by_version = collections.Counter()
    unknown_samples = collections.defaultdict(list)
    overloaded_bases = collections.defaultdict(int)

    for version_dir in sorted(JSON_ROOT.iterdir()):
        if not version_dir.is_dir():
            continue
        version = version_dir.name
        for fp in sorted(version_dir.rglob("*.json")):
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            rel = str(Path(fp).relative_to(JSON_ROOT))
            file_tag = file_tag_for(rel)
            nodes = data.get("节点", [])
            resolve_module = resolve_module_of(nodes)
            uid_counts = {}
            for node in nodes:
                uid, plain, base = compute_uid(version, node, resolve_module, uid_counts, file_tag)
                uid_files[uid].append(rel)
                uid_types[uid] = (node.get("类型", "Unknown"),
                                  node.get("名称") or node.get("签名", "unnamed"))
                total += 1
                if plain != base:
                    overloaded_bases[base] += 1
                node_type = node.get("类型", "Unknown")
                if node_type != "module":
                    name = node.get("名称") or node.get("签名", "unnamed")
                    parent = node.get("上级", "")
                    module = resolve_module(node)
                    if module == "未知模块":
                        unknown_by_version[version] += 1
                        if len(unknown_samples[version]) < 5:
                            unknown_samples[version].append(f"{node_type}:{parent}/{name}")

    print("=" * 60)
    print(f"总节点: {total}")
    print(f"重载/同键消歧 base 数: {len(overloaded_bases)},追加 #n 的节点数: {sum(overloaded_bases.values())}")
    print("\n[各版本仍为未知模块的节点数]")
    if not unknown_by_version:
        print("  无(父链解析后全部有模块)")
    for v, c in sorted(unknown_by_version.items()):
        print(f"  {v}: {c}")
        for s in unknown_samples[v]:
            print(f"    例: {s}")

    # 分类:模块根(设计内合并)、具名节点碰撞、未命名构件碰撞
    module_merges = {}
    named_dups = {}
    unnamed_dups = {}
    for u, fs in uid_files.items():
        if len(fs) <= 1:
            continue
        ntype, nname = uid_types[u]
        if ntype == "module":
            module_merges[u] = fs
        elif nname == "unnamed" or ntype == "Unknown":
            unnamed_dups[u] = fs
        else:
            named_dups[u] = fs

    print("\n[模块根跨文件同 uid(设计内:MERGE 合并为每版本每 Kit 一个 Module 节点)]")
    print(f"  共 {len(module_merges)} 个模块 uid 涉及 {sum(len(fs) for fs in module_merges.values())} 处记录")
    print(f"[未命名/Unknown 构件跨文件碰撞(会造成错误合并)]")
    print(f"  共 {len(unnamed_dups)} 个 uid 涉及 {sum(len(fs) for fs in unnamed_dups.values())} 处记录")
    for u, fs in sorted(unnamed_dups.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {u}  ({len(fs)} 处)")
    print(f"[具名节点跨文件碰撞(需逐项核实)]")
    print(f"  共 {len(named_dups)} 个 uid 涉及 {sum(len(fs) for fs in named_dups.values())} 处记录")
    for u, fs in sorted(named_dups.items(), key=lambda x: -len(x[1]))[:30]:
        print(f"  {u}  ({len(fs)} 处)")
        for f in fs[:5]:
            print(f"    {f}")

    out = {
        "total": total,
        "overloaded_bases": len(overloaded_bases),
        "hash_suffix_nodes": sum(overloaded_bases.values()),
        "unknown_module_by_version": dict(unknown_by_version),
        "module_merges": {u: fs for u, fs in module_merges.items()},
        "unnamed_dups": {u: fs for u, fs in unnamed_dups.items()},
        "named_dups": {u: fs for u, fs in named_dups.items()},
    }
    log_dir = Path(__file__).parent / "06_logs"
    log_dir.mkdir(exist_ok=True)
    with open(log_dir / "uid_collisions_full.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[已写出完整清单] 06_logs/uid_collisions_full.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
