# YU-SDKPACK-20261013：正式 SDK、继承与编译小样本

日期：2026-10-13。执行与自查进行中，待成员验收。

本批限定音频配置与 Button 样本。SDK 是软件开发工具包，正式发布包与源码仓库分别核验；继承是组件取得公共属性的机制。例如，Button 自己没写某字段，还必须检查其公共父类，才能判断它是否有该字段。

## 已核验

- OpenHarmony 4.1 Windows/Linux Public SDK 下载入口：[官方发布包](https://repo.huaweicloud.com/openharmony/os/4.1-Release/ohos-sdk-windows_linux-public.tar.gz)，[官方 SHA256](https://repo.huaweicloud.com/openharmony/os/4.1-Release/ohos-sdk-windows_linux-public.tar.gz.sha256)。SHA256 是文件指纹，用于确认下载内容与官方校验一致。
- 整包 2352145619 字节，SHA256 为 `67d532368880bef8a11ef2c7caa812501f19922c5815e59d1ca46b4460e1bdf9`。Windows ETS、JS、toolchains 三组件的指纹由已校验整包提取；组件版本为 4.1.7.5，API Level 为 11。API Level 表示接口等级，不能直接当发行版本号。
- 正式 Windows ETS 组件中 `ButtonAttribute.fontSize` 和可选的 `AudioStreamInfo.channelLayout: AudioChannelLayout` 存在。完整 Button→CommonMethod 链中没有 `minFontScale`；所选公开 audio 声明模块中没有 `AudioRendererInfo.volumeMode` 和 `AudioVolumeMode`。结论限定此发布包及所选类型，不推广到全部 SDK 或设备。
- 五发行固定源码的完整选定继承链核验通过：4.1、5.0.3 无 `minFontScale`，5.1.0、6.0、6.1 在 Button 自身声明。保留原始起始版本注释与 dynamic/static、ArkTS 语言映射条件，不自行推断条件优先级或设备支持。
- 新增下载恢复、继承与条件、解包保护及构建证据测试；最新完整 89 项回归通过，五发行继承链和正式 SDK 样本真实重跑通过。修复 Windows ZIP 成员名归一化掩盖反斜杠的问题，检查原始成员名。已有不同内容的 SDK 文件会被保留并拒绝覆盖。
- 五个 Windows 组件已补齐并校验为 4.1.7.5/API11。最小音频/Button工程通过真实 `assembleHap` 构建：`CompileArkTS`任务完成，生成字节码文件，源文件和产物指纹已再次核对。`channelLayout`与`fontSize`示例通过检查，设备功能未验证。
- 反向验证是故意加入不可用字段，检查开发工具是否会明确拒绝。两个独立样本分别得到 `minFontScale` 不属于 `ButtonAttribute`、`volumeMode` 不属于 `AudioRendererInfo` 的实际编译诊断，均符合4.1声明核验结果；正向通过报告保持独立。

证据：[正式包核验](public-sdk-4.1-verification.json)、[源码继承核验](sdk-inheritance-verification.json)、[实际构建记录](sdk-build-probe.json)。归档、缓存和完整日志留本地，不随本记录上传。

## 异常、未解决问题及处理方案

1. **下载提前结束**：最初只取得约 56 MB，不能当成完整包。已修为 16 MiB 分段续传，校验每段范围、总长度和整包指纹；真实下载与恢复测试通过。
2. **6.1 公共源码文件有一处解析诊断**：已再次核对归档和文件指纹。`DynamicNode` 类在第 33332 行打开，但下一个 `EdgeEffectOptions` 接口（第 33378 行）之前没有类结束的右大括号；TypeScript 5.9.3 在该接口处报告意外符号。它位于目标公共类结束之后，所选链核验与整文件语法状态分别记录。详见[原文异常证据](sdk-source-anomaly.json)。下一步核对同发行正式 SDK 和修改历史，再决定是否生成有依据的派生修正规则；官方原件保留，当前未施加修正，也未称对应 SDK 编译器验证通过。
3. **编译准备阶段的问题已修复**：使用纯英文工程与SDK目录，补齐native/previewer，修正构建任务入口及API11清单字段、启动资源后，真实构建已通过。构建工具版本为DevEco Studio 5.0.9.310、Hvigor/插件5.15.5。工具提示未配置签名，因此本批仅确认编译/打包；下一步设备安装与功能测试还需要签名和合适设备。解包曾产生大量重复目录查询，性能优化尚未完成，后续构建直接复用已校验SDK，不重复解包。
4. **其余正式发布包尚未核验**：6.1 等发行目前仍主要依靠固定源码证据，不能称为所有发行正式 SDK 已验证。下一步固定对应发布说明与校验值，沿用小样本流程核验。
5. **本批已同步**：PR #11提交`d4005d48ef782379590d323752a24a1f365c050c`新增19个本批工具和证据文件，线上Git blob全部与载荷一致，差异集合为19新增、零修改/删除。PR仍为草稿且未合并；完整工作计划保留本地。
6. **反向样本的附带诊断**：音频样本同时出现旧`ContentType`弃用警告，以及缺失属性导致的推断类型错误。目标`volumeMode`不存在的诊断已单独核实；没有把所有报错都归为版本不支持。后续保持显式类型，避免把这些附带诊断混入正向示例结论。

设备运行、共享数据库和网站联调尚未开展。编译检查实际代码能否通过开发工具；设备运行才检验实际功能。联调是将提取、数据库、查询、网站接起来验证，需要先使用独立测试环境。反向验证证据见[sdk-negative-controls.json](sdk-negative-controls.json)及两份独立诊断报告；五组件证据见[sdk-build-components.json](sdk-build-components.json)。
