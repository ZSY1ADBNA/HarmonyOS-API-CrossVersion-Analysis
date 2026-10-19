# API 身份规范 v2 与旧编号迁移

任务 YU-HANDOFF-20261018，2026-10-18。本文是供张舒阳重构的可执行契约；[参考实现](../tools/api_identity_v2.py)与[边界测试](../tools/test_api_identity_v2.py)已在隔离环境运行。尚未切换正式提取器、共享图谱或文档主键，不能据此声称全量迁移完成。

## 为什么需要三种编号

旧导入器的实际规则是 `version::parent::name`，无父级时为 `version::name`，并没有完整所属链、模块、类型或重载参数。例如两个模块中的 `Client.request(string)`，以及同一类的 `request(number)` 都可能被压到一个键。它不是稳定的跨版本身份。PR #8 的6.1数据有21,901条记录，却只有18,302个 `(类型,旧UID)` 键；差值3,599不能直接称为不同API丢失数，其中也可能有重复记录，但必须逐声明保留和核对。

把三件事分开：

- `source_id` 标记一份固定仓库快照。同提交供多个发行使用时只存一份来源，另存发行映射。
- `declaration_id` 标记快照中一个准确的声明位置。可用它取回原文；同名、重载、无法识别的声明都必须保留。
- `api_id` 标记**发行内、语言内的保守逻辑身份**。只有必要字段完整且解析归属明确才生成。不同发行的API编号不同；跨版本对应另建有证据的关系，不通过去掉版本号自动匹配。

`EVOLVES_TO` 仍只表示经确认的版本对应，不表示调用。文档块 `chunk_id`、工程及片段ID保持各自身份，通过映射表关联API，不拿名称充当外键。

## 已有实现与缺口

本地 `extract_arkts_api.cjs` 用SHA256处理 `[OpenHarmony,release,module,owners,kind,name,signature]`；声明ID处理 `[source_id,path,start,end]`。模块缺失时回退文件名，起止位置来自TypeScript UTF-16字符索引。泛型、static、导出别名、完整条件不都在身份里；原始参数文本中的格式和名称也会改变编号。源码中的 `@kit` 是功能分组，不等于可导入模块。

本地 Native 初始ID含头文件、owner、kind、name、类型；声明ID另含kind。`normalize_native_identities.py` 用整条记录指纹保留Clang多次访问中的变体。其指纹包含描述等字段，只是既有兼容处理，不能作为v2稳定API身份。

现有 `source_id`、这些64位十六进制ID、DocChunk的16位编号都属于旧算法；v2用显式前缀隔离。下游不得把旧ID直接改名为v2。

## 确定性序列化与算法

算法版本固定为 `ohapi-id-v2`。所有哈希输入为位置固定的JSON数组，只允许数组、字符串、null、布尔值和绝对值不大于2^53−1的整数；不允许对象、浮点数、NUL和孤立代理字符。UTF-8无BOM；JSON无缩进、无分隔空格，中文原样编码，JSON控制字符按标准转义。**不做Unicode正规化、大小写转换或trim后再哈希**，以免把合法不同标识符合并。换行/空白规范化只发生在语法解析形成签名时，不能对字符串字面量直接删除空白。

`digest(domain,payload) = domain + ':' + sha256(UTF8(JSON(["ohapi-id-v2",domain,payload])))`；输出完整64位小写十六进制，不截断。各语言实现须对相同测试向量得到相同字节和摘要。JSON数组代替 `a::b` 拼接，避免成员名称或路径含分隔符时碰撞。重算后仍须比较身份载荷；相同摘要但载荷不同为硬错误，不能覆盖。

来源载荷：`[platform,repository,commit,kind]`。repository必须是来源锁中的规范URL，Git remote别名/镜像域名不能未经证据视为同一来源；commit是完整40位小写Git SHA1，不接受分支名，资料种类区分arkts_api/native_api/docs/samples。此规范不声称Git对象本身改用了SHA256。

声明载荷：`[source_id,path,start_byte,end_byte,parser_profile,variant]`。path为仓库内相对路径，使用 `/`，不得含绝对盘符、空段、`.`、`..`、反斜杠。位置为原始UTF-8字节、0起点、左闭右开且非空。TypeScript的UTF-16索引须先把索引前原文编码成UTF-8再换算；中文和emoji要测，不能只改字段名。parser_profile记录解析器版本及目标配置；Native的variant保留宏/平台/展开实例区分信息，无变体时为null。行号另存用于展示，不代替字节位置。来源提交变更会产生新的声明ID，即使API逻辑身份不变。

API载荷的字段顺序：

```text
[platform,release_id,language,scope,owners,kind,name,static,signature,conditions]
```

- release_id取来源锁的发行身份，如 `OpenHarmony-6.1-Release`；与API Level、SDK包号和since分开。来源发行不明时为null并暂停生成api_id，不能回退最新版本。
- language区分arkts/js/native；scope为 `["module",可导入模块名]`、`["global_file",仓库路径]` 或 `["native_header",头文件路径]`。全局声明不伪造模块；文件作用域保守区分同名，后续有链接证据再建立对应。
- owners是完整的带类型外层链，如 `[["namespace","net"],["class","Client"]]`，按外到内排列，不包含声明自身。空数组表示确认的顶层，null表示尚未解析，二者不同。
- kind使用namespace/class/interface/function/method/constructor/getter/setter/call_signature/construct_signature/index_signature/property/enum/enum_member/type_alias/variable/export_alias及Native原生种类。不要把getter和setter都改成property。
- name保留真实标识符；无名构造、调用、构造签名、索引签名分别用 `<constructor>`、`<call>`、`<construct>`、`<index>`，它们是按kind限定的保留名称。不能把无法识别的任意声明都命名unknown。
- static必须为已知布尔值；容器和非成员声明用false。可选性、readonly、泛型、参数顺序、rest、返回值等属于下面的签名载荷。
- conditions为按条件维度排序的数组，如 `[["arch","arm64"],["macro","FEATURE_A=1"]]`；空数组仅表示解析配置已知且无额外条件。条件未知为null。配置不完整的Native声明保留事实，暂不生成确定api_id。

## 签名载荷与解析责任

参考哈希器只接受已经完成语法抽取的数组，**不把原始字符串自动解析成语义**。完整解析适配器仍需接入张舒阳的重构；不能把本参考函数称为完整ArkTS/C解析器。

建议固定下列签名类别：

```text
可调用：["call",泛型数组,参数数组,返回类型,成员可选性]
参数：[类型,optional,rest]              # 顺序不可重排
泛型：[名称,约束或null,默认类型或null]   # 按声明顺序
属性：["property",类型,optional,readonly]
容器：["container",泛型数组,基类数组]   # 不含成员体，增加一个方法不改类ID
别名：["alias",泛型数组,目标类型]
枚举成员：["enum_member",赋值表达式或null]
重导出：["export",目标模块,目标符号,本地别名,type_only]
Native：["native",类型标记数组,调用约定,链接类型]
```

类型使用解析器token或AST形成的有序数组，保留联合/交叉顺序和字面量原值，不擅自按文本排序或展开别名。简单内建类型可直接用字符串。匿名函数/对象类型递归保留成员种类、参数和返回；存在不支持结构时保留原文及诊断并令identity_status为unresolved。参数名通常不是调用身份，但涉及类型谓词、命名元组、泛型绑定、`typeof`等名字引用时必须保留相应绑定。不能用正则直接删除名字；尚未实现绑定分析时采用保守的token表达并记录profile，不将两种profile自动合并。

`identity_status=resolved` 只表示本发行的身份字段已解析，不能证明SDK公开或设备可用。public_scope、since、权限、SysCap、deprecated、描述、原文行号、SDK验证状态不直接进入逻辑ID；它们作为属性及证据保留。若权限等改变，只更新属性；若参数类型等改变，产生新逻辑身份及待比较关系。

## 边界案例与拒绝合并规则

1. 跨模块同名：`@ohos.a.Client.request` 与 `@ohos.b.Client.request` 的scope不同，编号不同。
2. 嵌套类型：`A.B.Client.request` 与 `A.Client.request` 的完整owners不同；不只取最近一层。
3. 重载：string和number参数、可选参数、rest参数、泛型约束不同要分开；相同签名多处声明保留全部declaration_id并形成逻辑分组，不覆盖原件。
4. 构造器/getter/setter/调用及索引签名：即使名字缺省也由kind与专用name区分；索引的键类型和值类型进入签名。
5. 回调和匿名类型：保留递归结构，无法分辨则返回api_id=null；不能把所有回调都简化为Function。
6. Kit重导出与别名：别名作为独立导出声明，额外记录 `EXPORTS` 候选到原件；未解析目标前不合并，也不把Kit名覆盖原始模块。
7. 无模块全局声明：如两个头文件/全局.d.ts有同名Color，保守用文件scope区分；“全局”是已知作用域，“未知模块”是状态，不能混同。
8. Native宏/条件/平台：宏函数参数和替换token保留；同位置不同预处理配置是不同变体。包含路径不同、USR缺失、展开访问重复要保留诊断。相同访问重复可计数，冲突变体不得丢弃。
9. 同名未知字段：必要字段未知则api_id=null；只用declaration_id定位，并记录reason及候选。两个null不构成同一逻辑API。
10. 类增添成员、注释/行号变化：不改变已确定的逻辑身份；原件快照或位置变化仍改变声明身份。

边界测试包含上述区别及发行切换、中文编码、分隔符、非法路径、未知状态和迁移分流。它验证参考载荷规则，不表示这些语法已全部接入生产提取器。

## 迁移、兼容与回滚

先冻结旧JSON、代码提交、每发行和类型数量及文件指纹。新库旁路生成，保持旧UID和所有声明；先对同名/重载/别名/全局/Native变体及中文位置小样本验证，再分批扩大。旧图谱的MERGE可能已覆盖记录，必须从JSON和固定源码重建，不能仅导出图谱剩余节点映射。

迁移表字段为legacy_id、declaration_ids、api_ids、status、证据及算法版本：

- one_to_one：全部声明都可解析且只有一个逻辑目标；兼容查询可以重定向，但返回全部声明证据。
- one_to_many：旧UID合并过多个目标，查询返回候选清单，要求模块/owner/签名进一步限定。
- ambiguous：有未解析或缺失声明；保留旧值及多候选，不能默认选择第一个。
- no_match：没有可定位声明；明确失败并追溯输入，不伪造新编号。

`migration_rows`提供这四种状态的参考实现。不能只按名称批量填ID；即使逻辑api_id相同，声明表也不得按它设置唯一约束。摘要重复载荷不同、位置越界、未记录profile应让该批失败并保留上一版本。

影响范围：提取JSON需要增加v2与旧字段；Neo4j的API/Declaration分开并保留映射；父级、模块、版本对应关系重建；文档/FTS/示例关联按迁移表更新；API详情/比较/网页/缓存必须处理多候选与未知。DocChunk旧编号不在这轮直接替换。全量更新前后比较每发行、类型和声明数，确认关系端点可定位、重复导入不覆盖、旧请求兼容、歧义不自动跳转；在独立数据库读回并回归页面，再讨论正式切换。回滚只切换新旧版本入口，不删旧库。

运行参考检查：`python -m unittest discover -s tools -p test_api_identity_v2.py`。本轮8项测试通过，包含19类身份差异子例；另附[3个跨语言固定向量](../examples/api-identity-v2-vectors.json)，Python与JavaScript原生JSON.stringify/crypto的UTF-8字节及完整摘要逐项相同。正式五发行数据、共享图谱与成员接收仍未迁移或验收。
