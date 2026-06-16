"""HarmonyOS API 跨版本分析 — Web Dashboard"""
import sys, json, os, re
from pathlib import Path
from flask import Flask, jsonify, request, render_template
from neo4j import GraphDatabase
from openai import OpenAI

app = Flask(__name__)

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

VERSIONS = ["API4.1", "API5.0", "API5.1", "API6.0"]


def run_cypher(query, **params):
    with driver.session() as s:
        return [dict(r) for r in s.run(query, **params)]


# ─── Page ───────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── API: Overview ──────────────────────────────────────

@app.route("/api/overview")
def api_overview():
    """每个版本的节点数、类型分布、模块数"""
    rows = run_cypher("""
        MATCH (n) WHERE n.sdk_version IS NOT NULL
        RETURN n.sdk_version AS version,
               labels(n)[0] AS label,
               count(n) AS cnt
        ORDER BY version, cnt DESC
    """)
    modules = run_cypher("""
        MATCH (m:Module) RETURN m.sdk_version AS version, count(m) AS modules
        ORDER BY version
    """)
    mod_map = {m["version"]: m["modules"] for m in modules}

    versions = {}
    for r in rows:
        v = r["version"]
        if v not in versions:
            versions[v] = {"total": 0, "types": {}, "modules": mod_map.get(v, 0)}
        versions[v]["total"] += r["cnt"]
        versions[v]["types"][r["label"]] = r["cnt"]

    return jsonify(versions)


# ─── API: Version list ──────────────────────────────────

@app.route("/api/versions")
def api_versions():
    return jsonify(VERSIONS)


# ─── API: Modules ───────────────────────────────────────

@app.route("/api/modules")
def api_modules():
    ver = request.args.get("version", "API6.0")
    rows = run_cypher("""
        MATCH (n {sdk_version: $ver})
        WHERE n.type IN ['class','interface','enum']
        RETURN n.module AS module, count(n) AS cnt
        ORDER BY cnt DESC
    """, ver=ver)
    return jsonify(rows)


# ─── API: Compare two versions (summary) ────────────────

@app.route("/api/compare")
def api_compare():
    old_ver = request.args.get("old", "API5.0")
    new_ver = request.args.get("new", "API5.1")

    # Common key set helper
    def key_set(ver):
        rows = run_cypher("""
            MATCH (n {sdk_version: $ver})
            WHERE n.type IN ['class','interface','enum']
            RETURN DISTINCT n.name + '|' + labels(n)[0] + '|' +
                   coalesce(n.parent_name,'') AS k, n.module AS m, n.name AS name,
                   labels(n)[0] AS type
        """, ver=ver)
        return rows

    old_rows = key_set(old_ver)
    new_rows = key_set(new_ver)

    old_keys = {r["k"] for r in old_rows}
    new_keys = {r["k"] for r in new_rows}

    added = [r for r in new_rows if r["k"] not in old_keys]
    removed = [r for r in old_rows if r["k"] not in new_keys]

    # Aggregate by module
    def by_module(items):
        groups = {}
        for r in items:
            m = r["m"]
            groups[m] = groups.get(m, 0) + 1
        return groups

    return jsonify({
        "old_version": old_ver,
        "new_version": new_ver,
        "old_total": len(old_rows),
        "new_total": len(new_rows),
        "added_count": len(added),
        "removed_count": len(removed),
        "added_by_module": by_module(added),
        "removed_by_module": by_module(removed),
        "added_list": sorted(added, key=lambda x: x["name"])[:200],
        "removed_list": sorted(removed, key=lambda x: x["name"])[:200],
    })


# ─── API: Compare detail (paginated) ────────────────────

@app.route("/api/compare-detail")
def api_compare_detail():
    old_ver = request.args.get("old", "API5.0")
    new_ver = request.args.get("new", "API5.1")
    direction = request.args.get("direction", "added")  # added | removed
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    skip = (page - 1) * per_page

    if direction == "added":
        query = """
            MATCH (n_old {sdk_version: $old})
            WHERE n_old.type IN ['class','interface','enum']
            WITH collect(DISTINCT n_old.name + '|' + labels(n_old)[0] + '|' +
                         coalesce(n_old.parent_name,'')) AS old_keys
            MATCH (n_new {sdk_version: $new})
            WHERE n_new.type IN ['class','interface','enum']
              AND NOT (n_new.name + '|' + labels(n_new)[0] + '|' +
                       coalesce(n_new.parent_name,'')) IN old_keys
            RETURN n_new.module AS module, labels(n_new)[0] AS type,
                   n_new.name AS name, n_new.description AS description
            ORDER BY module, type, name
            SKIP $skip LIMIT $per
        """
    else:
        query = """
            MATCH (n_new {sdk_version: $new})
            WHERE n_new.type IN ['class','interface','enum']
            WITH collect(DISTINCT n_new.name + '|' + labels(n_new)[0] + '|' +
                         coalesce(n_new.parent_name,'')) AS new_keys
            MATCH (n_old {sdk_version: $old})
            WHERE n_old.type IN ['class','interface','enum']
              AND NOT (n_old.name + '|' + labels(n_old)[0] + '|' +
                       coalesce(n_old.parent_name,'')) IN new_keys
            RETURN n_old.module AS module, labels(n_old)[0] AS type,
                   n_old.name AS name, n_old.description AS description
            ORDER BY module, type, name
            SKIP $skip LIMIT $per
        """

    rows = run_cypher(query, old=old_ver, new=new_ver, skip=skip, per=per_page)
    return jsonify(rows)


# ─── API: Graph data ────────────────────────────────────

@app.route("/api/graph")
def api_graph():
    ver = request.args.get("version", "API6.0")
    module = request.args.get("module", "")
    keyword = request.args.get("keyword", "")
    max_parents = int(request.args.get("max_parents", 30))

    # 1. 获取顶层节点（类/接口/枚举），可选过滤模块和关键词
    if keyword:
        filter_clause = "AND (n.name CONTAINS $kw OR n.description CONTAINS $kw)"
    else:
        filter_clause = ""
    if module:
        filter_clause += " AND n.module = $mod"

    parent_nodes = run_cypher(f"""
        MATCH (n {{sdk_version: $ver}})
        WHERE n.type IN ['class','interface','enum'] {filter_clause}
        WITH n, size([(n)<-[:HAS_PARENT]-(m) WHERE m.sdk_version=$ver|1]) AS member_count
        RETURN n.uid AS id, n.name AS label, labels(n)[0] AS group,
               n.type AS type, n.module AS module,
               COALESCE(n.description,'') AS description,
               COALESCE(n.since,'') AS since,
               member_count AS members
        ORDER BY members DESC
        LIMIT $max
    """, ver=ver, mod=module, kw=keyword, max=max_parents)

    if not parent_nodes:
        parent_nodes = run_cypher("""
            MATCH (n {sdk_version: $ver})
            WHERE n.type IN ['class','interface','enum']
            RETURN n.uid AS id, n.name AS label, labels(n)[0] AS group,
                   n.type AS type, n.module AS module,
                   COALESCE(n.description,'') AS description,
                   COALESCE(n.since,'') AS since,
                   0 AS members
            ORDER BY rand() LIMIT $max
        """, ver=ver, max=max_parents)

    parent_ids = [n["id"] for n in parent_nodes]
    parent_set = set(parent_ids)

    # 2. 获取这些父节点的子节点（方法/属性），并找到子节点所属的模块
    child_nodes = []
    edges = []
    if parent_ids:
        child_rows = run_cypher("""
            MATCH (child)-[:HAS_PARENT]->(parent)
            WHERE parent.uid IN $pids AND child.sdk_version = $ver
              AND child.type IN ['method','property']
            RETURN child.uid AS id, child.name AS label, labels(child)[0] AS group,
                   child.type AS type, COALESCE(child.return_type, child.property_type, '') AS sig,
                   parent.uid AS parent_id
            LIMIT 500
        """, pids=parent_ids, ver=ver)
        for r in child_rows:
            child_nodes.append({
                "id": r["id"], "label": r["label"], "group": r["group"],
                "type": r["type"], "sig": r["sig"], "isChild": True
            })
            edges.append({"from": r["id"], "to": r["parent_id"], "label": ""})

    # 3. 获取模块节点 + BELONGS_TO_MODULE 边
    module_set = {n.get("module", "") for n in parent_nodes if n.get("module") and n["module"] != "未知模块"}
    module_nodes = []
    if module_set:
        mod_rows = run_cypher("""
            MATCH (m:Module {sdk_version: $ver})
            WHERE m.name IN $mods
            RETURN m.uid AS id, m.name AS label, 'Module' AS group, 'module' AS type
        """, ver=ver, mods=list(module_set))
        module_nodes = [dict(r) for r in mod_rows]
        # Module edges
        for pn in parent_nodes:
            if pn.get("module"):
                # Find matching module node
                for mn in module_nodes:
                    if mn["label"] == pn["module"]:
                        edges.append({"from": pn["id"], "to": mn["id"], "label": "belongs"})

    # 4. 父节点之间的 HAS_PARENT（继承/实现）
    if parent_ids:
        parent_edges = run_cypher("""
            MATCH (a)-[:HAS_PARENT]->(b)
            WHERE a.uid IN $pids AND b.uid IN $pids
            RETURN a.uid AS from, b.uid AS to
        """, pids=parent_ids)
        for r in parent_edges:
            edges.append({"from": r["from"], "to": r["to"], "label": "extends"})

    all_nodes = parent_nodes + child_nodes + module_nodes
    return jsonify({"nodes": all_nodes, "edges": edges})


# ─── API: Growth trend ──────────────────────────────────

@app.route("/api/trend")
def api_trend():
    rows = run_cypher("""
        MATCH (n) WHERE n.sdk_version IN ['API4.1','API5.0','API5.1','API6.0']
          AND n.type IN ['class','interface','enum','method','property']
        RETURN n.sdk_version AS version,
               n.type AS type,
               count(n) AS cnt
        ORDER BY version, type
    """)

    types = ["class", "interface", "enum", "method", "property"]
    versions = ["API4.1", "API5.0", "API5.1", "API6.0"]

    # Build series per type
    series = {}
    for r in rows:
        t = r["type"]
        if t not in series:
            series[t] = {}
        series[t][r["version"]] = r["cnt"]

    result = []
    for t in types:
        result.append({
            "name": t,
            "data": [series.get(t, {}).get(v, 0) for v in versions]
        })

    return jsonify({"versions": versions, "series": result})


# ─── API: AI Chat ──────────────────────────────────────

SYSTEM_PROMPT = """你是 HarmonyOS API 跨版本分析助手。你通过 Neo4j 图数据库查询 API 变化数据。

## 数据库模型
- 5个版本：API4.1, API5.0, API5.1, API6.0
- 节点类型及属性：Module(name,sdk_version), Class(name,module,parent_name,description,since,sdk_version), Interface(同上), Enum(同上), Method(name,parent_name,module,return_type,sdk_version), Property(name,parent_name,module,property_type,sdk_version), TypeAlias, EnumMember, Struct, Namespace
- 关系：(子节点)-[:HAS_PARENT]->(父节点), (节点)-[:BELONGS_TO_MODULE]->(Module)
- 每个节点有 uid 属性，格式为 {version}::{parent}::{name}

## 跨版本对比方法
比较两个版本的 API 变化，用 name+type+parent_name 组合键（不是uid）：
- 新增：new版有但old版没有的
- 删除：old版有但new版没有的
示例Cypher：
MATCH (n_old {sdk_version: 'API5.0'})
WHERE n_old.type IN ['class','interface','enum']
WITH collect(DISTINCT n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name,'')) AS old_keys
MATCH (n_new {sdk_version: 'API5.1'})
WHERE n_new.type IN ['class','interface','enum']
  AND NOT (n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name,'')) IN old_keys
RETURN labels(n_new)[0] AS type, n_new.name AS name, n_new.module AS module, n_new.description AS desc
ORDER BY module, type, name

## 查询规则
1. 所有查询必须带 sdk_version 过滤
2. 返回结果不要超过 50 条（用 LIMIT）
3. 对比查询用上面 name+type+parent_name 组合键模式
4. 优先返回 name, type, module, description 字段

## 你的回复格式
你必须严格按照以下 JSON 格式回复，不要加任何其他文字：
```json
{
  "cypher": "你生成的Cypher查询（如不需要查询则填null）",
  "answer": "你的中文分析回答（清晰、有条理、要点列出）",
  "chart": "bar|table|none"
}
```

如果用户只是闲聊或问与API数据无关的问题，cypher填null，answer正常回复。
"""

client = None

def get_client():
    global client
    if client is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            # Try .env file
            env_file = Path(__file__).parent / ".env"
            if env_file.exists():
                for line in env_file.read_text(encoding='utf-8').splitlines():
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
        if not api_key:
            return None
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    return client


@app.route("/api/chat", methods=["POST"])
def api_chat():
    msg = request.json.get("message", "").strip()
    history = request.json.get("history", [])  # [{role, content}]

    if not msg:
        return jsonify({"error": "消息不能为空"}), 400

    c = get_client()
    if c is None:
        return jsonify({
            "answer": "⚠️ 未配置 AI。请在项目目录创建 `.env` 文件，写入：\n```\nDEEPSEEK_API_KEY=sk-你的DeepSeek密钥\n```\n获取密钥：https://platform.deepseek.com/api_keys",
            "cypher": None, "results": None
        })

    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-12:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": msg})

    try:
        resp = c.chat.completions.create(
            model="deepseek-chat",
            max_tokens=1024,
            messages=messages,
        )

        raw = resp.choices[0].message.content.strip()

        # Parse JSON from response
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
        if json_match:
            raw = json_match.group(1)
        parsed = json.loads(raw)
        cypher = parsed.get("cypher", "").strip()
        answer = parsed.get("answer", "")

        # Execute cypher if provided
        results = None
        if cypher and cypher.lower() != "null":
            try:
                results = run_cypher(cypher)
            except Exception as e:
                results = {"_error": str(e)}

        return jsonify({
            "answer": answer,
            "cypher": cypher if cypher.lower() != "null" else None,
            "results": results,
        })

    except json.JSONDecodeError:
        return jsonify({
            "answer": raw,
            "cypher": None,
            "results": None,
        })
    except Exception as e:
        return jsonify({
            "answer": f"❌ AI 请求失败：{str(e)}",
            "cypher": None,
            "results": None,
        })


# ─── Main ───────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  HarmonyOS API 跨版本分析 Dashboard")
    print("  打开 http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
