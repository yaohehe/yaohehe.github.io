#!/usr/bin/env python3
"""
全链路生成脚本 - AI生成内容后直接调用此脚本
AI只需生成 cn.txt 和 en.txt，然后调用 python3 此脚本
"""
import subprocess
import os
import sys

WORKSPACE = "/root/.openclaw/workspace/affiliate-blog"
TMP_DIR = "/tmp/article-gen"

def run_cmd(cmd, timeout=120):
    print(f"\n>>> {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.stdout:
        print(r.stdout)
    if r.returncode != 0:
        print(f"STDERR: {r.stderr}")
        print(f"❌ 失败 (exit {r.returncode})")
        sys.exit(1)
    return r

# Verify input files
if not os.path.exists(f"{TMP_DIR}/cn.txt"):
    print("❌ cn.txt 不存在")
    sys.exit(1)
if not os.path.exists(f"{TMP_DIR}/en.txt"):
    print("❌ en.txt 不存在")
    sys.exit(1)

print(f"✅ cn.txt: {os.path.getsize(f'{TMP_DIR}/cn.txt')} bytes")
print(f"✅ en.txt: {os.path.getsize(f'{TMP_DIR}/en.txt')} bytes")

# Step 1: HTML conversion
run_cmd(f"python3 {WORKSPACE}/generate-html.py")

# Step 2: Publish
run_cmd(f"python3 {WORKSPACE}/publish-articles.py")

print("\n✅ 全链路完成")
