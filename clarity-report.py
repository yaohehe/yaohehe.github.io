#!/usr/bin/env python3
"""
Microsoft Clarity Data Export API 集成
每天9AM获取关键指标，每周汇总分析
"""
import requests
import json
import os
from datetime import datetime

CLARITY_API_KEY = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ4M0FCMDhFNUYwRDMxNjdEOTRFMTQ3M0FEQTk2RTcyRDkwRUYwRkYiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiI3YzU2NmUwOC0xYmYyLTQyZGMtOTIzMi1kMTY2NGVmZGViNTQiLCJzdWIiOiIzMjg5MjY0NjExNDUyMTgxIiwic2NvcGUiOiJEYXRhLkV4cG9ydCIsIm5iZiI6MTc3NjU3NjU1NywiZXhwIjo0OTMwMTc2NTU3LCJpYXQiOjE3NzY1NzY1NTcsImlzcyI6ImNsYXJpdHkiLCJhdWQiOiJjbGFyaXR5LmRhdGEtZXhwb3J0ZXIifQ.QIta9zhfHullaOB3tRC_haIOXABk4T_TAha1bcCWZLW6TTPG9LVOlrHFARl0ubMjlVKkn5Rv2BGbItllXopSeD2zwy1dpQNhlUZMarthOWPlO9j6GHDLx7PzJ52HUIhPOlIRm05RJo3S8WqajqT7jjhkogBD5-I1MYP9gSLhKm64RHusyYgFC6KJh2Gs-1Y5fv19ZOR-kSmSTWOVwbAQDKmDGrbDIy09jJDnhnQaGKYnsj6juDKMKC9jL5s8yWBiypC5llGc-JpD4l7UkQJUHIfg0WfS6_LPYrxcVWP73isBEBKFYbpDjAl2dRudo8qKc0Hk-Ge3wSnVXtayYYRtrA"
CLARITY_ENDPOINT = "https://www.clarity.ms/export-data/api/v1/project-live-insights"
OUTPUT_DIR = "/root/.openclaw/workspace/affiliate-blog/reports"

def fetch_clarity_data(num_days=1, dimension1=None, dimension2=None, dimension3=None):
    """获取 Clarity 数据"""
    params = {"numOfDays": str(num_days)}
    if dimension1:
        params["dimension1"] = dimension1
    if dimension2:
        params["dimension2"] = dimension2
    if dimension3:
        params["dimension3"] = dimension3
    
    headers = {
        "Authorization": f"Bearer {CLARITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(CLARITY_ENDPOINT, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"⚠️ Clarity API 错误: {resp.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ 请求失败: {e}")
        return None

def parse_metric(data, metric_name):
    """从 Clarity 数据中提取指定指标"""
    if not data:
        return None
    for item in data:
        if item.get("metricName") == metric_name:
            return item.get("information", [])
    return None

def daily_report():
    """每日 Clarity 数据获取（每天最多2次API调用）"""
    print("📊 获取 Clarity 数据...")
    results = {"date": datetime.now().strftime("%Y-%m-%d"), "metrics": {}}
    
    # 调用1: Traffic + OS + Browser 维度
    data1 = fetch_clarity_data(num_days=1, dimension1="OS", dimension2="Browser")
    if data1:
        info = parse_metric(data1, "Traffic")
        if info:
            total_sessions = sum(int(i.get("totalSessionCount", 0)) for i in info)
            bot_sessions = sum(int(i.get("totalBotSessionCount", 0)) for i in info)
            real_sessions = total_sessions - bot_sessions
            pps = [i.get("pagesPerSessionPercentage") for i in info if i.get("pagesPerSessionPercentage")]
            avg_pps = round(sum(pps) / len(pps), 2) if pps else 0
            results["metrics"]["totalSessions"] = total_sessions
            results["metrics"]["botSessions"] = bot_sessions
            results["metrics"]["realSessions"] = real_sessions
            results["metrics"]["avgPagesPerSession"] = avg_pps
            print(f"  总会话: {total_sessions} | 真实: {real_sessions} | Bot: {bot_sessions}")
        else:
            print("  Traffic 数据为空（网站流量极低）")
    
    # 调用2: Popular Pages + URL
    data2 = fetch_clarity_data(num_days=1, dimension1="URL")
    if data2:
        info = parse_metric(data2, "Popular Pages")
        if info:
            top_pages = sorted([
                {"url": i.get("URL", ""), "title": i.get("Page Title", ""), "sessions": int(i.get("totalSessionCount", 0))}
                for i in info
            ], key=lambda x: x["sessions"], reverse=True)[:10]
            results["topPages"] = top_pages
            print(f"  热门页面: {len(top_pages)} 个")
        else:
            results["topPages"] = []
            print("  热门页面数据为空")
    
    # 保存结果
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = f"{OUTPUT_DIR}/clarity-daily-{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据已保存: {out_path}")
    
    # 追加到周报汇总
    weekly_path = f"{OUTPUT_DIR}/clarity-weekly-summary.json"
    weekly = []
    if os.path.exists(weekly_path):
        with open(weekly_path, "r") as f:
            weekly = json.load(f)
    # 保留最近7天
    weekly.append(results)
    if len(weekly) > 7:
        weekly = weekly[-7:]
    with open(weekly_path, "w") as f:
        json.dump(weekly, f, ensure_ascii=False, indent=2)
    
    return results

def weekly_summary():
    """周日汇总分析"""
    weekly_path = f"{OUTPUT_DIR}/clarity-weekly-summary.json"
    if not os.path.exists(weekly_path):
        print("⚠️ 无周报数据")
        return
    
    with open(weekly_path, "r") as f:
        weekly = json.load(f)
    
    total = sum(d["metrics"].get("totalSessions", 0) for d in weekly)
    real = sum(d["metrics"].get("realSessions", 0) for d in weekly)
    avg_pps = [d["metrics"].get("avgPagesPerSession", 0) for d in weekly if d["metrics"].get("avgPagesPerSession")]
    avg_pps_val = round(sum(avg_pps) / len(avg_pps), 2) if avg_pps else 0
    
    # 热门页面汇总
    all_pages = {}
    for d in weekly:
        for p in d.get("topPages", []):
            url = p["url"]
            all_pages[url] = all_pages.get(url, 0) + p["sessions"]
    top_all = sorted(all_pages.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print(f"📊 Clarity 本周汇总 ({weekly[0]['date']} ~ {weekly[-1]['date']}):")
    print(f"  总会话: {total} | 真实会话: {real} | 平均页面/会话: {avg_pps_val}")
    if top_all:
        print(f"  热门页面:")
        for url, sessions in top_all:
            print(f"    {sessions}次 - {url[:70]}")
    
    # 写入 SEO 分析
    report_path = f"{OUTPUT_DIR}/clarity-weekly-report-{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(report_path, "w") as f:
        f.write(f"Clarity 周报 ({weekly[0]['date']} ~ {weekly[-1]['date']})\n")
        f.write(f"总会话: {total} | 真实会话: {real} | 平均页面/会话: {avg_pps_val}\n")
        if top_all:
            f.write(f"热门页面:\n")
            for url, sessions in top_all:
                f.write(f"  {sessions}次 - {url}\n")
    print(f"✅ 周报已保存: {report_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "weekly":
        weekly_summary()
    else:
        daily_report()
