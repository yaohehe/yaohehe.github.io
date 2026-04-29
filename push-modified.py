#!/usr/bin/env python3
"""通过 GitHub API 批量推送所有已修改的文件"""
import os, base64, json, subprocess, requests

REPO = "yaohehe/yaohehe.github.io"
BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
COMMIT_MSG = "fix: 全站Clarity统计代码补全（66文件）"

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

# 获取 git status 里所有 Modified 文件
r = subprocess.run(['git', 'status', '--porcelain'],
    cwd=BLOG_DIR, capture_output=True, text=True)
modified = [line[3:].strip() for line in r.stdout.split('\n') if line.startswith(' M ')]
# 过滤只推 archive/ 下的文章（不含 index/sitemap）
article_files = [f for f in modified if f.startswith('archive/') and f.endswith('.html')]
print(f"待推送: {len(article_files)} 个文章文件")

def get_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        return r.json()['sha']
    return None

def push_file(path, content):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    sha = get_sha(path)
    data = {"message": COMMIT_MSG, "content": base64.b64encode(content.encode()).decode()}
    if sha:
        data["sha"] = sha
    r = requests.put(url, headers=headers, json=data, timeout=30)
    status = '✅' if r.status_code in (200,201) else f'❌{r.status_code}'
    print(f"  {status} {path}")
    return r.status_code in (200, 201)

ok, fail = 0, 0
for f in article_files:
    fpath = os.path.join(BLOG_DIR, f)
    if os.path.exists(fpath):
        with open(fpath, 'rb') as fh:
            content = fh.read().decode('utf-8')
        if push_file(f, content):
            ok += 1
        else:
            fail += 1

print(f"\n{'✅' if fail == 0 else '⚠️'} 批量推送完成: {ok} 成功, {fail} 失败")
