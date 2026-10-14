# API15实际编译与本批乱码修复

2026-10-14，批次YU-SDK503BUILD-20261014，执行与本地自查完成。此前发布审批超时，用户随后明确授权补齐成果并尝试合并PR #11到master；发布与合并状态以该PR实际记录为准。

## 乱码

自动任务名称和说明实际保存了U+FFFD替换字符。原因是上一批将中文JSON通过Windows终端的默认代码页输出后错误解码，再写回自动任务与GitHub；不是字体故障。本地UTF8原件完整。通过直接Unicode工具参数恢复自动任务中文；ASCII转义只读复核：名称为OpenHarmony小样本核验与后续验证，替换字符0、项目工作目录正确，状态仍为PAUSED，未自动重启任务。

限定本对话近期14个已上传文件核对Git blob，7个受影响：verify_sample_mapping.py、rehearse_sample_bridge.py、test_sample_bridge.py、sample-mapping-verification.json，以及sample-mapping-progress.md、sample-bridge-progress.md和sdk503-progress.md。已从本地UTF8原件准备正确载荷，新的JSON输出使用ensure_ascii=True，避免中文再次经过终端代码页转换。旧乱码已损失字符，不能靠猜测或重新选字体还原，必须使用完整原件。

此前远端create_tree的自动审批检查连续两次超时，按规则停止重试，修复载荷和本地原件保留。用户再次授权后创建修复文件树成功；本批采用ASCII转义载荷，并以上线Git blob对照本地UTF8原始字节，防止把同一份乱码互相比对误当正确。

## API15后续验证

沿用已校验的OpenHarmony5.0.3/SDK5.0.3.135正式整包，没有重新下载。五个Windows组件单独核对指纹并解包到新英文目录；先检查解包体积与磁盘余量，保护4.1原SDK和工程。解包为每个父目录仅检查和创建一次，保留危险路径、符号链接、重复ZIP及既有文件修改拒收。

实际首轮PreBuild明确要求module.abilities[0].srcEntry；API11示例的srcEntrance不满足API15清单。生成器按API15使用srcEntry，旧API11默认保留；只修改新工程并保留首轮失败证据sdk503-build-first-failure.json。修复后真实assembleHap成功，CompileArkTS完成且取得modules.abc，SHA256=76d60e5aa6952aabee187e17fd98d1138e7e63d6ffdf2235ecab78784a3640f4。实际构建41.531秒，工具DevEco5.0.9.310、Hvigor及插件5.15.5。

证据sdk503-build-components.json和sdk503-build-probe.json记录源码与产物指纹。14项相关回归通过。无签名配置的警告保留：本批只验证编译和打包，不证明设备安装或功能。设备运行、共享迁移、更多Kit和发行均未开展。用户已明确授权本PR合并master；完整workplan、SDK归档及私有资料不上传。无论合并结果如何，下一步继续API15的两个反向编译对照，验证缺失字段会被工具拒绝。
