# 只读工具约定

GET /tools读取六类工具定义；POST /tools/search等入口执行约定查询。必须明确来源发行；默认20条、最多100条。

保留source_release、coverage、unknown_conditions、truncation_status及每条source_url。来源发行与工程SDK是不同条件；api_id未知、候选关联和未验证SDK不能升级为确认结论。

非法输入400；证据/指纹/查询超时503。无匹配只说明当前覆盖范围无记录，不证明API不存在。模型超时/失败不回退无证据答案，比较必须包含选定发行。

同发行追问可显式传入history和history_version；错版或未知旧版丢弃历史，每轮重新取证。Harness自管模型配置，不包含凭据，也不是原生provider工具注册。

所有受锁文件（包括本说明、README、HTML和数据清单）均参与交付编号；数据清单在data/evidence-manifest-v2.json，8份数据库仍须放在它的同一目录或使用完全一致的外置清单。缺文件会拒绝启动。

本包不是完整离线数据或原件重建包；许可、共享获取位置、成员接收和独立验收仍需单独确认。
