#!/usr/bin/env python3
"""
博客监控脚本
检查网站可用性 + 文章统计，结果写入报告文件供 heartbeat 读取
"""
import requests
import os
from datetime import datetime

BLOG_URL = "https://yaohehe.github.io"
BLOG_DIR = "/root/.openclaw/workspace/affiliate-blog"
REPORT_FILE = "/root/.openclaw/workspace/affiliate-blog/reports/latest-monitor.txt"
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

THEMES = ["WordPress建站", "DevOps自动化", "联盟营销", "AI和OpenClaw自动化盈利", "云服务器/VPS/云计算"]

def ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def detect_theme(title):
    combined = title.lower()
    for theme in THEMES:
        kw = theme.lower()
        short_kw = kw.split('/')[0].split('和')[0].strip()
        if short_kw in combined or kw in combined:
            return theme
    return None

def main():
    print(f"[{ts()}] 🌐 博客监控开始")
    results = []

    # 1. 检查网站状态
    try:
        r = requests.get(BLOG_URL, timeout=10)
        status = "✅ 正常" if r.status_code == 200 else f"⚠️ HTTP {r.status_code}"
        results.append(f"网站状态: {status}")
    except Exception as e:
        results.append(f"网站状态: ❌ {e}")

    # 2. 文章统计
    cn_total = en_total = 0
    theme_counts = {t: 0 for t in THEMES}

    if os.path.exists(BLOG_DIR):
        for fname in os.listdir(BLOG_DIR):
            if not fname.endswith('.html'):
                continue
            is_en = '-en.html' in fname
            title = fname.replace('-', ' ').replace('.html', '')
            theme = detect_theme(title)
            if theme:
                theme_counts[theme] += 1
            if is_en:
                en_total += 1
            else:
                cn_total += 1

    results.append(f"文章统计: 中文{cn_total}篇 / 英文{en_total}篇")

    # 3. 主题覆盖
    covered = [t for t, c in theme_counts.items() if c > 0]
    not_covered = [t for t, c in theme_counts.items() if c == 0]
    results.append(f"主题覆盖: {' '.join([f'✅{t[:4]}' for t in covered])}")
    if not_covered:
        results.append(f"未覆盖: {' '.join([f'❌{t[:4]}' for t in not_covered])}")

    # 写入报告文件
    with open(REPORT_FILE, 'w') as f:
        f.write(f"🖥️ 博客监控 - {ts()}\n")
        for r in results:
            f.write(f"{r}\n")

    for r in results:
        print(f"  {r}")
    print(f"[{ts()}] ✅ 完成")

if __name__ == "__main__":
    main()
