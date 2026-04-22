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

CLARITY = '''<!-- Microsoft Clarity -->
<script type="text/javascript">
 (function(c,l,a,r,i,t,y){
 c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
 t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
 y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
 })(window, document, "clarity", "script", "wdy3avd2j9");
</script>'''

ADSENSE_IN_ARTICLE = '<ins class="adsbygoogle" style="display:block; text-align:center; margin:30px 0;" data-ad-client="ca-pub-3419621562136630" data-ad-slot="in-article" data-ad-format="auto"></ins>'
ADSENSE_PUSH = '<script>\n(adsbygoogle = window.adsbygoogle || []).push({});\n</script>'

# ===== 联盟链接配置 =====
# TODO: 将 YOUR_REF_CODE 替换为你实际的联盟 Ref ID
AFFILIATE_LINKS = {
    'DigitalOcean':    'https://m.do.co/c/ef5f58bd38d2',
    'Vultr':           'https://www.vultr.com/?ref=9890714',
    'AWS':             'https://aws.amazon.com/?tag=techpassive-20',
    'Amazon':          'https://www.amazon.com/?tag=techpassive-20',
    'MiniMax':         'https://platform.minimaxi.com/subscribe/token-plan?code=E5yur9NOub&source=link',
    
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


CSS_CN = '''.skip-link { position: absolute; top: -40px; left: 0; background: #0066cc; color: white; padding: 8px 16px; z-index: 100; text-decoration: none; }
.skip-link:focus { top: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.8; color: #333; }
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
.content table { overflow-x: auto; display: block; }
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
  .content table { display: block; overflow-x: auto; white-space: nowrap; }
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
  {CLARITY}
  <style>
{css}
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">跳到主要内容</a>
  <a href="/" class="back-btn">← 返回首页</a>
  <main id="main-content">
  <h1>{h1}</h1>
  <div class="post-tags">
    {tags_html}
  </div>
  <div class="content">
    {html_body}
  </div>
  <a href="/" class="back-btn">← 返回首页</a>
  </main>
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
  {CLARITY}
  <style>
{css}
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <a href="/" class="back-btn">← Back to Home</a>
  <main id="main-content">
  <h1>{h1}</h1>
  <div class="post-tags">
    {tags_html}
  </div>
  <div class="content">
    {html_body}
  </div>
  <a href="/" class="back-btn">← Back to Home</a>
  </main>
  {BAIDU_STATS}
  <div style="margin:30px 0; text-align:center;">
    {ADSENSE_IN_ARTICLE}
  </div>
  {ADSENSE_PUSH}
</body>
</html>'''


def _clean_metadata_title(title):
    """清理元数据标题字段中的污染前缀和格式标记"""
    original = title
    # 移除常见的前缀标记（注意：要保留正常标题中的"标题"二字）
    # "标题：xxx" 或 "标题: xxx" 或 "标题 xxx" → "xxx"
    title = re.sub(r'^[\s　]*标题[：:][\s　]*(.+)$', r'\1', title)
    # "title: xxx" 或 "title xxx" (行首) → "xxx"
    title = re.sub(r'^[\s　]*title[\s:]+(.+)$', r'\1', title, flags=re.IGNORECASE)
    # "一级标题：xxx" → "xxx"
    title = re.sub(r'^[\s　]*一级标题[：:][\s　]*(.+)$', r'\1', title)
    # "# xxx" (行首) → "xxx"  （AI 把 Markdown 标题语法混入了元数据行）
    title = re.sub(r'^[\s　]*#+[\s]*(.+)$', r'\1', title)
    title = title.strip()
    if title != original:
        print(f"  🧹 清理标题前缀: '{original[:40]}...' → '{title[:40]}...'")
    return title


def parse_metadata(content_lines):
    """解析元数据行：标题|描述|一级标题|标签1,标签2,标签3"""
    first_line = content_lines[0].strip()
    parts = first_line.split('|')
    if len(parts) < 4:
        print(f"❌ 元数据格式错误 (字段不足4个): {first_line[:80]}")
        sys.exit(1)

    # ---- 修复1: parts[0] 格式校验 + 清理 ----
    title = parts[0].strip()
    # 检测 parts[0] 是否被污染（元数据行格式错误：AI 把标题放到了 parts[0] 但带标记）
    parts0_dirty = (
        re.match(r'^[\s　]*标题[：:]', title) or
        re.match(r'^[\s　]*title[\s:]', title, re.IGNORECASE) or
        re.match(r'^[\s　]*一级标题[：:]', title) or
        re.match(r'^[\s　]*#', title)
    )
    if parts0_dirty:
        print(f"⚠️ 检测到 parts[0] 被污染: '{title[:60]}...'，尝试清理...")
        title = _clean_metadata_title(title)

    # ---- 修复2: parts[1] 描述字段校验 ----
    raw_desc = parts[1].strip()
    if raw_desc.startswith('标题') or raw_desc.startswith('title') or raw_desc.startswith('#'):
        print(f"⚠️ 检测到 parts[1] 异常（描述字段被标题污染）: '{raw_desc[:40]}...'")
    # Strip HTML tags from description (AI may include <a class="internal-link"> tags)
    description = re.sub(r'<[^>]+>', '', raw_desc)

    # ---- 修复3: h1 占位符检测（精确匹配避免误判） ----
    h1_raw = parts[2].strip()
    # 使用精确前缀匹配而非 contains，避免"如何设置标题"被误判
    h1_is_placeholder = (
        h1_raw in ('标题', '一级标题', 'title', 'headline', 'heading') or
        h1_raw.startswith('标题') and len(h1_raw) < 10 or
        h1_raw.startswith('title') and len(h1_raw) < 15
    )
    if h1_is_placeholder:
        print(f"⚠️ 检测到占位符 h1='{h1_raw}'，从正文中提取...")
        for line in content_lines[1:50]:
            line = line.strip()
            if line.startswith('# ') and len(line) > 5:
                h1_raw = line.lstrip('#').strip()
                print(f"  提取到 h1: {h1_raw[:60]}")
                break

    # Strip HTML tags from h1 (AI may embed <a class="internal-link"> in h1 field)
    h1 = re.sub(r'<[^>]+>', '', h1_raw)

    return {
        'title': title,
        'description': description,
        'h1': h1,
        'tags': [t.strip() for t in parts[3].split(',') if t.strip()]
    }


def text_to_html(text):
    """将 Markdown 纯文本转换为 HTML """
    lines = text.split('\n')
    html_parts = []
    in_list = False
    list_items = []

    # ---- 修复: 使用局部状态字典替代类属性，避免跨调用污染 ----
    state = {
        '_in_code_block': False,
        '_code_block_lines': [],
        '_table_header': None,
        '_table_rows': [],
    }

    def flush_table():
        """输出累积的 Markdown 表格并重置状态"""
        if state['_table_header'] is None:
            return ''
        headers = state['_table_header']
        rows = state['_table_rows']
        state['_table_header'] = None
        state['_table_rows'] = []
        th_html = ''.join([f'<th style="border:1px solid #ddd;padding:8px;background:#0066cc;color:white;">{h}</th>' for h in headers])
        tbody_html = ''
        for i, row in enumerate(rows):
            bg = '#f9f9f9' if i % 2 == 0 else 'white'
            def convert_cell_links(cell):
                def _convert(m):
                    text = m.group(1)
                    url = m.group(2).strip().replace(' ', '+')
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return f'<a href="{url}" target="_blank" rel="nofollow sponsored">{text}</a>'
                return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _convert, cell)
            td_html = ''.join([f'<td style="border:1px solid #ddd;padding:8px;">{convert_cell_links(c)}</td>' for c in row])
            tbody_html += f'<tr style="background:{bg}">{td_html}</tr>'
        return f'<table style="border-collapse:collapse;width:100%;margin:20px 0;font-size:0.95em;"><thead><tr>{th_html}</tr></thead><tbody>{tbody_html}</tbody></table>'

    for line in lines:
        line = line.rstrip()
        if line == lines[0] and '|' in line:
            continue
        if not line.strip() and len(html_parts) == 0:
            continue

        # Markdown 表格
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(re.match(r'^[-:]+$', c.replace(' ', '')) for c in cells if c):
                continue
            if state['_table_header'] is None:
                state['_table_header'] = cells
                state['_table_rows'] = []
            else:
                state['_table_rows'].append(cells)
            continue
        else:
            if state['_table_header'] is not None:
                html_parts.append(flush_table())

        # 列表项
        if line.startswith('- '):
            list_items.append(line[2:])
            in_list = True
            continue
        else:
            if in_list:
                def convert_item_links(item):
                    def _convert(m):
                        text = m.group(1)
                        url = m.group(2).strip()
                        if not url.startswith('http'):
                            url = 'https://' + url
                        return f'<a href="{url}" target="_blank" rel="nofollow sponsored">{text}</a>'
                    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', _convert, item)
                html_parts.append('<ul>' + ''.join([f'<li>{convert_item_links(item)}</li>' for item in list_items]) + '</ul>')
                list_items = []
                in_list = False

        # 多行代码块
        if line.strip().startswith('```'):
            if not state['_in_code_block']:
                state['_in_code_block'] = True
                state['_code_block_lines'] = []
            else:
                state['_in_code_block'] = False
                code_content = '\n'.join(state['_code_block_lines'])
                html_parts.append(f'<pre><code>{code_content}</code></pre>')
                state['_code_block_lines'] = []
            continue
        elif state['_in_code_block']:
            state['_code_block_lines'].append(line)
            continue

        # Markdown 链接
        if '](' in line:
            def convert_markdown_link(m):
                text = m.group(1)
                url = m.group(2)
                if not url.startswith('http'):
                    url = 'https://' + url
                url = url.strip().replace(' ', '+')
                return f'<a href="{url}" target="_blank" rel="nofollow sponsored">{text}</a>'
            line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', convert_markdown_link, line)
            html_parts.append(f'<p>{line}</p>')
        elif line.startswith('### '):
            html_parts.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            html_parts.append(f'<h2>{line[3:]}</h2>')
        elif '`' in line:
            line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
            html_parts.append(f'<p>{line}</p>')
        elif '**' in line:
            line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            html_parts.append(f'<p>{line}</p>')
        elif '*' in line:
            line = re.sub(r'\*(.+?)\*', '<em>\1</em>', line)
            html_parts.append(f'<p>{line}</p>')
        elif line.startswith('> '):
            html_parts.append(f'<blockquote>{line[2:]}</blockquote>')
        elif line.strip():
            html_parts.append(f'<p>{line}</p>')

    # 处理末尾未闭合的代码块
    if state['_in_code_block']:
        code_content = '\n'.join(state['_code_block_lines'])
        html_parts.append(f'<pre><code>{code_content}</code></pre>')

    # 处理末尾表格
    if state['_table_header'] is not None:
        html_parts.append(flush_table())

    result = '\n'.join(html_parts)
    result = re.sub(r'<strong>\s*</strong>', '', result)
    result = re.sub(r'<em>\s*</em>', '', result)
    result = re.sub(r'<code>\s*</code>', '', result)
    result = re.sub(r'<b>\s*</b>', '', result)
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
    
    # 预编译所有关键词的正则（避免循环内重复编译）
    brand_patterns = [
        (re.compile(r'\b(' + re.escape(kw) + r')\b'), url)
        for kw, url in BRAND_KEYWORDS
    ]
    for pattern, url in brand_patterns:
        # 用 split/join 策略：先按 <a ...>...</a> 分割，对非链接部分做替换
        parts = re.split(r'(<a\s[^>]*?>.*?</a>)', html_body, flags=re.DOTALL)
        new_parts = []
        for part in parts:
            if re.match(r'<a\s', part, re.IGNORECASE):
                new_parts.append(part)
            else:
                part = pattern.sub(
                    lambda m, _url=url: f'<a href="{_url}" target="_blank" rel="nofollow sponsored">{m.group(1)}</a>',
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
    <a href="{minimax_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#00d4aa;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">⭐ MiniMax Token Plan</a>
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
    <a href="{minimax_url}" target="_blank" rel="nofollow sponsored" style="display:inline-block;background:#00d4aa;color:white;padding:8px 16px;border-radius:5px;text-decoration:none;font-size:0.9em;">⭐ MiniMax Token Plan</a>
  </div>
</div>
'''


def generate_html(content, template, css):
    """填充 HTML 模板"""
    lines = content.strip().split('\n')
    meta = parse_metadata(lines)
    body_lines = lines[2:]  # 跳过元数据和空行
    html_body = text_to_html('\n'.join(body_lines))

    # 检查 h1 是否与正文第一个 h2 重复（AI 误将章节标题当作 h1）
    first_h2 = None
    m = re.search(r'<h2>([^<]+)</h2>', html_body)
    if m:
        first_h2 = m.group(1).strip()
    h1_to_use = meta['h1']
    if first_h2 and first_h2 == meta['h1']:
        print(f"⚠️ h1 与正文第一个 h2 相同 ('{h1_to_use[:50]}...')，用 title 替代")
        h1_to_use = meta['title']

    is_en = 'en' in css.lower() or 'lang="en"' in template
    html_body = insert_affiliate_links(html_body, is_en)

    # 追加联盟推荐箱
    box = AFFILIATE_BOX_EN if is_en else AFFILIATE_BOX_CN
    box_html = box.format(
        digitalocean_url=AFFILIATE_LINKS['DigitalOcean'],
        vultr_url=AFFILIATE_LINKS['Vultr'],
        cloudflare_url='',
        namecheap_url='',
        minimax_url=AFFILIATE_LINKS['MiniMax'],
    )
    html_body = html_body + box_html

    tags_html = ''.join([f'<span class="tag">{tag}</span>' for tag in meta['tags']])

    return template.format(
        title=meta['title'],
        description=meta['description'],
        h1=h1_to_use,
        tags_html=tags_html,
        html_body=html_body,
        css=css,
        BAIDU_STATS=BAIDU_STATS,
        GOOGLE_ANALYTICS=GOOGLE_ANALYTICS,
        CLARITY=CLARITY,
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
