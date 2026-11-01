# 黄宇鹏：接收数据与检索入口

先按 README.md 完成八库接收核验，再启动只读工具。你负责检索效果评测；本包的确定性回归只验证接口、来源和隔离，不提供独立效果评分。

八库清单：documents、document_names、declarations、sample_catalog、sample_contexts、project_notes、kit_routes、reconciliation。全部文件名和SHA256以 snapshot/evidence-manifest-v2.json 为准；不要单独更新正文或名称索引。

```powershell
$body = @{version='6.1'; query='createHttp'; scope='declarations'; limit=2} | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8547/tools/search -Method Post -ContentType application/json -Body $body
```

返回中保留 source_release、coverage、unknown_conditions、truncation_status，以及记录的 source_url/evidence。原件包 source-manifest.json 可把 source_id 对应到发行、仓库、固定commit、归档SHA256及相对台账；archives/内保留原始ZIP，licenses/另列可取得的根许可。先核对该原件包的总SHA256，再对照每份归档指纹。元数据路径已相对化，原归档字节未变，parent source_manifest_sha256 与快照一致。

数据重建入口分两层：取得同版快照并核验的可执行入口是 README.md 的 verify_member_delivery.py；从官方原件重新生成八库的既有工程入口为 tools/prepare_original_rebuild.py --destination <新目录>，然后在所准备目录运行 python -I tools/rebuild_evidence_from_originals.py。后者要求原工程的原件、台账、TypeScript/libclang/Node依赖和环境锁，本次运行包及原件来源包没有打包整套重建依赖，不能直接把上述命令用于这两个ZIP。既有本机原件重建证据保留；这不是成员环境重建通过，也不要求你补做完整API提取。

评测发现问题请给：交付编号、请求JSON、预期、实际响应、来源链接、去隐私证据和建议负责人。数据/只读工具阻断找余镕熙；检索效果归你；正式API映射找张舒阳。成员接收结果按 RECEIPT.json 回传。
