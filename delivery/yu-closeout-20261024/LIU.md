# 刘志华：六工具与聊天接入

先按 README.md 核验并启动。GET /tools 返回实际schema；POST /tools/search、detail、conditions、types、compare、examples 接收 application/json。非compare请求明确version；compare明确from_version和to_version。默认limit=20，一般整数范围1—100；compare至少为2（每个发行至少一条），即使通用schema的minimum=1，也以该比较分支的校验为准；请求例子见cases.json。保留现有字段，不把声明事实数当类/API总数。

响应中的 source_release、coverage、unknown_conditions、truncation_status 必须保留。有 source_url 的记录保留原文链接；conditions结果没有直接的source_url，应保留其evidence和声明ID，再调用同发行detail取得原文链接，不能补造URL。400表示非法请求；503表示证据不可用、指纹/查询失败；200空结果仅说明当前覆盖无匹配，不证明API不存在。api_id未知和候选关系不能改成正式绑定。

需要模型聊天时，在runtime目录运行（把占位参数替换为你的安装路径，模型配置由你本人管理）：

```powershell
python -I -B tools/run_locked_runtime.py --manifest ../snapshot/evidence-manifest-v2.json --member-chat --port 8559 --harness <Harness安装目录> --home <Harness自管目录> --node <Node程序> --model-output <新日志目录>
```

打开 http://127.0.0.1:8559/ 。这是固定聊天组件的隔离适配，不代表完整图谱页面或正式部署已集成。Harness桥接是受控JSON协议，不是原生provider function-calling注册。真实日志和凭据不进交付包。

POST /api/chat 请求为 message、version，可选history和history_version。同发行仅提交已成功完成的user/assistant对；换版立即清空，页面取消等待并丢弃旧响应，失败/超时轮次不进入下一问。服务端在途模型任务可能继续至本轮截止（120秒），忙碌时返回429；客户端取消不等于后端进程立即终止。后台也会丢弃错版或不完整历史。处理返回status，只有成功且有证据的回答才加入历史；失败不能展示为成功或回退无证据答案。

你负责完整AI/页面接入与成员环境验证；余镕熙负责本次数据和只读工具。发现整页应用问题记录请求/预期/实际/证据再归属，不把未接入页面写成后台已验证。
