"""导入后图谱检查：总节点/各版本节点数、Unknown/unnamed 残留、重复 uid。
用法：set NEO4J_PASSWORD=<密码> 后执行 python _check_graph.py [--out 06_logs/graph_check_YYYYMMDD.txt]
连接凭据取自环境变量 NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD,不写入代码。
"""
import os
import sys
from neo4j import GraphDatabase

URI = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687")
USER = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD", "")


def main():
    if not PASSWORD:
        sys.exit("未设置 NEO4J_PASSWORD 环境变量")
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    lines = []
    with driver.session() as s:
        total = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        lines.append(f"总节点: {total}")
        lines.append("[各版本节点数]")
        for r in s.run("MATCH (n) RETURN n.sdk_version AS v, count(n) AS c ORDER BY v"):
            lines.append(f"  {r['v']}: {r['c']}")
        lines.append("[重复 uid(应为 0)]")
        dup = list(s.run("MATCH (n) WITH n.uid AS u, count(*) AS c WHERE c > 1 RETURN u, c ORDER BY c DESC LIMIT 20"))
        if not dup:
            lines.append("  无")
        for r in dup:
            lines.append(f"  {r['u']}  x{r['c']}")
        lines.append("[Unknown 类型节点数(跨文件合并后残留)]")
        u = s.run("MATCH (n:Unknown) RETURN count(n) AS c").single()["c"]
        lines.append(f"  {u}")
        lines.append("[unnamed 名称节点数]")
        u = s.run("MATCH (n) WHERE n.name = 'unnamed' RETURN count(n) AS c").single()["c"]
        lines.append(f"  {u}")
        lines.append("[含文件标识 @xxxxxxxx 的节点数(修复后应>0)]")
        # 注意:模块名也含 @(如 @kit.ArkUI),需锚定末尾 8 位十六进制,不能用 CONTAINS '@'
        u = s.run("MATCH (n) WHERE n.uid =~ '.*@[0-9a-f]{8}$' RETURN count(n) AS c").single()["c"]
        lines.append(f"  {u}")
        lines.append("[含 #n 重载后缀的节点数]")
        u = s.run("MATCH (n) WHERE n.uid CONTAINS '#' RETURN count(n) AS c").single()["c"]
        lines.append(f"  {u}")
    driver.close()

    text = "\n".join(lines)
    print(text)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
