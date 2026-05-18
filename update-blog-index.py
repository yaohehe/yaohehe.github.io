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

# 统计代码
GOOGLE_ANALYTICS = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-JX42K3RMSC"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-JX42K3RMSC');
</script>'''
CLARITY = '''<!-- Microsoft Clarity -->
<script type="text/javascript">
 (function(c,l,a,r,i,t,y){
 c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
 t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
 y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
 })(window, document, "clarity", "script", "wdy3avd2j9");
</script>'''
BAIDU_STATS = '''<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
</script>'''

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
        .popular-section { margin-bottom: 40px; }
        .popular-section h2 { font-size: 1.5em; color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }
        .popular-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .popular-item { padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; transition: box-shadow 0.3s; }
        .popular-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .popular-item .popular-title { font-size: 1em; margin-bottom: 5px; }
        .popular-item .popular-title a { color: #3498db; text-decoration: none; font-weight: 600; }
        .popular-item .popular-title a:hover { text-decoration: underline; }
        .popular-meta { font-size: 0.85em; color: #888; margin-bottom: 8px; }
        .popular-tags { display: flex; gap: 5px; flex-wrap: wrap; }
        .popular-item .tag { background: #e8f4f8; color: #3498db; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
    </style>
<meta name="google-site-verification" content="aRTYFCdyaEkhMFAdwmfx53qD9csq3FcWdJvnRXx5QUQ" />
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-JX42K3RMSC"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-JX42K3RMSC');
    </script>
    <!-- Microsoft Clarity -->
    <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "wdy3avd2j9");
    </script>
    <!-- 百度统计 -->
    <script>
    var _hmt = _hmt || [];
    (function() {
      var hm = document.createElement("script");
      hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
    })();
    </script>
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

    <div class="popular-section">
        <h2>&#x1F525; 热门文章</h2>
        <div class="popular-grid">
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-29/2026-04-29-github-actions-troubleshooting-8-hour-pages-freeze.html">GitHub Actions疑难杂症：Pages冻结8小时复盘实录</a></div>
                <div class="popular-meta">发布于 2026年4月29日 · 52条内链</div>
                <div class="popular-tags"><span class="tag">GitHub Actions</span><span class="tag">DevOps</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-12/2026-04-12-complete-wordpress-website-setup-guide-2026-from-d.html">2026从零开始：WordPress建站完整指南（域名到上线）</a></div>
                <div class="popular-meta">发布于 2026年4月12日 · 45条内链</div>
                <div class="popular-tags"><span class="tag">WordPress</span><span class="tag">Web Dev</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-22/2026-04-22-amazon-basics-aa-batteries-which-pack-size-actuall.html">Amazon Basics AA电池哪款值得买：8款测试后说实话</a></div>
                <div class="popular-meta">发布于 2026年4月22日 · 30条内链</div>
                <div class="popular-tags"><span class="tag">Amazon Basics</span><span class="tag">Battery Review</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-26/2026-04-26-wordpress-https-ssl-setup-all-the-lets-encrypt-tra.html">WordPress + HTTPS + Let's Encrypt：所有踩过的坑</a></div>
                <div class="popular-meta">发布于 2026年4月26日 · 27条内链</div>
                <div class="popular-tags"><span class="tag">WordPress</span><span class="tag">Security</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-27/2026-04-27-amazon-basics-vs-gir-silicone-kitchen-utensils-in-depth-comparison.html">Amazon Basics vs GIR硅胶厨具：深度对比哪款值得买</a></div>
                <div class="popular-meta">发布于 2026年4月27日 · 26条内链</div>
                <div class="popular-tags"><span class="tag">Amazon Basics</span><span class="tag">Kitchen</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-25/2026-04-25-docker-gpu-configuration-traps-how-i-spent-3-days-.html">Docker GPU配置：我花了3天才打通NVIDIA容器支持</a></div>
                <div class="popular-meta">发布于 2026年4月25日 · 24条内链</div>
                <div class="popular-tags"><span class="tag">Docker</span><span class="tag">DevOps</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-12/2026-04-12-the-ultimate-guide-to-ai-powered-wordpress-site-bu.html">AI驱动的WordPress建站：2026完整指南（从入门到上线）</a></div>
                <div class="popular-meta">发布于 2026年4月12日 · 22条内链</div>
                <div class="popular-tags"><span class="tag">WordPress</span><span class="tag">AI</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-27/2026-04-27-amazon-basics-food-storage-containers-glass-vs-pla.html">Amazon Basics食品保鲜盒：玻璃款vs塑料款深度横评</a></div>
                <div class="popular-meta">发布于 2026年4月27日 · 20条内链</div>
                <div class="popular-tags"><span class="tag">Amazon Basics</span><span class="tag">Kitchen</span></div>
            </div>
        </div>
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
        .popular-section { margin-bottom: 40px; }
        .popular-section h2 { font-size: 1.5em; color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }
        .popular-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .popular-item { padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; transition: box-shadow 0.3s; }
        .popular-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .popular-item .popular-title { font-size: 1em; margin-bottom: 5px; }
        .popular-item .popular-title a { color: #3498db; text-decoration: none; font-weight: 600; }
        .popular-item .popular-title a:hover { text-decoration: underline; }
        .popular-meta { font-size: 0.85em; color: #888; margin-bottom: 8px; }
        .popular-tags { display: flex; gap: 5px; flex-wrap: wrap; }
        .popular-item .tag { background: #e8f4f8; color: #3498db; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
    </style>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-JX42K3RMSC"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-JX42K3RMSC');
    </script>
    <!-- Microsoft Clarity -->
    <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "wdy3avd2j9");
    </script>
    <!-- 百度统计 -->
    <script>
    var _hmt = _hmt || [];
    (function() {
      var hm = document.createElement("script");
      hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
    })();
    </script>
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

    <div class="popular-section">
        <h2>&#x1F525; Popular Articles</h2>
        <div class="popular-grid">
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-29/2026-04-29-github-actions-troubleshooting-8-hour-pages-freeze-en.html">GitHub Actions Troubleshooting: A Real 8-Hour Pages Freeze</a></div>
                <div class="popular-meta">Published Apr 29, 2026 · 52 internal links</div>
                <div class="popular-tags"><span class="tag">GitHub Actions</span><span class="tag">DevOps</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-12/2026-04-12-complete-wordpress-website-setup-guide-2026-from-d-en.html">Complete WordPress Website Setup Guide 2026: From Domain to Live Site</a></div>
                <div class="popular-meta">Published Apr 12, 2026 · 45 internal links</div>
                <div class="popular-tags"><span class="tag">WordPress</span><span class="tag">Web Dev</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-22/2026-04-22-amazon-basics-aa-batteries-which-pack-size-actuall-en.html">Amazon Basics AA Batteries: Which Pack Size Actually Gives You the Best Value?</a></div>
                <div class="popular-meta">Published Apr 22, 2026 · 30 internal links</div>
                <div class="popular-tags"><span class="tag">Amazon Basics</span><span class="tag">Battery Review</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-26/2026-04-26-wordpress-https-ssl-setup-all-the-lets-encrypt-tra-en.html">WordPress HTTPS & SSL Setup: All the Let's Encrypt Traps</a></div>
                <div class="popular-meta">Published Apr 26, 2026 · 27 internal links</div>
                <div class="popular-tags"><span class="tag">WordPress</span><span class="tag">Security</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-27/2026-04-27-amazon-basics-vs-gir-silicone-kitchen-utensils-in-depth-comparison-en.html">Amazon Basics vs GIR Silicone Kitchen Utensils: Which Is Worth It?</a></div>
                <div class="popular-meta">Published Apr 27, 2026 · 26 internal links</div>
                <div class="popular-tags"><span class="tag">Amazon Basics</span><span class="tag">Kitchen</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-25/2026-04-25-docker-gpu-configuration-traps-how-i-spent-3-days--en.html">Docker GPU Configuration: 3 Days Getting NVIDIA Containers to Work</a></div>
                <div class="popular-meta">Published Apr 25, 2026 · 24 internal links</div>
                <div class="popular-tags"><span class="tag">Docker</span><span class="tag">DevOps</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-12/2026-04-12-the-ultimate-guide-to-ai-powered-wordpress-site-bu-en.html">The Ultimate Guide to AI-Powered WordPress Site Building</a></div>
                <div class="popular-meta">Published Apr 12, 2026 · 22 internal links</div>
                <div class="popular-tags"><span class="tag">WordPress</span><span class="tag">AI</span></div>
            </div>
            <div class="popular-item">
                <div class="popular-title"><a href="archive/2026-04-27/2026-04-27-amazon-basics-food-storage-containers-glass-vs-pla-en.html">Amazon Basics Food Storage Containers: Glass vs Plastic</a></div>
                <div class="popular-meta">Published Apr 27, 2026 · 20 internal links</div>
                <div class="popular-tags"><span class="tag">Amazon Basics</span><span class="tag">Kitchen</span></div>
            </div>
        </div>
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
    """从文件名提取日期 YYYY-MM-DD（从路径或文件名中提取）"""
    # 使用 basename 去掉路径前缀（如 archive/2026-04-12/ 前缀）
    basename = os.path.basename(filename)
    m = re.match(r'^(\d{4}-\d{2}-\d{2})', basename)
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

    # 扫描所有 HTML 文件（去重：同一文件名优先使用 archive/ 版本）
    # 根因：同时扫描 root 和 archive/ 时，未追踪的根目录文件会生成错误链接
    # 解决：同一 basename 文件同时存在于 root 和 archive 时，优先使用 archive 版本（规范发布位置）
    # 防护：检测根目录孤立 HTML 文件（不在 git 追踪中）并报警，防止 publish-articles.py 复制残留
    import collections
    root_files = glob.glob(os.path.join(BLOG_DIR, '*.html'))
    archive_files = glob.glob(os.path.join(BLOG_DIR, 'archive', '**', '*.html'), recursive=True)

    # 检测根目录孤立文件（不在 git 追踪的 HTML，排除索引文件本身）
    import subprocess
    r = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '-I', '*.html',
                        '--ignore-case'], capture_output=True, text=True, cwd=BLOG_DIR)
    orphaned_html = [f.strip() for f in r.stdout.splitlines() if f.strip().endswith('.html')]
    if orphaned_html:
        print(f"⚠️ 检测到 {len(orphaned_html)} 个根目录孤立 HTML 文件（不在 git 追踪中），已从索引扫描中排除:")
        for f in orphaned_html[:5]:
            print(f"  排除: {f}")
        if len(orphaned_html) > 5:
            print(f"  ... 还有 {len(orphaned_html) - 5} 个")

    # basename -> filepath, archive 版本优先
    file_by_basename = {}
    for f in archive_files:
        bn = os.path.basename(f)
        if bn not in file_by_basename:
            file_by_basename[bn] = f
    for f in root_files:
        bn = os.path.basename(f)
        if bn in orphaned_html:
            continue  # 跳过孤立文件，不加入索引
        if bn not in file_by_basename:
            file_by_basename[bn] = f
    
    html_files = [f for bn, f in file_by_basename.items() if bn not in (
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
