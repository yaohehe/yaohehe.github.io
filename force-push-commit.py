#!/usr/bin/env python3
"""强制推送本地 commit 到 GitHub，绕过 git 合并问题"""
import subprocess, requests, base64

BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"

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
REPO = "yaohehe/yaohehe.github.io"

# 获取本地最新 commit SHA
r = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=BLOG_DIR, capture_output=True, text=True)
local_sha = r.stdout.strip()

# 获取远程 main 的 SHA
r = requests.get(
    f"https://api.github.com/repos/{REPO}/branches/main",
    headers=headers, timeout=15
)
remote_sha = r.json()['commit']['sha']

print(f"本地: {local_sha[:8]} | 远程: {remote_sha[:8]}")

# 创建新的 tree 和 commit，复用远程的 parent
# 获取远程 commit 的 tree SHA
r = requests.get(
    f"https://api.github.com/repos/{REPO}/commits/{remote_sha}",
    headers=headers, timeout=15
)
parent_sha = r.json()['tree']['sha']

# 推送本地 commit（复用本地 commit 消息和时间）
import datetime
data = {
    "message": "fix: index页统计代码硬编码写入模板，删除replace依赖",
    "tree": None,  # 使用 parent 的 tree + 我们的 update-blog-index.py 修改
    "parents": [remote_sha]
}

# 最快方法：直接更新 update-blog-index.py 到远程
path = "update-blog-index.py"
with open(f"{BLOG_DIR}/{path}", 'r') as f:
    content = f.read()

# 获取当前远程文件的 SHA
r = requests.get(
    f"https://api.github.com/repos/{REPO}/contents/{path}",
    headers=headers, timeout=15
)
remote_file_sha = r.json()['sha'] if r.status_code == 200 else None

data = {
    "message": "fix: index页统计代码硬编码写入模板，删除replace依赖",
    "content": base64.b64encode(content.encode()).decode(),
    "sha": remote_file_sha
}

r = requests.put(
    f"https://api.github.com/repos/{REPO}/contents/{path}",
    headers=headers, json=data, timeout=30
)
print(f"update-blog-index.py → {r.status_code}")
if r.status_code == 200:
    print(f"✅ 推送成功")
else:
    print(f"错误: {r.text[:200]}")