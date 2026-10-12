# ArkUI属性与音频枚举适配及逐步自查

2026-10-12。继续五个正式发行的小样本扩展，处理Button的type、fontColor、fontWeight、labelStyle、minFontScale，以及AudioSampleFormat、AudioChannelLayout、AudioVolumeMode三类音频枚举。所有结果仍为文档候选，不代表SDK公开API、设备可用性或工程编译已确认。

## 原文与范围

五发行各读取Button页和音频枚举页，共10份固定原文。前三发行枚举在js-apis-audio.md，6.0/6.1在arkts-apis-audio-e.md。核对已发布yu-source-lock.json中的来源集合、提交、发行、平台、API Level、归档指纹和文件数，拒绝来源标签漂移；逐输入同时核对SHA256及Git blob指纹，原件不改写。

4.1 Button使用三列属性表，较新发行使用独立属性标题、调用式签名和参数表。旧表中选定属性保存参数类型，不凭空补签名。fontWeight类型中的转义竖线保留为联合类型，不误拆成额外表格列。属性自身元信息与参数说明分别提取，参数版本不覆盖属性版本。

4.1第66行实际为名为value的四列异常行，与三列表头不符。该行不在本批五个选定属性中，完整保存于报告source_anomalies，标为隔离待核对；不猜成fontSize，不宣称原文问题已修复。选定属性出现异常列、未知必填值、重复标题或缺失签名时阻止批次发布。

minFontScale在本次4.1/5.0.3代表页没有声明区段，AudioVolumeMode在4.1/5.0.3/5.1.0代表页没有区段，共5处代表页缺口。只记录对应固定文档未找到，不推断SDK不存在，也不用较新发行补旧发行。

## 查错与修复

新适配器仅允许Button→属性→选定属性的确切标题层级，以及音频枚举的二级标题。复查加固了同名嵌套区段排除及参数表名称与签名名称一致性，防止其他容器或示例区段误生成声明、错误参数挂到属性。枚举成员保留十进制、负数及十六进制原始赋值，成员元信息与枚举类型元信息分开。

新增12项回归覆盖新旧版式、联合类型、参数版本隔离、原文异常隔离、选定异常拒收、重复标题/成员/表头、未知必填值、示例与其他容器排除、歧义签名、参数名核对、成员归属及版本、来源锁/原文指纹拒收、错误发行/路径边界，以及真实管线失败保留上一批成对产物。路径边界测试使用解析路径注入，不依赖Windows创建符号链接权限。

首次运行测试时，沙箱默认临时目录无法创建子目录；改用忽略的数据目录内的测试临时目录后执行，未把权限错误视为解析成功。最终完整65项测试通过，其中本批12项；Python编译及变更检查另见workplan。

## 最终真实重跑与检索

最终结果：23条组件属性、19条参数、12条枚举类型、279条枚举成员，共333条候选。不是333个不同公开API。19项批次检查及10份输入的60项检查全部通过，零选定范围警告，1条非选定源表格异常保留，5处代表页缺口保留。

原文区段、声明签名、选定表格行覆盖、唯一身份和父子归属分别检查。独立SQLite+FTS重复入库不增加条数，全文索引完整性通过，五发行均能按发行/归属检索fontWeight及CH_LAYOUT_STEREO，实际只读连接拒绝DELETE，未知发行空结果。失败覆盖检查及指纹错误不会更新current.json或上一批数据库/正文。

真实命令行查询抽查：4.1 labelStyle保留10+且签名为空；6.1 minFontScale保留18+、ArkUI.Full及原始联合类型签名；6.1 CH_LAYOUT_STEREO保留0x3，父级为11+/Core；SYSTEM_GLOBAL保留0，父级为19+/Volume。4.1的SYSTEM_GLOBAL无本批匹配，不作为SDK不存在证明。查询证据保存于忽略批次目录query-evidence.json。

独立批次位于data/delivery/structured/yu-attributes-enums，current.json原子指向两份带指纹产物；查询默认批次仍为此前语义试点，使用此批时显式选择--batch-root。报告见[attributes-enums-pilot.json](attributes-enums-pilot.json)。

```powershell
python tools/extract_attributes_enums.py
python tools/query_document_candidates.py --batch-root data/delivery/structured/yu-attributes-enums --release OpenHarmony-6.1-Release --owner AudioVolumeMode --name SYSTEM_GLOBAL --kind enum_member
python tools/query_document_candidates.py --batch-root data/delivery/structured/yu-attributes-enums --release OpenHarmony-6.1-Release --owner Button --name minFontScale --kind component_attribute
python -m unittest discover -s tools -p 'test_*.py'
```

测试需要可写的系统临时目录；在受限Windows沙箱中可将TEMP和TMP指向已创建的data/delivery/test-temp，仅影响当前测试进程。

## 未完成与下一步

全Kit与全部属性覆盖、中文自然语言检索、SDK声明及公开范围核验、代表工程编译、共享库和网站联调、成员验收尚未完成。下一步先对这批字段引用的枚举建立带证据的关联，并选择小样本核对固定发行SDK声明；每一步仍按查错、修复、回归、真实重跑及workplan记录推进。此批不清空、导入或修改共享数据库，不覆盖队友解析器。
