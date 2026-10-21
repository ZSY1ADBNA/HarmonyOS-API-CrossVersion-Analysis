# 余镕熙：2026-10-24 交付候选

本目录提供同版只读运行代码、包外校验器和操作说明。下载状态、文件名、SHA256及支持范围见 RELEASE.json。大文件放百度网盘；当前入口待提供，尚未完成云端交付。成员本人接收和评测单独记录。

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
