# 证据工具独立运行代码包

本包只含运行代码。8份数据库需要按runtime-lock.json中的相对文件名和SHA256另行取得；不把这个代码包当成完整数据交付。

先运行 `python tools/run_locked_runtime.py --manifest <数据目录>/evidence-manifest-v2.json --verify`；启动工具删除--verify，启动隔离页面改用--preview。两种入口均先核对代码及全部数据指纹。页面仅查询工具事实，不表示成员现有页面接入通过。

刘志华：使用/tools工具定义和六类查询。模型桥接已含在tools/harness_model_bridge.py中；Harness需要独立安装及自行管理的模型配置，不在包内携带凭据。原工作区已有U03真实模型两轮验证，接收方仍须核对自己的环境；这不是原生function-calling注册或独立验收。模型与页面执行路径相互独立。

黄宇鹏：正文与名称索引必须成对匹配。正式完整重建还需要固定原件归档、来源台账、解析器和环境锁，本运行包不宣称包含这些重建输入。查询效果评测由接收方开展。

代码与数据组合身份见runtime-lock.json。数据指纹失配应返回错误，不能回退旧库。上游原文与团队代码许可仍需在正式分发前核对。

成员聊天组件的隔离适配也在本包中：在上述启动命令改用--member-chat，并显式提供--harness <安装目录> --home <Harness自管目录> --node <Node入口> --model-output <本机测试日志目录>。该路径复用固定成员聊天区与Agent，图谱完整面板、正式部署及成员验收未接入。点击发送才执行本轮请求，模型配置不在包内。

完整数据接收入口：先用 `python tools/receive_runtime_data.py --manifest <发送方数据目录>/evidence-manifest-v2.json --destination <全新接收目录> --preflight` 检查容量；去掉--preflight才逐文件复制和复核SHA256。本包会先校验自己的代码锁及数据清单，默认保留接收盘30GiB可用空间；不足时不创建接收目录，失败的部分目录保留，不覆盖旧接收。本工具不提供尚未建立的团队下载地址；仍须先取得同版的8个数据库。它只接收快照，不宣称能从20份官方原件独立重建全部库。
