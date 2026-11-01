# 本地小样本交付清单

本清单仅覆盖OpenHarmony 4.1/API11和5.0.3/API15中的fontSize/channelLayout及本批查询、解释、会话和验证工具。执行与自查不代替负责人或验收人确认。

verify_local_query_delivery.py使用固定文件白名单建立local-query-delivery-manifest.json，分开已在PR12的反向对照、原待发布查询五文件、本地新功能。按原始UTF8字节核对SHA256、Git文件指纹、JSON格式、替换字符及已发布收据一致性；核对正式声明/编译证据目录仍有四条记录，检查当前HTTP、模型契约、开发适配题报告对应的代码与输入指纹。

旧浏览器和会话报告明确标为阶段记录，不能因为文件存在就宣称所有当前代码重新通过整个浏览器验收。SDK与编译证据表示此前已记录结果，本次仅核指纹，不重新下载或编译；模型契约是模拟供给方，不代表真实模型调用。

复核方式（不启动服务、不访问远端、不写数据库）：

```text
python tools/verify_local_query_delivery.py --write-manifest
python tools/verify_local_query_delivery.py
```

已有清单与当前文件不符时拒绝自动覆盖，需先核对变化后再建立新批。清单排除完整工作计划、无关既有修改、凭据、SDK原件、数据库运行目录、私有日志、截图及缓存。此清单不执行上传或合并。

待处理项：当前环境未配置真实模型密钥；原28道候选题仍需完整参考答案和人工验收；原五查询文件已发布至草稿PR12并核对11文件指纹；本地新功能批尚未发布，上传前必须实时核对远端基线，不把历史头当当前基线。具体文件、字节数与核对结果以清单和local-query-delivery-verification.json为准。

复现修复：安装版本及步骤见verified-query-reproduction.md和根目录requirements-query-preview.txt。核验器改用query-publication-verification.json收据，不再依赖本机忽略目录载荷。
