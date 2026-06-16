# HarmonyOS API 跨版本变化分析

基于 Neo4j 知识图谱，分析 OpenHarmony SDK 5 个版本（API4.1 → API5.0 → API5.1 → API6.0 + earliest API）的 API 变化。

## 架构

```
.d.ts 源码 → [extract] → JSON → [import] → Neo4j → [query] → 报告/图表
```

| 阶段 | 输入 | 输出 | 核心脚本 |
|------|------|------|----------|
| 提取源码 | Git 分支 | `01_source_files/` | `extract_versions.py` |
| 解析 API | `.d.ts` 文件 | `03_extracted_json/` | `batch_extract.py` → `extract_api_info.py` |
| 增强注释 | JSON | JSON（+结构化字段） | `enhance_json.py` |
| 导入图谱 | JSON | Neo4j 节点+关系 | `_run_import.py`（**正确版本**） |
| 生成报告 | Neo4j | Markdown | `_gen_report.py` |

## 环境

- **Neo4j**: `bolt://127.0.0.1:7687`，用户 `neo4j`，密码 `12345678`
- **Python**: 需 `neo4j` 驱动（`pip install neo4j`）
- **数据**: JSON 在 `03_extracted_json/`（已上传 GitHub），源码在 `01_source_files/`（需自行提取）
- **GitHub**: `ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis`

## 脚本速查

| 脚本 | 用途 | 运行方式 |
|------|------|----------|
| `_run_extract.py` | 一键提取所有版本 API 定义 | `python _run_extract.py` |
| `_run_import.py` | 一键导入 Neo4j（**用这个，别用 neo4j_import.py**） | `python _run_import.py` |
| `_gen_report.py` | 生成完整 Markdown 分析报告 | `python _gen_report.py` |
| `run_analysis.py` | 控制台输出 10 项分析结果 | `python 04_analysis_queries/run_analysis.py` |

> `neo4j_import.py` 有 UID 冲突 bug（不含版本前缀），不要使用。

## Neo4j 数据模型

**节点标签**: Module, Class, Interface, Enum, Method, Property, TypeAlias, EnumMember, Struct, Namespace, CallSignature, ExportImport

**关系**:
- `(node)-[:HAS_PARENT]->(parent)` — 成员→所属类/接口
- `(node)-[:BELONGS_TO_MODULE]->(module)` — 节点→所属模块

**关键属性**: `uid`（版本前缀格式 `{version}::{parent}::{name}`），`name`, `type`, `sdk_version`, `parent_name`, `module`, `description`, `since`, `syscap`, `return_type`, `property_type`, `decorators`, `extends`

## 跨版本查询模式

比较两个版本的关键：用 `name + type + parent_name` 组合键，不直接用 uid。

```cypher
// 模板：查 new_ver 比 old_ver 新增的类/接口
MATCH (n_old {sdk_version: 'old_ver'})
WHERE n_old.type IN ['class','interface','enum']
WITH collect(DISTINCT n_old.name + '|' + labels(n_old)[0] + '|' + coalesce(n_old.parent_name,'')) AS old_keys
MATCH (n_new {sdk_version: 'new_ver'})
WHERE n_new.type IN ['class','interface','enum']
  AND NOT (n_new.name + '|' + labels(n_new)[0] + '|' + coalesce(n_new.parent_name,'')) IN old_keys
RETURN n_new.module AS 模块, labels(n_new)[0] AS 类型, n_new.name AS 名称
```

把 `new_ver` 和 `old_ver` 互换就是查删除。

## 常见任务

### 从头跑通全流程
```
1. python extract_versions.py     # 从 SDK 仓库提取 .d.ts
2. python _run_extract.py         # 解析为 JSON
3. python _run_import.py          # 导入 Neo4j（会清空旧数据）
4. python _gen_report.py          # 生成报告
```

### 查看特定版本对比
打开 `http://localhost:7474`，执行 `cross_version_analysis.cypher` 中对应查询，改版本号即可。

### 查询知识图谱
结果面板点 **GRAPH** 按钮查看关系图。节点可拖拽，点击看属性卡片。

### 修改对比版本
所有查询中的 `'API4.1'` / `'API5.0'` 可替换为任意版本名（`API4.1`, `API5.0`, `API5.1`, `API6.0`）。

## 已知限制

1. 解析用正则而非 TS AST，复杂泛型/联合类型可能遗漏
2. 只检测新增/删除，不检测签名变化
3. 每次导入清空全库，无法增量追加
4. 路径和密码硬编码在脚本中
5. 源码 `01_source_files/` 需自行从 OpenHarmony SDK 仓库提取
