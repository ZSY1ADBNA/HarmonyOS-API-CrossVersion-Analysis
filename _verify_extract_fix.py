"""提取端「未知模块」修复小样本验证：用修复后的 extract_api_info.py 重新解析 6.1 的
bluetooth.access / bluetooth.connection,与已提交 JSON 对比节点数与未知模块数。

用法：python _verify_extract_fix.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_api_info import simplify_api

SAMPLES = [
    ("@ohos.bluetooth.access.d.ts", "03_extracted_json/API6.1/ets/@ohos.bluetooth.access.json"),
    ("@ohos.bluetooth.connection.d.ts", "03_extracted_json/API6.1/ets/@ohos.bluetooth.connection.json"),
]


def unknown_count(nodes):
    return sum(1 for n in nodes
               if n.get("类型") != "module" and n.get("所属模块", "未知模块") == "未知模块")


def name_seq(nodes):
    return [n.get("名称") or n.get("签名", "") for n in nodes]


def main():
    for dts_name, json_rel in SAMPLES:
        dts = Path("01_source_files/API6.1/default/openharmony/ets/api") / dts_name
        old_json = Path(json_rel)
        print("=" * 60)
        print(dts_name)
        if not dts.exists():
            print(f"  [SKIP] 源文件不存在: {dts}")
            continue
        result = simplify_api(str(dts))
        if result is None:
            print("  [FAIL] simplify_api 返回 None(无 @kit 或解析失败)")
            continue
        new_nodes = result.get("节点", [])
        old_nodes = json.loads(old_json.read_text(encoding="utf-8")).get("节点", []) if old_json.exists() else []
        print(f"  旧 JSON 节点数: {len(old_nodes)}, 未知模块: {unknown_count(old_nodes)}")
        print(f"  新提取节点数: {len(new_nodes)}, 未知模块: {unknown_count(new_nodes)}")
        if old_nodes:
            same_count = len(old_nodes) == len(new_nodes)
            same_seq = name_seq(old_nodes) == name_seq(new_nodes)
            print(f"  节点数一致: {same_count}, 名称顺序一致: {same_seq}")


if __name__ == "__main__":
    main()
