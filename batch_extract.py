import os
import sys
import time
import json
import shutil
import traceback
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# ==================== 添加 extract_api_info.py 的路径 ====================
# 获取当前脚本所在目录
SCRIPT_DIR = Path(__file__).parent
# 将脚本目录添加到 Python 路径，以便导入 extract_api_info
sys.path.insert(0, str(SCRIPT_DIR))

# 导入 extract_api_info 模块
import extract_api_info

# ==================== 配置 ====================
# 项目根目录
PROJECT_ROOT = r"C:\Users\MR\Desktop\HarmonyAPI_Project"

# 源文件目录（7个版本的 .d.ts 文件）
SOURCE_ROOT = Path(PROJECT_ROOT) / "01_source_files"

# 输出目录（JSON 文件）
OUTPUT_ROOT = Path(PROJECT_ROOT) / "03_extracted_json"

# 日志目录
LOG_DIR = Path(PROJECT_ROOT) / "06_logs"


def find_all_dts_files():
    """扫描所有版本文件夹下的 .d.ts 文件"""
    all_files = []
    
    print("[SCAN] 正在扫描源文件目录...")
    
    # 遍历 01_source_files 下的所有版本文件夹
    for version_dir in SOURCE_ROOT.iterdir():
        if not version_dir.is_dir():
            continue
        
        version_name = version_dir.name
        print(f"\n[SCAN] 扫描版本: {version_name}")
        
        # 查找 ets/api 目录（主要）
        ets_api_dir = version_dir / "default" / "openharmony" / "ets" / "api"
        js_api_dir = version_dir / "default" / "openharmony" / "js" / "api"
        
        ets_count = 0
        js_count = 0
        
        # 处理 ets 版本
        if ets_api_dir.exists():
            for dts_file in ets_api_dir.rglob("*.d.ts"):
                # 计算相对路径，用于生成输出文件名
                rel_path = dts_file.relative_to(ets_api_dir)
                output_name = str(rel_path).replace("\\", "_").replace("/", "_").replace(".d.ts", ".json")
                
                all_files.append({
                    "path": str(dts_file),
                    "version": version_name,
                    "output_dir": str(OUTPUT_ROOT / version_name / "ets"),
                    "output_name": output_name,
                    "type": "ets"
                })
                ets_count += 1
        
        # 处理 js 版本
        if js_api_dir.exists():
            for dts_file in js_api_dir.rglob("*.d.ts"):
                rel_path = dts_file.relative_to(js_api_dir)
                output_name = str(rel_path).replace("\\", "_").replace("/", "_").replace(".d.ts", ".json")
                
                all_files.append({
                    "path": str(dts_file),
                    "version": version_name,
                    "output_dir": str(OUTPUT_ROOT / version_name / "js"),
                    "output_name": output_name,
                    "type": "js"
                })
                js_count += 1
        
        print(f"   [OK] ets: {ets_count} 个文件, js: {js_count} 个文件")
    
    return all_files


def process_single_file(file_info):
    """处理单个 .d.ts 文件，调用 simplify_api 生成 JSON"""
    try:
        path = file_info["path"]
        version = file_info["version"]
        output_dir = file_info["output_dir"]
        output_name = file_info["output_name"]
        
        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        output_path = Path(output_dir) / output_name
        
        # 调用 extract_api_info 的 simplify_api 函数
        # 注意：simplify_api 需要返回一个 dict
        result = extract_api_info.simplify_api(str(path))
        
        if result is None:
            # 没有 @kit 注释的文件，返回空结构
            result = {
                "节点": [
                    {
                        "名称": f"@{version}_{Path(path).stem}",
                        "类型": "module",
                        "描述": f"从 {Path(path).name} 提取",
                        "层级": 0
                    }
                ]
            }
        
        # 确保结果中有版本信息
        if "节点" in result:
            for node in result["节点"]:
                if "版本" not in node:
                    node["版本"] = version
        
        # 写入 JSON 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 统计节点数
        node_count = len(result.get("节点", []))
        
        return {
            "success": True,
            "file": path,
            "version": version,
            "output": str(output_path),
            "nodes": node_count
        }
        
    except Exception as e:
        return {
            "success": False,
            "file": file_info["path"],
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def main():
    print("=" * 70)
    print("HarmonyOS API 批量提取工具（使用原 extract_api_info）")
    print("=" * 70)
    print(f"[DIR] 项目目录: {PROJECT_ROOT}")
    print(f"[DIR] 源文件目录: {SOURCE_ROOT}")
    print(f"[DIR] 输出目录: {OUTPUT_ROOT}")

    # 1. 扫描所有 .d.ts 文件
    print("\n[SCAN] 正在扫描 .d.ts 文件...")
    all_files = find_all_dts_files()

    if not all_files:
        print("[ERR] 未找到任何 .d.ts 文件")
        print("   请确认 01_source_files 下有以下结构:")
        print("   APIxxx/default/openharmony/ets/api/*.d.ts")
        print("   APIxxx/default/openharmony/js/api/*.d.ts")
        return
    
    print(f"\n[INFO] 总共找到 {len(all_files)} 个 .d.ts 文件")

    # 按版本统计
    version_stats = {}
    type_stats = {"ets": 0, "js": 0}
    for f in all_files:
        ver = f["version"]
        version_stats[ver] = version_stats.get(ver, 0) + 1
        type_stats[f.get("type", "unknown")] += 1

    print("\n[VERSIONS] 各版本文件数量:")
    for ver, count in sorted(version_stats.items()):
        print(f"   {ver}: {count} 个")
    print(f"\n[TYPES] 按类型分布: ets={type_stats['ets']}, js={type_stats['js']}")

    # 2. 询问是否继续
    print(f"\n[WARN] 将生成 {len(all_files)} 个 JSON 文件到 {OUTPUT_ROOT}")
    confirm = input("\n是否开始处理？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    # 3. 并行处理（注意：simplify_api 可能不是线程安全的，但多进程是独立的）
    workers = min(multiprocessing.cpu_count(), 4)
    print(f"\n[CONFIG] 使用 {workers} 个进程并行处理")
    print("[START] 开始处理...\n")
    
    start_time = time.time()
    results = []
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_single_file, f): f for f in all_files}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)
            status = "[OK]" if result["success"] else "[FAIL]"
            file_name = Path(result["file"]).name
            if result["success"]:
                print(f"[{i+1}/{len(all_files)}] {status} {file_name} -> {result.get('nodes', 0)} 个节点")
            else:
                print(f"[{i+1}/{len(all_files)}] {status} {file_name}")
                print(f"       错误: {result.get('error', '未知错误')[:150]}")
    
    # 4. 统计结果
    elapsed = time.time() - start_time
    success = sum(1 for r in results if r["success"])
    fail = len(results) - success
    total_nodes = sum(r.get("nodes", 0) for r in results if r["success"])
    
    print("\n" + "=" * 70)
    print("[STATS] 处理完成统计")
    print("=" * 70)
    print(f"[OK] 成功: {success} 个文件")
    print(f"[FAIL] 失败: {fail} 个文件")
    print(f"[NODES] 共提取节点: {total_nodes} 个")
    print(f"[TIME] 总耗时: {elapsed:.2f} 秒")
    if len(all_files) > 0:
        print(f"[SPEED] 平均速度: {elapsed/len(all_files):.2f} 秒/文件")

    # 按版本统计
    print("\n[VERSIONS] 各版本处理结果:")
    version_result = {}
    for r in results:
        ver = r["version"]
        if ver not in version_result:
            version_result[ver] = {"success": 0, "fail": 0, "nodes": 0}
        if r["success"]:
            version_result[ver]["success"] += 1
            version_result[ver]["nodes"] += r.get("nodes", 0)
        else:
            version_result[ver]["fail"] += 1
    
    for ver, stats in sorted(version_result.items()):
        total = stats['success'] + stats['fail']
        success_rate = stats['success'] / total * 100 if total > 0 else 0
        print(f"   {ver}: 成功 {stats['success']}, 失败 {stats['fail']} ({success_rate:.1f}%) - {stats['nodes']} 个节点")
    
    print(f"\n[OUTPUT] JSON 文件保存在: {OUTPUT_ROOT}")
    
    # 保存处理日志
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"extract_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"提取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总文件数: {len(all_files)}\n")
        f.write(f"成功: {success}\n")
        f.write(f"失败: {fail}\n")
        f.write(f"总节点数: {total_nodes}\n")
        f.write(f"总耗时: {elapsed:.2f}秒\n")
        
        # 写入失败的文件列表
        if fail > 0:
            f.write("\n失败的文件:\n")
            for r in results:
                if not r["success"]:
                    f.write(f"  {r['file']}: {r.get('error', '')}\n")
    
    print(f"[LOG] 日志已保存: {log_file}")


if __name__ == "__main__":
    main()