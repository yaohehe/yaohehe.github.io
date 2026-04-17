#!/usr/bin/env python3
"""
每日SEO工作日志
扫描 yaohehe.github.io 统计近30小时内发布的文章，
追加到 ~/self-improving/domains/seo.md
"""
import os
import re
import glob
from datetime import datetime, timedelta

PUBLISH_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
MEMORY_FILE = os.path.expanduser("~/self-improving/domains/seo.md")

def get_articles():
    """获取所有文章"""
    articles = []
    for path in glob.glob(os.path.join(PUBLISH_DIR, "*.html")):
        fname = os.path.basename(path)
        if fname in ('index.html', 'index-en.html', 'sitemap.xml', 'robots.txt'):
            continue
        m = re.match(r'^(\d{4}-\d{2}-\d{2})', fname)
        if not m:
            continue
        date = m.group(1)
        # 读取标题
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            title_m = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
            title = title_m.group(1) if title_m else fname
        except:
            title = fname
        articles.append({'date': date, 'fname': fname, 'title': title})
    return articles

def main():
    cutoff = (datetime.now() - timedelta(hours=30)).strftime('%Y-%m-%d')
    articles = get_articles()
    recent = [a for a in articles if a['date'] >= cutoff]
    recent.sort(key=lambda x: x['date'], reverse=True)

    cn = [a for a in recent if not a['fname'].endswith('-en.html') and '-en.' not in a['fname']]
    en = [a for a in recent if a['fname'].endswith('-en.html') or '-en.' in a['fname']]

    if recent:
        lines = [f"📝 近30h发布：{len(recent)}篇（{len(cn)}CN+{len(en)}EN）"]
        for a in recent:
            lang = "🇨🇳" if a not in en else "🇺🇸"
            lines.append(f"  {a['date']} {lang} {a['title'][:50]}")
        log = '\n'.join(lines)
    else:
        log = "📝 近30h无新发布"

    print(log)

    # 追加到 seo.md
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} — 每日日志\n{log}\n"
    with open(MEMORY_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)
    print(f"✅ 已追加到 {MEMORY_FILE}")

if __name__ == '__main__':
    main()
