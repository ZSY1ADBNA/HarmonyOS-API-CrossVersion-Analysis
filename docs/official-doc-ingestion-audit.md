# 官方说明文档全量入库审计与踩坑记录

最后更新：2026-10-09（Asia/Shanghai）
适用阶段：总体计划 1.0 步骤 05A、05B 及后续 Kit 扩展任务
核心原则：**不试图用单一通用脚本解决全部 52 个 Kit 的所有排版差异；后续 Kit 与版本入库由对应 Agent 结合模块特征按需编写或适配专用脚本。**

---

## 一、审计背景与核心结论

为评估当前官方文档解析与检索脚本（`doc_rag/` 体系）能否直接推广至全量 52 个 Kit 及全部 4 个大版本（`v6.0.0.1-Release`、`v6.1-LTS`、`v7.0-Release`、`docs-master`），团队对 `official/` 目录下全部 **13,887 个 Markdown 文件** 开展了全量压力测试与规则审计。

**审计核心定论**：
1. **语法运行安全（0 Crash）**：现有解析器具备良好的 Python 语法健壮性，全量扫描 13,887 个文档未触发任何未捕获的运行时异常（Unhandled Exceptions）。
2. **数据逻辑缺陷严重（不可盲目全量入库）**：在数据完整性、主键唯一性、索引同步、层级归属和数据库性能五个维度存在硬伤。如果直接用单一脚本盲目全量入库，会导致大量数据静默丢失、属性错位覆盖及性能崩溃。
3. **后续协作方针**：后续扩展其他 Kit（如 ArkUI、AbilityKit、Native C-API）时，各 Agent 必须阅读本文档列出的已知陷阱，针对目标模块的具体 Markdown 排版特征按需调整或独立编写解析逻辑，严禁未经校验直接全量灌库。

---

## 二、六大关键隐患与技术深层成因

### 1. 废弃类 H1 识别失败导致参数被错当属性与主键碰撞（P0 阻断）
- **现象**：全量 4 个版本中存在 **440 ~ 500 次主键静默覆盖**（后一条记录直接抹掉前一条）。
- **根因分析**：
  - 官方文档中部分标题为 `# 废弃的Interface (VideoPlayer)`，正则表达式 `r"^#\s+(Interface|Class...)"` 因前置中文字符未能识别出容器，导致容器名为空。
  - 下属二级标题方法（如 `## setDisplaySurface`）被降级兜底划分为 `class`。
  - 解析器随后将该方法内部的**参数表格**（`| 参数名 | 类型 |`）误判为**类属性表格**；当该方法存在多个重载、参数同名时，生成的 `chunk_id` 完全相同，在 SQLite 中触发 `REPLACE` 覆盖。
- **影响**：不仅丢失了数据，而且方法参数被污染为虚假的“类属性”。

### 2. 无二级标题文档整篇静默蒸发（Zero-Chunk Loss，P0 阻断）
- **现象**：每个版本均有 **83 ~ 86 个文件** 入库结果为 0 个 Chunk（完全未入库且不报错）。
- **根因分析**：
  - 解析器强制依赖 `^(#{2,4})\s+(.+)$` 正则匹配二级至四级标题。
  - 若文档仅包含 `# H1`，正文直接使用列表项或表格罗列内容，匹配列表为空，函数直接 `return []`。
- **影响**：
  - 核心文档 **`commonEvent-definitions.md`（916 行全量系统公共事件定义）** 被整体丢弃；
  - 各设备 SysCap 规范列表（`phone-syscap-list.md` 等 52KB）、ArkUI 基础样式文档均未入库。

### 3. C-API 枚举与错误码表格双重拦截丢失（P0 阻断）
- **现象**：Native / C-API 头文件文档（如 `apis-ipc-kit/capi-ipc-error-code-h.md`、`capi-relational-store-error-code-h.md`）中的枚举错误码提取出的属性条目全为 **0**。
- **根因分析**：
  - **第一层拦截**：C 头文件标题常为 `## 枚举类型说明`，未含 "Enum" 被划为 `class`，其下的具体枚举被误归为 `method`。在属性解析前置检查中，`category in ["method", "function"]` 被提前 `return []` 拦截退出；
  - **第二层拦截**：官方 C-API 表头格式为 `| 枚举值 | 描述 |` 或 `| 字段 | 描述 |`，现有表头关键词匹配规则缺少 `枚举值`、`枚举项`、`字段`。

### 4. ArkUI 组件层级脱节破坏精确检索（P1）
- **现象**：组件（如 `# Button`、`# Text`）未带 `Class/Interface` 关键字，组件属性（如 `### fontSize`）位于 `## 属性` 之下，父级名字被解析成字符串 `"属性"`。
- **影响**：
  - `full_name` 变为 `Button.属性.fontSize`；
  - 调用 `DocRetriever.search_by_name("Button.fontSize")` 精确匹配与模糊匹配**全部返回 0 条**。

### 5. FTS5 无索引全表扫描删除引发性能崩溃与孤儿脏索引（P1）
- **性能悬崖**：
  - 在 `doc_chunks_fts` 中，`chunk_id` 被定义为 `UNINDEXED`。
  - 每批入库 500 条数据时，执行 500 次 `DELETE FROM doc_chunks_fts WHERE chunk_id = ?;`，SQLite 必须进行 500 次全表扫描。
  - 全量 4 个版本共约 **323,633 个 Chunks**，全表扫描将累计执行 **524 亿次行比较**，单纯在扫描删除上就要消耗 **~78 分钟**（而正常批量插入仅需 2 秒以内，性能劣化 2,000 倍以上）。
- **孤儿索引**：
  - 若批次内发生主键覆盖，主表仅存 1 条，但 FTS 虚表被无条件插入多条，产生孤儿脏索引。当前库中已存在 7 条脏索引。

### 6. CLI 默认参数导致跨版本与跨 Kit 串味覆盖（P1）
- **现象**：`ingest_official_docs.py` 中 `--version` 默认设为 `"v6.0.0.1-Release"`，`--kit` 默认设为 `"apis-network-kit"`。
- **风险**：若后续操作者执行 `python ingest_official_docs.py --zip official/docs-OpenHarmony-v6.1-LTS-...zip` 未显式传参，脚本会将 v6.1 内容打上 v6.0 的版本标签写入库中，若加上 `--clear` 则会误清空已有 v6.0 数据。

---

## 三、给后续 Agent 的适配与开发指南

当接手后续新 Kit（如 ArkUI、AbilityKit、MediaKit、C-API）或新版本的文档解析与入库时，请严格遵守以下操作准则：

### 1. 坚持“按需小样本”验证原则
- **严禁全量一次性灌库**：每个新 Kit 入库前，先单独抽取 1~2 个代表性文件运行解析测试，打印生成的 `category`、`parent_title`、`api_name` 和抽取字段。
- **针对性调整解析逻辑**：
  - **若处理 ArkUI 组件**：需将 H1 组件名直接绑定为属性的 `parent_title`，确保 `Component.attribute` 格式可查；
  - **若处理 C-API / NDK**：需补充 `枚举值`、`枚举项`、`宏名称`、`结构体成员` 等表头映射，并绕过普通方法的提前返回逻辑；
  - **若处理规范/事件列表文档**：当缺少二级标题时，必须提供兜底的单块（Overview Chunk）抽取逻辑，不能静默返回空。

### 2. 数据库写入防坑准则
- **FTS5 写入优化**：不要在每次批量写入前循环执行无索引的 `DELETE`；仅在确认存在更新覆盖时按需精准处理，或优先依赖独立的版本重建模式。
- **批次去重**：向 SQLite 和 FTS 插入前，务必在内存中对 `batch` 按 `chunk_id` 执行去重，防止 FTS 虚表产生孤儿记录。
- **开启 WAL 模式**：
  ```sql
  PRAGMA journal_mode = WAL;
  PRAGMA synchronous = NORMAL;
  PRAGMA busy_timeout = 30000;
  ```
- **CLI 参数必须显式指定**：使用命令行脚本时，必须显式传入 `--version` 与 `--kit`，不要依赖默认缺省值。

---

## 四、相关文件索引

- 核心解析实现：[`doc_rag/parser.py`](../doc_rag/parser.py)
- 索引与数据库管理：[`doc_rag/indexer.py`](../doc_rag/indexer.py)
- 检索与对比引擎：[`doc_rag/retriever.py`](../doc_rag/retriever.py)
- 自动化测试套件：[`test_official_doc_rag.py`](../test_official_doc_rag.py)
- 任务追踪记录：[`workplan.md`](../workplan.md)
