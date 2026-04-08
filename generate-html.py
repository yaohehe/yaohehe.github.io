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
.content code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
.content pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
.content blockquote { border-left: 4px solid #0066cc; margin: 15px 0; padding: 10px 15px; background: #f9f9f9; }
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
  <h1>{h1}</h1>
  <div class="post-tags">
    {tags_html}
  </div>
  <div class="content">
    {html_body}
  </div>
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
  <h1>{h1}</h1>
  <div class="post-tags">
    {tags_html}
  </div>
  <div class="content">
    {html_body}
  </div>
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
    # 英文年份：如 "(2024)" 或 "2024 Edition" → "(2026)" / "2026 Edition"
    title = re.sub(r'\b(20\d{2})\b', current_year, title)
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

        # 标题
        if line.startswith('### '):
            html_parts.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            html_parts.append(f'<h2>{line[3:]}</h2>')
        # 粗体
        elif '**' in line:
            line = re.sub(r'\*\*(.+?)\*\*', '<strong>\1</strong>', line)
            html_parts.append(f'<p>{line}</p>')
        # 斜体
        elif '*' in line:
            line = re.sub(r'\*(.+?)\*', '<em>\1</em>', line)
            html_parts.append(f'<p>{line}</p>')
        # 行内代码
        elif '`' in line:
            line = re.sub(r'`(.+?)`', '<code>\1</code>', line)
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

    # 处理末尾列表
    if in_list:
        html_parts.append('<ul>' + ''.join([f'<li>{item}</li>' for item in list_items]) + '</ul>')

    return '\n'.join(html_parts)


def generate_html(content, template, css):
    """填充 HTML 模板"""
    lines = content.strip().split('\n')
    meta = parse_metadata(lines)
    body_lines = lines[2:]  # 跳过元数据和空行
    html_body = text_to_html('\n'.join(body_lines))

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
