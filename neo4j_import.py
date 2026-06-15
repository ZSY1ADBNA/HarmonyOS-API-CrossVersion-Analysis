import os
import json
import time
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from neo4j import GraphDatabase

# ==================== 配置 ====================
NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
JSON_ROOT = PROJECT_ROOT / "03_extracted_json"

# 创建驱动
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def create_indexes(tx):
    """创建索引加速导入"""
    tx.run("CREATE INDEX IF NOT EXISTS FOR (n:API) ON (n.uid)")
    for label in ["Module", "Namespace", "Class", "Interface", "Enum",
                  "Method", "Property", "TypeAlias", "EnumMember", "Struct",
                  "CallSignature", "ExportImport", "Unknown"]:
        tx.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.uid)")


def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def make_uid(node_type, name, parent=""):
    """生成唯一 ID"""
    if parent:
        return f"{parent}::{name}"
    return f"{name}"


def make_label(node_type):
    """类型映射到 Neo4j 标签"""
    mapping = {
        "module": "Module",
        "namespace": "Namespace",
        "class": "Class",
        "interface": "Interface",
        "enum": "Enum",
        "method": "Method",
        "property": "Property",
        "type_alias": "TypeAlias",
        "enum_member": "EnumMember",
        "struct": "Struct",
        "call_signature": "CallSignature",
        "export_import": "ExportImport",
    }
    return mapping.get(node_type, "Unknown")


def batch_import_file(session, file_path, version):
    """批量导入单个 JSON 文件到 Neo4j"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        nodes = data.get("节点", [])
        if not nodes:
            return {"file": file_path, "status": "skip", "reason": "无节点"}

        # ---- 第一步：构建节点数据 ----
        node_records = []
        parent_map = {}  # name -> parent_name

        for node in nodes:
            node_type = node.get("类型", "Unknown")
            name = node.get("名称") or node.get("签名", "unnamed")
            parent = node.get("上级", "")
            module = node.get("所属模块", "")
            level = node.get("层级", 0)
            description = node.get("功能描述", "")
            comments = node.get("注释信息", [])

            # 提取 @since 和 @syscap
            since_version = ""
            syscap = ""
            for c in comments:
                if c.startswith("@since"):
                    since_version = c.replace("@since", "").strip()
                elif c.startswith("@syscap"):
                    syscap = c.replace("@syscap", "").strip()

            uid = make_uid(node_type, name, parent)
            parent_map[name] = parent
            label = make_label(node_type)

            props = {
                "uid": uid,
                "name": name,
                "type": node_type,
                "description": description,
                "comments": "\n".join(comments),
                "since": since_version,
                "syscap": syscap,
                "sdk_version": version,
                "parent_name": parent,
                "module": module,
                "level": level,
            }

            # 类型特有字段
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

        # ---- 第二步：批量创建节点 ----
        for label, props in node_records:
            session.run(f"""
                MERGE (n:{label} {{uid: $uid}})
                SET n = $props
            """, uid=props["uid"], props=props)

        # ---- 第三步：构建关系 ----
        relations = []
        name_to_uid = {}
        for _, props in node_records:
            name_to_uid[props["name"]] = props["uid"]

        module_nodes_created = set()

        for _, props in node_records:
            uid = props["uid"]
            parent_name = props["parent_name"]
            module = props["module"]

            # HAS_PARENT: 子节点 -> 父节点
            if parent_name and parent_name in name_to_uid:
                parent_uid = name_to_uid[parent_name]
                if parent_uid != uid:
                    relations.append({
                        "from_uid": uid,
                        "to_uid": parent_uid,
                        "rel_type": "HAS_PARENT"
                    })

            # BELONGS_TO_MODULE: 非模块节点 -> 模块节点
            if module and module != "未知模块" and module != uid:
                if module not in name_to_uid and module not in module_nodes_created:
                    module_uid = f"module::{module}"
                    session.run("""
                        MERGE (m:Module {uid: $uid})
                        SET m.name = $name, m.type = 'module', m.sdk_version = $ver
                    """, uid=module_uid, name=module, ver=version)
                    name_to_uid[module] = module_uid
                    module_nodes_created.add(module)

                module_uid = name_to_uid.get(module, f"module::{module}")
                relations.append({
                    "from_uid": uid,
                    "to_uid": module_uid,
                    "rel_type": "BELONGS_TO_MODULE"
                })

        # ---- 第四步：批量创建关系 ----
        # 按关系类型分组
        rels_by_type = {}
        for rel in relations:
            rt = rel["rel_type"]
            if rt not in rels_by_type:
                rels_by_type[rt] = []
            rels_by_type[rt].append(rel)

        for rel_type, rel_list in rels_by_type.items():
            # 分批执行，每批 500 条
            batch_size = 500
            for i in range(0, len(rel_list), batch_size):
                batch = rel_list[i:i + batch_size]
                session.run(f"""
                    UNWIND $rels AS rel
                    MATCH (a {{uid: rel.from_uid}})
                    MATCH (b {{uid: rel.to_uid}})
                    MERGE (a)-[:{rel_type}]->(b)
                """, rels=batch)

        return {
            "file": file_path,
            "status": "success",
            "nodes": len(node_records),
            "relations": len(relations),
            "version": version
        }

    except Exception as e:
        return {
            "file": file_path,
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "version": version
        }


def collect_all_json_files(root_path):
    """收集所有 JSON 文件，按版本分组"""
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
    print("Neo4j 知识图谱导入工具")
    print("=" * 70)
    print(f"JSON 目录: {JSON_ROOT}")
    print(f"Neo4j 地址: {NEO4J_URI}")

    # 1. 收集文件
    print("\n正在扫描 JSON 文件...")
    files = collect_all_json_files(JSON_ROOT)
    print(f"找到 {len(files)} 个 JSON 文件")

    if not files:
        print("未找到任何 JSON 文件，请确认目录结构: 03_extracted_json/版本名/*.json")
        return

    # 按版本统计
    version_count = {}
    for _, v in files:
        version_count[v] = version_count.get(v, 0) + 1

    print("\n各版本文件数量:")
    for v, c in sorted(version_count.items()):
        print(f"  {v}: {c} 个")

    # 2. 询问版本过滤
    print("\n可用版本:", ", ".join(sorted(version_count.keys())))
    ver_filter = input("输入要导入的版本（回车导入全部）: ").strip()

    if ver_filter:
        files = [(f, v) for f, v in files if v == ver_filter]
        if not files:
            print(f"未找到版本 {ver_filter} 的文件")
            return
        print(f"过滤后: {len(files)} 个文件")

    # 3. 连接测试
    print("\n测试 Neo4j 连接...")
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS n")
            print("连接成功")
    except Exception as e:
        print(f"连接失败: {e}")
        print("请确保 Neo4j 数据库已启动，且账号密码正确")
        return

    # 4. 创建索引 + 可选清空
    print("\n创建索引...")
    with driver.session() as session:
        session.execute_write(create_indexes)
    print("索引创建完成")

    confirm = input("\n是否清空现有数据库？(y/n): ")
    if confirm.lower() == 'y':
        with driver.session() as session:
            session.execute_write(clear_database)
        print("数据库已清空")

    # 5. 开始导入
    workers = 4
    print(f"\n使用 {workers} 个线程并行处理")
    print("开始导入...\n")

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for file_path, version in files:
            future = executor.submit(batch_import_file, driver.session(), file_path, version)
            futures[future] = (file_path, version)

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)

            file_name = Path(result["file"]).name
            if result["status"] == "success":
                print(f"[{i + 1}/{len(files)}] OK {file_name} -> {result['nodes']} nodes, {result['relations']} rels")
            elif result["status"] == "skip":
                print(f"[{i + 1}/{len(files)}] SKIP {file_name} - {result.get('reason', '')}")
            else:
                print(f"[{i + 1}/{len(files)}] FAIL {file_name} - {result.get('error', 'error')[:100]}")

    # 6. 统计
    elapsed = time.time() - start_time
    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    total_nodes = sum(r.get("nodes", 0) for r in results if r["status"] == "success")
    total_relations = sum(r.get("relations", 0) for r in results if r["status"] == "success")

    print("\n" + "=" * 70)
    print("导入完成")
    print("=" * 70)
    print(f"成功: {success} 个文件")
    print(f"失败: {errors} 个文件")
    print(f"总节点数: {total_nodes}")
    print(f"总关系数: {total_relations}")
    print(f"总耗时: {elapsed:.2f} 秒 ({elapsed / 60:.1f} 分钟)")

    # 按版本统计
    print("\n各版本结果:")
    version_result = {}
    for r in results:
        ver = r.get("version", "unknown")
        if ver not in version_result:
            version_result[ver] = {"success": 0, "error": 0, "nodes": 0, "relations": 0}
        if r["status"] == "success":
            version_result[ver]["success"] += 1
            version_result[ver]["nodes"] += r.get("nodes", 0)
            version_result[ver]["relations"] += r.get("relations", 0)
        else:
            version_result[ver]["error"] += 1

    for ver, stats in sorted(version_result.items()):
        print(f"  {ver}: success={stats['success']}, error={stats['error']}, "
              f"nodes={stats['nodes']}, relations={stats['relations']}")

    # 7. 关闭驱动
    driver.close()


if __name__ == "__main__":
    main()
