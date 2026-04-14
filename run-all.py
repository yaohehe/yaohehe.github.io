#!/usr/bin/env python3
"""
一键生成+发布脚本
所有步骤顺序执行，避免 session 中途退出
"""
import subprocess
import sys
import os

def run(cmd, timeout=120):
    print(f"\n>>> {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.stdout:
        print(r.stdout)
    if r.returncode != 0:
        print(f"❌ 命令失败 (exit {r.returncode})")
        if r.stderr:
            print(r.stderr)
        sys.exit(1)
    return r

WORKSPACE = "/root/.openclaw/workspace/affiliate-blog"
TMP_DIR = "/tmp/article-gen"
GIT_REPO = "/root/.openclaw/workspace/yaohehe.github.io"

# Step 1: Clean and create dir
run(f"rm -rf {TMP_DIR} && mkdir -p {TMP_DIR}")

# Step 2: Generate content (AI writes cn.txt and en.txt)
print("\n=== 请生成文章内容 ===")
print("中文文章写入: /tmp/article-gen/cn.txt")
print("英文文章写入: /tmp/article-gen/en.txt")
print("格式: 第一行必须是 元数据|元数据|元数据|元数据 (四字段用|分隔，单行)")
print("完成后按 Enter 继续...")
input()

# Verify files exist
if not os.path.exists(f"{TMP_DIR}/cn.txt") or not os.path.exists(f"{TMP_DIR}/en.txt"):
    print("❌ cn.txt 或 en.txt 不存在，生成中断")
    sys.exit(1)

print(f"✅ 中文稿: {os.path.getsize(f'{TMP_DIR}/cn.txt')} bytes")
print(f"✅ 英文稿: {os.path.getsize(f'{TMP_DIR}/en.txt')} bytes")

# Step 3: HTML conversion
run(f"python3 {WORKSPACE}/generate-html.py")

# Step 4: Publish
run(f"python3 {WORKSPACE}/publish-articles.py")

print("\n✅ 全部完成")
