# 团队更新、6.1覆盖与未知数据核查

2026-10-18，任务YU-HANDOFF-20261018。GitHub连接器读取分支、PR、固定树与文件；另只读下载固定公开提交归档，在隔离目录统计。没有拉取覆盖当前工作区，没有访问成员数据库或部署，也没有主动给成员发消息。

## 远端实际状态

默认master为[458e12a](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/commit/458e12a68aa3d056d76d22077e594b22c8a45032)，最后合入的是[PR #13](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/pull/13)两发行证据查询预览；[PR #12](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/pull/12)反向SDK检查也已合入。这些主要是我们之前的有限样本成果，不能当作其他成员新完成全量接入。

[PR #8](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/pull/8)仍open、未合并，head=[fbd458e](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/commit/fbd458e1977b7e9615f1e54143224d1e63ef6ec3)。与本轮master分叉，ahead 3、behind 31；不能在脏工作区盲目合并。三个分支独有提交为：

- [459bca9](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/commit/459bca9f7547f389193aff5305e52c6383e454bf)：聊天对null cypher使用 `(parsed.get("cypher") or "").strip()`。本地旧版仍有原风险，不能继续说团队完全没修；该修复不等于已形成RAG推荐闭环，且非字符串异常仍需单独检查。
- [1f8dde6](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/commit/1f8dde62f2b852d1fb87cd5cd168196a668a132d)：新增902份API6.1 JSON，更新版本列表、提取版本配置与报告生成器变量遮蔽修复。workplan记录从GitCode的OpenHarmony-6.1-Release取得来源、成员本机导入及网页检查；缺固定上游SHA/原始源码锁，不能证明与我们固定的6.1快照相同。线上部署和十项分析未重跑是其记录的未完成项。
- [fbd458e](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/commit/fbd458e1977b7e9615f1e54143224d1e63ef6ec3)：删除1250份历史API目录JSON，并记录本机图谱删除23,208节点。忽略的3978份.d.ts删除数量来自成员记录，Git树不能独立证实这些原件。

[PR #6](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/pull/6)文档RAG已合入，但 `feat/doc-rag-05a` 后续[1cc670d](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/commit/1cc670d8b2a18599fb82df24c2af973bd12a7825)修复属性碰撞、无二级标题漏块、FTS孤儿和空查询仍在分支，比较master为ahead 1/behind 32。其29项测试和6781块是该提交记录，本轮未替成员重建其数据库。[PR #7](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/pull/7)题集/问题反馈仍open。提交账号不用于推断现实身份。

## 6.1声明和旧ID压缩

从1f8dde6归档读取API、API6.0、API6.1共3017份JSON，并对每份原始字节重算Git blob SHA1，与GitHub连接器返回的固定树逐项一致。归档SHA256为 `b00c6b81cc7498f8cd922424132f68954b133e9bd865263b2af7a017e7d09d49`。

API6.1有902文件、21,901条节点，18075条模块缺失/未知（82.53%）。方法及属性有12419条，其中12102条未知（97.45%）。因此“约82%”接近全部记录比例，不能直接用于方法/属性分母。903条since缺失，其中902个是合成模块根节点；尚不能据此称903个API缺since。

按旧导入器的 `(类型, version::parent::name)` 模拟MERGE分组，只有18,302个键，1526组重复，记录数比键数多3599。API6.0对应20375条记录、16570键、差3805。该计算与成员workplan的节点数字相符，但没有运行其图谱；记录差包括重复声明和潜在错合并，不能全计为独立公开API损失。新ID必须从原始JSON/源码重建，不能只迁移MERGE后的剩余节点。

## “未知模块”的原因

固定分支 `extract_api_info.py` 的 `extract_info(...,isIn=True)` 不返回所属模块，递归 `process_body` 却只从该结果读取模块，缺失便填“未知模块”。例如构造的 `@kit AudioKit → namespace demo → interface Client → request` 夹具，即使顶层有明确Kit，内层接口和方法仍变未知。隔离副本补上父级分组传播后4条记录数量不变、内层分组恢复，前后原始结果均保留。**这是已复现的解析缺陷，不能解释为官方要求这些成员标成未知。**

另外对我们固定6.1源码的 `api/@ohos.bluetooth.access.d.ts` 实际重放旧解析器：34条记录、32条未知；隔离补传分组后未知降为0，记录数及名称顺序不变。源码SHA256为8a4984833adc9e841801dc7159832dd845f1854765abe355c237d1b66db823a0。这是实际官方原件的局部回归，不是对全部902份或成员生产数据的修复验收。

同时必须区分：@kit是功能分组，不一定是可导入的@ohos模块；修复Kit传播也不等于补齐了导入模块。正式重构应分别保存kit、module/scope、完整owner和证据；全局声明没有导入模块可以是正常情况，不能强行从名字造模块。没有@kit时旧 `simplify_api` 直接返回None也是潜在漏收入口；全局/无Kit文件应进入保留原文的状态队列，不能算成功零API。

## 被删的“未知版本”究竟是什么

删除目标是**目录标签恰好为API、来源发行不明的一整组数据**，不是逐条检查since为空后过滤。可见提取/导入代码没有发现“缺since就删除”的统一条件；since从注释读出、来源发行取目录名，两者是不同字段。

该目录1250份JSON共56919条记录，since缺失1250条，恰好对应合成模块根节点；大量实际声明有since。旧MERGE键23208、记录差33711、22897重复组。缺since不能作为这批删除的理由。来源发行未经核实也不应直接加入正式推荐；合理做法是保留在隔离待溯源区。

本轮已使用[恢复工具](../../tools/recover_unversioned_api.py)把1250文件/56919记录全部恢复到新SQLite隔离库，按文件blob+路径+记录序号唯一保存；原JSON、since、路径原样保留，release_id=null、release_status=source_release_unverified，不连接Neo4j、不加入正式推荐。重复输出路径会被拒绝。该库留本地忽略目录，GitHub发布工具和复现步骤：

```text
# 先取得公开仓库固定提交1f8dde62f2b852d1fb87cd5cd168196a668a132d的zip，校验上述SHA256
python tools/recover_unversioned_api.py --archive snapshot.zip --output recovered-unversioned.db
```

预期files=1250、records=56919、graph_updated=false。需要原.d.ts与构建/来源证据才能确定发行；Git历史可恢复JSON，不能恢复从未跟踪的原始SDK文件。后续对固定上游候选逐文件/声明比较，记录exact/multiple/no match；相同声明多发行存在时仍不可唯一推断发行。不得给全批套一个since或最新发行。正式回流需v2身份及隔离导入/查询对账后另行授权。

## 我们的6.1实际到哪层

本轮重新读取来源清单、逐文件台账、提取状态、声明文件及SQLite，不以计划中写过6.1代替实施证据：

- 采集台账：samples 53465文件，固定77133bb8c86d46bd3b448a8e1346dcf485c31213；docs 16053文件，固定a0014e019a5bc611aaf3e90d083b54e6244fd973；ArkTS源码3755文件，固定13cee6598da31c0a3354feeee0f0773aac32fb31；Native源码1015文件，固定5a4dee21e8a9436c14c2fb84c9afce21212e9983。台账文件数不是API数。docs/samples原件content目录当前已不在本地，不能说本机仍有完整可发全量包；本轮小包自带选定原文片段。
- ArkTS提取：943文件语法成功、7文件有诊断、369份.d.ets待SDK解析器，共1319个目标文件；51900声明事实。普通TypeScript不能假装处理.d.ets。
- Native提取：113文件成功、560带诊断、21失败/超时，共694头文件；去重保留变体后32406候选事实，真实SDK include/宏/目标配置未确认。
- 存储：api-facts-v3.db的6.1共84306声明，等于51900+32406；v1仅51900，v2没有6.1。必须明确用哪个库，不能凭文件名v2/v3猜覆盖。全部84306的公开SDK范围仍是待确认状态。
- 查询：既有事实库可按6.1准确名称/ID只读检索；本轮starter另给6.1文档候选查询。完整中文需求、类型展开、全Kit语义与全部示例关联尚未完成。
- SDK验证：未取得6.1代表工程编译/设备运行证据；4.1/5.0.3的fontSize/channelLayout及API9/10原工程历史验证不能外推6.1。来源锁中的API23仅为映射标签，非本轮正式SDK实测。

更完整的数字见[机器可读核查结果](team-update-audit-20261018.json)。输入台账表示历史采集成功；原件是否仍在、字节是否重新核验、解析是否完整、SDK能否编译是不同层级。6.1 ArkTS当前内容文件比台账少1份：构建工具的custom_comment_parser.ts，非.d.ts目标声明；完整重建解析工具仍需恢复并校验，不能用旧collected状态掩盖磁盘现状。

## 本轮检查与下一步

已复现分组传递缺陷并在隔离副本修复；恢复库56919记录和since计数对账；v2身份/恢复测试8项、starter测试5项通过，包含真实回环HTTP。测试先发现SQLite上下文并不会自动close导致Windows文件占用，已改显式关闭并回归；本机网络请求由沙箱禁止，使用经审核的本机测试权限重跑通过。

尚未做：替成员发布6.1部署、合并PR #8/分支修复、共享数据库切换、正式全量ID迁移与五发行完整接收。下一步先将v2适配器接入固定源码提取，并分别修复Kit传播、导入模块和无Kit保留；重建受影响JSON/关系，再用独立图谱与页面读回。后续覆盖按原七阶段计划继续，接收反馈不是准备数据与工具的前置阻塞。
