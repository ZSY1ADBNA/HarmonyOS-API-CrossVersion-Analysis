"""无交互批量提取 - 自动确认并处理所有版本"""
import sys
sys.path.insert(0, r"C:\Users\MR\Desktop\HarmonyAPI_Project")

from pathlib import Path
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

OUTPUT_ROOT = Path(r"C:\Users\MR\Desktop\HarmonyAPI_Project\03_extracted_json")
LOG_DIR = Path(r"C:\Users\MR\Desktop\HarmonyAPI_Project\06_logs")


def main():
    from batch_extract import find_all_dts_files, process_single_file

    print("=" * 70)
    print("HarmonyOS API 批量提取工具 - 自动模式")
    print("=" * 70)

    # 扫描文件
    print("\n[SCAN] 正在扫描...")
    all_files = find_all_dts_files()
    print(f"[INFO] 共找到 {len(all_files)} 个 .d.ts 文件")

    # 统计
    version_stats = {}
    for f in all_files:
        ver = f["version"]
        version_stats[ver] = version_stats.get(ver, 0) + 1
    print("\n[VERSIONS] 各版本文件数量:")
    for ver, count in sorted(version_stats.items()):
        print(f"   {ver}: {count} 个")

    # 自动处理
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
            file_name = Path(result["file"]).name
            status = "[OK]" if result["success"] else "[FAIL]"
            if result["success"]:
                print(f"[{i+1}/{len(all_files)}] {status} {file_name} -> {result.get('nodes', 0)} nodes")
            else:
                print(f"[{i+1}/{len(all_files)}] {status} {file_name}: {result.get('error', '')[:100]}")

    # 统计
    elapsed = time.time() - start_time
    success = sum(1 for r in results if r["success"])
    fail = len(results) - success
    total_nodes = sum(r.get("nodes", 0) for r in results if r["success"])

    print("\n" + "=" * 70)
    print("[STATS] 处理完成")
    print("=" * 70)
    print(f"[OK] 成功: {success}")
    print(f"[FAIL] 失败: {fail}")
    print(f"[NODES] 总节点: {total_nodes}")
    print(f"[TIME] 耗时: {elapsed:.1f}s ({elapsed/60:.1f}min)")

    version_result = {}
    for r in results:
        ver = r["version"]
        if ver not in version_result:
            version_result[ver] = {"ok": 0, "fail": 0, "nodes": 0}
        if r["success"]:
            version_result[ver]["ok"] += 1
            version_result[ver]["nodes"] += r.get("nodes", 0)
        else:
            version_result[ver]["fail"] += 1

    print("\n[VERSIONS] 各版本结果:")
    for ver, stats in sorted(version_result.items()):
        print(f"   {ver}: ok={stats['ok']}, fail={stats['fail']}, nodes={stats['nodes']}")

    # 日志
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"extract_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Files: {len(all_files)}, Success: {success}, Fail: {fail}\n")
        f.write(f"Nodes: {total_nodes}, Time: {elapsed:.1f}s\n")
        for r in results:
            if not r["success"]:
                f.write(f"FAIL: {r['file']}: {r.get('error', '')}\n")
    print(f"[LOG] {log_file}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
