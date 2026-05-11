#!/usr/bin/env python3
"""批量推送 archive 文章到根目录 - 内存优化版"""
import os, base64, requests, subprocess, sys

WORKDIR = "/root/.openclaw/workspace/yaohehe.github.io"
REPO = "yaohehe/yaohehe.github.io"

# Get token
TOKEN = subprocess.run(
    ['git', 'config', '--get', 'remote.origin.url'],
    cwd=WORKDIR, capture_output=True, text=True
).stdout.strip()
s = TOKEN.index('x-access-token:') + len('x-access-token:')
e = TOKEN.index('@')
TOKEN = TOKEN[s:e]

HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

def get_sha(path):
    """通过 API 获取文件 SHA（避免 git ls-files 的内存问题）"""
    try:
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("sha")
    except:
        pass
    return None

def push_one(fname, fpath):
    """推送单个文件"""
    with open(fpath, 'rb') as fp:
        content = fp.read()
    data = {
        "message": f"auto: publish {fname}",
        "content": base64.b64encode(content).decode()
    }
    sha = get_sha(fname)
    if sha:
        data["sha"] = sha
    try:
        r = requests.put(f"https://api.github.com/repos/{REPO}/contents/{fname}", headers=HEADERS, json=data, timeout=20)
        return (r.status_code in (200, 201), r.status_code)
    except Exception as e:
        return (False, str(e)[:30])

# Scan archive for untracked files
# GitHub API already has these files - get list from API to avoid git ls-files
r = requests.get(f"https://api.github.com/repos/{REPO}/contents/", headers=HEADERS, timeout=15)
if r.status_code != 200:
    print(f"❌ Cannot list repo: {r.status_code}")
    sys.exit(1)

api_files = {f['name'] for f in r.json() if f['name'].endswith('.html')}
print(f"📊 GitHub root HTMLs: {len(api_files)}")

# Find archive files not in API root
archive_dir = os.path.join(WORKDIR, "archive")
files_to_push = []
for sub in sorted(os.listdir(archive_dir)):
    sub_path = os.path.join(archive_dir, sub)
    if not os.path.isdir(sub_path):
        continue
    for f in sorted(os.listdir(sub_path)):
        if f.endswith('.html') and f not in api_files:
            files_to_push.append((f, os.path.join(sub_path, f)))

print(f"📄 待推送: {len(files_to_push)} 篇")

ok, fail = 0, []
total = len(files_to_push)
for i, (fname, fpath) in enumerate(files_to_push):
    success, code = push_one(fname, fpath)
    if success:
        ok += 1
    else:
        fail.append((fname, code))
    if (i+1) % 20 == 0 or success:
        print(f"[{i+1}/{total}] {'✅' if success else '❌'} {fname[:40]}")

print(f"\n✅ 完成: {ok}/{total} 成功")
if fail:
    print(f"❌ 失败 {len(fail)} 篇:")
    for fname, code in fail[:5]:
        print(f"  {fname}: {code}")