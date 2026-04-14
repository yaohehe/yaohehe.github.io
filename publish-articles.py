#!/usr/bin/env python3
"""
纯 Python 发布脚本 - 不依赖 AI模型
检查 drafts/，如有草稿则发布到 GitHub
"""
import os
import sys
import base64
import requests
import shutil
import json
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.openclaw/memory/self-improving")

def log_script_error(command, error, fix="", priority="high"):
    """写错误到 self-improving errors.jsonl"""
    entry = {
        "type": "error",
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "error": error,
        "fix": fix,
        "priority": priority,
        "status": "pending",
        "source": "publish-articles.py"
    }
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(f"{MEMORY_DIR}/errors.jsonl", "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

DRAFTS_DIR = "/root/.openclaw/workspace/affiliate-blog/drafts"
PUBLISH_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
BLOG_DIR = "/root/.openclaw/workspace/affiliate-blog"

def extract_token_from_git_remote(cwd_path):
    """从 git remote URL 中提取 token"""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            cwd=cwd_path,
            capture_output=True, text=True, timeout=10
        )
        remote_url = result.stdout.strip()
        if 'x-access-token:' in remote_url:
            token_start = remote_url.index('x-access-token:') + len('x-access-token:')
            token_end = remote_url.index('@')
            return remote_url[token_start:token_end]
    except Exception as e:
        print(f"  ⚠️ 从 {cwd_path} 提取 token 失败: {e}", flush=True)
    return None

# 优先级：env > PUBLISH_DIR git remote > BLOG_DIR git remote
TOKEN = os.environ.get('GITHUB_TOKEN', os.environ.get('GITHUB_API_TOKEN', ''))
if not TOKEN:
    TOKEN = extract_token_from_git_remote(PUBLISH_DIR)
if not TOKEN:
    TOKEN = extract_token_from_git_remote(BLOG_DIR)
if not TOKEN:
    raise RuntimeError("❌ 无法获取 GITHUB_TOKEN：环境变量和 git remote URL 均不可用")

print(f"  🔑 Token 已获取: {TOKEN[:8]}...", flush=True)

REPO = "yaohehe/yaohehe.github.io"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_file_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def push_file(filepath, content, message=None):
    url = f"https://api.github.com/repos/{REPO}/contents/{filepath}"
    if message is None:
        message = f"auto: publish {os.path.basename(filepath)}"
    data = {
        "message": message,
        "content": base64.b64encode(content).decode()
    }
    sha = get_file_sha(filepath)
    if sha:
        data["sha"] = sha
    try:
        r = requests.put(url, headers=HEADERS, json=data, timeout=30)
        if r.status_code in (200, 201):
            print(f"✅ {filepath}")
            return True
        else:
            print(f"❌ {filepath}: {r.status_code} {r.text[:200]}")
            log_script_error(
                f"requests.put {url}",
                f"HTTP {r.status_code}: {r.text[:300]}",
                fix="检查 GitHub token 权限和网络状态",
                priority="high"
            )
            return False
    except Exception as e:
        print(f"❌ {filepath}: {type(e).__name__}: {e}")
        log_script_error(
            f"requests.put {url}",
            f"{type(e).__name__}: {str(e)}",
            fix="检查网络连接和 GitHub API 可用性",
            priority="high"
        )
        return False

def push_local_file(local_path, repo_path=None, message=None):
    """读取本地文件并通过 GitHub API 推送到指定仓库路径"""
    if repo_path is None:
        repo_path = local_path
    if message is None:
        message = f"auto: update {os.path.basename(repo_path)}"
    with open(local_path, 'rb') as f:
        content = f.read()
    return push_file(repo_path, content, message)

def main():
    print(f"[{datetime.now()}] === 发布脚本开始 ===")

    # 0. 检查并推送脚本修改（generate-html.py）
    script_files = {
        f"{PUBLISH_DIR}/generate-html.py": "yaohehe.github.io/generate-html.py",
    }
    for local_path, repo_path in script_files.items():
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                local_content = f.read()
            # 获取远程 SHA
            url = f"https://api.github.com/repos/{REPO}/contents/{repo_path}"
            r = requests.get(url, headers=HEADERS)
            if r.status_code == 200:
                import base64 as b64mod
                remote_sha = r.json().get("sha")
                remote_content_b64 = r.json().get("content", "")
                remote_content = b64mod.b64decode(remote_content_b64).decode('utf-8', errors='replace')
                if remote_content.encode() != local_content:
                    print(f"📝 脚本有更新，推送 {repo_path}...")
                    push_local_file(local_path, repo_path, message=f"auto: update {os.path.basename(repo_path)}")
                else:
                    print(f"📝 {repo_path} 无变化，跳过")
            else:
                print(f"⚠️ 无法获取 {repo_path} 的远程状态")

    # 1. 检查 drafts
    if not os.path.exists(DRAFTS_DIR):
        print("✅ drafts 目录不存在，跳过")
        return

    files = [f for f in os.listdir(DRAFTS_DIR) if f.endswith('.html')]
    if not files:
        print("📭 drafts 为空，无草稿待发布")
        return

    print(f"📄 发现 {len(files)} 篇草稿: {files}")

    # 2. 复制到发布目录
    for f in files:
        src = os.path.join(DRAFTS_DIR, f)
        dst = os.path.join(PUBLISH_DIR, f)
        shutil.copy2(src, dst)
        print(f"  📋 复制: {f}")

    # 3. 运行索引同步
    import subprocess
    print("🔄 运行索引同步...")
    r = subprocess.run(
        ["python3", f"{BLOG_DIR}/update-blog-index.py"],
        cwd=PUBLISH_DIR,
        capture_output=True, text=True
    )
    if r.stdout:
        print(r.stdout[:500])
    if r.returncode != 0:
        print(f"⚠️ 索引同步异常: {r.stderr[:200]}")

    # 4. 推送到 GitHub
    print("🚀 推送草稿...")
    pushed = 0
    for f in files:
        filepath = os.path.join(PUBLISH_DIR, f)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as fp:
                content = fp.read()
            if push_file(f, content):
                pushed += 1

    # 5. 推送 index 和 sitemap
    for fname in ['index.html', 'index-en.html', 'sitemap.xml']:
        fpath = os.path.join(PUBLISH_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, 'rb') as fp:
                content = fp.read()
            push_file(fname, content)

    # 6. 归档草稿
    print("🗃️  归档草稿...")
    archive_base = f"{BLOG_DIR}/archive"
    today = datetime.now().strftime('%Y-%m-%d')
    archive_dir = os.path.join(archive_base, today)
    os.makedirs(archive_dir, exist_ok=True)
    for f in files:
        src = os.path.join(DRAFTS_DIR, f)
        dst = os.path.join(archive_dir, f)
        shutil.move(src, dst)
        print(f"  📦 {f} -> {archive_dir}/")

    if pushed == 0 and files:
        print(f"❌ 发布失败：{len(files)} 篇草稿全部推送失败，退出码 1")
        sys.exit(1)

    print(f"✅ 发布完成 | 篇数：{pushed}")
    print(f"[{datetime.now()}] === 发布脚本结束 ===")

if __name__ == '__main__':
    main()
