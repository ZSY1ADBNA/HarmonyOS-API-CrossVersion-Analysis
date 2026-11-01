# 两样本证据查询与版本比较

2026-10-14。延续用户授权的合并后后续工作，范围为fontSize/channelLayout在4.1/API11和5.0.3/API15的4条已核验声明，不扩展全部Kit。

## 结果

新增tools/query_verified_samples.py：按明确发行和成员名查询，返回完整签名、所属类型/模块、可选性、参数、成员和父级原始注释条件、正式SDK文件及归档指纹、官方归档链接和对应真实编译报告。指纹清单verified-sample-query-manifest.json固定4份声明/编译报告，查询时检查文件指纹、SDK版本/API Level/发行身份和样本归属。

4.1与5.0.3的两个成员签名一致；channelLayout的metadata和ancestor_metadata不同，原样分别返回。比较方向反转时交换旧/新证据，不自动推断运行行为相同或正式跨版本身份。图谱旧标签API5.0明确对应5.0.3，查询使用5.0不伪匹配。未知发行或成员返回no_verified_sample，附absence_in_sdk_proven=false，表示资料范围内没有已核验样本，不能用来证明SDK没有该API。

只读指查询路径不修改证据输入或数据库；准备清单时通过--write-manifest显式创建指纹记录。已有不同清单不会自动覆盖。输出使用ASCII转义JSON，解码后完整保留中文及Unicode，避免此前终端代码页损坏。清单和报告应随Git版本一起核对。

## 实际检查

3项回归通过：未知发行与图标签区别、真实注释差异及方向、报告篡改拒收和即使更新指纹仍拒绝错误API版本。11项实际本地查询检查通过，含4条样本、所有SDK来源、channelLayout可选性、两个签名一致、成员/父级差异、反向比较、未知发行/名称、设备等价不推断、图标签及全部输入指纹保持不变。证据verified-sample-query-verification.json。

复现：先运行python tools/query_verified_samples.py --release 4.1 --name channelLayout，再运行python tools/query_verified_samples.py --release 4.1 --compare-with 5.0.3 --name channelLayout。运行tools/test_verified_sample_query.py检查错误证据拒收。

## 边界与交接

本轮实际运行的是本地证据查询，尚未接入现有Flask接口、RAG智能体或浏览器页面。查询重新检查已提交报告的指纹，不在每次查询重新下载SDK或编译；真实SDK/编译证据在对应报告中，设备运行仍未验证。用户授权的PR #11已正常合并master；本轮反向及查询成果在后续草稿PR #12待审，不自动合并。共享及生产数据保持不变。

当前已授权小样本计划完成：乱码恢复、两发行正向/反向编译、隔离映射/查询和本地证据比较均有相应范围证据。后续可在明确服务部署基线后接入HTTP及检索评测；本轮不自动扩大。完整工作计划仅本地维护。
