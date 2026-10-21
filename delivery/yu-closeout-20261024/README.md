# 余镕熙：2026-10-24 交付候选

本目录提供同版只读运行代码、包外校验器和操作说明。下载状态、文件名、SHA256及支持范围见 RELEASE.json。百度网盘分享页可打开；文件名和显示大小已与本地清单核对，下载的 DELIVERY.json 与本地清单 SHA256 一致。分享链接和提取码由交付负责人向接收成员单独提供。三个大包的云端文件尚未经下载后逐字节核验，接收者须按清单自行验哈希。网盘内 README.md 仍保留上传时的“入口待提供”文字，以本页和 RELEASE.json 的当前交付状态为准。成员本人接收和评测单独记录。

## 网盘五个文件的用途

- `DELIVERY.json`：本次上传清单，列出三个 ZIP 的准确字节数和 SHA256，以及运行代码、数据的交付编号。下载后可先核对它本身，再用它核对大包；文件内上传时的云端状态是历史记录，以本页和 `RELEASE.json` 为准。
- `README.md`：上传时随包提供的接收操作说明。启动与校验步骤仍可用，但其中“入口待提供”的状态已过时；当前状态以 GitHub 本页为准。
- `full-snapshot-v18-original-rebuild.zip`：主要运行包，含 `runtime/` 下同版只读代码与 `snapshot/` 下八个数据库及清单。需要运行六个查询工具的接收者必须下载，并保持代码、正文库和名称索引同版。
- `member-handoff-20261024.zip`：接收补充包，含包外验证脚本 `verify_member_delivery.py`、成员操作说明、请求例子、支持范围和待填回执；不含八个数据库。与主运行包解压到同一个全新目录后按下文校验。
- `fixed-original-sources-20261024-v2.zip`：独立的来源追溯包，含 20 份固定官方原件归档、对应台账和许可。需要查原文、示例或出处时单独解压；运行六个查询工具不依赖它，也不能把它当作 SDK 安装包。

最小接收组合是 `DELIVERY.json`、主运行包和接收补充包；需追溯原始材料时再取来源包。三个 ZIP 的准确字节数和 SHA256 均见 `RELEASE.json`。页面显示的 GB/KB 仅是四舍五入值，不能代替哈希校验。

## 接收与启动

需要 Python 3.12（SQLite 含 FTS5）。六工具使用标准库；只有模型聊天需要另装 Node、DeepSeek Harness 和由接收者自行管理的模型配置。SDK 安装包和凭据不随包分发。

1. 核对下载文件的 SHA256：在 PowerShell 运行 `Get-FileHash <下载文件> -Algorithm SHA256`，与交付清单逐字比对。
2. 把快照包和补充说明包解压到同一个全新目录，得到 runtime/、snapshot/ 和 verify_member_delivery.py；保留接收盘至少30GiB可用空间。
3. 在解压目录运行：

```powershell
python -B verify_member_delivery.py --runtime runtime --manifest snapshot/evidence-manifest-v2.json --report receiver-check.json --http
```

receiver-check.json 的 passed=true、complete=true 表示本次本机代码锁、八库指纹、SQLite/计数和HTTP检查通过；不代表成员签收、设备测试或完整API认证。报告不得写入 runtime/ 或 snapshot/，已有报告不能覆盖；复查请换新文件名。验证器是单独提供的补充工具，不在原运行包32文件锁中，其摘要由补充清单固定。

4. 启动只读工具：

```powershell
cd runtime
python -I -B tools/run_locked_runtime.py --manifest ../snapshot/evidence-manifest-v2.json --port 8547
```

在浏览器打开 http://127.0.0.1:8547/health；GET /tools 获取六工具定义。需要查询预览页时在启动命令加 --preview。3080是Harness工作台，不是项目问答页。停止服务用 Ctrl+C。

## 分工与范围

黄宇鹏见 HUANG.md；刘志华见 LIU.md；请求例子见 cases.json（从27项实际HTTP回归中选取的13个可直接请求例子，并非全部测试夹具）；已知限制与问题归属见 LIMITS.md。成员回执按 RECEIPT.json 填写，不由提供方代填。

运行包的数据编号为 openharmony-evidence-b3e990996fafe2c22e3b，代码/数据组合编号为 oh-evidence-628f16d59b78c6d06659。正文与名称索引必须同版成对，不能混入旧库或修改锁来绕过校验。

原件来源包单独解压至sources/等新目录，不与runtime/和snapshot/混放。它保留20份官方固定归档、来源台账和原有许可；它用于取得原文/示例、追溯固定提交，不含SDK安装包，也不是完整原件重建环境。上游版权、署名、许可和文件内声明随原件保留。正式API提取和身份映射由张舒阳负责。

本候选的最终执行证据见 ACCEPTANCE.json。后台、页面、真实模型、成员接收各自记录；没有证据的项目保留未验证。

