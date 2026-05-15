#!/usr/bin/env python3
import os, base64, requests, subprocess

TOKEN = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], cwd='.', capture_output=True, text=True).stdout.strip()
s = TOKEN.index('x-access-token:') + len('x-access-token:')
e = TOKEN.index('@')
TOKEN = TOKEN[s:e]

REPO = "yaohehe/yaohehe.github.io"
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
archive_dir = "archive"

def get_sha(path):
    try:
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{path}", headers=HEADERS, timeout=10)
        return r.json().get("sha") if r.status_code == 200 else None
    except: return None

def push_file(filepath, content, msg=None):
    url = f"https://api.github.com/repos/{REPO}/contents/{filepath}"
    data = {"message": msg or f"auto: publish {os.path.basename(filepath)}", "content": base64.b64encode(content).decode()}
    sha = get_sha(filepath)
    if sha: data["sha"] = sha
    try:
        r = requests.put(url, headers=HEADERS, json=data, timeout=20)
        return (r.status_code in (200, 201), r.status_code)
    except Exception as e:
        return (False, str(e)[:50])

tracked = set(subprocess.run(['git', 'ls-files'], cwd='.', capture_output=True, text=True).stdout.strip().split('\n'))

files = []
for sub in sorted(os.listdir(archive_dir)):
    sp = os.path.join(archive_dir, sub)
    if not os.path.isdir(sp): continue
    for f in sorted(os.listdir(sp)):
        if f.endswith('.html'):
            full_path = os.path.join(sub, f)  # 完整路径，避免 basename 重复导致的误判
            if full_path not in tracked:
                files.append((sub, f, os.path.join(sp, f)))

print(f"Total: {len(files)}")
ok, fail = 0, []
for i, (sub, fname, fpath) in enumerate(files):
    # 用完整路径推送（如 archive/2026-05-15/2026-05-15-article.html），避免重复文件名冲突
    remote_path = os.path.join(sub, fname)
    with open(fpath, 'rb') as fp: c = fp.read()
    success, code = push_file(remote_path, c)
    if success: ok += 1
    else: fail.append((remote_path, code))
    if (i+1) % 10 == 0: print(f"[{i+1}/{len(files)}] ok={ok}")

print(f"DONE: {ok}/{len(files)} ok, {len(fail)} failed")
if fail: print("FAILED:", [f for f,_ in fail[:5]])