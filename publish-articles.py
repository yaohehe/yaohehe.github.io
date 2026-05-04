#!/usr/bin/env python3
"""
publish-articles.py - 稳定发布脚本 v2

核心改进：
- 不依赖 drafts 目录
- 从 yaohehe.github.io/archive/ 读取当天文章作为唯一数据源
- 独立运行，不依赖 AI 生成流程的调用

工作流：
1. 扫描 yaohehe.github.io/archive/ 当天修改的 HTML 文件
2. 运行 update-blog-index.py（生成 index + sitemap + 检测断链）
3. 将所有变更（archive/* + index + sitemap）推送到 GitHub
4. 验证推送结果（HTTP 200）
"""
import os
import re
import sys
import base64
import json
import shutil
import subprocess
import requests
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.openclaw/memory/self-improving")
YAOHEHE_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
REPO = "yaohehe/yaohehe.github.io"

# 统计代码常量（防止 git pull 覆盖后注入）
GOOGLE_ANALYTICS = '''<!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-YQZQY6XDXN"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-YQZQY6XDXN');
    </script>'''

CLARITY_STATS = '''<!-- Microsoft Clarity -->
    <script type="text/javascript">
     (function(c,l,a,r,i,t,y){
     c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
     t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
     y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
     })(window, document, "clarity", "script", "wdy3avd2j9");
    </script>'''

BAIDU_STATS = '''<!-- Baidu Tongji -->
    <script>
    var _hmt = _hmt || [];
    (function() {
      var hm = document.createElement("script");
      hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
    })();
    </script>'''

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {msg}", flush=True)

def log_error(command, error, fix, priority="high"):
    entry = {
        "type": "error", "timestamp": datetime.now().isoformat(),
        "command": command, "error": error, "fix": fix,
        "priority": priority, "status": "pending", "source": "publish-articles.py"
    }
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(f"{MEMORY_DIR}/errors.jsonl", "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_github_token():
    """从 git remote 提取 token"""
    try:
        r = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=10
        )
        url = r.stdout.strip()
        if 'x-access-token:' in url:
            s = url.index('x-access-token:') + len('x-access-token:')
            e = url.index('@')
            return url[s:e]
    except:
        pass
    return None

TOKEN = get_github_token()
if not TOKEN:
    raise RuntimeError("❌ 无法获取 GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
log(f"🔑 Token 已获取: {TOKEN[:8]}...")

def get_file_sha(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def push_file(filepath, content, message=None):
    """通过 GitHub API 推送单个文件"""
    url = f"https://api.github.com/repos/{REPO}/contents/{filepath}"
    if message is None:
        message = f"auto: publish {os.path.basename(filepath)}"
    data = {
        "message": message,
        "content": base64.b64encode(content).decode()
    }
    sha = get_file_sha(filepath)
    if sha:
        data["sha"] = sha
    try:
        r = requests.put(url, headers=HEADERS, json=data, timeout=30)
        if r.status_code in (200, 201):
            log(f"✅ {filepath}")
            return True
        else:
            log(f"❌ {filepath}: {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        log(f"❌ {filepath}: {type(e).__name__}: {e}")
        return False

def find_articles_to_publish():
    """扫描 yaohehe.github.io/archive/ 找出当天需要发布的文章"""
    articles = []
    today = datetime.now().strftime('%Y-%m-%d')
    archive_dir = os.path.join(YAOHEHE_DIR, "archive")

    # 扫描当天目录
    today_dir = os.path.join(archive_dir, today)
    if os.path.isdir(today_dir):
        for f in os.listdir(today_dir):
            if f.endswith('.html') and '-en.html' not in f:
                fp = os.path.join(today_dir, f)
                articles.append((f"archive/{today}/{f}", fp))

    return articles

def run_update_index():
    """运行索引同步（这个已经在 yaohehe.github.io 本地操作）"""
    log("🔄 运行索引同步...")
    r = subprocess.run(
        ["python3", f"{YAOHEHE_DIR}/update-blog-index.py"],
        cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=60
    )
    if r.stdout:
        for line in r.stdout.split('\n')[-5:]:
            if line.strip():
                log(f"  {line}")
    if r.returncode != 0:
        log(f"⚠️ 索引同步异常: {r.stderr[:200]}")
        return False
    return True

def verify_no_broken_links():
    """验证 index 中所有链接都指向真实存在的文件"""
    log("🔍 验证索引链接完整性...")
    broken = []
    for idx_file in ['index.html', 'index-en.html']:
        idx_path = os.path.join(YAOHEHE_DIR, idx_file)
        if not os.path.exists(idx_path):
            continue
        with open(idx_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for href_m in re.finditer(r'href="([^"]+)"', content):
            href = href_m.group(1)
            if href.startswith('http') or href.startswith('//') or href in ('index.html', 'index-en.html', '#'):
                continue
            file_path = os.path.join(YAOHEHE_DIR, href)
            if not os.path.exists(file_path):
                broken.append((idx_file, href, file_path))

    if broken:
        log(f"❌ 索引验证失败：发现 {len(broken)} 个断链:")
        for idx_f, href, path in broken[:5]:
            log(f"  [{idx_f}] {href}")
        return False
    log("✅ 索引链接验证通过")
    return True

def verify_and_fix_tracking_codes():
    """验证并修复 index.html / index-en.html 的统计代码（最后防线）"""
    log("🔍 验证统计代码完整性...")
    fixed = 0
    for fname in ['index.html', 'index-en.html']:
        fpath = os.path.join(YAOHEHE_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        has_ga = 'G-YQZQY6XDXN' in content
        has_clarity = 'wdy3avd2j9' in content
        has_baidu = '5217d6a8f8299c6b114858ac6e719e2b' in content

        if has_ga and has_clarity and has_baidu:
            continue  # 完整，无需修复

        # 注入缺失的统计代码
        if not has_ga:
            # 找到 </head> 前插入
            content = content.replace('</head>', GOOGLE_ANALYTICS + '\n</head>')
        if not has_clarity:
            content = content.replace('</head>', CLARITY_STATS + '\n</head>')
        if not has_baidu:
            content = content.replace('</head>', BAIDU_STATS + '\n</head>')

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

        # 推送修复后的文件
        with open(fpath, 'rb') as f:
            push_file(fname, f.read())

        log(f"✅ 已修复 {fname} 统计代码（GA={has_ga}, Clarity={has_clarity}, Baidu={has_baidu}）")
        fixed += 1

    if fixed == 0:
        log("✅ 统计代码验证通过")
    return True

def main():
    log("=== 发布脚本开始 ===")

    # Step 1: 运行索引同步（更新 index.html, index-en.html, sitemap.xml）
    if not run_update_index():
        log("❌ 索引同步失败，退出")
        sys.exit(1)

    # Step 2: 验证索引无断链
    if not verify_no_broken_links():
        log("❌ 发现断链，退出")
        sys.exit(1)

    # Step 3: 找出当天需要发布的文章
    articles = find_articles_to_publish()
    log(f"📄 发现 {len(articles)} 篇当天文章待发布")

    # Step 4: 推送文章文件
    pushed = 0
    for remote_path, local_path in articles:
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                content = f.read()
            if push_file(remote_path, content):
                pushed += 1

    # Step 5: 推送 index + sitemap
    for fname in ['index.html', 'index-en.html', 'sitemap.xml']:
        fpath = os.path.join(YAOHEHE_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, 'rb') as f:
                content = f.read()
            push_file(fname, content)

    # Step 7: 验证并修复统计代码（防止 git pull 覆盖导致丢失）
    if not verify_and_fix_tracking_codes():
        log("⚠️ 统计代码修复失败，重试...")
        verify_and_fix_tracking_codes()

    if pushed == 0 and not articles:
        log("📭 无新文章待发布")
    elif pushed == 0:
        log(f"❌ 推送失败：{len(articles)} 篇文章全部失败")
        sys.exit(1)

    log(f"✅ 发布完成 | 文章：{pushed}")
    log("=== 发布脚本结束 ===")

if __name__ == '__main__':
    main()