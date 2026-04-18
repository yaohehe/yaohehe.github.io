#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechPassive 博客文章生成脚本
将纯文本内容转换为带 SEO 优化的 HTML 页面
"""
import os
import re
import sys
import glob

# ===== 配置 =====
TEMP_DIR = "/tmp/article-gen"
DRAFTS_DIR = "/root/.openclaw/workspace/affiliate-blog/drafts"
TEMPLATE_DIR = "/root/.openclaw/workspace/affiliate-blog"

BAIDU_STATS = '''<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
</script>'''

GOOGLE_ANALYTICS = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-YQZQY6XDXN"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-YQZQY6XDXN');
</script>'''

ADSENSE_IN_ARTICLE = '<ins class="adsbygoogle" style="display:block; text-align:center; margin:30px 0;" data-ad-client="ca-pub-3419621562136630" data-ad-slot="in-article" data-ad-format="auto"></ins>'
ADSENSE_PUSH = '<script>\n(adsbygoogle = window.adsbygoogle || []).push({});\n</script>'

# ===== 联盟链接配置 =====
# TODO: 将 YOUR_REF_CODE 替换为你实际的联盟 Ref ID
AFFILIATE_LINKS = {
    'DigitalOcean':    'https://m.do.co/c/ef5f58bd38d2',
    'Vultr':           'https://www.vultr.com/?ref=9890714',
    'Linode':          'https://www.linode.com/?r=YOUR_REF_CODE',
    'AWS':             'https://aws.amazon.com/?tag=techpassive-20',
    'Amazon':          'https://www.amazon.com/?tag=techpassive-20',
    'Cloudflare':       'https://www.cloudflare.com/?affiliate=YOUR_REF_CODE',
    'Namecheap':        'https://www.namecheap.com/?affiliate=YOUR_REF_CODE',
    'GitHub':           'https://github.com/?ref=YOUR_REF_CODE',
    'JetBrains':        'https://jb.gg/aaaaaa?ref=YOUR_REF_CODE',
    'WordPress':        'https://wordpress.org/?ref=YOUR_REF_CODE',
    'Kubernetes':       'https://kubernetes.io/?ref=YOUR_REF_CODE',
    'Docker':           'https://www.docker.com/?ref=YOUR_REF_CODE',
    'Terraform':        'https://www.terraform.io/?ref=YOUR_REF_CODE',
    'Ansible':          'https://www.ansible.com/?ref=YOUR_REF_CODE',
    'Jenkins':          'https://www.jenkins.io/?ref=YOUR_REF_CODE',
    'GitLab':           'https://gitlab.com/?ref=YOUR_REF_CODE',
    'Datadog':          'https://www.datadoghq.com/?ref=YOUR_REF_CODE',
    'Sentry':           'https://sentry.io/?ref=YOUR_REF_CODE',
    'WP Engine':        'https://wpengine.com/?ref=YOUR_REF_CODE',
    'SiteGround':       'https://www.siteground.com/?ref=YOUR_REF_CODE',
    'Bluehost':         'https://www.bluehost.com/?ref=YOUR_REF_CODE',
    'HostGator':        'https://www.hostgator.com/?ref=YOUR_REF_CODE',
    'Kadence':          'https://www.kadencewp.com/?ref=YOUR_REF_CODE',
    'Rank Math':        'https://rankmath.com/?ref=YOUR_REF_CODE',
    'Wordfence':        'https://www.wordfence.com/?ref=YOUR_REF_CODE',
    'ShortPixel':       'https://shortpixel.com/?ref=YOUR_REF_CODE',
    'Sucuri':           'https://sucuri.net/?ref=YOUR_REF_CODE',
    'Elementor':        'https://elementor.com/?ref=YOUR_REF_CODE',
    'Divi':             'https://www.elegantthemes.com/?ref=YOUR_REF_CODE',
    'GeneratePress':    'https://generatepress.com/?ref=YOUR_REF_CODE',
    'Astra':            'https://wpastra.com/?ref=YOUR_REF_CODE',
    'Udemy':            'https://www.udemy.com/?ref=YOUR_REF_CODE',
    'Coursera':         'https://www.coursera.org/?ref=YOUR_REF_CODE',
    'Notion':           'https://www.notion.so/?ref=YOUR_REF_CODE',
    'Zapier':           'https://zapier.com/?ref=YOUR_REF_CODE',
    'Make':             'https://www.make.com/?ref=YOUR_REF_CODE',
    'n8n':              'https://n8n.io/?ref=YOUR_REF_CODE',
    'Pabbly':           'https://www.pabbly.com/?ref=YOUR_REF_CODE',
    'UpdraftPlus':      'https://updraftplus.com/?ref=YOUR_REF_CODE',
    'WPForms':          'https://wpforms.com/?ref=YOUR_REF_CODE',
    'Gravity Forms':     'https://www.gravityforms.com/?ref=YOUR_REF_CODE',
    'Semrush':          'https://www.semrush.com/?ref=YOUR_REF_CODE',
    'Fathom':           'https://usefathom.com/?ref=YOUR_REF_CODE',
    'Plausible':        'https://plausible.io/?ref=YOUR_REF_CODE',
    'Ghost':            'https://ghost.org/?ref=YOUR_REF_CODE',
    'Netlify':          'https://www.netlify.com/?ref=YOUR_REF_CODE',
    'Vercel':           'https://vercel.com/?ref=YOUR_REF_CODE',
    'Supabase':         'https://supabase.com/?ref=YOUR_REF_CODE',
    'Railway':          'https://railway.app/?ref=YOUR_REF_CODE',
    'Render':           'https://render.com/?ref=YOUR_REF_CODE',
    'Fly.io':           'https://fly.io/?ref=YOUR_REF_CODE',
    '1Password':        'https://1password.com/?ref=YOUR_REF_CODE',
    'LastPass':         'https://www.lastpass.com/?ref=YOUR_REF_CODE',
    'ExpressVPN':       'https://www.expressvpn.com/?ref=YOUR_REF_CODE',
    'NordVPN':          'https://nordvpn.com/?ref=YOUR_REF_CODE',
    'YouTube':          'https://www.youtube.com/?ref=YOUR_REF_CODE',
    'MongoDB':          'https://www.mongodb.com/?ref=YOUR_REF_CODE',
    'PostgreSQL':       'https://www.postgresql.org/?ref=YOUR_REF_CODE',
    'Redis':            'https://redis.io/?ref=YOUR_REF_CODE',
    '阿里云':           'https://www.aliyun.com/?ref=YOUR_REF_CODE',
    '腾讯云':           'https://cloud.tencent.com/?ref=YOUR_REF_CODE',
    '蓝队':             'https://www.bluehost.com/?ref=YOUR_REF_CODE',
}


CSS_CN = '''body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; color: #333; }
h1 { color: #1a1a1a; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
.tag { background: #0066cc; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-right: 5px; }
.post-tags { margin: 15px 0; }
.content { margin: 20px 0; }
.content p { margin: 15px 0; text-align: justify; }
.content h2 { color: #0066cc; margin-top: 30px; }
.content h3 { color: #0055aa; margin-top: 25px; }
.content ul, .content ol { margin: 15px 0; padding-left: 25px; }
.content li { margin: 8px 0; }
.content a { color: #0066cc; text-decoration: none; }
.content a:hover { text-decoration: underline; }
.content code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: "SF Mono", "Fira Code", Consolas, monospace; font-size: 0.9em; color: #c7254e; border: 1px solid #e0e0e0; }
.content pre { background: #1e1e1e; color: #d4d4d4; padding: 16px 20px; border-radius: 8px; overflow-x: auto; margin: 20px 0; border: 1px solid #333; font-family: "SF Mono", "Fira Code", Consolas, monospace; font-size: 0.88em; line-height: 1.6; }
.content pre code { background: none; border: none; color: inherit; padding: 0; font-size: inherit; border-radius: 0; }
.content blockquote { border-left: 4px solid #0066cc; margin: 15px 0; padding: 10px 15px; background: #f9f9f9; }
.back-btn { display: inline-block; margin: 30px 0; padding: 10px 24px; background: #0066cc; color: white; text-decoration: none; border-radius: 6px; font-size: 0.95em; transition: background 0.2s; }
.back-btn:hover { background: #0055aa; text-decoration: none; color: white; }

/* 响应式设计 - 移动端适配 */
@media (max-width: 600px) {
  body { padding: 12px; }
  h1 { font-size: 1.6em; }
  .content h2 { font-size: 1.3em; }
  .content h3 { font-size: 1.1em; }
  .content p { margin: 12px 0; text-align: left; }
  .content pre { padding: 12px; margin: 15px 0; }
  .content ul, .content ol { padding-left: 20px; }
  .tag { font-size: 0.75em; padding: 2px 6px; }
  .back-btn { padding: 8px 16px; font-size: 0.85em; }
}

@media (max-width: 400px) {
  body { padding: 10px; font-size: 14px; }
  .content pre { font-size: 0.8em; padding: 10px; }
}
'''

CSS_EN = CSS_CN

HTML_TEMPLATE_CN = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - TechPassive</title>
  <meta name="description" content="{description}">
  {GOOGLE_ANALYTICS}
  <style>
{css}
  </style>
</head>
<body>
  <a href="/" class="back-btn">← 返回首页</a>
  <h1>{h1}</h1>
  <div class="post-tags">
    {tags_html}
  </div>
  <div class="content">
    {html_body}
  </div>
  <a href="/" class="back-btn">← 返回首页</a>
  {BAIDU_STATS}
  <div style="margin:30px 0; text-align:center;">
    {ADSENSE_IN_ARTICLE}
  </div>
  {ADSENSE_PUSH}
</body>
</html>'''

HTML_TEMPLATE_EN = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - TechPassive</title>
  <meta name="description" content="{description}">
  {GOOGLE_ANALYTICS}
  <style>
{css}
  </style>
</head>
<body>
  <a href="/" class="back-btn">← Back to Home</a>
  <h1>{h1}</h1>
  <div class="post-tags">
    {tags_html}
  </div>
  <div class="content">
    {html_body}
  </div>
  <a href="/" class="back-btn">← Back to Home</a>
  {BAIDU_STATS}
  <div style="margin:30px 0; text-align:center;">
    {ADSENSE_IN_ARTICLE}
  </div>
  {ADSENSE_PUSH}
</body>
</html>'''


def parse_metadata(content_lines):
    """解析元数据行：标题|描述|一级标题|标签1,标签2,标签3"""
    first_line = content_lines[0].strip()
    parts = first_line.split('|')
    if len(parts) < 4:
        print(f"❌ 元数据格式错误: {first_line}")
        sys.exit(1)
    import re
    from datetime import datetime
    title = parts[0].strip()
    current_year = datetime.now().strftime('%Y')
    # 中文年份：如 "2024年新手必看" → "2026年新手必看"
    title = re.sub(r'\b(20\d{2})年\b', f'{current_year}年', title)
    # 英文年份：如 "(2024)"、"2024 Beginners"、"2024 Edition" → "(2026)"、"2026 Beginners"、"2026 Edition"
    title = re.sub(r'\b(20\d{2})\b(?!\d)', current_year, title)  # 避免重复替换已替换过的
    title = re.sub(r'\((20\d{2})\)', f'({current_year})', title)  # 处理括号内年份如 "(2024)"
    title = re.sub(r'\b(20\d{2})( Beginners| Edition| Guide| Tutorial)?\b', f'{current_year}\2', title)  # 处理 "2024 Beginners" 等
    return {
        'title': title,
        'description': parts[1].strip(),
        'h1': parts[2].strip(),
        'tags': [t.strip() for t in parts[3].split(',') if t.strip()]
    }


def text_to_html(text):
    """将 Markdown 纯文本转换为 HTML"""
    lines = text.split('\n')
    html_parts = []
    in_list = False
    list_items = []

    for line in lines:
        line = line.rstrip()
        # 跳过元数据行（第一行）
        if line == lines[0] and '|' in line:
            continue
        # 跳过空行（在元数据后立即出现的）
        if not line.strip() and len(html_parts) == 0:
            continue

        # Markdown 表格
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            # 跳过分隔行（如 |---|---|
            if all(re.match(r'^[-:]+$', c.replace(' ', '')) for c in cells if c):
                continue
            # 判断是否是表头（第一行）或数据行
            if not hasattr(text_to_html, '_table_header'):
                text_to_html._table_header = cells
                text_to_html._table_rows = []
                continue
            else:
                text_to_html._table_rows.append(cells)
                continue
        else:
            # 输出累积的表格
            if hasattr(text_to_html, '_table_header'):
                headers = text_to_html._table_header
                rows = text_to_html._table_rows
                del text_to_html._table_header
                del text_to_html._table_rows
                # 构建 HTML table
                th_html = ''.join([f'<th style="border:1px solid #ddd;padding:8px;background:#0066cc;color:white;">{h}</th>' for h in headers])
                tbody_html = ''
                for i, row in enumerate(rows):
                    bg = '#f9f9f9' if i % 2 == 0 else 'white'
                    td_html = ''.join([f'<td style="border:1px solid #ddd;padding:8px;">{c}</td>' for c in row])
                    tbody_html += f'<tr style="background:{bg}">{td_html}</tr>'
                table_html = f'<table style="border-collapse:collapse;width:100%;margin:20px 0;font-size:0.95em;"><thead><tr>{th_html}</tr></thead><tbody>{tbody_html}</tbody></table>'
                html_parts.append(table_html)

        # 列表项
        if line.startswith('- '):
            list_items.append(line[2:])
            in_list = True
            continue
        else:
            if in_list:
                html_parts.append('<ul>' + ''.join([f'<li>{item}</li>' for item in list_items]) + '</ul>')
                list_items = []
                in_list = False

        # 多行代码块（``` ``` ```）
        if line.strip().startswith('```'):
            if not hasattr(text_to_html, '_in_code_block'):
                text_to_html._in_code_block = True
                text_to_html._code_block_lines = []
                # 提取语言标识（如 ```python）
                lang = line.strip()[3:].strip()
                text_to_html._code_lang = lang
            else:
                # 结束代码块
                text_to_html._in_code_block = False
                code_content = '\n'.join(text_to_html._code_block_lines)
                code_html = f'<pre><code>{code_content}</code></pre>'
                html_parts.append(code_html)
                del text_to_html._code_block_lines
                del text_to_html._code_lang
                del text_to_html._in_code_block
            continue
        elif hasattr(text_to_html, '_in_code_block') and text_to_html._in_code_block:
            text_to_html._code_block_lines.append(line)
            continue

        # Markdown 链接 [text](url) - 必须在其他模式之前处理
        if '](' in line:
            # 匹配 [text](url) 格式，转换为 <a href="url">text</a>
            def convert_markdown_link(m):
                text = m.group(1)
                url = m.group(2)
                # 确保 url 以 http/https 开头
                if not url.startswith('http'):
                    url = 'https://' + url
                # 清理 url 中的特殊字符
                url = url.strip().replace(' ', '+')
                return f'<a href="{url}" target="_blank" rel="nofollow sponsored">{text}</a>'
            
            line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', convert_markdown_link, line)
            html_parts.append(f'<p>{line}</p>')
        # 标题
        elif line.startswith('### '):
            html_parts.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            html_parts.append(f'<h2>{line[3:]}</h2>')
        # 行内代码（优先于粗体处理，避免 ` 被 ** 误消耗）
        elif '`' in line:
            line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
            html_parts.append(f'<p>{line}</p>')
        # 粗体：允许空内容（匹配 ** 和 ** 之间的任何内容，包括空）
        elif '**' in line:
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            html_parts.append(f'<p>{line}</p>')
        # 斜体
        elif '*' in line:
            line = re.sub(r'\*(.+?)\*', '<em>\1</em>', line)
            html_parts.append(f'<p>{line}</p>')
        # 引用
        elif line.startswith('> '):
            html_parts.append(f'<blockquote>{line[2:]}</blockquote>')
        # 普通段落
        elif line.strip():
            html_parts.append(f'<p>{line}</p>')
        # 空行
        elif not line.strip():
            pass  # 忽略空行

    # 处理末尾未闭合的代码块
    if hasattr(text_to_html, '_in_code_block') and text_to_html._in_code_block:
        code_content = '\n'.join(text_to_html._code_block_lines)
        html_parts.append(f'<pre><code>{code_content}</code></pre>')
        del text_to_html._code_block_lines
        del text_to_html._in_code_block

    # 处理末尾列表
    if hasattr(text_to_html, '_table_header'):
        headers = text_to_html._table_header
        rows = text_to_html._table_rows
        del text_to_html._table_header
        del text_to_html._table_rows
        th_html = ''.join([f'<th style="border:1px solid #ddd;padding:8px;background:#0066cc;color:white;">{h}</th>' for h in headers])
        tbody_html = ''
        for i, row in enumerate(rows):
            bg = '#f9f9f9' if i % 2 == 0 else 'white'
            td_html = ''.join([f'<td style="border:1px solid #ddd;padding:8px;">{c}</td>' for c in row])
            tbody_html += f'<tr style="background:{bg}">{td_html}</tr>'
        table_html = f'<table style="border-collapse:collapse;width:100%;margin:20px 0;font-size:0.95em;"><thead><tr>{th_html}</tr></thead><tbody>{tbody_html}</tbody></table>'
        html_parts.append(table_html)

    result = '\n'.join(html_parts)
    
    # 清理空标签（AI 生成时常产生 <strong></strong> 这种空标签）
    result = re.sub(r'<strong>\s*</strong>', '', result)
    result = re.sub(r'<em>\s*</em>', '', result)
    result = re.sub(r'<code>\s*</code>', '', result)
    result = re.sub(r'<b>\s*</b>', '', result)
    # 清理空段落（清理空标签后可能遗留空 <p></p>）
    result = re.sub(r'<p>\s*</p>', '', result)
    
    return result


def insert_affiliate_links(html_body, is_en):
    """在 HTML 正文中插入联盟链接（仅匹配与工具/品牌相关的关键词）"""
    # 关键词白名单：只匹配明确的工具/品牌名，不会与普通英文单词混淆
    # 格式: (关键词, URL)
    BRAND_KEYWORDS = [
        ('DigitalOcean', AFFILIATE_LINKS['DigitalOcean']),
        ('Vultr', AFFILIATE_LINKS['Vultr']),
        ('AWS', AFFILIATE_LINKS['AWS']),
        # ('Amazon', AFFILIATE_LINKS['Amazon']),  # 移除：Amazon链接已在Markdown链接中指定，避免URL被二次转换
        ('Cloudflare', AFFILIATE_LINKS['Cloudflare']),
        ('Namecheap', AFFILIATE_LINKS['Namecheap']),
        ('GitHub', AFFILIATE_LINKS['GitHub']),
        ('JetBrains', AFFILIATE_LINKS['JetBrains']),
        ('Linode', AFFILIATE_LINKS['Linode']),
        ('WordPress', AFFILIATE_LINKS['WordPress']),
        ('Kubernetes', AFFILIATE_LINKS['Kubernetes']),
        ('Docker', AFFILIATE_LINKS['Docker']),
        ('Terraform', AFFILIATE_LINKS['Terraform']),
        ('Ansible', AFFILIATE_LINKS['Ansible']),
        ('Jenkins', AFFILIATE_LINKS['Jenkins']),
        ('GitLab', AFFILIATE_LINKS['GitLab']),
        ('Datadog', AFFILIATE_LINKS['Datadog']),
        ('Sentry', AFFILIATE_LINKS['Sentry']),
        ('Notion', AFFILIATE_LINKS['Notion']),
        ('Zapier', AFFILIATE_LINKS['Zapier']),
        ('n8n', AFFILIATE_LINKS['n8n']),
        ('Pabbly', AFFILIATE_LINKS['Pabbly']),
        ('Netlify', AFFILIATE_LINKS['Netlify']),
        ('Vercel', AFFILIATE_LINKS['Vercel']),
        ('Supabase', AFFILIATE_LINKS['Supabase']),
        ('WP Engine', AFFILIATE_LINKS['WP Engine']),
        ('SiteGround', AFFILIATE_LINKS['SiteGround']),
        ('Bluehost', AFFILIATE_LINKS['Bluehost']),
        ('HostGator', AFFILIATE_LINKS['HostGator']),
        ('Kadence', AFFILIATE_LINKS['Kadence']),
        ('Rank Math', AFFILIATE_LINKS['Rank Math']),
        ('Wordfence', AFFILIATE_LINKS['Wordfence']),
        ('ShortPixel', AFFILIATE_LINKS['ShortPixel']),
        ('Sucuri', AFFILIATE_LINKS['Sucuri']),
        ('Elementor', AFFILIATE_LINKS['Elementor']),
        ('Divi', AFFILIATE_LINKS['Divi']),
        ('GeneratePress', AFFILIATE_LINKS['GeneratePress']),
        ('Astra', AFFILIATE_LINKS['Astra']),
        ('Udemy', AFFILIATE_LINKS['Udemy']),
        ('Coursera', AFFILIATE_LINKS['Coursera']),
        ('1Password', AFFILIATE_LINKS['1Password']),
        ('LastPass', AFFILIATE_LINKS['LastPass']),
        ('ExpressVPN', AFFILIATE_LINKS['ExpressVPN']),
        ('NordVPN', AFFILIATE_LINKS['NordVPN']),
        ('YouTube', AFFILIATE_LINKS['YouTube']),
    ]
    
    for keyword, url in BRAND_KEYWORDS:
        # 用 split/join 策略：先按 <a ...>...</a> 分割，对非链接部分做替换
        parts = re.split(r'(<a\s[^>]*?>.*?</a>)', html_body, flags=re.DOTALL)
        new_parts = []
        for part in parts:
            if re.match(r'<a\s', part, re.IGNORECASE):
                new_parts.append(part)  # 不修改已有链接
            else:
                # 区分大小写匹配关键词，加上链接
                pattern = re.compile(r'\b(' + re.escape(keyword) + r')\b')
                part = pattern.sub(
                    lambda m: f'<a href="{url}" target="_blank" rel="nofollow sponsored">{m.group(1)}</a>',
                    part
                )
                new_parts.append(part)
        html_body = ''.join(new_parts)
    return html_body


AFFILIATE_BOX_CN = '''
<div style="background:#fff8e1;border-left:4px solid #f39c12;padding:20px;margin:30px 0;border-radius:8px;">
  <h3 style="margin:0 0 10px;color:#b7791f;">🔗 推荐阅读</h3>
  <p style="margin:0 0 15px;color:#666;">以下是我们精心挑选的优质工具，使用推荐链接支持我们持续产出高质量内容：</p>
  <div style="display:flex;flex-wrap:wrap;gap:10px;">
    <a href="{digitalocean_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#0058ff;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">DigitalOcean 云服务器</a>
    <a href="{vultr_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#0058ff;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">Vultr 高性能 VPS</a>
    <a href="{cloudflare_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#f38020;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">Cloudflare CDN</a>
    <a href="{namecheap_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#de6800;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">Namecheap 域名</a>
  </div>
</div>
'''

AFFILIATE_BOX_EN = '''
<div style="background:#fff8e1;border-left:4px solid #f39c12;padding:20px;margin:30px 0;border-radius:8px;">
  <h3 style="margin:0 0 10px;color:#b7791f;">🔗 Recommended Tools</h3>
  <p style="margin:0 0 15px;color:#666;">These are carefully selected tools. Using our affiliate links supports us to keep producing quality content:</p>
  <div style="display:flex;flex-wrap:wrap;gap:10px;">
    <a href="{digitalocean_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#0058ff;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">DigitalOcean Cloud</a>
    <a href="{vultr_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#0058ff;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">Vultr VPS</a>
    <a href="{cloudflare_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#f38020;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">Cloudflare CDN</a>
    <a href="{namecheap_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#de6800;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">Namecheap Domains</a>
  </div>
</div>
'''


def generate_html(content, template, css):
    """填充 HTML 模板"""
    lines = content.strip().split('\n')
    meta = parse_metadata(lines)
    body_lines = lines[2:]  # 跳过元数据和空行
    html_body = text_to_html('\n'.join(body_lines))

    is_en = 'en' in css.lower() or 'lang="en"' in template
    html_body = insert_affiliate_links(html_body, is_en)

    # 追加联盟推荐箱
    box = AFFILIATE_BOX_EN if is_en else AFFILIATE_BOX_CN
    box_html = box.format(
        digitalocean_url=AFFILIATE_LINKS['DigitalOcean'],
        vultr_url=AFFILIATE_LINKS['Vultr'],
        cloudflare_url=AFFILIATE_LINKS['Cloudflare'],
        namecheap_url=AFFILIATE_LINKS['Namecheap'],
    )
    html_body = html_body + box_html

    tags_html = ''.join([f'<span class="tag">{tag}</span>' for tag in meta['tags']])

    return template.format(
        title=meta['title'],
        description=meta['description'],
        h1=meta['h1'],
        tags_html=tags_html,
        html_body=html_body,
        css=css,
        BAIDU_STATS=BAIDU_STATS,
        GOOGLE_ANALYTICS=GOOGLE_ANALYTICS,
        ADSENSE_IN_ARTICLE=ADSENSE_IN_ARTICLE,
        ADSENSE_PUSH=ADSENSE_PUSH
    )


def make_filename(content, is_en):
    """生成文件名：YYYY-MM-DD-主题-slug[-en].html"""
    lines = content.strip().split('\n')
    meta = parse_metadata(lines)
    title = meta['title']

    # 从标题提取 slug
    slug = title.lower()
    slug = re.sub(r'[^\w\u4e00-\u9fa5\s-]', '', slug)  # 保留中文、英文、数字、空格、连字符
    slug = re.sub(r'[\s]+', '-', slug)  # 空格变连字符
    slug = slug[:50]  # 限制长度

    # 从文件名路径提取日期（如果存在）
    date_str = None
    filepath = None

    # 尝试从输入内容中提取日期（内容文件的路径可能包含日期）
    txt_files = glob.glob(f"{TEMP_DIR}/*.txt")
    for txt_file in txt_files:
        basename = os.path.basename(txt_file)
        match = re.search(r'(\d{4}-\d{2}-\d{2})', basename)
        if match:
            date_str = match.group(1)
            break

    if not date_str:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')

    suffix = '-en' if is_en else ''
    return f"{date_str}-{slug}{suffix}.html"


def process_txt_file(txt_file, is_en):
    """处理单个文本文件"""
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    template = HTML_TEMPLATE_EN if is_en else HTML_TEMPLATE_CN
    css = CSS_EN if is_en else CSS_CN

    html = generate_html(content, template, css)
    filename = make_filename(content, is_en)

    os.makedirs(DRAFTS_DIR, exist_ok=True)
    filepath = os.path.join(DRAFTS_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    size = os.path.getsize(filepath)
    print(f"✅ [{'en' if is_en else 'cn'}] {filename} ({size} bytes)")
    return filename


def main():
    # 读取 /tmp/article-gen/ 下的所有 .txt 文件
    txt_files = sorted(glob.glob(f"{TEMP_DIR}/*.txt"))
    if not txt_files:
        print("❌ 未找到文章内容文件，请先运行 AI 生成阶段")
        sys.exit(1)

    for txt_file in txt_files:
        basename = os.path.basename(txt_file)
        is_en = basename.startswith('en')
        try:
            process_txt_file(txt_file, is_en)
        except Exception as e:
            print(f"❌ 处理失败 {basename}: {e}")
            sys.exit(1)

    # 验证输出
    html_files = glob.glob(f"{DRAFTS_DIR}/*.html")
    print(f"\n📝 共生成 {len(html_files)} 篇草稿")
    print("SUCCESS")


if __name__ == '__main__':
    main()
