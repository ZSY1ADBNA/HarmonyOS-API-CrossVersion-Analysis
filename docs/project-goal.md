# 项目目标与验收方向

## 项目目标

制作一个查询合适 API 的工具。用户描述自己的需求，工具接入 AI；AI 收到请求后结合 RAG 库，查询能符合需求的 API，推荐合适的一个或多个 API，并说明各个 API 的差异、选择理由和适用条件。

这里的 RAG 是“先检索项目数据及文档证据，再让 AI 基于这些证据回答”。Neo4j 可作为检索源，不要求一开始就引入向量数据库。当前项目标签、真实 SDK/API Level、系统能力、权限和废弃状态应作为推荐约束；缺少目标版本等关键条件时先澄清，不能把未知信息当已满足。

## 预期流程

用户需求及版本约束 → 检索候选 API 和原始文档 → 核对适用性 → AI 根据检索结果比较推荐 → 网站展示推荐与来源。

每个推荐至少说明：API 名称、所属模块/导入方式、适用版本、解决的需求、选择理由、与其他候选的差异及来源。权限、系统能力、废弃、平台限制未知时明确未知。无证据或无匹配时说明检索不足，不编造 API。相关类型或辅助 API 可以作为组合推荐，但要说明用途和调用关系的证据。

## 当前状态（2026-10-05 静态核对）

依据 master 提交 131a142074d68a322aafbfef9ac3f3d77b85caa2：
- 已有多版本 JSON、Neo4j 导入、图谱展示和 AI 聊天入口。
- app.py 的 /api/chat 先让模型生成 answer 和 cypher，再执行 cypher；结果没有交回 AI 生成最终推荐，尚未形成检索结果支撑回答的闭环。
- SDK 过滤与条数限制写在提示词中，后台未强制检查；模型查询直接交给数据库执行，没有服务端只读约束。
- 提示词允许 cypher=null，但代码对该值直接 .strip()，存在合法空查询导致异常的路径。
- 当前以跨版本分析为主，尚未建立推荐结果的固定字段、证据来源与验收集。不得把现有聊天称为完整、已验收的 RAG 推荐工具。
- JSON 抽样 @ohos.bluetooth.access.json 有 31 条节点，包含参数/错误信息等字段；导入器映射不覆盖所有这些字段，推荐所需信息需逐项检查。@since 抽样含 ArkTS 版本映射文本，不能粗略当成单一数字版本。
- 数据库和网站实测尚未完成。用户提供网址 http://47.114.40.66:5000/；网页工具未读取成功，不能据此认定服务故障。

## 完成标准

用户给出需求及目标版本后，返回有数据/文档依据的可用候选；多个候选能解释功能、约束和使用成本的差异。缺失条件、无候选、模型不可用、查询失败时都有清楚说明。

验收覆盖需求检索、版本过滤、证据可追溯、比较解释、无匹配与错误处理，并检查模型输出不能改变数据库。详细任务、复现步骤和完成效果统一见 [workplan](../workplan.md)。

## 只读现场检查（待执行）

由有权限成员在实际 Neo4j Browser 执行并提供去除凭据的输出；这些查询不修改图谱：

```cypher
CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition;
MATCH (n) RETURN labels(n) AS labels, n.sdk_version AS version, count(*) AS count;
MATCH ()-[r]->() RETURN type(r) AS relation, count(*) AS count;
MATCH (n) WHERE n.sdk_version IS NOT NULL
RETURN n.sdk_version AS version, count(*) AS total,
sum(CASE WHEN coalesce(n.description,'')='' THEN 1 ELSE 0 END) AS missing_description,
sum(CASE WHEN coalesce(n.module,'')='' THEN 1 ELSE 0 END) AS missing_module;
MATCH (n) WHERE n.uid IS NOT NULL
WITH n.uid AS uid, count(*) AS c WHERE c > 1 RETURN uid, c LIMIT 20;
```

UID 重复查询无法发现历史 MERGE 已覆盖掉的节点，必须同时与 JSON/原始源码样本核对。先确认部署提交与数据库版本，再比较网站 /api/versions、/api/overview 等只读接口和数据库实际结果。AI 聊天测试须在查询只读控制完善的测试实例进行。
