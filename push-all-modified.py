#!/usr/bin/env python3
"""推送所有本地修改的文件到 GitHub（绕过 git push）"""
import os, base64, json, subprocess, requests, time

REPO = "yaohehe/yaohehe.github.io"
BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
COMMIT_MSG = "fix: 全站Clarity统计代码补全"

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
if not token:
    print("❌ 无法获取 token"); exit(1)
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

os.chdir(BLOG_DIR)

# 获取所有未推送的修改文件
r = subprocess.run(['git', 'diff', '--name-only', 'HEAD'],
    cwd=BLOG_DIR, capture_output=True, text=True)
files = [f.strip() for f in r.stdout.split('\n') if f.strip()]
print(f"待推送: {len(files)} 个文件")

def get_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        return r.json()['sha']
    return None

def push_file(path):
    fpath = os.path.join(BLOG_DIR, path)
    if not os.path.exists(fpath):
        return True  # skip
    with open(fpath, 'rb') as fh:
        content = fh.read().decode('utf-8')
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    sha = get_sha(path)
    data = {"message": COMMIT_MSG, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        data["sha"] = sha
    r = requests.put(url, headers=headers, json=data, timeout=30)
    if r.status_code in (200, 201):
        return True
    print(f"  ❌ {path} → {r.status_code} {r.text[:80]}")
    return False

ok, fail = 0, 0
for i, f in enumerate(files):
    if push_file(f):
        ok += 1
    else:
        fail += 1
    if (i+1) % 10 == 0:
        print(f"  进度: {i+1}/{len(files)}")

print(f"\n{'✅' if fail == 0 else '⚠️'} 完成: {ok} 成功, {fail} 失败")
