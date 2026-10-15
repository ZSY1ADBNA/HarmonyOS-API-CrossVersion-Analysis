# 两成员查询预览复现

范围为OpenHarmony 4.1/API11、5.0.3/API15的ButtonAttribute.fontSize与AudioStreamInfo.channelLayout。网页给出带出处的规则说明，不生成真实模型答案。无需数据库、SDK下载或模型密钥。

新功能依赖草稿PR #12中的原查询工具和证据，PR #12尚未合并。仅下载master不具备完整依赖；发布时必须包含明确的前置提交，不能声称master已有这些功能。

在仓库根目录使用Python 3.11或更新版本的独立环境。实际依赖版本见requirements-query-preview.txt；本批在Windows已有隔离依赖中核对这些版本，并未另外下载验证安装源。

```text
python -m venv .venv-query
.venv-query/Scripts/python -m pip install -r requirements-query-preview.txt
.venv-query/Scripts/python tools/serve_verified_search.py
```

浏览器打开http://127.0.0.1:15052。先确认端口未被其他服务占用；已有本项目服务可直接访问，不要重复启动或停止他人进程。输入fontSize、选择4.1应返回ButtonAttribute声明及来源；追问5.0.3应切换证据，询问默认值应提示证据不足。清空上下文后旧请求不能覆盖新结果。

```text
python tools/verify_local_query_delivery.py
python -m unittest discover -s tools -p test_verified*.py
node --test tools/test_verified_search_ui.cjs
```

交付核验只读已提交文件并生成本地核验报告，不访问远端，不写数据库。它用发布收据中的原始字节指纹检查前置文件，不要求私有发布载荷。历史浏览器报告仅证明当时的阶段结果；上述命令不代替当前实际浏览器、设备运行或人工验收。

真实模型调用仍未验证，原28道候选题尚未人工验收。不要配置共享数据库或运行清库导入来复现本预览。
