# OpenHarmony API 数据问题反馈

日期：2026-10-10  
对应任务：整理 AI 检查发现的数据与代码问题，供人工校验及后续修复。  
状态：AI 扫描与隔离复现完成，待人工校验；尚未修复。

## 检查范围

本次检查针对 [HarmonyOS-API-CrossVersion-Analysis](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis) 仓库中的 OpenHarmony 数据及其提取、入库和版本比较代码，基线提交为 `35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c`。

实际扫描 `03_extracted_json` 下全部 4432 个 JSON 文件，共 123458 条节点记录，覆盖 API、API4.1、API5.0、API5.1、API6.0 五个目录。其中 API 目录来源仍待确认，其他目录名也不直接等同 API Level。以下数量均为未去重的 JSON 记录数量，不是数据库实际节点数或唯一 API 数量。

检查采用全量 JSON 扫描、源码阅读以及实际函数的临时样本复现。入库和查询使用模拟会话，没有连接真实数据库、调用模型或修改正式数据。本反馈不包含另一批 HarmonyOS SDK 的历史统计及日志问题。

## 1. 模块归属大量缺失

**发现：** 123458 条记录中，105645 条的直接“所属模块”为“未知模块”，约占 **85.57%**。module 根节点缺少“所属模块”的情况另算，不计入这一数量。

**证据：** 提取器内部递归的 `extract_info(..., isIn=True)` 没有继承所属模块，后续处理使用“未知模块”兜底；实际调用已复现字段丢失。API6.0 的 `@ohos.net.http.json` 中，createHttp 的上级为 http，但所属模块为未知模块。

**影响：** 难以准确按模块检索、推荐导入入口，图谱中的模块归属关系也会不完整。

**建议：** 沿明确归属链继承信息，分清 Kit、导入模块、命名空间和直接父对象；不能只按 API 名称前缀猜模块。

代码依据：[内部归属处理](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/extract_api_info.py#L231)、[递归调用](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/extract_api_info.py#L613)。

## 2. 参数及属性的必填、可选信息不可靠

**发现：** 当前 54775 个参数条目中，标为可选的条目数为 0。提取器从 `@param` 注释构造参数，并统一设置“必填”为 True；属性声明中的 `?` 也没有单独保存。

**复现：** `fetch(value?: string): Promise<string>;` 配有对应 `@param` 时，value 被标为必填。声明有参数但没有 `@param` 时，参数列表为空。相同元数据下，`value?: string;` 与 `value: string;` 得到相同属性结构。

**影响：** 无法准确回答“这个参数能不能省略”“哪些配置字段必填”，也无法可靠比较可选性变化。

**建议：** 参数顺序、类型、可选性和 rest 信息应以声明为准，再关联注释说明。可选性、默认值和示例值需要分别保存、核实。

代码依据：[参数提取](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/extract_api_info.py#L67)、[属性提取](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/extract_api_info.py#L537)。

## 3. 部分声明未正确识别，提取成功不等于内容完整

**发现：** 当前有 **5081 条记录缺少类型**。解析器未识别声明时，仍可能输出只含描述、注释和层级的对象。

**复现与样本：** `type Box<T> = T;` 输出无类型、无名称的记录。API6.0 的 `@internal_component_ets_ability_component.json` 中也存在缺类型、缺名称的记录。另一个无 `@kit`、但含合法导出函数的临时文件，经批处理后只留下占位模块，仍标记为成功。

**影响：** 部分 API 无法定位；提取成功率不能直接证明覆盖完整。缺类型和名称的记录进入数据库后，还可能因相同回退名称而合并。

**建议：** 分类检查未识别语法，保留原始声明及位置；区分完整成功、部分成功、跳过和失败。无 `@kit` 应与是否能解析声明分开处理。

**待核实：** 5081 条记录的具体语法分布，以及当前 SDK 中需要覆盖的无 `@kit` 文件数量。不能把全部记录归因为泛型，也不能据临时样本估算真实漏提数量。

代码依据：[声明处理](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/extract_api_info.py#L483)、[无 Kit 回退](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/batch_extract.py#L108)。

## 4. 版本内身份键不足，不同记录可能在入库时覆盖

**发现：** 普通 UID 使用 `版本::父级::名称`，未包含完整模块/归属路径、签名或语言条件。入库按“类型标签＋UID”合并，再设置整份属性。

**真实样本：** API6.0 的 `@internal_component_ets_button.json` 中，ButtonAttribute.labelStyle 有以下两条记录：

| 参数 value 的类型 | since_version | 语言标记 | 当前映射的标签与 UID |
|---|---|---|---|
| LabelStyle | 11 | 此条未记录 @arkts 1.2 | Method，API6.0::ButtonAttribute::labelStyle |
| ButtonLabelStyle | 20 | @arkts 1.2 | Method，API6.0::ButtonAttribute::labelStyle |

**影响：** 当前导入逻辑无法分别保留这两条记录，后写属性会覆盖先写属性。两者究竟属于重载还是语言/条件变体，仍需对照上游声明确认。

**建议：** 先建立能够区分版本内声明和条件变体的身份，再设计跨版本实体对应。不能只用名称识别 API。

全量扫描发现 28332 组重复的“标签＋UID”，其中 7765 组包含不完全相同的 JSON 记录。这些组也包含正常重复和不同注释，不能全部认定为独立 API 丢失。

代码依据：[UID 构造](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/_run_import.py#L32)、[合并写入](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/_run_import.py#L99)。

## 5. JSON 已有结构信息未完整进入数据库

**发现：** 指定导入器没有映射 parameters、error_codes、return_description 等结构字段；调用签名正文、枚举值、导入别名映射也未完整保存。

| JSON 中的非空字段 | 含该信息的节点记录数 |
|---|---:|
| parameters | 33477 |
| error_codes | 22192 |
| return_description | 19518 |

**复现：** 给方法样本填入参数、错误码和返回说明，捕获实际导入函数提交的属性，均未包含这三个结构字段。

**影响：** 图谱无法直接支撑参数和错误码等结构查询。这属于入库映射问题，不能全部归为提取同学未提供数据。部分文本仍可能保留在 comments 中。

**建议：** 建立 JSON→图谱字段映射表，检查节点类型是否逐项覆盖；按 Neo4j 支持的属性或节点关系结构保存嵌套信息。

代码依据：[导入属性映射](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/_run_import.py#L73)。

## 6. 父级关系和跨版本对应需要进一步核实

**发现：** 入库的名称映射使用短名称，同名对象可能覆盖映射；关系端点仅按 UID 匹配。跨版本比较通常使用名称＋标签＋父级，未充分区分模块、签名和语言条件。

**复现：** 同名、不同标签的父对象可生成相同 UID，模拟会话确认关系查询无法唯一指定端点。模拟两个版本各有一个同名、同标签、同父级但模块不同的对象，比较结果为新增 0、删除 0，也未报告模块变化。

**影响：** 存在错误父级、多个端点及跨版本误配的风险；节点总量一致不能证明关系正确。现有比较无法自动判断两个对象是无关同名还是实际迁移。

**建议：** 建关系时使用完整、唯一的版本内身份；跨版本对应保存双方来源和确认状态。更名、移动和替代需证据，替代关系不应强行共用实体 ID。

**待核实：** 在独立测试数据库中确认真实关系端点和数量；当前只验证了代码与模拟查询路径。

代码依据：[名称映射](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/_run_import.py#L104)、[关系端点查询](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/_run_import.py#L143)、[版本比较键](https://github.com/ZSY1ADBNA/HarmonyOS-API-CrossVersion-Analysis/blob/35e72f782fd3c4e618b0b904b9f669f5b3f5dd2c/app.py#L93)。

## 建议处理顺序

1. **提取阶段：** 核对模块归属、参数/属性可选性及未识别声明，记录失败与覆盖范围。
2. **入库阶段：** 先修正版本内身份，再补字段映射和关系端点；用独立测试数据库核对样本。
3. **跨版本阶段：** 固定双版本上游提交，核对实体对应、声明差异与条件变化。
4. **查询助手阶段：** 使用用户模拟题检查数据是否足够回答，再补官方文档检索。调用顺序、示例及选型说明不必全部放进 JSON。

## 验证材料与人工校验记录

随本反馈一并保存以下材料：

- [复算与隔离复现程序](repository_audit.py)：读取当前仓库 JSON 和实际函数，写入本目录结果文件。
- [扫描与复现结果](repository-audit-results.json)：包含统计、碰撞样本及函数输出，不含真实凭据。

在仓库根目录运行：

```powershell
python -u docs/review-2026-10-10/repository_audit.py
```

逐项校验时填写：

| 问题 | 人工结论 | 核查人／日期 | 上游声明或数据库证据 |
|---|---|---|---|
| 1. 模块归属 | 待核查 | — | — |
| 2. 必填与可选 | 待核查 | — | — |
| 3. 声明识别与覆盖 | 待核查 | — | — |
| 4. 身份键与记录覆盖 | 待核查 | — | — |
| 5. 入库字段映射 | 待核查 | — | — |
| 6. 关系与跨版本对应 | 待核查 | — | — |

本次完成的是 AI 检查、程序复算和隔离复现。上游原声明逐项人工核查、真实数据库验证、SDK 编译和设备运行尚未完成；问题清单不等于人工验收或修复完成。查询助手自身的其他问题另有内部完整清单，本反馈聚焦当前数据及数据链路。
