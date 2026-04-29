#!/usr/bin/env python3
"""通过 GitHub API 推送关键文件（绕过 git push 的网络问题）"""
import os, base64, json, subprocess

REPO = "yaohehe/yaohehe.github.io"
FILES = ["index.html", "index-en.html", "sitemap.xml"]
BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
COMMIT_MSG = "fix: 首页统计代码修复 via API push"

def get_token():
    r = subprocess.run(['git', 'config', '--get', 'remote.origin.url'],
        cwd=BLOG_DIR, capture_output=True, text=True, timeout=10)
    url = r.stdout.strip()
    if 'x-access-token:' in url:
        s = url.index('x-access-token:') + len('x-access-token:')
        e = url.index('@')
        return url[s:e]
    return None

def get_sha(path):
    import requests
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        return r.json()['sha']
    return None

def push_file(path, content):
    import requests
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    sha = get_sha(path)
    data = {"message": COMMIT_MSG, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        data["sha"] = sha
    r = requests.put(url, headers=headers, json=data, timeout=30)
    print(f"  {'✅' if r.status_code in (200,201) else '❌'} {path} → {r.status_code}")
    return r.status_code in (200, 201)

token = get_token()
if not token:
    print("❌ 无法获取 token"); exit(1)

headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

os.chdir(BLOG_DIR)
ok = 0
for f in FILES:
    fpath = os.path.join(BLOG_DIR, f)
    if os.path.exists(fpath):
        with open(fpath, 'rb') as fh:
            content = fh.read().decode('utf-8')
        if push_file(f, content):
            ok += 1

print(f"\n{'✅' if ok == len(FILES) else '⚠️'} 推送完成: {ok}/{len(FILES)}")
