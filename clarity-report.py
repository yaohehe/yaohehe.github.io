#!/usr/bin/env python3
"""
Microsoft Clarity MCP API 集成
通过自然语言查询方式获取网站分析数据
每天9AM获取关键指标，每周汇总分析
MCP API: https://clarity.microsoft.com/mcp/dashboard/query
配额: 10次/天，3天窗口，3维度/次
"""
import requests
import json
import os
from datetime import datetime

CLARITY_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ4M0FCMDhFNUYwRDMxNjdEOTRFMTQ3M0FEQTk2RTcyRDkwRUYwRkYiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiI3YzU2NmUwOC0xYmYyLTQyZGMtOTIzMi1kMTY2NGVmZGViNTQiLCJzdWIiOiIzMjg5MjY0NjExNDUyMTgxIiwic2NvcGUiOiJEYXRhLkV4cG9ydCIsIm5iZiI6MTc3NjU3NjU1NywiZXhwIjo0OTMwMTc2NTU3LCJpYXQiOjE3NzY1NzY1NTcsImlzcyI6ImNsYXJpdHkiLCJhdWQiOiJjbGFyaXR5LmRhdGEtZXhwb3J0ZXIifQ.QIta9zhfHullaOB3tRC_haIOXABk4T_TAha1bcCWZLW6TTPG9LVOlrHFARl0ubMjlVKkn5Rv2BGbItllXopSeD2zwy1dpQNhlUZMarthOWPlO9j6GHDLx7PzJ52HUIhPOlIRm05RJo3S8WqajqT7jjhkogBD5-I1MYP9gSLhKm64RHusyYgFC6KJh2Gs-1Y5fv19ZOR-kSmSTWOVwbAQDKmDGrbDIy09jJDnhnQaGKYnsj6juDKMKC9jL5s8yWBiypC5llGc-JpD4l7UkQJUHIfg0WfS6_LPYrxcVWP73isBEBKFYbpDjAl2dRudo8qKc0Hk-Ge3wSnVXtayYYRtrA"
MCP_ENDPOINT = "https://clarity.microsoft.com/mcp/dashboard/query"
OUTPUT_DIR = "/root/.openclaw/workspace/affiliate-blog/reports"

# 每日配额计数器（全局记录调用次数，避免超限）
QUOTA_FILE = "/root/.openclaw/workspace/affiliate-blog/reports/clarity-mcp-quota.json"

def get_quota():
    """获取今日已用配额"""
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(QUOTA_FILE):
        with open(QUOTA_FILE) as f:
            data = json.load(f)
        if data.get("date") == today:
            return data.get("used", 0)
    return 0

def record_quota(used):
    """记录今日配额使用"""
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(QUOTA_FILE, "w") as f:
        json.dump({"date": today, "used": used}, f)

def mcp_query(query_str, max_retries=1):
    """通过 Clarity MCP API 发送自然语言查询"""
    used = get_quota()
    if used >= 10:
        print(f"⚠️ MCP 配额已用尽（{used}/10），跳过查询")
        return None
    
    headers = {
        "Authorization": f"Bearer {CLARITY_TOKEN}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                MCP_ENDPOINT,
                headers=headers,
                json={"query": query_str, "timezone": "UTC"},
                timeout=20
            )
            record_quota(used + 1)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("dataErrorType") == 0:
                    return data
                else:
                    print(f"⚠️ 查询错误 ({query_str[:40]}...): dataErrorType={data.get('dataErrorType')}")
                    return None
            else:
                print(f"⚠️ MCP API 错误: {resp.status_code} - {resp.text[:100]}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ 查询失败，重试: {e}")
            else:
                print(f"⚠️ 查询异常: {e}")
                return None
    return None

def parse_sessions(data):
    """从 MCP 数据中解析会话数"""
    if not data or not data.get("data"):
        return None
    for row in data["data"]:
        if "DistinctSessionCount" in row:
            return {
                "sessions": int(row.get("DistinctSessionCount", 0)),
                "users": int(row.get("DistinctUserCount", 0))
            }
    return None

def parse_scroll_depth(data):
    """解析滚动深度数据"""
    if not data or not data.get("data"):
        return []
    result = []
    for row in data["data"]:
        result.append({
            "device": row.get("Device", "Unknown"),
            "avg_scroll_depth": row.get("AvgScrollDepthPercent", 0)
        })
    return result

def parse_top_pages(data):
    """解析热门页面数据"""
    if not data or not data.get("data"):
        return []
    result = []
    for row in data["data"]:
        result.append({
            "url": row.get("VisitedUrl", ""),
            "sessions": int(row.get("SessionCount", 0))
        })
    return result

def parse_browser_data(data):
    """解析浏览器维度数据"""
    if not data or not data.get("data"):
        return []
    result = []
    for row in data["data"]:
        result.append({
            "browser": row.get("Browser", "Unknown"),
            "sessions": int(row.get("SessionCount", 0)),
            "avg_duration": round(float(row.get("AvgTotalDurationInSeconds", 0)), 2),
            "avg_active": round(float(row.get("AvgActiveDurationInSeconds", 0)), 2)
        })
    return result

def daily_report():
    """每日 Clarity MCP 数据获取（每天最多2次 MCP 调用）"""
    print("📊 通过 MCP API 获取 Clarity 数据...")
    used = get_quota()
    print(f"  MCP 配额: {used}/10")
    
    results = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "metrics": {},
        "mcp_queries": []
    }
    
    # === 调用1: 总会话 + 独立用户 ===
    print("  [1/2] 查询总会话和独立用户...")
    data1 = mcp_query("Total sessions, distinct session count, and distinct user count for non-bot sessions over the last 1 day")
    if data1:
        parsed = parse_sessions(data1)
        if parsed:
            results["metrics"]["totalSessions"] = parsed["sessions"]
            results["metrics"]["distinctUsers"] = parsed["users"]
            results["mcp_queries"].append(data1.get("query", ""))
            print(f"  ✅ 总会话: {parsed['sessions']} | 独立用户: {parsed['users']}")
        else:
            print("  ⚠️ 会话数据解析失败")
    
    # === 调用2: 热门页面 + 浏览器维度（分开查避免混淆）===
    print("  [2/2] 查询热门页面 Top 5...")
    data2 = mcp_query("Top 5 most visited pages by session count for the last 1 day, show URL and session count")
    if data2:
        pages = parse_top_pages(data2)
        if pages:
            results["topPages"] = pages[:5]
            results["mcp_queries"].append(data2.get("query", ""))
            print(f"  ✅ 热门页面: {len(pages)} 个")
        else:
            results["topPages"] = []
            print("  ⚠️ 热门页面数据为空")
    
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
    weekly.append(results)
    if len(weekly) > 7:
        weekly = weekly[-7:]
    with open(weekly_path, "w") as f:
        json.dump(weekly, f, ensure_ascii=False, indent=2)
    
    return results

def weekly_summary():
    """周日汇总分析（MCP 方式）"""
    weekly_path = f"{OUTPUT_DIR}/clarity-weekly-summary.json"
    if not os.path.exists(weekly_path):
        print("⚠️ 无周报数据")
        return
    
    with open(weekly_path, "r") as f:
        weekly = json.load(f)
    
    total = sum(d["metrics"].get("totalSessions", 0) for d in weekly)
    users = sum(d["metrics"].get("distinctUsers", 0) for d in weekly)
    
    # 热门页面汇总
    all_pages = {}
    for d in weekly:
        for p in d.get("topPages", []):
            url = p["url"]
            all_pages[url] = all_pages.get(url, 0) + p["sessions"]
    top_all = sorted(all_pages.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print(f"📊 Clarity 本周 MCP 汇总 ({weekly[0]['date']} ~ {weekly[-1]['date']}):")
    print(f"  总会话: {total} | 独立用户: {users} | 平均页面/会话: N/A (MCP不返回PPS)")
    if top_all:
        print(f"  热门页面:")
        for url, sessions in top_all:
            print(f"    {sessions}次 - {url[:70]}")
    
    # 写入 SEO 分析
    report_path = f"{OUTPUT_DIR}/clarity-weekly-report-{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Clarity 周报 MCP版 ({weekly[0]['date']} ~ {weekly[-1]['date']})\n")
        f.write(f"总会话: {total} | 独立用户: {users}\n")
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
