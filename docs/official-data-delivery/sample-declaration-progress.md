# 本批任务进度与验证记录

## YU-DECL-VERIFY-20261012 异常缺口与小样本声明核验

- 状态：本批源码核验与自查完成，待成员验收；用户明确授权实施计划，本批仅推进第1、2步，保留现有改动及官方原件，不开展工程编译或共享库联调。
- [x] 核对五发行interface_sdk-js固定提交与既有文档指纹来源；官方源码声明、发布SDK包和实际编译分别记录，未知不当作通过。
- 进展（2026-10-13）：复用已保存的五发行声明归档，逐文件SHA256/Git blob及归档指纹核验；取得4.1文档历史提交2027c65cf14cc88cb8bbb5a10df68aec31e6f776及父提交f2345b138f205c8cdf37a8885dabd7abe1596c9c的原文，明确fontSize行被替换为四列value行。与4.1 ButtonAttribute.fontSize(value: Length)共同支撑有证据修正，原件不改。新版since含动态/静态及语言映射，全部原文保留，尚未等同发布SDK验证。
- [x] 异常及缺口核查完成（2026-10-13）：4.1 fontSize有修改前原文/明确替换差异/同发行声明三重证据，新增精确指纹守卫修正规则，原件不改。三发行18,794份中文Markdown完整扫描/指纹通过；4项在目标源码类型中未声明，5.0.3同名minFontScale属于Text且源码核对，不补到Button。发布SDK/继承完整性仍未确认，不提升为所有SDK不可用证明。
- [x] 小样本源码对照与真实重跑完成：11源码文件、18声明、11文档候选（含1修正）、10组字段对照；13批次检查通过，72项回归通过（新增7项）。保留动态/静态及语言映射原文、声明/祖先公开限制标签；所有发布SDK公开状态仍未验证。复查修复同名归属、真实签名类型比较与Windows中文编码；失败批次不替换上一批成对产物。4个真实命令行查询附修正/声明证据均通过。
- [x] 发布核对：新草稿PR #11已创建，feat/yu-declaration-check-20261013基于master 32faf38ca6c547b679b60272d0cdd9efe843096d，提交6302971cd4d52e8729c590e32b455cc0ce1c3edd；9个线上Git blob与载荷一致，完整变更集合为7新增/2修改，draft=true/merged=false。AGENTS讲解规范已同步，本地完整workplan不上传，保留现有分支/未提交改动。
- 新产物：inspect_sample_declarations.cjs、verify_sample_declarations.py、test_sample_declarations.py、sample-declaration-verification.json、异常缺口与小样本声明核验.md；query_document_candidates.py增加修正与源码证据展示。
- 发布前复查：发现旧source-lock.json仅在本地存在，改为本批独立sample-declaration-source-lock.json，十个来源只保存官方版本/提交/指纹，不携带个人路径；默认入口已改并重跑验证。远端master为32faf38ca6c547b679b60272d0cdd9efe843096d，原PR #10已merged=true；本地旧分支与未提交改动保留，不切换或上传旧历史。
- 发布异常及恢复：报告上传自动审批超时，未视为不安全或成功；精简重复源码注释并保留本地完整证据后允许的一次重试成功。最后报告格式调整后7项相关回归及真实重跑再次通过；新增独立来源锁默认入口实跑通过。
- 未完成：对应发布SDK包、继承/导出核验、多组注释完整条件模型、工程编译和共享库联调；成员验收未完成。
- 最后更新时间：2026-10-13（Asia/Shanghai）。


说明：只同步本批任务记录；完整workplan保存在本地。对应发布SDK包、工程编译及共享系统联调均未确认。
