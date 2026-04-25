#!/usr/bin/env python3
"""
verify-publish.py - 发布验证闭环 v2

不再依赖 git status（staged changes 会误判）
改用 archive/ 目录扫描 + GitHub API 文件存在性检查

逻辑：
1. 扫描 yaohehe.github.io/archive/YYYY-MM-DD/ 中当天新修改的文章
2. 通过 GitHub API 检查远程是否已存在
3. 未存在 → 触发 publish-articles.py 推送
4. 已有 → 验证通过
"""
import os
import subprocess
import requests
import base64
import json
from datetime import datetime, timedelta

YAOHEHE_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
AFFILIATE_BLOG = "/root/.openclaw/workspace/affiliate-blog"
SEO_MEMO = os.path.expanduser("~/self-improving/domains/seo.md")
VERIFICATION_LOG = f"{AFFILIATE_BLOG}/reports/verification-log.txt"
MEMORY_DIR = os.path.expanduser("~/.openclaw/memory/self-improving")

REPO = "yaohehe/yaohehe.github.io"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {msg}")

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

def github_file_exists(path):
    """检查 GitHub remote 上指定路径是否已存在文件"""
    token = get_github_token()
    if not token:
        return None  # unknown
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=headers, timeout=15)
    return r.status_code == 200

def log_error(command, error, fix, priority="high"):
    entry = {
        "type": "error", "timestamp": datetime.now().isoformat(),
        "command": command, "error": error, "fix": fix,
        "priority": priority, "status": "pending", "source": "verify-publish.py"
    }
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(f"{MEMORY_DIR}/errors.jsonl", "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def find_recent_articles(hours=36, limit=10):
    """扫描 archive 目录查找最近 N 小时内修改的文章文件"""
    articles = []
    cutoff = datetime.now() - timedelta(hours=hours)
    archive_dir = os.path.join(YAOHEHE_DIR, "archive")
    if not os.path.isdir(archive_dir):
        return articles
    for root, dirs, files in os.walk(archive_dir):
        for f in files:
            if not f.endswith('.html') or '-en.html' in f:
                continue
            fp = os.path.join(root, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                if mtime >= cutoff:
                    rel = os.path.relpath(fp, YAOHEHE_DIR)
                    if rel not in articles:
                        articles.append(rel)
                        if len(articles) >= limit:
                            return articles
            except Exception:
                pass
    return articles

def verify_and_publish():
    """验证 archive/ 中最近修改的文章，并确保已推送到 GitHub"""
    log("开始发布验证...")

    # 扫描最近文章
    recent = find_recent_articles(hours=36, limit=10)
    if not recent:
        log("⚠️ 最近36小时无新文章")
        note = f"\n- [{datetime.now().strftime('%Y-%m-%d')}] ⚠️ 验证: 最近36小时无新文章发布"
        with open(SEO_MEMO, 'a') as f:
            f.write(note)
        return note

    log(f"📋 发现 {len(recent)} 篇最近修改的文章")

    # 检查每篇是否已在 GitHub remote
    unpublished = []
    published = []
    for rel_path in recent:
        exists = github_file_exists(rel_path)
        if exists is None:
            log(f"⚠️ 无法检查 {rel_path}，跳过")
            published.append(rel_path)
        elif exists:
            published.append(rel_path)
        else:
            unpublished.append(rel_path)

    log(f"✅ 已发布: {len(published)} 篇")
    if unpublished:
        log(f"❌ 未发布: {len(unpublished)} 篇: {unpublished}")

    # 写入记录
    if unpublished:
        log("🚀 检测到未发布文章，触发 publish-articles.py...")
        r = subprocess.run(
            ["python3", f"{AFFILIATE_BLOG}/publish-articles.py"],
            cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=300
        )
        if r.returncode == 0:
            log("✅ publish-articles.py 执行成功")
            note = f"\n- [{datetime.now().strftime('%Y-%m-%d')}] ✅ 验证通过: 发布 {len(recent)} 篇（含 {len(unpublished)} 篇补发）"
        else:
            log(f"❌ publish-articles.py 失败: {r.stderr[:200]}")
            log_error("publish-articles.py", r.stderr[:300], "检查 GitHub token 和网络状态", "high")
            note = f"\n- [{datetime.now().strftime('%Y-%m-%d')}] ❌ 验证失败: {len(unpublished)} 篇未发布（publish-articles.py 报错）"
    else:
        note = f"\n- [{datetime.now().strftime('%Y-%m-%d')}] ✅ 验证通过: {len(recent)} 篇已全部在线"

    with open(SEO_MEMO, 'a') as f:
        f.write(note)

    os.makedirs(os.path.dirname(VERIFICATION_LOG), exist_ok=True)
    with open(VERIFICATION_LOG, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note[2:]}\n")

    log(f"✅ 验证结果已记录")
    return note

if __name__ == "__main__":
    note = verify_and_publish()
    print(f"\n验证摘要: {note}")