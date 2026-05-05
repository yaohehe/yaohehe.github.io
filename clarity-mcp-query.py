#!/usr/bin/env python3
"""
Clarity MCP 查询工具 - 直接调用 Microsoft Clarity MCP API
无需通过 npm MCP SDK，用 Node.js child_process 做 stdio 中间层
"""
import subprocess
import json
import os
from datetime import datetime

CLARITY_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjQ4M0FCMDhFNUYwRDMxNjdEOTRFMTQ3M0FEQTk2RTcyRDkwRUYwRkYiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiI3YzU2NmUwOC0xYmYyLTQyZGMtOTIzMi1kMTY2NGVmZGViNTQiLCJzdWIiOiIzMjg5MjY0NjExNDUyMTgxIiwic2NvcGUiOiJEYXRhLkV4cG9ydCIsIm5iZiI6MTc3NjU3NjU1NywiZXhwIjo0OTMwMTc2NTU3LCJpYXQiOjE3NzY1NzY1NTcsImlzcyI6ImNsYXJpdHkiLCJhdWQiOiJjbGFyaXR5LmRhdGEtZXhwb3J0ZXIifQ.QIta9zhfHullaOB3tRC_haIOXABk4T_TAha1bcCWZLW6TTPG9LVOlrHFARl0ubMjlVKkn5Rv2BGbItllXopSeD2zwy1dpQNhlUZMarthOWPlO9j6GHDLx7PzJ52HUIhPOlIRm05RJo3S8WqajqT7jjhkogBD5-I1MYP9gSLhKm64RHusyYgFC6KJh2Gs-1Y5fv19ZOR-kSmSTWOVwbAQDKmDGrbDIy09jJDnhnQaGKYnsj6juDKMKC9jL5s8yWBiypC5llGc-JpD4l7UkQJUHIfg0WfS6_LPYrxcVWP73isBEBKFYbpDjAl2dRudo8qKc0Hk-Ge3wSnVXtayYYRtrA"

NPM_BIN = "/tmp/node_modules/.bin/clarity-mcp-server"

def send(proc, req):
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()

def recv(proc):
    line = proc.stdout.readline()
    if not line:
        return None
    resp = json.loads(line.strip())
    if "method" in resp and "id" not in resp:
        return recv(proc)
    return resp

def mcp_call(proc, method, params=None, req_id=1):
    req = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params:
        req["params"] = params
    send(proc, req)
    return recv(proc)

def init_server(proc):
    """初始化 MCP Server 连接"""
    mcp_call(proc, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {"roots": {"listChanged": True}},
        "clientInfo": {"name": "clarity-query", "version": "1.0.0"}
    })
    while True:
        r = recv(proc)
        if r and r.get("method") == "notifications/initialized":
            break

def query(query_str, proc):
    """执行一个自然语言查询"""
    resp = mcp_call(proc, "tools/call", {
        "name": "query-analytics-dashboard",
        "arguments": {"query": query_str}
    }, req_id=3)
    if resp and "result" in resp:
        for b in resp["result"].get("content", []):
            if b.get("type") == "text":
                return b["text"]
    elif resp and "error" in resp:
        return f"❌ {resp['error']}"
    return "❌ 无响应"

def run_query(query_str, label):
    """执行查询并格式化输出"""
    print(f"\n{'='*60}")
    print(f"📊 {label}")
    print("="*60)
    proc = subprocess.Popen(
        ["node", NPM_BIN, f"--clarity_api_token={CLARITY_TOKEN}"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )
    try:
        init_server(proc)
        result = query(query_str, proc)
        print(result)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()

def main():
    print("🔌 Clarity MCP 查询工具")
    print("="*60)
    
    # 测试1: 总会话
    run_query("Total sessions, bot sessions, and pages per session for the last 1 day", "过去1天流量概况")
    
    # 测试2: 滚动深度
    run_query("Scroll depth broken down by device type for the past 2 days", "按设备类型的滚动深度")
    
    # 测试3: 热门页面
    run_query("Top 5 most visited pages by session count for the last 3 days", "热门页面 Top 5")
    
    # 测试4: 浏览器维度
    run_query("Traffic and engagement time segmented by browser for the past 2 days", "按浏览器维度的流量和参与时间")
    
    # 测试5: 用户体验
    run_query("Rage clicks and dead clicks count for the last 7 days", "用户体验指标 (Rage/Dead clicks)")
    
    print("\n✅ 所有查询完成")

if __name__ == "__main__":
    main()
