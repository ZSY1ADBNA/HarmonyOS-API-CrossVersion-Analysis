# AI 技术导航

开始工作先读 [CONTRIBUTING](CONTRIBUTING.md)、[AGENTS](AGENTS.md)、[workplan](workplan.md)。有新进展立即记录 workplan，不在本文件另建任务清单。

## 当前实现

.d.ts → JSON → Neo4j → 查询 / 报告 / 网站。

- extract_versions.py：从本地 SDK 分支提取源码。
- _run_extract.py：调用 batch_extract.py、extract_api_info.py 解析。
- enhance_json.py：增强注释字段。
- _run_import.py：指定导入入口，会清空连接的默认数据库，先核实独立测试实例和配置。
- 04_analysis_queries/run_analysis.py、cross_version_analysis.cypher：分析查询。
- _gen_report.py：报告生成，含需核对的固定叙述。
- app.py、templates/index.html：Flask 网站。

代码引用 neo4j 驱动及 Flask，但完整依赖与统一版本尚未建立，不把两项包名视为已验证完整安装清单。连接配置仍在代码，不将真实凭据复制到文档。

## 模型与限制

节点、关系、UID、数据字段和版本对应见[数据规范](docs/data-contract.md)。API4.1、API5.0、API5.1、API6.0 是项目标签，API 目录来源待核实。

解析包含正则和状态机，复杂语法完整性未在本次运行验证。现有 UID 未包含模块和完整签名，旧 neo4j_import.py 不作为默认入口，现有入口也不是已验证无缺陷。

查询多处按名称、类型标签与父级比较，需逐项核对匹配；已有部分返回值变化检查，完整签名/重载仍待验证。路径、清库、环境及来源问题见 workplan。

## 接续工作

核实当前任务分支、成果、验证证据和下一步；没有记录就注明缺失，不推断历史完成。无法访问仓库的 AI 需成员提供入口文档、任务代码与未提交补丁。运行流程前核实路径、依赖和隔离测试数据库。

## 目标方向

以[项目目标](docs/project-goal.md)为准，现有聊天尚未实现“数据库检索结果交回 AI 再生成推荐”的完整闭环。后续完善及勾选结果统一维护 workplan，不能仅修改提示词就宣称已完成 RAG。
