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

def run_cmd(cmd, timeout=120, fatal=True):
    print(f"\n>>> {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        print(f"STDERR: {e}")
        print(f"❌ 超时 (timeout {timeout}s)")
        log_script_error(cmd, f"Timeout after {timeout}s", fix="增加 timeout 或优化脚本性能", priority="high")
        if fatal:
            sys.exit(1)
        return None
    except Exception as e:
        print(f"STDERR: {e}")
        print(f"❌ 异常 ({type(e).__name__}): {e}")
        log_script_error(cmd, f"{type(e).__name__}: {str(e)}", fix="检查系统环境和命令可用性", priority="high")
        if fatal:
            sys.exit(1)
        return None
    if r.stdout:
        print(r.stdout)
    if r.returncode != 0:
        print(f"STDERR: {r.stderr}")
        print(f"⚠️ 失败 (exit {r.returncode})")
        log_script_error(cmd, f"exit {r.returncode}: {r.stderr[:300]}", priority="medium")
        if fatal:
            sys.exit(1)
        return None
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

# Step 1: HTML conversion (非致命，drafts 存在时跳过)
drafts_before = set(os.listdir(f"{WORKSPACE}/drafts")) if os.path.exists(f"{WORKSPACE}/drafts") else set()
gen_ok = run_cmd(f"python3 {WORKSPACE}/generate-html.py", fatal=False) is not None
drafts_after = set(os.listdir(f"{WORKSPACE}/drafts")) if os.path.exists(f"{WORKSPACE}/drafts") else set()
new_drafts = drafts_after - drafts_before

if not new_drafts:
    print(f"⚠️ 未生成新草稿，尝试使用 /tmp/article-gen 中的内容")
    # 直接复制 tmp 到 drafts 目录
    for fname in ["cn.html", "en.html"]:
        tmp_path = f"{TMP_DIR}/{fname}"
        if os.path.exists(tmp_path):
            import shutil
            dst = f"{WORKSPACE}/drafts/{datetime.now().strftime('%Y-%m-%d')}-{fname.replace('.html','.txt').replace('cn','cn').replace('en','en')}.html"
            shutil.copy2(tmp_path, dst)
            print(f"  📋 复制: {os.path.basename(dst)}")

# Step 2: Publish (无论 generate 是否成功，只要 drafts 有内容就执行)
run_cmd(f"python3 {WORKSPACE}/publish-articles.py", timeout=300)

print("\n✅ 全链路完成")
