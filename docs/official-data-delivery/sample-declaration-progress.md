# 本批任务进度与验证记录

## YU-DECL-VERIFY-20261012 异常缺口与小样本声明核验

- 状态：本批源码核验与自查完成，待发布核对及成员验收；用户明确授权实施计划，本批仅推进第1、2步，保留现有改动及官方原件，不开展工程编译或共享库联调。
- [x] 核对五发行interface_sdk-js固定提交与既有文档指纹来源；官方源码声明、发布SDK包和实际编译分别记录，未知不当作通过。
- 进展（2026-10-13）：复用已保存的五发行声明归档，逐文件SHA256/Git blob及归档指纹核验；取得4.1文档历史提交2027c65cf14cc88cb8bbb5a10df68aec31e6f776及父提交f2345b138f205c8cdf37a8885dabd7abe1596c9c的原文，明确fontSize行被替换为四列value行。与4.1 ButtonAttribute.fontSize(value: Length)共同支撑有证据修正，原件不改。新版since含动态/静态及语言映射，全部原文保留，尚未等同发布SDK验证。
- [x] 异常及缺口核查完成（2026-10-13）：4.1 fontSize有修改前原文/明确替换差异/同发行声明三重证据，新增精确指纹守卫修正规则，原件不改。三发行18,794份中文Markdown完整扫描/指纹通过；4项在目标源码类型中未声明，5.0.3同名minFontScale属于Text且源码核对，不补到Button。发布SDK/继承完整性仍未确认，不提升为所有SDK不可用证明。
- [x] 小样本源码对照与真实重跑完成：11源码文件、18声明、11文档候选（含1修正）、10组字段对照；13批次检查通过，72项回归通过（新增7项）。保留动态/静态及语言映射原文、声明/祖先公开限制标签；所有发布SDK公开状态仍未验证。复查修复同名归属、真实签名类型比较与Windows中文编码；失败批次不替换上一批成对产物。4个真实命令行查询附修正/声明证据均通过。
- [ ] 发布核对：本地完整工作计划已更新；准备将本批工具、报告和独立记录从最新master建立独立任务分支和新草稿PR（PR #10已在外部合并，本轮未执行合并），不上传整份workplan或忽略数据，保持未合并。
- 新产物：inspect_sample_declarations.cjs、verify_sample_declarations.py、test_sample_declarations.py、sample-declaration-verification.json、异常缺口与小样本声明核验.md；query_document_candidates.py增加修正与源码证据展示。
- 发布前复查：发现旧source-lock.json仅在本地存在，改为本批独立sample-declaration-source-lock.json，十个来源只保存官方版本/提交/指纹，不携带个人路径；默认入口已改并重跑验证。远端master为32faf38ca6c547b679b60272d0cdd9efe843096d，原PR #10已merged=true；本地旧分支与未提交改动保留，不切换或上传旧历史。
- 未完成：对应发布SDK包、继承/导出核验、多组注释完整条件模型、工程编译和共享库联调；成员验收未完成。
- 最后更新时间：2026-10-13（Asia/Shanghai）。


说明：仅同步本批任务记录；完整workplan保存在本地。实际发布SDK包、工程编译及共享系统联调均未确认。
