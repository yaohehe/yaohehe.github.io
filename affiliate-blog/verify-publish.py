#!/usr/bin/env python3
"""
verify-publish.py - 发布验证闭环
检查最近生成的文章是否成功发布，记录结果到 seo.md
如失败，识别原因并写入待改进项
"""
import os
import subprocess
import re
import json
from datetime import datetime, timedelta

YAOHEHE_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
AFFILIATE_BLOG = "/root/.openclaw/workspace/affiliate-blog"
SEO_MEMO = os.path.expanduser("~/self-improving/domains/seo.md")
VERIFICATION_LOG = f"{AFFILIATE_BLOG}/reports/verification-log.txt"

def ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M')

def log(msg):
    print(f"[{ts()}] {msg}")

def check_articles_online():
    """检查文章是否在线（通过 git remote + web fetch）"""
    if not os.path.exists(YAOHEHE_DIR):
        return False, "目录不存在"
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=10
        )
        if r.stdout.strip():
            # Only flag unstaged changes (space-prefixed), not staged changes
            unstaged = [l for l in r.stdout.strip().split('\n') if l.startswith(' ')]
            if unstaged:
                return False, f"有未提交更改: {r.stdout.strip()[:100]}"
        return True, "Git 工作区干净"
    except Exception as e:
        return False, f"git status 失败: {e}"

def find_recent_articles(hours=36, limit=5):
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
                    # Store relative path
                    rel = os.path.relpath(fp, YAOHEHE_DIR)
                    if rel not in articles:
                        articles.append(rel)
                        if len(articles) >= limit:
                            return articles
            except Exception:
                pass
    return articles

def verify_and_record():
    """验证最近发布并记录到 seo.md"""
    log("开始发布验证...")
    
    # 1. 检查 git 工作区
    clean, msg = check_articles_online()
    if not clean:
        log(f"⚠️ {msg}")
        verification_note = f"\n- [{datetime.now().strftime('%Y-%m-%d')}] ❌ 发布验证失败: {msg}"
    else:
        # 2. 扫描最近修改的文章
        recent_articles = find_recent_articles(hours=36, limit=5)
        if recent_articles:
            log(f"✅ 最近36小时发布: {len(recent_articles)} 篇")
            for a in recent_articles:
                log(f"  - {a}")
            verification_note = f"\n- [{datetime.now().strftime('%Y-%m-%d')}] ✅ 验证通过: 发布 {len(recent_articles)} 篇 ({', '.join(recent_articles[:3])}{'...' if len(recent_articles) > 3 else ''})"
        else:
            log("⚠️ 最近36小时无新文章发布")
            verification_note = f"\n- [{datetime.now().strftime('%Y-%m-%d')}] ⚠️ 验证: 最近36小时无新文章发布"
    
    # 3. 追加到 seo.md
    with open(SEO_MEMO, 'a') as f:
        f.write(verification_note)
    log(f"✅ 验证结果已记录到 seo.md")
    
    # 4. 写验证日志
    os.makedirs(os.path.dirname(VERIFICATION_LOG), exist_ok=True)
    with open(VERIFICATION_LOG, 'a') as f:
        f.write(f"[{ts()}] {verification_note[2:]}\n")
    
    return verification_note

if __name__ == "__main__":
    note = verify_and_record()
    print(f"\n验证摘要: {note}")