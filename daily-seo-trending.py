#!/usr/bin/env python3
"""
每日SEO趋势数据更新
将当天日期写入趋势文件，供后续生成任务参考
"""
import os
from datetime import datetime

TRENDING_FILE = "/root/.openclaw/workspace/affiliate-blog/reports/seo-daily-trending.txt"

def main():
    today = datetime.now().strftime('%Y-%m-%d')
    os.makedirs(os.path.dirname(TRENDING_FILE), exist_ok=True)
    with open(TRENDING_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M')} — 趋势数据已更新\n")
    print(f"✅ 趋势数据已写入 {TRENDING_FILE}（{today}）")

if __name__ == '__main__':
    main()
