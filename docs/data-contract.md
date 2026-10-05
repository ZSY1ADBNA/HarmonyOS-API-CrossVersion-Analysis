# 数据与结果规范

本文件区分现有实现和后续要求。技术依据：提交 3a7a99e9fd0293fdf159bdf9f1789c7243e39bf0 的静态检查；本次未运行数据流程。

## 流程与入口

.d.ts → batch_extract.py / extract_api_info.py → JSON → _run_import.py → Neo4j → 查询 / 报告 / 网站。

[extract_versions.py](../extract_versions.py) 获取源码；[_run_extract.py](../_run_extract.py) 无交互解析；[enhance_json.py](../enhance_json.py) 增强注释。[导入入口](../_run_import.py)为当前指定入口。旧 neo4j_import.py 不作为默认入口，不能据此推断现有导入器已无缺陷。

## 来源与版本

当前提取脚本配置：
- OpenHarmony-4.1-Release → API4.1
- OpenHarmony-5.0.3-Release → API5.0
- OpenHarmony-5.1.0-Release → API5.1
- OpenHarmony-6.0-Release → API6.0

这些是项目标签，不等同 API Level。JSON 另有 API 目录，来源待确认，不能未经核实称为“最早版本”。

源码仅由本地 interface_sdk-js 路径指向；历史数据对应的上游 URL 与固定提交尚待补齐。生成记录应包含来源 URL、SHA、版本对应、范围、生成命令、解析器版本和许可。只记录可变分支名不足以复现。

01_source_files/、02_dts_index/ 当前被忽略。提取会切换上游分支、删除重建对应输出目录；使用独立上游副本并核实目标路径。

## JSON

已提交数据位于 03_extracted_json/<版本>/。现有批处理采用 UTF-8、ensure_ascii=False、indent=2；保持稳定输出，不将全量格式转换混入逻辑修改。

当前导入读取顶层“节点”列表，以及“类型”“名称”（回退“签名”）、“上级”“所属模块”“层级”“功能描述”“注释信息”、since_version、system_capability 等字段；按节点类型读取“返回值”“属性类型”“装饰器”“父类”。这是当前行为，不是完整且已验证的 Schema。

改字段前核对提取、导入、查询和网页使用方，说明空值与兼容策略。保留完整签名、重载及来源证据属于后续要求，不宣称已经满足。人工修正需记录依据和可重复应用的方法。

提取修改先用代表性 .d.ts 小样本检查 JSON，再更新受影响正式数据；延期时在 workplan 写范围、原因与后续任务。

## 图谱

提交导入、查询、模型说明和索引/约束定义；运行目录、锁、日志、凭据和个人数据库不入库。共享快照另行版本化并提供恢复步骤。

当前节点标签包括 Module、Namespace、Class、Interface、Enum、Method、Property、TypeAlias、EnumMember、Struct、CallSignature、ExportImport、Unknown。
- HAS_PARENT：成员 → 父节点。
- BELONGS_TO_MODULE：节点 → 模块。

普通 UID 为 version::parent::name 或 version::name，模块另有 version::module::module_name。普通 UID 未包含模块、完整签名或类型，存在跨模块同名和重载碰撞风险；名称映射也需验证。

导入执行 MATCH (n) DETACH DELETE n，使用默认数据库且无选择参数。小样本必须核实隔离实例与输入范围。记录失败文件、图中实际数量、抽样属性和查询结果，不能把脚本累计处理条数当成实际图中数量。

## 查询、报告与网站

比较需明确旧版、新版与匹配规则。现有代码多处用名称、标签和父级组合，不同查询逻辑可能不同，无法保证重载或跨模块正确匹配。已有部分返回值变化检查，不应说完全没有签名相关查询，也不能说已完整分析签名。

报告需记录输入、代码版本、查询和生成步骤。_gen_report.py 包含固定叙述和数字，生成后仍需核对其与查询结果一致。

[app.py](../app.py) 和[模板](../templates/index.html)提供展示；影响相关字段或查询时，连接测试图谱检查页面。网站正常显示不能证明提取完整。

当前个人路径、硬编码连接、环境版本及来源追溯问题见 [workplan](../workplan.md)。所有新进展按[协作规范](../CONTRIBUTING.md)立即记录。
