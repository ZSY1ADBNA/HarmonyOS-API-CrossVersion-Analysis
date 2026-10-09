# HarmonyOS API 跨版本变化分析

基于 Neo4j 知识图谱的 HarmonyOS SDK API 多版本迁移分析。

## 项目目标

制作需求驱动的 API 查询与推荐工具：用户描述需求，AI 结合 RAG 库检索合适 API，推荐一个或多个候选，说明差异、理由和适用条件。现有跨版本分析是支撑能力，完整推荐流程仍在建设中。

目标、当前差距和验收方向见[项目目标](docs/project-goal.md)，详细后续任务见[工作计划](workplan.md)。任务完成后在对应位置打勾，并记录实际效果和验证证据。

## OpenHarmony 查询助手实施计划

[总体计划 1.0](docs/openharmony-query-plan/总体计划1.0.md)及六个步骤说明：从两版本小样本修复提取与入库，分批扩大范围，将跨版本信息和差异查询融入全过程。包含任务关系图、工作量建议及 28 道待核对候选题；实施状态与验收统一见 workplan.md。

## 协作与 AI 接手入口

新成员或新 AI 按顺序阅读：

1. [CONTRIBUTING.md](CONTRIBUTING.md)：团队操作、提交与验证。
2. [AGENTS.md](AGENTS.md)：AI 开工、执行与交接。
3. [workplan.md](workplan.md)：任务、成果、验证证据、阻塞与下一步。
4. 数据任务查阅[数据规范](docs/data-contract.md)，官方文档入库与 RAG 任务查阅[官方文档入库审计与踩坑记录](docs/official-doc-ingestion-audit.md)，技术导航见 [CLAUDE.md](CLAUDE.md)。

有新的进展，必须第一时间记录入 workplan.md。其他 AI 不一定自动读取这些文档；无法访问仓库时，由成员提供文档、当前代码与未提交补丁。

默认分支为 master。Windows/macOS 可继续使用；统一环境版本和配置外置待落实。以下统计是已有仓库结果，本次未重新运行验证。

## 覆盖版本

| 版本 | SDK 节点数 | 类/接口/枚举 |
|------|-----------|-------------|
| API4.1 | 6,197 | 2,025 |
| API5.0 | 15,335 | 6,152 |
| API5.1 | 16,468 | 6,715 |
| API6.0 | 16,570 | 6,741 |

## 版本变化概要

| 升级路径 | 新增类/接口 | 删除 | 特征 |
|----------|-----------|------|------|
| 4.1→5.0 | +1,729 | -64 | 框架创立期 |
| 5.0→5.1 | +158 | -6 | 增量更新 |
| 5.1→6.0 | +228 | -222 | 架构重构 |

## 文件结构

```
├── HarmonyOS_API_跨版本变化分析报告.md   # 详细分析文档（2,847 行）
├── 04_analysis_queries/
│   ├── cross_version_analysis.cypher  # 13类Cypher分析查询
│   └── run_analysis.py               # 自动化分析脚本
├── _run_import.py                     # Neo4j批量导入脚本
├── batch_extract.py                   # JSON批量提取脚本
├── extract_api_info.py               # API信息提取器
├── extract_versions.py               # 多版本文件提取
├── _run_extract.py                   # 无交互提取入口
└── _gen_report.py                     # 分析报告生成器
```

## 使用方法

以下是现有入口。提取脚本仍含个人 Windows 路径；先核实输入输出、Python 依赖和数据库连接，环境待办见 workplan.md。

### 1. 提取API定义
```bash
python _run_extract.py
```

### 2. 导入Neo4j

**此入口会清空连接的默认数据库。** 验证使用独立测试实例，先核实连接与输入范围；当前没有数据库选择参数。
```bash
python _run_import.py
```

### 3. 生成分析报告
```bash
python _gen_report.py
```

### 4. 交互式查询（Neo4j Browser）
打开 `http://localhost:7474`，执行 `04_analysis_queries/cross_version_analysis.cypher` 中的查询。
