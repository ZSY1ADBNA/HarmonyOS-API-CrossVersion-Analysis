"""跨版本 API 变化分析报告生成器"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase
from pathlib import Path

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
OUTPUT_DIR = Path(__file__).parent

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def run_query(session, query, desc=""):
    """执行查询并打印表格式结果"""
    records = list(session.run(query))
    if not records:
        print(f"\n--- {desc}: (无结果) ---")
        return records

    print(f"\n{'='*80}")
    print(f" {desc}  ({len(records)} 条)")
    print(f"{'='*80}")
    keys = records[0].keys()
    for rec in records[:40]:
        parts = [f"{k}={rec[k]}" for k in keys]
        print("  " + " | ".join(parts))
    if len(records) > 40:
        print(f"  ... 还有 {len(records) - 40} 条")
    return records


def main():
    print("=" * 80)
    print("HarmonyOS API 跨版本迁移分析报告")
    print("=" * 80)

    with driver.session() as session:

        # 1. 版本概览
        run_query(session, """
            MATCH (n)
            WHERE n.sdk_version IS NOT NULL
            WITH n.sdk_version AS version, labels(n)[0] AS label, count(n) AS cnt
            ORDER BY version, cnt DESC
            RETURN version, label, cnt
        """, "版本节点分布")

        # 2. 总节点数
        run_query(session, """
            MATCH (n)
            WHERE n.sdk_version IS NOT NULL
            RETURN n.sdk_version AS version, count(n) AS total_nodes
            ORDER BY version
        """, "各版本总节点数")

        # 3. 模块数
        run_query(session, """
            MATCH (m:Module)
            RETURN m.sdk_version AS version, count(m) AS module_count
            ORDER BY version
        """, "各版本模块数量")

        # 4. 类型分布
        run_query(session, """
            MATCH (n)
            WHERE n.sdk_version IS NOT NULL
            RETURN n.sdk_version AS version, labels(n)[0] AS type, count(n) AS cnt
            ORDER BY version, cnt DESC
        """, "各版本类型分布")

        # 5. 版本对变化统计
        run_query(session, """
            WITH [
              {from: 'API4.1', to: 'API5.0'},
              {from: 'API5.0', to: 'API5.1'},
              {from: 'API5.1', to: 'API6.0'},
              {from: 'API4.1', to: 'API6.0'}
            ] AS pairs
            UNWIND pairs AS pair
            MATCH (n_old {sdk_version: pair.from})
            WHERE n_old.type IN ['class', 'interface', 'method', 'property', 'enum']
            WITH pair, collect(DISTINCT coalesce(n_old.parent_name, '') + '::' + n_old.name + '|' + labels(n_old)[0]) AS old_keys
            MATCH (n_new {sdk_version: pair.to})
            WHERE n_new.type IN ['class', 'interface', 'method', 'property', 'enum']
            RETURN pair.from + ' -> ' + pair.to AS upgrade_path,
                   size(old_keys) AS from_count,
                   size(collect(DISTINCT coalesce(n_new.parent_name, '') + '::' + n_new.name + '|' + labels(n_new)[0])) AS to_count
            ORDER BY upgrade_path
        """, "版本变化总览")

        # 6. 最多的新增API（API5.1 vs API5.0 按模块）
        run_query(session, """
            MATCH (n_old {sdk_version: 'API5.0'})
            WHERE n_old.type IN ['class', 'interface', 'method', 'property', 'enum']
            WITH collect(DISTINCT coalesce(n_old.parent_name, '') + '::' + n_old.name + '|' + labels(n_old)[0]) AS old_keys
            MATCH (n_new {sdk_version: 'API5.1'})
            WHERE n_new.type IN ['class', 'interface', 'method', 'property', 'enum']
              AND NOT (coalesce(n_new.parent_name, '') + '::' + n_new.name + '|' + labels(n_new)[0]) IN old_keys
            RETURN n_new.module AS module, labels(n_new)[0] AS type, count(n_new) AS added
            ORDER BY added DESC
            LIMIT 20
        """, "API5.0->5.1 新增最多的模块 TOP20")

        # 7. since版本分布
        run_query(session, """
            MATCH (n)
            WHERE n.since IS NOT NULL AND n.since <> ''
              AND n.type IN ['class', 'interface', 'method', 'property', 'enum']
            RETURN n.since AS since_version, count(n) AS count
            ORDER BY since_version, count DESC
        """, "API @since 版本标注分布")

        # 8. SystemCapability TOP
        run_query(session, """
            MATCH (n)
            WHERE n.syscap IS NOT NULL AND n.syscap <> ''
            RETURN n.syscap AS system_capability, count(n) AS count
            ORDER BY count DESC
            LIMIT 20
        """, "SystemCapability TOP20")

        # 9. 最新版本(API6.0)中最大的模块
        run_query(session, """
            MATCH (n {sdk_version: 'API6.0'})
            WHERE n.type IN ['class', 'interface', 'method', 'property', 'enum']
            RETURN n.module AS module, count(n) AS api_count
            ORDER BY api_count DESC
            LIMIT 20
        """, "API6.0 模块规模 TOP20")

        # 10. 仅在一个版本中存在的API（可能是实验性API）
        run_query(session, """
            MATCH (n)
            WHERE n.type IN ['class', 'interface']
              AND n.sdk_version IS NOT NULL
            WITH n.name AS name, collect(DISTINCT n.sdk_version) AS versions
            WHERE size(versions) = 1
            RETURN versions[0] AS only_version, count(name) AS api_count
            ORDER BY only_version
        """, "仅单一版本存在的类/接口")

    driver.close()
    print(f"\n{'='*80}")
    print(" 分析完成")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
