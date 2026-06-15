import os
import sys
import shutil
from pathlib import Path

# 配置
REPO_PATH = Path(r"C:\Users\MR\Desktop\interface_sdk-js")
PROJECT_ROOT = Path(r"C:\Users\MR\Desktop\HarmonyAPI_Project")
SOURCE_ROOT = PROJECT_ROOT / "01_source_files"

# 要提取的版本：Git分支 -> 项目目录名
VERSIONS = {
    "OpenHarmony-4.1-Release":    "API4.1",
    "OpenHarmony-5.0.3-Release":  "API5.0",
    "OpenHarmony-5.1.0-Release":  "API5.1",
    "OpenHarmony-6.0-Release":    "API6.0",
}


def run_git(*args):
    import subprocess
    cmd = ["git", "-C", str(REPO_PATH)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def count_dts(directory):
    return len(list(Path(directory).rglob("*.d.ts")))


def main():
    print("=" * 70)
    print("多版本 HarmonyOS API 文件提取工具")
    print("=" * 70)

    for branch, version_name in VERSIONS.items():
        print(f"\n{'='*70}")
        print(f"处理: {branch} -> {version_name}")
        print(f"{'='*70}")

        # 1. 检出分支
        print(f"  切换分支到 {branch}...")
        result = run_git("checkout", branch)
        if result.returncode != 0:
            print(f"  检出失败: {result.stderr}")
            # 尝试从 origin 检出
            result = run_git("checkout", "-b", branch, f"origin/{branch}")
            if result.returncode != 0:
                print(f"  从 origin 检出也失败，跳过")
                continue

        # 2. 复制 api/ 目录
        src_api = REPO_PATH / "api"
        dst_api = SOURCE_ROOT / version_name / "default" / "openharmony" / "ets" / "api"

        if not src_api.exists():
            print(f"  api/ 目录不存在，跳过")
            continue

        # 清空目标目录
        if dst_api.exists():
            shutil.rmtree(dst_api)

        dst_api.parent.mkdir(parents=True, exist_ok=True)

        print(f"  复制 {src_api} -> {dst_api}")
        shutil.copytree(src_api, dst_api)

        file_count = count_dts(dst_api)
        print(f"  完成: {file_count} 个 .d.ts 文件")

    print(f"\n{'='*70}")
    print("所有版本提取完成")
    print(f"{'='*70}")
    print(f"文件位于: {SOURCE_ROOT}")

    for version_name in VERSIONS.values():
        vdir = SOURCE_ROOT / version_name / "default" / "openharmony" / "ets" / "api"
        if vdir.exists():
            print(f"  {version_name}: {count_dts(vdir)} 个 .d.ts 文件")


if __name__ == "__main__":
    main()
