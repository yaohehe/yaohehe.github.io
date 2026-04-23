#!/usr/bin/env python3
"""
更新博客索引和 sitemap
扫描 yaohehe.github.io 中的所有文章 HTML，
生成更新后的 index.html、index-en.html 和 sitemap.xml
"""
import os
import re
import glob
from datetime import datetime

BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"

INDEX_HEADER_CN = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechPassive - 零成本被动收入实战</title>
    <meta name="description" content="分享真实可执行的被动收入方法，从零开始构建在线收入流">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; border-bottom: 2px solid #eee; margin-bottom: 40px; }
        h1 { font-size: 2.5em; color: #2c3e50; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 1.2em; }
        .lang-toggle { margin: 20px 0; }
        .lang-toggle a { color: #3498db; text-decoration: none; margin: 0 10px; }
        .lang-toggle a:hover { text-decoration: underline; }
        .post-list { list-style: none; }
        .post-item { margin-bottom: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; transition: box-shadow 0.3s; }
        .post-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .post-title { font-size: 1.4em; margin-bottom: 10px; }
        .post-title a { color: #3498db; text-decoration: none; }
        .post-title a:hover { text-decoration: underline; }
        .post-meta { color: #999; font-size: 0.9em; margin-bottom: 10px; }
        footer { text-align: center; padding: 40px 0; margin-top: 40px; border-top: 2px solid #eee; color: #666; }
        .affiliate-disclaimer { background: #fff8e1; padding: 15px; border-radius: 8px; margin-bottom: 30px; font-size: 0.9em; color: #666; }
    </style>
<meta name="google-site-verification" content="aRTYFCdyaEkhMFAdwmfx53qD9csq3FcWdJvnRXx5QUQ" />
</head>
<body>
    <header>
        <h1>TechPassive</h1>
        <p class="subtitle">零成本被动收入实战</p>
        <div class="lang-toggle">
            <a href="index.html">中文</a> | <a href="index-en.html">English</a>
        </div>
    </header>

    <div class="affiliate-disclaimer">
        ⚠️ 本文包含联盟链接。如果您通过这些链接购买，我可能会获得佣金，但不会增加您的费用。这有助于我们持续产出优质内容。
    </div>

    <ul class="post-list">
'''

INDEX_HEADER_EN = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechPassive - Passive Income That Works</title>
    <meta name="description" content="Practical guides on passive income, automation, and making money online with technology">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; border-bottom: 2px solid #eee; margin-bottom: 40px; }
        h1 { font-size: 2.5em; color: #2c3e50; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 1.2em; }
        .lang-toggle { margin: 20px 0; }
        .lang-toggle a { color: #3498db; text-decoration: none; margin: 0 10px; }
        .lang-toggle a:hover { text-decoration: underline; }
        .post-list { list-style: none; }
        .post-item { margin-bottom: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; transition: box-shadow 0.3s; }
        .post-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .post-title { font-size: 1.4em; margin-bottom: 10px; }
        .post-title a { color: #3498db; text-decoration: none; }
        .post-title a:hover { text-decoration: underline; }
        .post-meta { color: #999; font-size: 0.9em; margin-bottom: 10px; }
        footer { text-align: center; padding: 40px 0; margin-top: 40px; border-top: 2px solid #eee; color: #666; }
        .affiliate-disclaimer { background: #fff8e1; padding: 15px; border-radius: 8px; margin-bottom: 30px; font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <header>
        <h1>TechPassive</h1>
        <p class="subtitle">Passive Income That Works</p>
        <div class="lang-toggle">
            <a href="index.html">中文</a> | <a href="index-en.html">English</a>
        </div>
    </header>

    <div class="affiliate-disclaimer">
        ⚠️ This site contains affiliate links. If you purchase through them, I may earn a commission at no extra cost to you. This helps us keep producing quality content.
    </div>

    <ul class="post-list">
'''

INDEX_FOOTER = '''    </ul>
    <footer>
        <p>&copy; 2026 TechPassive. All rights reserved.</p>
    </footer>
</body>
</html>
'''


def get_date_from_filename(filename):
    """从文件名提取日期 YYYY-MM-DD"""
    m = re.match(r'^(\d{4}-\d{2}-\d{2})', filename)
    if m:
        return m.group(1)
    return None


def get_title_from_html(filepath):
    """从 HTML 文件中提取标题（h1 或 title）"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # 优先找 h1（处理嵌套标签情况）
        m = re.search(r'<h1[^>]*>(.*?)</h1>', content)
        if m:
            title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if title:
                return title
        # 其次找 title
        m = re.search(r'<title>([^<]+)</title>', content)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return os.path.splitext(os.path.basename(filepath))[0]


def generate_index(articles, header, footer):
    """生成索引 HTML"""
    items = []
    for date, filename, title in articles:
        items.append(
            f'        <li class="post-item">\n'
            f'            <h2 class="post-title"><a href="{filename}">{title}</a></h2>\n'
            f'            <p class="post-meta">发布于 {date}</p>\n'
            f'        </li>'
        )
    return header + '\n'.join(items) + '\n' + footer


def generate_sitemap(articles, today):
    """生成 sitemap XML"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             '  <url>',
             '    <loc>https://yaohehe.github.io/</loc>',
             f'    <lastmod>{today}</lastmod>',
             '    <changefreq>daily</changefreq>',
             '    <priority>1.0</priority>',
             '  </url>',
             '  <url>',
             '    <loc>https://yaohehe.github.io/index-en.html</loc>',
             f'    <lastmod>{today}</lastmod>',
             '    <changefreq>daily</changefreq>',
             '    <priority>1.0</priority>',
             '  </url>']
    for date, filename, title in articles:
        url = f'https://yaohehe.github.io/{filename}'
        lines.append('  <url>')
        lines.append(f'    <loc>{url}</loc>')
        lines.append(f'    <lastmod>{date}</lastmod>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>0.8</priority>')
        lines.append('  </url>')
    lines.append('</urlset>')
    return '\n'.join(lines) + '\n'


def main():
    today = datetime.now().strftime('%Y-%m-%d')

    # 扫描所有 HTML 文件
    html_files = glob.glob(os.path.join(BLOG_DIR, '*.html')) + glob.glob(os.path.join(BLOG_DIR, 'archive', '**', '*.html'), recursive=True)
    html_files = [f for f in html_files if os.path.basename(f) not in (
        'index.html', 'index-en.html', 'sitemap.xml'
    )]

    cn_articles = []
    en_articles = []

    for filepath in html_files:
        filename = filepath.replace(BLOG_DIR + '/', '')  # keep archive/ prefix
        date = get_date_from_filename(filename)
        if not date:
            continue
        title = get_title_from_html(filepath)
        if filename.endswith('-en.html') or '-en.' in filename:
            en_articles.append((date, filename, title))
        else:
            cn_articles.append((date, filename, title))

    # 按日期降序排序
    cn_articles.sort(key=lambda x: x[0], reverse=True)
    en_articles.sort(key=lambda x: x[0], reverse=True)
    all_articles = cn_articles + en_articles

    print(f"📊 扫描完成：{len(cn_articles)} 篇中文文章，{len(en_articles)} 篇英文文章")

    # 生成 index.html
    index_cn = generate_index(cn_articles, INDEX_HEADER_CN, INDEX_FOOTER)
    with open(os.path.join(BLOG_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_cn)
    print(f"✅ index.html 已更新（{len(cn_articles)} 篇）")

    # 生成 index-en.html
    index_en = generate_index(en_articles, INDEX_HEADER_EN, INDEX_FOOTER)
    with open(os.path.join(BLOG_DIR, 'index-en.html'), 'w', encoding='utf-8') as f:
        f.write(index_en)
    print(f"✅ index-en.html 已更新（{len(en_articles)} 篇）")

    # 生成 sitemap.xml
    sitemap = generate_sitemap(all_articles, today)
    with open(os.path.join(BLOG_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print(f"✅ sitemap.xml 已更新（{len(all_articles)} 篇）")

    print(f"📅 更新日期：{today}")


if __name__ == '__main__':
    main()
