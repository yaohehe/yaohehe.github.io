#!/usr/bin/env python3
"""
publish-articles.py - 稳定发布脚本 v2

核心改进：
- 不依赖 drafts 目录
- 从 yaohehe.github.io/archive/ 读取当天文章作为唯一数据源
- 独立运行，不依赖 AI 生成流程的调用

工作流：
1. 扫描 yaohehe.github.io/archive/ 当天修改的 HTML 文件
2. 运行 update-blog-index.py（生成 index + sitemap + 检测断链）
3. 将所有变更（archive/* + index + sitemap）推送到 GitHub
4. 验证推送结果（HTTP 200）
"""
import os
import re
import sys
import base64
import json
import shutil
import subprocess
import requests
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.openclaw/memory/self-improving")
YAOHEHE_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
BLOG_DIR = "/root/.openclaw/workspace/affiliate-blog"
REPO = "yaohehe/yaohehe.github.io"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {msg}", flush=True)

def log_error(command, error, fix, priority="high"):
    entry = {
        "type": "error", "timestamp": datetime.now().isoformat(),
        "command": command, "error": error, "fix": fix,
        "priority": priority, "status": "pending", "source": "publish-articles.py"
    }
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(f"{MEMORY_DIR}/errors.jsonl", "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_github_token():
    """从 git remote 提取 token"""
    try:
        r = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=10
        )
        url = r.stdout.strip()
        if 'x-access-token:' in url:
            s = url.index('x-access-token:') + len('x-access-token:')
            e = url.index('@')
            return url[s:e]
    except:
        pass
    return None

TOKEN = get_github_token()
if not TOKEN:
    raise RuntimeError("❌ 无法获取 GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
log(f"🔑 Token 已获取: {TOKEN[:8]}...")

def get_file_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def push_file(filepath, content, message=None):
    """通过 GitHub API 推送单个文件"""
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
            log(f"✅ {filepath}")
            return True
        else:
            log(f"❌ {filepath}: {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        log(f"❌ {filepath}: {type(e).__name__}: {e}")
        return False

def find_articles_to_publish():
    """扫描 yaohehe.github.io/archive/ 找出当天需要发布的文章"""
    articles = []
    today = datetime.now().strftime('%Y-%m-%d')
    archive_dir = os.path.join(YAOHEHE_DIR, "archive")

    # 扫描当天目录
    today_dir = os.path.join(archive_dir, today)
    if os.path.isdir(today_dir):
        for f in os.listdir(today_dir):
            if f.endswith('.html') and '-en.html' not in f:
                fp = os.path.join(today_dir, f)
                articles.append((f"archive/{today}/{f}", fp))

    return articles

def run_update_index():
    """运行索引同步（这个已经在 yaohehe.github.io 本地操作）"""
    log("🔄 运行索引同步...")
    r = subprocess.run(
        ["python3", f"{BLOG_DIR}/update-blog-index.py"],
        cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=60
    )
    if r.stdout:
        for line in r.stdout.split('\n')[-5:]:
            if line.strip():
                log(f"  {line}")
    if r.returncode != 0:
        log(f"⚠️ 索引同步异常: {r.stderr[:200]}")
        return False
    return True

def verify_no_broken_links():
    """验证 index 中所有链接都指向真实存在的文件"""
    log("🔍 验证索引链接完整性...")
    broken = []
    for idx_file in ['index.html', 'index-en.html']:
        idx_path = os.path.join(YAOHEHE_DIR, idx_file)
        if not os.path.exists(idx_path):
            continue
        with open(idx_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for href_m in re.finditer(r'href="([^"]+)"', content):
            href = href_m.group(1)
            if href.startswith('http') or href.startswith('//') or href in ('index.html', 'index-en.html', '#'):
                continue
            file_path = os.path.join(YAOHEHE_DIR, href)
            if not os.path.exists(file_path):
                broken.append((idx_file, href, file_path))

    if broken:
        log(f"❌ 索引验证失败：发现 {len(broken)} 个断链:")
        for idx_f, href, path in broken[:5]:
            log(f"  [{idx_f}] {href}")
        return False
    log("✅ 索引链接验证通过")
    return True

def main():
    log("=== 发布脚本开始 ===")

    # Step 1: 运行索引同步（更新 index.html, index-en.html, sitemap.xml）
    if not run_update_index():
        log("❌ 索引同步失败，退出")
        sys.exit(1)

    # Step 2: 验证索引无断链
    if not verify_no_broken_links():
        log("❌ 发现断链，退出")
        sys.exit(1)

    # Step 3: 找出当天需要发布的文章
    articles = find_articles_to_publish()
    log(f"📄 发现 {len(articles)} 篇当天文章待发布")

    # Step 4: 推送文章文件
    pushed = 0
    for remote_path, local_path in articles:
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                content = f.read()
            if push_file(remote_path, content):
                pushed += 1

    # Step 5: 推送 index + sitemap
    for fname in ['index.html', 'index-en.html', 'sitemap.xml']:
        fpath = os.path.join(YAOHEHE_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, 'rb') as f:
                content = f.read()
            push_file(fname, content)

    if pushed == 0 and not articles:
        log("📭 无新文章待发布")
    elif pushed == 0:
        log(f"❌ 推送失败：{len(articles)} 篇文章全部失败")
        sys.exit(1)

    log(f"✅ 发布完成 | 文章：{pushed}")
    log("=== 发布脚本结束 ===")

if __name__ == '__main__':
    main()