#!/usr/bin/env python3
"""
全链路生成脚本 - AI生成内容后直接调用此脚本
AI只需生成 cn.txt 和 en.txt，然后调用 python3 此脚本
"""
import subprocess
import os
import sys
import json
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.openclaw/memory/self-improving")

def log_script_error(command, error, fix="", priority="medium"):
    """写错误到 self-improving errors.jsonl"""
    entry = {
        "type": "error",
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "error": error,
        "fix": fix,
        "priority": priority,
        "status": "pending",
        "source": "run-pipeline.py"
    }
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(f"{MEMORY_DIR}/errors.jsonl", "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

WORKSPACE = "/root/.openclaw/workspace/affiliate-blog"
TMP_DIR = "/tmp/article-gen"

def run_cmd(cmd, timeout=120):
    print(f"\n>>> {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        print(f"STDERR: {e}")
        print(f"❌ 超时 (timeout {timeout}s)")
        log_script_error(cmd, f"Timeout after {timeout}s", fix="检查命令执行时间，必要时增加 timeout", priority="medium")
        sys.exit(1)
    except Exception as e:
        print(f"STDERR: {e}")
        print(f"❌ 异常 ({type(e).__name__}): {e}")
        log_script_error(cmd, f"{type(e).__name__}: {str(e)}", fix="检查系统环境和命令可用性", priority="medium")
        sys.exit(1)
    if r.stdout:
        print(r.stdout)
    if r.returncode != 0:
        print(f"STDERR: {r.stderr}")
        print(f"❌ 失败 (exit {r.returncode})")
        log_script_error(cmd, f"exit {r.returncode}: {r.stderr[:300]}", priority="medium")
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
