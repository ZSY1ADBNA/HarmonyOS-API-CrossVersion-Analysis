"""AI Agent: DeepSeek function-calling loop over read-only Neo4j queries.

设计要点：
- 零新依赖：HTTP 由 app.call_ai 完成（stdlib urllib），本模块只做循环与工具
- 循环导入规避：本模块顶部不 import app，所有 app 侧对象在函数内懒导入
- 安全核心：validate_cypher 只读护栏（公网站点，模型生成的 Cypher 必须过这关）
- 误报可接受（模型收到中文错误会改写重试）；漏报不可接受，所以黑名单从宽
"""
import json
import re

MAX_ITERATIONS = 6           # 工具调用循环上限
MAX_ROWS = 50                # 每条查询硬性结果上限
MAX_TOOL_RESULT_CHARS = 4000 # 回传给模型的结果序列化截断长度
MAX_STEP_ROWS = 20           # 前端轨迹每步保留的行数
DEFAULT_VERSIONS = ["API4.1", "API5.0", "API5.1", "API6.0", "API6.1"]


# ─── 只读护栏 ──────────────────────────────────────────

# 整词、忽略大小写。CALL/LOAD/FOREACH/apoc/gds 全拦：
# 宁可误伤（模型改写重试），不可放过写操作。
FORBIDDEN_KEYWORDS = (
    r"\bCREATE\b", r"\bMERGE\b", r"\bSET\b", r"\bDELETE\b",
    r"\bDETACH\b", r"\bREMOVE\b", r"\bDROP\b", r"\bLOAD\b",
    r"\bFOREACH\b", r"\bCALL\b", r"\bSTART\b",
    r"\bapoc\b", r"\bgds\b",
)
FORBIDDEN_RE = re.compile("|".join(FORBIDDEN_KEYWORDS), re.IGNORECASE)

# LIMIT 子句：数字（模型写的，可钳制）或 $参数（内部工具写的，信任）
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+|\$\w+)", re.IGNORECASE)


def _strip_comments(q):
    """剥掉 /* */ 与 // 注释再检查。正则朴素，误杀可接受，放过不可接受。"""
    q = re.sub(r"/\*.*?\*/", " ", q, flags=re.DOTALL)
    q = re.sub(r"//[^\n]*", " ", q)
    return q


def validate_cypher(query):
    """返回 (ok, error, cleaned_query)。

    cleaned_query：剥注释后的查询，附带强制 LIMIT（内部工具的 $参数 LIMIT 保留）。
    """
    if not query or not query.strip():
        return False, "查询为空", ""
    q = query.strip()
    if ";" in q:
        return False, "不允许包含多条语句（分号）", q
    bare = _strip_comments(q)
    m = FORBIDDEN_RE.search(bare)
    if m:
        return False, (f"查询被安全策略拦截：检测到只读禁止的关键字 {m.group(0).upper()}。"
                       "本工具只允许 MATCH...RETURN 形式的只读查询，请改写后重试。"), q

    # LIMIT 强制
    cleaned = bare.rstrip().rstrip(";")
    lm = _LIMIT_RE.search(cleaned)
    if lm:
        if lm.group(1).isdigit() and int(lm.group(1)) > MAX_ROWS:
            cleaned = re.sub(r"\bLIMIT\s+\d+", f"LIMIT {MAX_ROWS}",
                             cleaned, count=1, flags=re.IGNORECASE)
        # $参数形式（内部工具）原样保留
    else:
        cleaned += f" LIMIT {MAX_ROWS}"
    return True, None, cleaned


def safe_execute_cypher(query, params=None):
    """护栏执行。返回 {ok, rows, error, cypher}。

    - read-only 会话仅纵深防御（Neo4j Community 不强制），真正的防线是关键字黑名单
    - timeout 尽力而为：驱动不支持该 kwarg 时退化为普通 run
    """
    ok, err, cleaned = validate_cypher(query)
    if not ok:
        return {"ok": False, "rows": [], "error": err, "cypher": query}
    try:
        from app import driver  # 懒导入，避免循环
        from neo4j import READ_ACCESS
        with driver.session(default_access_mode=READ_ACCESS) as s:
            try:
                result = s.run(cleaned, timeout=15, **(params or {}))
            except Exception:
                # timeout 在该驱动版本不被支持时退化为普通 run；
                # 真查询错误会在下面的迭代中再次抛出
                result = s.run(cleaned, **(params or {}))
            rows = [dict(r) for r in result]
        return {"ok": True, "rows": rows[:MAX_ROWS], "count": len(rows[:MAX_ROWS]),
                "error": None, "cypher": cleaned}
    except Exception as e:
        return {"ok": False, "rows": [],
                "error": (f"Neo4j 查询执行失败：{str(e)[:300]}。请检查 Cypher 语法、"
                          "属性名（type/sdk_version 等均为小写）和版本号后重试。"),
                "cypher": cleaned}


def _versions():
    try:
        from app import VERSIONS
        return VERSIONS
    except Exception:
        return DEFAULT_VERSIONS


def _err(msg):
    return {"ok": False, "error": msg}


def _ok(rows, count=None, note=None):
    return {"ok": True, "rows": rows,
            "count": len(rows) if count is None else count,
            "note": note or ""}


# ─── 工具实现 ──────────────────────────────────────────

def tool_run_cypher(args):
    """通用逃生舱：模型手写的只读 Cypher，过护栏执行。"""
    query = args.get("query", "")
    return safe_execute_cypher(query)


def tool_search_api(args):
    """按关键字搜索 API（name/description/module 三字段模糊匹配）。"""
    kw = str(args.get("keyword", "")).strip()
    if not kw:
        return _err("keyword 不能为空")
    limit = min(int(args.get("limit") or 20), MAX_ROWS)
    ver = args.get("version")
    ver_clause = "AND n.sdk_version = $ver" if ver in _versions() else ""
    query = f"""
        MATCH (n)
        WHERE n.type IN ['class','interface','enum','method','property']
          AND (n.name CONTAINS $kw OR n.description CONTAINS $kw OR n.module CONTAINS $kw)
          {ver_clause}
        RETURN labels(n)[0] AS type, n.name AS name, n.module AS module,
               n.sdk_version AS sdk_version, COALESCE(n.description,'') AS description
        ORDER BY type, name
        LIMIT $lim
    """
    params = {"kw": kw, "lim": limit}
    if ver in _versions():
        params["ver"] = ver
    res = safe_execute_cypher(query, params)
    if res["ok"]:
        res["note"] = f"搜索关键字'{kw}'，共 {res['count']} 条（截断显示前 {len(res['rows'])} 条）"
    return res


def tool_list_modules(args):
    """列出某版本模块及其中类/接口/枚举数量，降序。"""
    ver = args.get("version") or "API6.1"
    if ver not in _versions():
        return _err(f"无效版本 {ver}，可选：{', '.join(_versions())}")
    query = """
        MATCH (n {sdk_version: $ver})
        WHERE n.type IN ['class','interface','enum']
        RETURN n.module AS module, count(n) AS cnt
        ORDER BY cnt DESC
        LIMIT $lim
    """
    return safe_execute_cypher(query, {"ver": ver, "lim": 30})


def tool_compare_versions(args):
    """跨版本对比：name+type+coalesce(parent_name) 组合键（不用 uid）。"""
    old_ver = args.get("old_version", "")
    new_ver = args.get("new_version", "")
    direction = args.get("direction") or "added"
    vers = _versions()
    if old_ver not in vers or new_ver not in vers:
        return _err(f"版本号无效，可选：{', '.join(vers)}")
    if old_ver == new_ver:
        return _err("old_version 与 new_version 相同，无法对比")
    if direction not in ("added", "removed"):
        return _err("direction 只能是 added 或 removed")
    page = max(int(args.get("page") or 1), 1)
    per_page = min(max(int(args.get("per_page") or 20), 1), MAX_ROWS)
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
                   n_new.name AS name, COALESCE(n_new.description,'') AS description
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
                   n_old.name AS name, COALESCE(n_old.description,'') AS description
            ORDER BY module, type, name
            SKIP $skip LIMIT $per
        """
    res = safe_execute_cypher(query, {"old": old_ver, "new": new_ver,
                                      "skip": skip, "per": per_page})
    if res["ok"]:
        res["note"] = (f"{new_ver} 相比 {old_ver} {('新增' if direction == 'added' else '删除')}"
                       f"的 API（第{page}页，{len(res['rows'])} 条）")
    return res


def tool_overview_stats(args):
    """各版本节点总数、类型分布、模块数。"""
    try:
        from app import run_cypher  # 懒导入
        rows = run_cypher("""
            MATCH (n) WHERE n.sdk_version IS NOT NULL
            RETURN n.sdk_version AS version, labels(n)[0] AS label, count(n) AS cnt
            ORDER BY version, cnt DESC
        """)
        mods = run_cypher("""
            MATCH (m:Module) RETURN m.sdk_version AS version, count(m) AS modules
            ORDER BY version
        """)
        mod_map = {m["version"]: m["modules"] for m in mods}
        versions = {}
        for r in rows:
            v = r["version"]
            if v not in versions:
                versions[v] = {"version": v, "total": 0,
                               "types": {}, "modules": mod_map.get(v, 0)}
            versions[v]["total"] += r["cnt"]
            versions[v]["types"][r["label"]] = r["cnt"]
        out = [{"version": v, **info} for v, info in versions.items()]
        return _ok(out, note="每个版本的总节点数、类型分布与模块数")
    except Exception as e:
        return _err(f"统计查询失败：{str(e)[:200]}")


def tool_growth_trend(args):
    """各类型 API 跨版本数量趋势（原始行）。"""
    query = """
        MATCH (n) WHERE n.sdk_version IN ['API4.1','API5.0','API5.1','API6.0','API6.1']
          AND n.type IN ['class','interface','enum','method','property']
        RETURN n.sdk_version AS version, n.type AS type, count(n) AS cnt
        ORDER BY version, type
    """
    res = safe_execute_cypher(query)
    if res["ok"]:
        res["note"] = "5 类 API（class/interface/enum/method/property）在 5 个版本中的数量"
    return res


def tool_graph_neighbors(args):
    """类/接口/枚举详情：成员方法/属性、继承父类、所属模块。"""
    name = str(args.get("class_name", "")).strip()
    if not name:
        return _err("class_name 不能为空")
    ver = args.get("version")
    try:
        from app import run_cypher  # 懒导入
        if ver in _versions():
            nodes = run_cypher("""
                MATCH (n {name: $cn, sdk_version: $ver})
                WHERE n.type IN ['class','interface','enum']
                RETURN n.uid AS uid, labels(n)[0] AS type, n.name AS name,
                       n.module AS module, n.sdk_version AS sdk_version,
                       COALESCE(n.description,'') AS description,
                       COALESCE(n.since,'') AS since, COALESCE(n.extends,'') AS extends
                LIMIT 1
            """, cn=name, ver=ver)
        else:
            nodes = run_cypher("""
                MATCH (n {name: $cn})
                WHERE n.type IN ['class','interface','enum']
                RETURN n.uid AS uid, labels(n)[0] AS type, n.name AS name,
                       n.module AS module, n.sdk_version AS sdk_version,
                       COALESCE(n.description,'') AS description,
                       COALESCE(n.since,'') AS since, COALESCE(n.extends,'') AS extends
                ORDER BY n.sdk_version DESC LIMIT 5
            """, cn=name)
        if not nodes:
            return _err(f"未找到名为 '{name}' 的类/接口/枚举（名称需精确匹配）")
        node = nodes[0]
        uid = node["uid"]
        members = run_cypher("""
            MATCH (child)-[:HAS_PARENT]->(parent {uid: $uid})
            WHERE child.type IN ['method','property']
            RETURN child.type AS type, child.name AS name,
                   COALESCE(child.return_type, child.property_type, '') AS sig
            ORDER BY type, name LIMIT 100
        """, uid=uid)
        parents = run_cypher("""
            MATCH (n {uid: $uid})-[:HAS_PARENT]->(p)
            RETURN labels(p)[0] AS type, p.name AS name, p.sdk_version AS sdk_version
            LIMIT 20
        """, uid=uid)
        node["member_count"] = len(members)
        return _ok([node], note="节点详情见 rows[0]；members 为其方法/属性；parents 为继承父类"), \
            None
    except Exception as e:
        return _err(f"查询失败：{str(e)[:200]}"), None


# ─── 工具 schema（传给 DeepSeek） ────────────────────────

def _tool(name, desc, props, required):
    return {"type": "function", "function": {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props,
                       "required": required, "additionalProperties": False},
    }}


_VERSION_PROP = {"type": "string", "enum": DEFAULT_VERSIONS,
                 "description": "版本号，可选，默认 API6.1"}

TOOLS = [
    _tool("search_api",
          "按关键字搜索API。keyword 会同时匹配节点 name、description 和 module 字段"
          "（如'蓝牙'或'bluetooth'）。可选指定版本。",
          {"keyword": {"type": "string", "description": "搜索关键字"},
           "version": dict(_VERSION_PROP),
           "limit": {"type": "integer", "description": "返回条数，默认20，最大50"}},
          ["keyword"]),
    _tool("list_modules",
          "列出某版本模块及其中类/接口/枚举数量，按数量降序。",
          {"version": dict(_VERSION_PROP)},
          []),
    _tool("compare_versions",
          "对比两个版本的API差异。direction=added 表示 new_version 相比 old_version 新增的API，"
          "direction=removed 表示删除的。内部使用 name+类型+parent_name 组合键对比（不是uid），"
          "已处理跨版本父类改名问题。",
          {"old_version": {"type": "string", "enum": DEFAULT_VERSIONS},
           "new_version": {"type": "string", "enum": DEFAULT_VERSIONS},
           "direction": {"type": "string", "enum": ["added", "removed"],
                         "description": "默认 added"},
           "page": {"type": "integer", "description": "页码，从1开始，默认1"},
           "per_page": {"type": "integer", "description": "每页条数，默认20，最大50"}},
          ["old_version", "new_version"]),
    _tool("overview_stats",
          "获取所有版本的总体统计：每个版本的节点总数、各类型（Class/Interface/Enum/Method/Property等）数量、模块数量。",
          {}, []),
    _tool("growth_trend",
          "获取各版本 class/interface/enum/method/property 的数量增长趋势数据。",
          {}, []),
    _tool("graph_neighbors",
          "查看某个类/接口/枚举的详细信息及其关联：所属模块、成员方法/属性、继承的父类。"
          "class_name 需精确匹配节点 name。",
          {"class_name": {"type": "string", "description": "类/接口/枚举名称"},
           "version": dict(_VERSION_PROP)},
          ["class_name"]),
    _tool("run_cypher",
          "直接执行只读Cypher查询。仅允许 MATCH...RETURN，禁止 CREATE/MERGE/SET/DELETE 等写操作。\n"
          "数据模型：节点标签 Module/Class/Interface/Enum/Method/Property/TypeAlias/EnumMember/Struct/Namespace；"
          "关键属性（全部小写）：name, type, sdk_version, parent_name, module, description, since, syscap, "
          "return_type, property_type；关系：(成员)-[:HAS_PARENT]->(父), (节点)-[:BELONGS_TO_MODULE]->(Module)。\n"
          "注意：1) 必须过滤 sdk_version；2) 属性名小写，type 取值小写如 'class'；"
          "3) 跨版本对比用 name+'|'+labels(n)[0]+'|'+coalesce(n.parent_name,'') 组合键而非 uid；"
          "4) 结果自动限制最多50条。优先使用其他专用工具，仅当它们无法满足时才用本工具。",
          {"query": {"type": "string", "description": "只读 Cypher 查询语句"}},
          ["query"]),
]


# ─── Agent 系统提示词 ───────────────────────────────────

AGENT_SYSTEM_PROMPT = """你是 HarmonyOS API 跨版本分析助手，通过工具查询 Neo4j 知识图谱回答问题。
数据覆盖 5 个版本：API4.1, API5.0, API5.1, API6.0, API6.1。

## 工作方式
1. 优先使用专用工具（search_api、compare_versions、overview_stats 等），它们已封装常见复杂查询。
2. 只有专用工具无法满足时才使用 run_cypher 直接写只读 Cypher。
3. 一次工具调用无法回答时，可多次调用；拿到数据后必须给出最终中文回答。
4. 如果某个工具反复报错（如查询被安全策略拦截），不要死循环重试，改用其他工具或基于已有信息回答，
   并简要说明数据获取的限制。
5. 回答要求：最终回答必须完全使用中文（包括开头和过渡语，不要出现"I have the information"等英文引导语）、
   要点清晰、引用具体数字（新增X个、占比Y%等）。
   闲聊或与API数据无关的问题直接回答，不要调用工具。"""


# ─── 工具分发与 Agent 循环 ──────────────────────────────

TOOL_IMPLS = {
    "run_cypher": tool_run_cypher,
    "search_api": tool_search_api,
    "list_modules": tool_list_modules,
    "compare_versions": tool_compare_versions,
    "overview_stats": tool_overview_stats,
    "growth_trend": tool_growth_trend,
    "graph_neighbors": tool_graph_neighbors,
}


def execute_tool(name, args):
    """执行单个工具，返回 (step_dict, content_str_for_model)。绝不抛异常。"""
    impl = TOOL_IMPLS.get(name)
    if impl is None:
        step = {"tool": name, "args": args, "ok": False, "error": f"未知工具 {name}",
                "cypher": None, "result_summary": "未知工具", "rows": []}
        content = json.dumps({"ok": False, "error": f"未知工具 {name}"}, ensure_ascii=False)
        return step, content
    try:
        res = impl(args)
        if isinstance(res, tuple):  # graph_neighbors 返回 (res, None) 双值，兼容
            res = res[0]
    except Exception as e:
        res = _err(f"工具执行异常：{str(e)[:300]}")
    cypher = res.get("cypher")
    rows = res.get("rows", []) or []
    if res.get("ok"):
        summary = f"返回 {res.get('count', len(rows))} 条结果"
        if res.get("note"):
            summary = res["note"]
    else:
        summary = f"执行失败：{res.get('error', '')[:120]}"
    step = {"tool": name, "args": args, "ok": bool(res.get("ok")),
            "error": res.get("error"), "cypher": cypher,
            "result_summary": summary, "rows": rows[:MAX_STEP_ROWS]}
    content = {k: v for k, v in res.items() if k != "cypher"}
    s = json.dumps(content, ensure_ascii=False, default=str)
    if len(s) > MAX_TOOL_RESULT_CHARS:
        s = s[:MAX_TOOL_RESULT_CHARS] + f' ...（输出过长已截断，共 {len(rows)} 条）'
    return step, s


def run_agent(user_msg, history, ai_caller, max_iterations=MAX_ITERATIONS):
    """Agent 循环。返回 /api/chat 响应 dict；返回 None 表示应回退单发模式。

    ai_caller: 即 app.call_ai(messages, tools=...) -> 原始响应 dict 或 None
    """
    messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
    for h in history[-8:]:
        if isinstance(h, dict) and h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    steps, last_rows, last_cypher = [], None, None
    seen_calls = {}  # (tool, args_json) -> 次数，用于无进展判定

    for _ in range(max_iterations):
        resp = ai_caller(messages, tools=TOOLS)
        if resp is None:
            return None  # AI 不可用 → 由 app.py 走单发 fallback
        try:
            choice = resp["choices"][0]
        except (KeyError, IndexError):
            return None
        msg = choice.get("message") or {}
        tool_calls = msg.get("tool_calls") or []

        if tool_calls:
            # 完整保留 assistant 消息（含 content/reasoning_content/tool_calls），
            # thinking 模式下漏传 reasoning_content 会触发 400
            messages.append(dict(msg))
            for tc in tool_calls:
                name = tc.get("function", {}).get("name", "")
                raw_args = tc.get("function", {}).get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if raw_args.strip() else {}
                    if not isinstance(args, dict):
                        args = {}
                except json.JSONDecodeError:
                    args = {}
                    messages.append({"role": "tool", "tool_call_id": tc.get("id"),
                                     "content": json.dumps(
                                         {"ok": False,
                                          "error": f"工具参数JSON解析失败：{raw_args[:200]}，请重新生成合法JSON参数。"},
                                         ensure_ascii=False)})
                    steps.append({"tool": name, "args": {}, "ok": False,
                                  "error": "参数JSON解析失败", "cypher": None,
                                  "result_summary": "参数解析失败", "rows": []})
                    continue
                step, content = execute_tool(name, args)
                steps.append(step)
                if step["ok"] and step.get("rows"):
                    last_rows, last_cypher = step["rows"], step.get("cypher")
                messages.append({"role": "tool", "tool_call_id": tc.get("id"),
                                 "content": content})
                # 无进展判定：同一 (工具, 参数) 重复出现 → 提前终止，防死循环
                call_key = (name, json.dumps(args, ensure_ascii=False, sort_keys=True))
                seen_calls[call_key] = seen_calls.get(call_key, 0) + 1
                if seen_calls[call_key] >= 2:
                    return {"mode": "agent",
                            "answer": ("检测到工具被重复调用且未取得新结果，已停止查询。"
                                       "以下是最后获取的数据，可尝试换个问法。"),
                            "steps": steps, "cypher": last_cypher, "results": last_rows}
            continue

        answer = (msg.get("content") or "").strip()
        if not answer:
            answer = "（AI 未生成回答）"
        return {"mode": "agent", "answer": answer, "steps": steps,
                "cypher": last_cypher,
                "results": last_rows if last_rows else (steps[-1]["rows"] if steps else None)}

    return {"mode": "agent",
            "answer": "已执行多轮查询但仍未获得完整结论（达到最大查询轮数）。"
                      "以下是最后获取的结果，可进一步细化提问。",
            "steps": steps, "cypher": last_cypher, "results": last_rows}
