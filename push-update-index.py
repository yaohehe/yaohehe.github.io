#!/usr/bin/env python3
"""推送 update-blog-index.py 到 GitHub"""
import subprocess, requests, base64

BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
REPO = "yaohehe/yaohehe.github.io"

def get_token():
    r = subprocess.run(['git', 'config', '--get', 'remote.origin.url'],
        cwd=BLOG_DIR, capture_output=True, text=True, timeout=10)
    url = r.stdout.strip()
    if 'x-access-token:' in url:
        s = url.index('x-access-token:') + len('x-access-token:')
        e = url.index('@')
        return url[s:e]
    return None

token = get_token()
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

path = "update-blog-index.py"
with open(f"{BLOG_DIR}/{path}") as f:
    content = f.read()

r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}",
    headers=headers, timeout=15)
sha = r.json()['sha'] if r.status_code == 200 else None

data = {
    "message": "fix: index页统计代码硬编码写入模板",
    "content": base64.b64encode(content.encode()).decode()
}
if sha:
    data["sha"] = sha

r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{path}",
    headers=headers, json=data, timeout=30)
print(f"update-blog-index.py → {r.status_code} {'✅' if r.status_code in (200,201) else '❌'}")
