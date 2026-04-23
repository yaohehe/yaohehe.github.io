#!/usr/bin/env python3
"""
insert-internal-links.py
文章生成后，根据文章主题/标签，查找相关已有文章，插入内链
"""
import os
import re
import sys

WORKSPACE = "/root/.openclaw/workspace/affiliate-blog"
DRAFTS_DIR = f"{WORKSPACE}/drafts"
PUBLISH_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
TMP_DIR = "/tmp/article-gen"


def load_existing_articles():
    """读取已发布文章列表（标题、标签、文件名）"""
    articles = []
    if not os.path.exists(PUBLISH_DIR):
        return articles
    
    for fname in os.listdir(PUBLISH_DIR):
        if not fname.endswith(".html") or fname.startswith("."):
            continue
        path = os.path.join(PUBLISH_DIR, fname)
        content = open(path, "r", encoding="utf-8").read()
        
        # 提取标题
        h1_m = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
        title = h1_m.group(1).strip() if h1_m else fname
        
        # 提取标签
        tags_m = re.findall(r'class="tag"[^>]*>([^<]+)</a>', content)
        tags = [t.strip() for t in tags_m]
        
        articles.append({
            "filename": fname,
            "title": title,
            "tags": tags,
            "path": path
        })
    return articles


def find_related_articles(new_article_content, articles, limit=2):
    """基于文章内容/标签，找出最相关的已发布文章"""
    # 提取新文章标签
    tags_m = re.findall(r'class="tag"[^>]*>([^<]+)</a>', new_article_content)
    new_tags = [t.strip() for t in tags_m]
    
    # 提取新文章 h1 标题关键词
    h1_m = re.search(r'<h1[^>]*>([^<]+)</h1>', new_article_content)
    h1_title = h1_m.group(1).strip() if h1_m else ""
    
    # 简单关键词匹配
    keywords = set(new_tags)
    # 从标题拆词
    for word in re.split(r'[-\s/]', h1_title):
        if len(word) > 2:
            keywords.add(word)
    
    scored = []
    for art in articles:
        score = 0
        for kw in keywords:
            if kw in art["title"] or kw in " ".join(art["tags"]):
                score += 1
            # 同标签加分
            for t in new_tags:
                if t in art["tags"]:
                    score += 2
        
        if score > 0:
            scored.append((score, art))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]


def build_links(new_article_content, related):
    """根据相关文章，构建内链列表 (关键词, URL)"""
    links = []
    
    for score, art in related:
        title = art["title"]
        url = f"/{art['filename']}"
        tags = art.get("tags", [])
        
        # Try to use a short, reliable keyword from tags (prefer 2-3 word tags)
        main_word = None
        if tags:
            for tag in tags:
                # Use tag as keyword if it's 3-15 chars and alphanumeric
                tag_clean = tag.strip().lower()
                if 3 <= len(tag_clean) <= 15 and re.match(r'^[a-z0-9\s]+$', tag_clean):
                    main_word = tag_clean
                    break
        
        # Fallback: extract first 8 chars of title, only alphanumeric
        if not main_word:
            title_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', title).strip()
            words = title_clean.split()
            for w in words:
                if len(w) >= 3:
                    main_word = w
                    break
            if not main_word:
                main_word = title_clean[:8].strip() or title[:8]
        
        links.append((main_word, url))
    
    return links


def insert_internal_links_to_html(html_content, links):
    """
    向 HTML 内容中插入内链（匹配关键词加链接，使用 .internal-link 样式）
    links: list of (keyword, url) 元组列表
    """
    # Only process content inside <body>, leave <head> (including <title> and <meta>) untouched
    head_match = re.search(r'<head[^>]*>.*?</head>', html_content, flags=re.DOTALL | re.IGNORECASE)
    if head_match:
        head = head_match.group(0)
        body = html_content[head_match.end():]
        for keyword, url in links:
            body = _add_links_to_text(body, keyword, url)
        return html_content[:head_match.start()] + head + body
    else:
        # No head tag found, process as before (shouldn't happen in practice)
        for keyword, url in links:
            html_content = _add_links_to_text(html_content, keyword, url)
        return html_content


def _add_links_to_text(text, keyword, url):
    """Add internal links to text (non-anchor parts only)."""
    parts = re.split(r'(<a\s[^>]*?>.*?</a>)', text, flags=re.DOTALL)
    new_parts = []
    for part in parts:
        if re.match(r'<a\s', part, re.IGNORECASE):
            new_parts.append(part)
        else:
            pattern = re.compile(r'\b(' + re.escape(keyword) + r')\b')
            part = pattern.sub(
                lambda m: f'<a href="{url}" class="internal-link">{m.group(1)}</a>',
                part
            )
            new_parts.append(part)
    return ''.join(new_parts)


def self_heal_internal_links(html_content):
    """
    自检内链：删除不可点击或格式不规范的链接（只留真实可点击路径）
    Only processes <body> content, leaves <head> untouched.
    返回清理后的内容和被删除的链接数
    """
    head_match = re.search(r'<head[^>]*>.*?</head>', html_content, flags=re.DOTALL | re.IGNORECASE)
    if head_match:
        head = head_match.group(0)
        body = html_content[head_match.end():]
        body, removed = _heal_links_body(body, original_count=None)
        return html_content[:head_match.start()] + head + body, removed
    else:
        return _heal_links_body(html_content, original_count=None)


def _heal_links_body(html_content, original_count=None):
    """Core healing logic for body content only."""
    if original_count is None:
        original_count = len(re.findall(r'<a[^>]*class="internal-link"', html_content))

    def fix_anchor(m):
        full_match = m.group(0)
        # 提取 href
        href_m = re.search(r'href="([^"]+)"', full_match)
        if not href_m:
            # 无href，整个移除
            inner_m = re.search(r'>([^<]+)</a>', full_match)
            return inner_m.group(1) if inner_m else ''
        href = href_m.group(1)
        # 可点击：真实路径（/开头或 .html/.htm 或 http）
        if href.startswith('/') or href.endswith('.html') or href.endswith('.htm') or href.startswith('http'):
            return full_match  # 保留
        # 不可点击：替换为纯文本
        inner_m = re.search(r'>([^<]+)</a>', full_match)
        return inner_m.group(1) if inner_m else ''

    html_content = re.sub(
        r'<a[^>]*class="internal-link"[^>]*>.*?</a>',
        fix_anchor,
        html_content,
        flags=re.DOTALL
    )

    remaining = len(re.findall(r'<a[^>]*class="internal-link"', html_content))
    removed = original_count - remaining
    return html_content, removed


def process_single_file(target_file, existing):
    """处理单个HTML文件的内链插入"""
    content = open(target_file, "r", encoding="utf-8").read()

    # 找相关文章（最多2篇）
    related = find_related_articles(content, existing, limit=2)
    if not related:
        print(f"⚠️ [{os.path.basename(target_file)}] 未找到相关文章，跳过")
        return False

    print(f"🔗 [{os.path.basename(target_file)}] 相关文章:")
    for score, art in related:
        print(f"  - [{score}] {art['title']} ({','.join(art['tags']) or '无标签'})")

    # 构建内链
    links = build_links(content, related)

    # 插入内链
    new_content = insert_internal_links_to_html(content, links)

    # 自检：清理不可点击的链接
    new_content, removed = self_heal_internal_links(new_content)
    if removed > 0:
        print(f"🩹 [{os.path.basename(target_file)}] 自检清理: 移除了 {removed} 条不规范内链")

    # 写回
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ [{os.path.basename(target_file)}] 内链插入完成: {len(links)} 条（清理后保留 {len(links) - removed} 条）")
    return True


def main():
    import time
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            # 处理所有HTML文件
            if not os.path.exists(DRAFTS_DIR):
                print("⚠️ drafts 目录不存在")
                return
            files = [f for f in os.listdir(DRAFTS_DIR) if f.endswith(".html") and not f.startswith(".")]
            if not files:
                print("⚠️ drafts 为空")
                return
            # 按修改时间排序
            files.sort(key=lambda f: os.path.getmtime(os.path.join(DRAFTS_DIR, f)), reverse=True)
            targets = [os.path.join(DRAFTS_DIR, f) for f in files]
        else:
            html_file = sys.argv[1]
            if os.path.exists(html_file):
                targets = [html_file]
            else:
                targets = [f"{DRAFTS_DIR}/{html_file}"]
    else:
        # 找出本次流水线新生成的 HTML 文件（10分钟内修改的）
        if not os.path.exists(DRAFTS_DIR):
            print("⚠️ drafts 目录不存在")
            return
        files = [f for f in os.listdir(DRAFTS_DIR) if f.endswith(".html") and not f.startswith(".")]
        if not files:
            print("⚠️ drafts 为空")
            return
        now = time.time()
        # 选10分钟内修改过的文件（本次流水线生成）
        recent = [f for f in files if (now - os.path.getmtime(os.path.join(DRAFTS_DIR, f))) < 600]
        if not recent:
            # fallback：最新1个
            recent = [sorted(files, key=lambda f: os.path.getmtime(os.path.join(DRAFTS_DIR, f)), reverse=True)[0]]
        targets = [os.path.join(DRAFTS_DIR, f) for f in recent]

    # 读取已发布文章（一次性加载）
    existing = load_existing_articles()
    print(f"📚 已发布文章: {len(existing)} 篇")

    if not existing:
        print("⚠️ 无已发布文章，跳过内链插入")
        return

    any_success = False
    for target_file in targets:
        ok = process_single_file(target_file, existing)
        if ok:
            any_success = True

    if not any_success:
        sys.exit(1)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()