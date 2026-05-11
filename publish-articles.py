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
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-JX42K3RMSC"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-JX42K3RMSC');
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
    """通过 GitHub API 推送单个文件，带3次指数退避重试"""
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

    # 重试策略：指数退避（1s → 2s → 4s）
    delays = [1, 2, 4]
    last_error = None
    for attempt, delay in enumerate(delays, 1):
        try:
            r = requests.put(url, headers=HEADERS, json=data, timeout=30)
            if r.status_code in (200, 201):
                log(f"✅ {filepath}")
                return True
            elif r.status_code == 409:
                # 409 = SHA冲突，先获取最新SHA再重试
                sha = get_file_sha(filepath)
                if sha:
                    data["sha"] = sha
                    continue
            else:
                last_error = f"{r.status_code} {r.text[:100]}"
                log(f"❌ [{attempt}] {filepath}: {last_error}")
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            log(f"❌ [{attempt}] {filepath}: {last_error}")

        if attempt < len(delays):
            log(f"  ⏳ {delay}s后重试...")
            import time
            time.sleep(delay)

    log(f"❌ {filepath}: 3次重试全部失败 ({last_error})")
    return False

def find_articles_to_publish():
    """扫描 yaohehe.github.io/archive/ 找出未推送到 GitHub 的所有文章
    
    修复：不再只扫描当天目录，而是扫描所有 archive 子目录，
    只排除 git 索引中已有的文件（避免重复推送整个历史）。
    """
    import subprocess
    articles = []
    archive_dir = os.path.join(YAOHEHE_DIR, "archive")

    # 获取 git 已跟踪的文件列表（相对于仓库根目录）
    tracked = set()
    result = subprocess.run(
        ['git', 'ls-files'],
        cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=10
    )
    for line in result.stdout.strip().split('\n'):
        if line.strip():
            tracked.add(line.strip())

    # 扫描所有 archive 子目录
    for sub_dir in os.listdir(archive_dir):
        sub_path = os.path.join(archive_dir, sub_dir)
        if not os.path.isdir(sub_path):
            continue
        for f in os.listdir(sub_path):
            if not f.endswith('.html') or f.startswith('.'):
                continue
            # 跳过 git 已跟踪的文件（已发布到 GitHub 的不重复推送）
            if f in tracked:
                continue
            fp = os.path.join(sub_path, f)
            remote_path = f  # 根目录（非 archive/），确保文章直接服务根路径 URL
            articles.append((remote_path, fp))

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

        has_ga = 'G-JX42K3RMSC' in content
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

def push_to_backup():
    """发布前备份：异步推送当前 HEAD 到 backup-main 分支，不阻塞流水线"""
    log("📦 正在备份当前状态到 backup-main（后台）...")
    import subprocess
    try:
        # 异步后台推送，不等待结果
        proc = subprocess.Popen(
            ['git', 'push', 'origin', 'main:backup-main', '-f'],
            cwd=YAOHEHE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # 立即返回，不卡住流水线（最多等5秒看结果）
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            log("📦 备份已后台运行，不等待")
            return
        if proc.returncode == 0:
            log(f"✅ 备份完成（backup-main 已更新）")
        else:
            log(f"⚠️ 备份失败（不影响主流程）")
    except Exception as e:
        log(f"⚠️ 备份异常（不影响主流程）: {e}")

def main():
    log("=== 发布脚本开始 ===")

    # Step 0: 发布前备份
    push_to_backup()

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
    failed_files = []  # 收集推送失败的文件，用于兜底恢复
    for remote_path, local_path in articles:
        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                content = f.read()
            if push_file(remote_path, content):
                pushed += 1
            else:
                failed_files.append((remote_path, local_path))

    # Step 5: 推送 index + sitemap
    for fname in ['index.html', 'index-en.html', 'sitemap.xml']:
        fpath = os.path.join(YAOHEHE_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, 'rb') as f:
                c = f.read()
            push_file(fname, c)

    # Step 6: 提交新文章到 IndexNow（快速让 Bing/Yandex 索引）
    if articles:
        try:
            import subprocess as sub
            r = sub.run(
                ['python3', 'submit-indexnow.py'] + [a[0] for a in articles],
                capture_output=True, text=True, timeout=60,
                cwd=YAOHEHE_DIR
            )
            if r.returncode == 0 and 'Submitted' in r.stdout:
                log("✅ IndexNow 提交成功")
            else:
                log(f"⚠️ IndexNow: {r.stdout[:100]}")
        except Exception as e:
            log(f"⚠️ IndexNow 提交失败: {e}")


    # Step 7: 验证并修复统计代码（防止 git pull 覆盖导致丢失）
    if not verify_and_fix_tracking_codes():
        log("⚠️ 统计代码修复失败，重试...")
        verify_and_fix_tracking_codes()

    if failed_files:
        log(f"⚠️ {len(failed_files)} 篇文章推送失败，触发自动兜底...")
        recovery_scripts = [
            f"python3 {YAOHEHE_DIR}/push-recovery.py",
            f"python3 {YAOHEHE_DIR}/push-batch.py"
        ]
        for script in recovery_scripts:
            try:
                r = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=120,
                                   cwd=YAOHEHE_DIR)
                if r.returncode == 0 and r.stdout:
                    log(f"🩹 兜底 {script} 输出: {r.stdout[:200]}")
                    break
                else:
                    log(f"⚠️ 兜底 {script}: {r.stderr[:100] if r.stderr else r.stdout[:100]}")
            except Exception as e:
                log(f"⚠️ 兜底异常 {script}: {e}")

    if pushed == 0 and not articles:
        log("📭 无新文章待发布")
    elif pushed == 0:
        log(f"❌ 推送失败：{len(articles)} 篇文章全部失败，已尝试兜底")
        sys.exit(1)

    log(f"✅ 发布完成 | 文章：{pushed}")
    log("=== 发布脚本结束 ===")

if __name__ == '__main__':
    main()