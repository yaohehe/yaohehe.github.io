#!/usr/bin/env python3
"""
每日8点文章简报生成脚本
扫描 yaohehe.github.io 目录，统计文章数量、中英文比例、主题覆盖
输出简洁报告并通过 sessions_send 发送到 main session
"""
import os
import re
import sys
from datetime import datetime

PUBLISH_DIR = "/root/.openclaw/workspace/yaohehe.github.io"

def extract_topic(tags_str):
    """从标签中识别主题"""
    if not tags_str:
        return None
    tag_map = {
        "WordPress建站": ["WordPress", "wordpress", "建站", "网站"],
        "DevOps自动化": ["DevOps", "CI/CD", "GitHub Actions", "Docker", "自动化", "pipeline"],
        "联盟营销": ["联盟营销", "Affiliate", "affiliate", "变现", "佣金"],
        "AI和OpenClaw自动化盈利": ["AI", "OpenClaw", "自动化盈利", "被动收入"],
        "云服务器/VPS": ["云服务器", "VPS", "Vultr", "DigitalOcean", "AWS", "阿里云", "腾讯云", "云计算"],
    }
    for topic, keywords in tag_map.items():
        if any(kw in tags_str for kw in keywords):
            return topic
    return None

def scan_articles():
    """扫描所有文章"""
    if not os.path.exists(PUBLISH_DIR):
        return None

    articles = []
    for fname in os.listdir(PUBLISH_DIR):
        if not fname.endswith('.html'):
            continue
        if fname in ['index.html', 'index-en.html', 'sitemap.xml', 'robots.txt']:
            continue
        path = os.path.join(PUBLISH_DIR, fname)
        stat = os.stat(path)

        # 读取 meta 标签
        with open(path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')

        title_m = re.search(r'<title>([^<]+)</title>', content)
        tags_m = re.search(r'<meta name="keywords" content="([^"]+)"', content)
        date_m = re.search(r'<meta name="date" content="([^"]+)"', content)
        author_m = re.search(r'<meta name="author" content="([^"]+)"', content)

        title = title_m.group(1) if title_m else fname
        tags = tags_m.group(1) if tags_m else ""
        date_str = date_m.group(1) if date_m else ""
        author = author_m.group(1) if author_m else ""

        # 判断语言
        is_en = bool(re.search(r'\b(how to|guide|tutorial|complete|best|the|2026)\b', title, re.I))

        # 提取主题
        topic = extract_topic(tags)

        articles.append({
            'title': title,
            'tags': tags,
            'date': date_str,
            'author': author,
            'is_en': is_en,
            'topic': topic,
            'fname': fname,
        })

    return articles

def generate_report(articles):
    """生成简报文本"""
    total = len(articles)
    cn = [a for a in articles if not a['is_en']]
    en = [a for a in articles if a['is_en']]

    # 主题覆盖
    topics = {
        "WordPress建站": 0,
        "DevOps自动化": 0,
        "联盟营销": 0,
        "AI和OpenClaw自动化盈利": 0,
        "云服务器/VPS": 0,
    }
    for a in articles:
        if a['topic']:
            topics[a['topic']] = topics.get(a['topic'], 0) + 1

    topic_lines = []
    for topic, count in topics.items():
        status = f"✅ {count}篇" if count > 0 else f"❌ 0篇"
        topic_lines.append(f"{status} | {topic}")

    report = f"""📊 TechPassive 简报

共 {total} 篇（中文 {len(cn)} + 英文 {len(en)}）

主题覆盖：
{" | ".join(topic_lines)}

最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}"""
    return report

def main():
    articles = scan_articles()
    if articles is None:
        report = "📊 简报：无法读取文章目录"
    else:
        report = generate_report(articles)

    print(report)

    # 通过 sessions_send 发送到 main session
    try:
        import json
        with open(os.path.expanduser("~/.openclaw/agents/main/sessions/_active")) as f:
            active = json.load(f)
        session_key = active.get("sessionKey", "agent:main:lightclawbot:direct:1407429596")
    except:
        session_key = "agent:main:lightclawbot:direct:1407429596"

    # 打印用于 sessions_send 的信息
    print(f"\n[SEND_TO_SESSION]")
    print(f"sessionKey: {session_key}")
    print(f"message: {report}")

if __name__ == "__main__":
    main()
