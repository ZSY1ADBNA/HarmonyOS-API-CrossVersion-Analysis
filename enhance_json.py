import os
import json
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== 配置 ====================
# 输入：batch_extract.py 生成的 JSON 目录
JSON_ROOT = r"C:\Users\MR\Desktop\HarmonyAPI_Project\03_extracted_json"
# 输出：增强后的 JSON 目录
OUTPUT_ROOT = r"C:\Users\MR\Desktop\HarmonyAPI_Project\03_extracted_json"


# ==================== 提取函数 ====================
def extract_since_version(comments: list) -> str:
    for line in comments:
        if line.startswith('@since'):
            return line.replace('@since', '').strip()
    return ""


def extract_system_capability(comments: list) -> str:
    for line in comments:
        if line.startswith('@syscap'):
            return line.replace('@syscap', '').strip()
    return ""


def extract_param_descriptions(comments: list) -> dict:
    """从注释中提取参数说明"""
    param_desc = {}
    for line in comments:
        if line.startswith('@param'):
            content = line.replace('@param', '').strip()
            match = re.match(r'\{([^}]+)\}\s+(\w+)\s*[-]?\s*(.*)', content)
            if match:
                type_, name, desc = match.groups()
                param_desc[name] = {
                    "类型": type_.strip(),
                    "说明": desc.strip()
                }
            else:
                parts = content.split(' ', 1)
                if len(parts) >= 2:
                    name = parts[0]
                    desc = parts[1] if len(parts) > 1 else ''
                    param_desc[name] = {
                        "类型": "any",
                        "说明": desc.strip()
                    }
    return param_desc


def extract_parameters_from_node(node: dict) -> list:
    """从节点提取参数列表"""
    if node.get("类型") != "method":
        return []

    comments = node.get("注释信息", [])
    param_descriptions = extract_param_descriptions(comments)

    parameters = []
    for param_name, info in param_descriptions.items():
        parameters.append({
            "名称": param_name,
            "类型": info.get("类型", "any"),
            "必填": True,
            "说明": info.get("说明", "")
        })

    return parameters


def extract_return_description(comments: list) -> str:
    for line in comments:
        if line.startswith('@returns') or line.startswith('@return'):
            content = line.replace('@returns', '').replace('@return', '').strip()
            match = re.match(r'\{([^}]+)\}\s*(.*)', content)
            if match:
                return match.group(2).strip()
            return content.strip()
    return ""


def extract_error_codes(comments: list) -> list:
    errors = []
    for line in comments:
        if line.startswith('@throws'):
            content = line.replace('@throws', '').strip()
            match = re.search(r'(\d+)', content)
            if match:
                error_code = match.group(1)
                desc = ''
                if '-' in content:
                    desc = content.split('-', 1)[1].strip()
                errors.append({
                    "code": error_code,
                    "description": desc
                })
    return errors


def enhance_node(node: dict) -> dict:
    """增强单个节点，添加新字段"""
    comments = node.get("注释信息", [])

    node["since_version"] = extract_since_version(comments)
    node["system_capability"] = extract_system_capability(comments)
    node["parameters"] = extract_parameters_from_node(node)
    node["return_description"] = extract_return_description(comments)
    node["error_codes"] = extract_error_codes(comments)

    return node


def enhance_json_file(file_path: str, output_path: str):
    """处理单个 JSON 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "节点" not in data:
            return {"file": file_path, "status": "skip", "reason": "无节点"}

        for node in data["节点"]:
            enhance_node(node)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"file": file_path, "status": "success", "nodes": len(data["节点"])}

    except Exception as e:
        return {"file": file_path, "status": "error", "error": str(e)}


def collect_all_json_files(root_path):
    """收集所有 JSON 文件"""
    root = Path(root_path)
    files = []
    for json_file in root.rglob("*.json"):
        rel_path = json_file.relative_to(root)
        output_path = Path(OUTPUT_ROOT) / rel_path
        files.append((str(json_file), str(output_path)))
    return files


def main():
    print("=" * 70)
    print("JSON 增强工具（从注释提取字段）")
    print("=" * 70)
    print(f"输入目录: {JSON_ROOT}")
    print(f"输出目录: {OUTPUT_ROOT}")

    print("\n正在扫描 JSON 文件...")
    files = collect_all_json_files(JSON_ROOT)
    print(f"找到 {len(files)} 个 JSON 文件")

    if not files:
        print("未找到任何 JSON 文件")
        return

    confirm = input("\n将生成增强版 JSON 文件，是否继续？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return

    workers = 4
    print(f"\n使用 {workers} 个线程并行处理")
    print("开始处理...\n")

    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(enhance_json_file, f, out): (f, out) for f, out in files}

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)

            if result["status"] == "success":
                print(f"[{i + 1}/{len(files)}] [OK] {Path(result['file']).name} -> {result['nodes']} 个节点")
            elif result["status"] == "skip":
                print(f"[{i + 1}/{len(files)}] [SKIP] {Path(result['file']).name} - {result.get('reason', '跳过')}")
            else:
                print(f"[{i + 1}/{len(files)}] [FAIL] {Path(result['file']).name} - {result.get('error', '错误')[:50]}")

    elapsed = time.time() - start_time
    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")

    print("\n" + "=" * 70)
    print("处理完成")
    print("=" * 70)
    print(f"成功: {success} 个文件")
    print(f"失败: {errors} 个文件")
    print(f"总耗时: {elapsed:.2f} 秒")
    print(f"\n增强版 JSON 保存在: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
