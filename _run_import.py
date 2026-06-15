"""无交互 Neo4j 批量导入"""
import os
import sys
import json
import time
import traceback
from pathlib import Path
from neo4j import GraphDatabase

# 配置
NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
PROJECT_ROOT = Path(__file__).parent
JSON_ROOT = PROJECT_ROOT / "03_extracted_json"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def create_indexes(tx):
    tx.run("CREATE INDEX IF NOT EXISTS FOR (n:API) ON (n.uid)")
    for label in ["Module", "Namespace", "Class", "Interface", "Enum",
                  "Method", "Property", "TypeAlias", "EnumMember", "Struct",
                  "CallSignature", "ExportImport", "Unknown"]:
        tx.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.uid)")


def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def make_uid(node_type, name, version, parent=""):
    if parent:
        return f"{version}::{parent}::{name}"
    return f"{version}::{name}"


def make_label(node_type):
    mapping = {
        "module": "Module", "namespace": "Namespace", "class": "Class",
        "interface": "Interface", "enum": "Enum", "method": "Method",
        "property": "Property", "type_alias": "TypeAlias",
        "enum_member": "EnumMember", "struct": "Struct",
        "call_signature": "CallSignature", "export_import": "ExportImport",
    }
    return mapping.get(node_type, "Unknown")


def batch_import_file(session, file_path, version):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        nodes = data.get("节点", [])
        if not nodes:
            return {"file": str(file_path), "status": "skip", "reason": "无节点", "version": version}

        node_records = []
        parent_map = {}

        for node in nodes:
            node_type = node.get("类型", "Unknown")
            name = node.get("名称") or node.get("签名", "unnamed")
            parent = node.get("上级", "")
            module = node.get("所属模块", "")
            level = node.get("层级", 0)
            description = node.get("功能描述", "")
            comments = node.get("注释信息", [])

            since_version = node.get("since_version", "")
            syscap = node.get("system_capability", "")

            uid = make_uid(node_type, name, version, parent)
            parent_map[name] = parent
            label = make_label(node_type)

            props = {
                "uid": uid, "name": name, "type": node_type,
                "description": description,
                "comments": "\n".join(comments) if comments else "",
                "since": since_version, "syscap": syscap,
                "sdk_version": version, "parent_name": parent,
                "module": module, "level": level,
            }

            if node_type == "method" and "返回值" in node:
                props["return_type"] = node["返回值"]
            if node_type == "property" and "属性类型" in node:
                props["property_type"] = node["属性类型"]
            if "装饰器" in node:
                deco = node["装饰器"]
                props["decorators"] = "\n".join(deco) if isinstance(deco, list) else deco
            if "父类" in node:
                props["extends"] = node["父类"]

            node_records.append((label, props))

        # 批量创建节点
        for label, props in node_records:
            session.run("MERGE (n:%s {uid: $uid}) SET n = $props" % label,
                        uid=props["uid"], props=props)

        # 构建关系
        name_to_uid = {}
        for _, props in node_records:
            name_to_uid[props["name"]] = props["uid"]

        module_nodes_created = set()
        relations = []

        for _, props in node_records:
            uid = props["uid"]
            parent_name = props["parent_name"]
            module = props["module"]

            if parent_name and parent_name in name_to_uid:
                parent_uid = name_to_uid[parent_name]
                if parent_uid != uid:
                    relations.append({
                        "from_uid": uid, "to_uid": parent_uid, "rel_type": "HAS_PARENT"
                    })

            if module and module != "未知模块" and module != uid:
                if module not in name_to_uid and module not in module_nodes_created:
                    module_uid = f"{version}::module::{module}"
                    session.run("MERGE (m:Module {uid: $uid}) SET m.name = $name, m.type = 'module', m.sdk_version = $ver",
                                uid=module_uid, name=module, ver=version)
                    name_to_uid[module] = module_uid
                    module_nodes_created.add(module)
                module_uid = name_to_uid.get(module, f"{version}::module::{module}")
                relations.append({
                    "from_uid": uid, "to_uid": module_uid, "rel_type": "BELONGS_TO_MODULE"
                })

        # 批量创建关系
        rels_by_type = {}
        for rel in relations:
            rt = rel["rel_type"]
            rels_by_type.setdefault(rt, []).append(rel)

        for rel_type, rel_list in rels_by_type.items():
            for i in range(0, len(rel_list), 500):
                batch = rel_list[i:i + 500]
                session.run("""
                    UNWIND $rels AS rel
                    MATCH (a {uid: rel.from_uid})
                    MATCH (b {uid: rel.to_uid})
                    MERGE (a)-[:%s]->(b)
                """ % rel_type, rels=batch)

        return {
            "file": str(file_path), "status": "success",
            "nodes": len(node_records), "relations": len(relations), "version": version
        }

    except Exception as e:
        return {
            "file": str(file_path), "status": "error",
            "error": str(e), "version": version
        }


def collect_json_files(root_path):
    root = Path(root_path)
    files = []
    for version_dir in root.iterdir():
        if not version_dir.is_dir():
            continue
        version = version_dir.name
        for json_file in version_dir.rglob("*.json"):
            files.append((str(json_file), version))
    return files


def main():
    print("=" * 70)
    print("Neo4j 批量导入工具 - 自动模式")
    print("=" * 70)

    # 扫描文件
    print("\n[SCAN] 扫描 JSON 文件...")
    files = collect_json_files(JSON_ROOT)
    print(f"[INFO] 找到 {len(files)} 个 JSON 文件")

    version_count = {}
    for _, v in files:
        version_count[v] = version_count.get(v, 0) + 1
    print("\n[VERSIONS] 各版本文件数量:")
    for v, c in sorted(version_count.items()):
        print(f"   {v}: {c} 个")

    # 测试连接
    print("\n[TEST] 测试 Neo4j 连接...")
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        print("[OK] 连接成功")
    except Exception as e:
        print(f"[FAIL] 连接失败: {e}")
        return

    # 索引
    print("\n[INDEX] 创建索引...")
    with driver.session() as session:
        session.execute_write(create_indexes)
    print("[OK] 索引就绪")

    # 清空数据库
    print("\n[CLEAR] 清空现有数据...")
    with driver.session() as session:
        session.execute_write(clear_database)
    print("[OK] 数据库已清空")

    # 串行导入（稳定可靠）
    print(f"\n[START] 开始导入 {len(files)} 个文件...\n")
    start_time = time.time()
    results = []

    with driver.session() as session:
        for i, (file_path, version) in enumerate(files):
            result = batch_import_file(session, file_path, version)
            results.append(result)
            fname = Path(file_path).name
            if result["status"] == "success":
                print(f"[{i+1}/{len(files)}] OK {fname} -> {result['nodes']} nodes, {result['relations']} rels")
            elif result["status"] == "skip":
                print(f"[{i+1}/{len(files)}] SKIP {fname}")
            else:
                print(f"[{i+1}/{len(files)}] FAIL {fname}: {result.get('error', '')[:100]}")

    elapsed = time.time() - start_time
    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    skips = sum(1 for r in results if r["status"] == "skip")
    total_nodes = sum(r.get("nodes", 0) for r in results if r["status"] == "success")
    total_rels = sum(r.get("relations", 0) for r in results if r["status"] == "success")

    print("\n" + "=" * 70)
    print("[STATS] 导入完成")
    print("=" * 70)
    print(f"[OK] 成功: {success}, [SKIP] 跳过: {skips}, [FAIL] 失败: {errors}")
    print(f"[NODES] 总节点: {total_nodes}")
    print(f"[RELS] 总关系: {total_rels}")
    print(f"[TIME] 耗时: {elapsed:.1f}s ({elapsed/60:.1f}min)")

    print("\n[VERSIONS] 各版本结果:")
    version_result = {}
    for r in results:
        ver = r.get("version", "unknown")
        if ver not in version_result:
            version_result[ver] = {"ok": 0, "err": 0, "nodes": 0, "rels": 0}
        if r["status"] == "success":
            version_result[ver]["ok"] += 1
            version_result[ver]["nodes"] += r.get("nodes", 0)
            version_result[ver]["rels"] += r.get("relations", 0)
        else:
            version_result[ver]["err"] += 1
    for ver, stats in sorted(version_result.items()):
        print(f"   {ver}: ok={stats['ok']}, err={stats['err']}, nodes={stats['nodes']}, rels={stats['rels']}")

    driver.close()


if __name__ == "__main__":
    main()
