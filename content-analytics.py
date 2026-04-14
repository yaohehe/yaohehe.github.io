#!/usr/bin/env python3
"""
每周内容分析脚本 - 替代 AI 分析
统计文章主题覆盖、中英文比例，给出下周建议
"""
import os
import glob
import re
from datetime import datetime

YAOHEHE_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
BLOG_DIR = "/root/.openclaw/workspace/affiliate-blog"
REPORTS_DIR = f"{BLOG_DIR}/reports"
LATEST_FILE = f"{REPORTS_DIR}/latest-analytics.txt"
os.makedirs(REPORTS_DIR, exist_ok=True)

def ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

THEMES = ["WordPress建站", "DevOps自动化", "联盟营销", "AI和OpenClaw自动化盈利", "云服务器/VPS/云计算"]

def detect_theme(title):
    combined = title.lower()
    detected = []
    for theme in THEMES:
        kw = theme.lower()
        short_kw = kw.split('/')[0].split('和')[0].split('(')[0].strip()
        if short_kw in combined or kw in combined:
            detected.append(theme)
    return detected

def count_articles(base_dir):
    """统计某目录下所有已发布的 HTML 文章"""
    cn = en = 0
    theme_counts = {t: 0 for t in THEMES}
    articles = []
    
    if not os.path.exists(base_dir):
        return cn, en, theme_counts, articles
    
    for fname in os.listdir(base_dir):
        if not fname.endswith('.html'):
            continue
        is_en = '-en.html' in fname or '-en-' in fname
        title = fname.replace('-', ' ').replace('.html', '')
        themes = detect_theme(title)
        
        for t in themes:
            theme_counts[t] += 1
        
        if is_en:
            en += 1
        else:
            cn += 1
        
        articles.append((fname, title, themes, is_en))
    
    return cn, en, theme_counts, articles

def main():
    print(f"[{ts()}] 📊 每周内容分析开始")
    
    # 统计已发布文章
    cn_published, en_published, theme_counts, all_articles = count_articles(YAOHEHE_DIR)
    
    # 统计草稿
    cn_drafts = en_drafts = 0
    drafts_dir = f"{BLOG_DIR}/drafts"
    if os.path.exists(drafts_dir):
        for f in os.listdir(drafts_dir):
            if f.endswith('.html'):
                if '-en-' in f or '-en.' in f:
                    en_drafts += 1
                else:
                    cn_drafts += 1
    
    total = cn_published + en_published
    covered = [t for t, c in theme_counts.items() if c > 0]
    not_covered = [t for t, c in theme_counts.items() if c == 0]
    
    print(f"  已发布: {total} 篇 (中文{cn_published} / 英文{en_published})")
    print(f"  草稿待发: {cn_drafts + en_drafts} 篇 (中文{cn_drafts} / 英文{en_drafts})")
    print(f"  主题覆盖: {' '.join([f'✅{t[:4]}' for t in covered])}")
    if not_covered:
        print(f"  未覆盖: {' '.join([f'❌{t[:4]}' for t in not_covered])}")
    
    # 生成报告
    today = datetime.now().strftime('%Y-%m-%d')
    report_file = f"{REPORTS_DIR}/weekly-analytics-{today}.txt"
    with open(report_file, 'w') as f:
        f.write(f"📊 每周内容分析报告 - {today}\n\n")
        f.write(f"已发布: {total} 篇 (中文{cn_published} / 英文{en_published})\n")
        f.write(f"草稿待发: {cn_drafts + en_drafts} 篇 (中文{cn_drafts} / 英文{en_drafts})\n\n")
        f.write("主题覆盖:\n")
        for t, c in theme_counts.items():
            status = "✅" if c > 0 else "❌"
            f.write(f"  {status} {t}: {c} 篇\n")
        if not_covered:
            f.write(f"\n建议: 优先补充未覆盖主题\n")
    
    # 写 latest 文件供 heartbeat 读取
    with open(LATEST_FILE, 'w') as f:
        f.write(f"📈 每周内容分析 - {today}\n")
        f.write(f"总{total}篇 | 中文{cn_published}/英文{en_published} | 草稿{cn_drafts+en_drafts}篇\n")
        f.write(f"覆盖: {', '.join(covered)}\n")
        if not_covered:
            f.write(f"未覆盖: {', '.join(not_covered)}\n")
    print(f"\n✅ 报告: {report_file}")
    
    # 输出摘要供 cron 汇报
    print(f"\n=== CRON_REPORT ===")
    print(f"总{total}篇 | 中文{cn_published}/英文{en_published} | 草稿{cn_drafts+en_drafts}篇")
    print(f"覆盖: {' '.join([t for t in covered])}")
    if not_covered:
        print(f"未覆盖: {' '.join(not_covered)}")

if __name__ == "__main__":
    main()
