#!/usr/bin/env python3
"""通过 GitHub API 创建 deployment 以触发 Pages 重建"""
import subprocess, requests

def get_token():
    r = subprocess.run(['git', 'config', '--get', 'remote.origin.url'],
        cwd="/root/.openclaw/workspace/yaohehe.github.io", capture_output=True, text=True, timeout=10)
    url = r.stdout.strip()
    if 'x-access-token:' in url:
        s = url.index('x-access-token:') + len('x-access-token:')
        e = url.index('@')
        return url[s:e]
    return None

token = get_token()
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

# 触发 Pages 重新构建 - 通过创建新 commit
import base64, json

# 读取当前 index.html 内容
with open('/root/.openclaw/workspace/yaohehe.github.io/index.html') as f:
    content = f.read()

# 获取当前 SHA
r = requests.get(
    "https://api.github.com/repos/yaohehe/yaohehe.github.io/contents/index.html",
    headers=headers, timeout=15
)
sha = r.json()['sha'] if r.status_code == 200 else None

# 强制更新 index.html（同内容但新 commit 触发 Pages）
data = {
    "message": "chore: trigger Pages rebuild",
    "content": base64.b64encode(content.encode()).decode(),
    "sha": sha
}
r = requests.put(
    "https://api.github.com/repos/yaohehe/yaohehe.github.io/contents/index.html",
    headers=headers, json=data, timeout=30
)
print(f"Push status: {r.status_code}")
if r.status_code in (200, 201):
    print(f"New SHA: {r.json()['commit']['sha'][:12]}")
    print("✅ Pages rebuild should start shortly")
else:
    print(f"Error: {r.text[:200]}")
