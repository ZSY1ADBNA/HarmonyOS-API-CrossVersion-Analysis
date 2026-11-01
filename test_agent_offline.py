"""agent.py 离线测试：护栏 + Agent 循环（假 AI）+ 真工具冒烟（需本地 Neo4j）。

用法：
  python test_agent_offline.py            # 全部测试（真工具部分需要本地 Neo4j 7687 在跑）
  python test_agent_offline.py --no-db    # 跳过真工具冒烟，无需 Neo4j
"""
import json
import sys

import agent


def _tool_call_response(call_id, name, args):
    return {"choices": [{"message": {"role": "assistant", "content": None,
                                     "tool_calls": [
                                         {"id": call_id, "type": "function",
                                          "function": {"name": name, "arguments": args}}
                                     ]},
                         "finish_reason": "tool_calls"}]}


def _final_response(text):
    return {"choices": [{"message": {"role": "assistant", "content": text},
                         "finish_reason": "stop"}]}


# ─── 1. 护栏表驱动测试 ─────────────────────────────────

BAD_QUERIES = [
    "MATCH (n) DELETE n",
    "MERGE (n:Class {name:'x'})",
    "MATCH (n) SET n.x=1",
    "MATCH (n) DETACH DELETE n",
    "CREATE (n)",
    "MATCH (n) REMOVE n.p",
    "CALL apoc.periodic.iterate('MATCH (n) RETURN n','DELETE n',{})",
    "LOAD CSV FROM 'http://x' AS r RETURN r",
    "MATCH (n) FOREACH (x IN [1] | CREATE (y))",
    "MATCH (n) DROP n",
    "MATCH (n) RETURN n; MATCH (m) DELETE m",   # 多语句走私
    "MATCH (n) WHERE n.desc = 'set me up' RETURN n",  # 字符串误伤可接受，必须拒绝
]

GOOD_QUERIES = [
    "MATCH (n {sdk_version:'API6.0'}) RETURN n.name LIMIT 10",
    "MATCH (n) WHERE n.name CONTAINS 'bluetooth' RETURN n",
    "MATCH (n) RETURN n ORDER BY n.name",
    "MATCH (a)-[:HAS_PARENT]->(b) RETURN a.name, b.name LIMIT 20",
    # 注释会被剥掉后再检查，注释内容不会执行，放行是安全的
    "// 注释里写 delete 不构成威胁\nMATCH (n) RETURN n",
]


def test_guardrail():
    for q in BAD_QUERIES:
        ok, err, cleaned = agent.validate_cypher(q)
        assert not ok, f"应拒绝但放行: {q!r} (err={err!r})"
    for q in GOOD_QUERIES:
        ok, err, cleaned = agent.validate_cypher(q)
        assert ok, f"应放行但拒绝: {q!r} (err={err!r})"
    # LIMIT 强制
    _, _, c = agent.validate_cypher("MATCH (n) RETURN n")
    assert "LIMIT 50" in c, c
    _, _, c = agent.validate_cypher("MATCH (n) RETURN n LIMIT 100000")
    assert "LIMIT 50" in c and "100000" not in c, c
    _, _, c = agent.validate_cypher("MATCH (n) RETURN n LIMIT 10")
    assert "LIMIT 10" in c and "LIMIT 50" not in c, c
    # 内部工具的 $参数 LIMIT 保留
    _, _, c = agent.validate_cypher("MATCH (n) RETURN n LIMIT $lim")
    assert "LIMIT $lim" in c, c
    print("[PASS] 护栏测试通过（%d 坏查询全拒，%d 好查询全放行）"
          % (len(BAD_QUERIES), len(GOOD_QUERIES)))


# ─── 2. Agent 循环测试（假 AI，无网络） ──────────────────

def test_agent_loop():
    captured = {}
    script = [
        _tool_call_response("call_1", "list_modules", '{"version": "API6.0"}'),
        _final_response("API6.0 共有 45 个模块。"),
    ]

    def fake_ai(messages, tools=None, max_tokens=1024):
        captured["messages"] = messages
        captured["tools"] = tools
        return script.pop(0)

    out = agent.run_agent("API6.0有哪些模块？", [], fake_ai)
    assert out["mode"] == "agent", out
    assert out["steps"][0]["tool"] == "list_modules", out["steps"]
    assert captured["tools"] is not None and len(captured["tools"]) == 7
    # role=tool 必须紧跟带 tool_calls 的 assistant 消息且 tool_call_id 配对
    msgs = captured["messages"]
    tc_idx = next(i for i, m in enumerate(msgs) if m.get("tool_calls"))
    assert msgs[tc_idx + 1]["role"] == "tool"
    assert msgs[tc_idx + 1]["tool_call_id"] == "call_1"
    print("[PASS] Agent 循环测试通过（工具调用 → tool 消息配对 → 最终回答）")


def test_malformed_args_and_repeat_break():
    # 畸形参数：循环不崩溃，回传中文错误后继续
    script = [
        _tool_call_response("c1", "search_api", "{bad json"),
        _final_response("参数错误，我重新回答。"),
    ]

    def fake_ai(messages, tools=None, max_tokens=1024):
        return script.pop(0)

    out = agent.run_agent("搜索蓝牙", [], fake_ai)
    assert out["mode"] == "agent"
    assert out["steps"][0]["error"] == "参数JSON解析失败"
    print("[PASS] 畸形参数测试通过")

    # 同一 (工具, 参数) 重复 2 次 → 无进展终止
    script = [
        _tool_call_response("c1", "run_cypher",
                            '{"query": "MATCH (n) CREATE (m)"}'),
        _tool_call_response("c2", "run_cypher",
                            '{"query": "MATCH (n) CREATE (m)"}'),
    ]

    def fake_ai2(messages, tools=None, max_tokens=1024):
        return script.pop(0)

    out = agent.run_agent("创建节点", [], fake_ai2)
    assert out["mode"] == "agent" and len(out["steps"]) == 2
    assert "重复调用" in out["answer"], out["answer"]
    assert all(not s["ok"] for s in out["steps"])
    print("[PASS] 无进展终止测试通过（重复调用被拦，写查询被护栏拒绝）")


# ─── 3. 真工具冒烟（需本地 Neo4j） ───────────────────────

def test_real_tools():
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("[SKIP] 跳过真工具冒烟：neo4j 驱动未安装")
        return
    try:
        res = agent.safe_execute_cypher(
            "MATCH (n {sdk_version:'API5.0'}) RETURN n.name AS name LIMIT 3")
    except Exception as e:
        print(f"[SKIP] 跳过真工具冒烟：本地 Neo4j 不可用（{str(e)[:120]}）")
        return
    assert res["ok"], res["error"]
    assert 0 < len(res["rows"]) <= 3
    res2 = agent.tool_compare_versions(
        {"old_version": "API5.0", "new_version": "API5.1"})
    assert res2["ok"], res2["error"]
    print(f"[PASS] 真工具冒烟通过（safe_execute_cypher {len(res['rows'])} 条；"
          f"compare_versions 返回 {res2['count']} 条）")


if __name__ == "__main__":
    test_guardrail()
    test_agent_loop()
    test_malformed_args_and_repeat_break()
    if "--no-db" not in sys.argv:
        test_real_tools()
    print("\n全部通过 ")
