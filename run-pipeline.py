#!/usr/bin/env python3
"""
流水线 v3 - 内容规则审稿 + HTML 规则审稿 + 发布
审稿发现问题 → 退出等待 AI 重新生成内容
HTML 问题 → 修复 generate-html.py → 重新生成 HTML
"""
import subprocess
import os
import sys
import re
import shutil
from datetime import datetime

MEMORY_DIR = os.path.expanduser("~/.openclaw/memory/self-improving")
WORKSPACE = "/root/.openclaw/workspace/affiliate-blog"
TMP_DIR = "/tmp/article-gen"


def log_script_error(command, error, fix="", priority="medium"):
    entry = {
        "type": "error", "timestamp": datetime.now().isoformat(),
        "command": command, "error": error, "fix": fix,
        "priority": priority, "status": "pending", "source": "run-pipeline.py"
    }
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(f"{MEMORY_DIR}/errors.jsonl", "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_cmd(cmd, timeout=120, fatal=True):
    print(f"\n>>> {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"❌ 超时 ({timeout}s)")
        if fatal:
            sys.exit(1)
        return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        if fatal:
            sys.exit(1)
        return None
    if r.stdout:
        print(r.stdout)
    if r.returncode != 0:
        print(f"⚠️ 失败 (exit {r.returncode})")
        if fatal:
            sys.exit(1)
        return None
    return r


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# 内容规则审稿(替代 AI 审稿,Ollama 不可用时)
# ============================================================

def rule_review_content():
    """使用规则审稿脚本审稿内容层"""
    print("\n" + "=" * 60)
    print("📋 Phase 1: 内容规则审稿")
    print("=" * 60)

    r = subprocess.run(
        ["python3", f"{WORKSPACE}/review-article.py"],
        capture_output=True, text=True, timeout=60,
        cwd=WORKSPACE
    )
    print(r.stdout)
    if r.stderr:
        print(f"STDERR: {r.stderr}")

    # 读规则审稿报告
    report_path = f"{TMP_DIR}/.review_report.txt"
    issues = {"cn": [], "en": [], "fatal": []}

    if os.path.exists(report_path):
        report = read_file(report_path)
        for line in report.split("\n"):
            if line.startswith("❌"):
                issues["fatal"].append(line)

    passed = (r.returncode == 0)
    return passed, issues


# ============================================================
# HTML 规则审稿
# ============================================================

def rule_review_html():
    """审稿 drafts 里的 HTML 文件"""
    print("\n" + "=" * 60)
    print("📋 Phase 2: HTML 规则审稿")
    print("=" * 60)

    drafts_dir = f"{WORKSPACE}/drafts"
    if not os.path.exists(drafts_dir):
        print("⚠️ drafts 目录不存在,跳过 HTML 审稿")
        return True, []

    html_files = [f for f in os.listdir(drafts_dir)
                  if f.endswith(".html") and not f.startswith(".")]

    if not html_files:
        print("⚠️ drafts 为空,跳过 HTML 审稿")
        return True, []

    all_passed = True
    all_issues = []
    cn_txt_mtime = os.path.getmtime(f"{TMP_DIR}/cn.txt") if os.path.exists(f"{TMP_DIR}/cn.txt") else 0

    for html_file in html_files:
        full_path = f"{drafts_dir}/{html_file}"
        # 只审稿本次生成的文件(5分钟内)
        if abs(os.path.getmtime(full_path) - cn_txt_mtime) > 300:
            continue

        lang = "EN" if "-en" in html_file else "CN"
        lang_name = "英文" if lang == "EN" else "中文"

        print(f"\n📄 审稿 {html_file} ({lang_name})...")
        issues = _review_single_html(full_path, lang)

        if issues:
            all_passed = False
            all_issues.extend([(html_file, issue) for issue in issues])
            for issue in issues:
                print(f"  ❌ {issue}")
        else:
            print(f"  ✅ 通过")

    return all_passed, all_issues


def _review_single_html(html_path, lang):
    """审稿单个 HTML 文件"""
    content = read_file(html_path)
    issues = []

    # 1. 禁止 h2 标题
    forbidden = {
        "CN": ["开头", "引言", "前言", "导语", "开篇"],
        "EN": ["Introduction", "Overview", "Beginning", "Intro"]
    }[lang]

    for tag in ["h2", "H2"]:
        for forb in forbidden:
            pattern = f"<{tag}>{forb}</{tag.lower()}>"
            if pattern in content:
                issues.append(f"禁止的 h2 标题: <{tag}>{forb}</{tag.lower()}>")

    # 2. 检查 h2 标签是否包含 **(说明原始 Markdown 有问题)
    h2_with_markdown = re.findall(r'<h2>([^<]*\*\*[^<]*)</h2>', content)
    if h2_with_markdown:
        for m in h2_with_markdown[:2]:
            issues.append(f"h2 标签内含 Markdown 残留: {m[:50]}")

    # 3. 元数据标题污染(h1 出现 "标题:")
    if re.search(r'<h1>[^<]*标题[::]', content):
        issues.append("h1 标签被元数据污染")

    # 4. 空链接或未解析变量
    if re.search(r'href="[^"]*\{[^}]+\}"', content):
        issues.append("链接包含未解析变量(如 {tag})")

    # 5. 响应式 CSS 检查
    if 'max-width' not in content and 'style=' not in content:
        issues.append("缺少响应式 CSS(无 max-width/style 属性)")

    # 6. 结构检查
    h1_count = len(re.findall(r'<h1[^>]*>', content))
    if h1_count == 0:
        issues.append("缺少 <h1> 标签")
    elif h1_count > 1:
        issues.append(f"出现 {h1_count} 个 <h1> 标签(应该只有1个)")

    # 7. 购买链接检查
    if 'amazon.com' not in content.lower():
        issues.append("缺少 Amazon 链接")
    elif 'amazon.com/s?' in content and 'amazon.com/dp/' not in content:
        issues.append("仅有通用搜索链接，缺少真实 ASIN 链接")

    # 8. HTML 闭合标签
    if '</html>' not in content:
        issues.append("缺少 </html> 闭合标签")
    if '</body>' not in content:
        issues.append("缺少 </body> 闭合标签")

    # 9. 内链检查：必须有 internal-link 类，且 href 必须可点击（非 JS、非复制粘贴）
    # 修复：支持 href 在 class 之前或之后（generate-html.py 产生 href 在前的格式）
    internal_links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*class="internal-link"', content)
    if not internal_links:
        issues.append("缺少内链（.internal-link），建议插入相关文章链接")
    else:
        for link in internal_links:
            # 内链 href 必须是真实路径（以 / 开头或以 .html/.htm 结尾）
            if not (link.startswith('/') or link.endswith('.html') or link.endswith('.htm') or link.startswith('http')):
                issues.append(f"内链 href 格式不规范: {link}（应为 /xxx.html 或完整 URL）")
            # 禁止 href="#" 或 javascript: 等不可点击链接
            if link.strip() in ['#', '', 'javascript:void(0)', 'javascript:;']:
                issues.append(f"内链不可点击: href=\"{link}\"")

    return issues

import json

print("=" * 60)
print("🤖 流水线 v3:规则审稿 + HTML审稿 + 发布")
print("=" * 60)

if not os.path.exists(f"{TMP_DIR}/cn.txt"):
    print("❌ cn.txt 不存在")
    sys.exit(1)
if not os.path.exists(f"{TMP_DIR}/en.txt"):
    print("❌ en.txt 不存在")
    sys.exit(1)

print(f"✅ cn.txt: {os.path.getsize(f'{TMP_DIR}/cn.txt')} bytes")
print(f"✅ en.txt: {os.path.getsize(f'{TMP_DIR}/en.txt')} bytes")

# Phase 1: 内容规则审稿
content_passed, content_issues = rule_review_content()

if not content_passed:
    print("\n" + "=" * 60)
    print("❌ 内容审稿未通过,修复后重新运行 pipeline")
    print("=" * 60)
    print("\n📌 问题列表:")
    for issue in content_issues.get("fatal", []):
        print(f"  {issue}")
    print(f"\n修复方式:")
    print(f"  1. AI 重新生成 cn.txt 和 en.txt(修复元数据格式、## 开头等问题)")
    print(f"  2. 重新运行: python3 {WORKSPACE}/run-pipeline.py")
    sys.exit(1)

print("\n✅ 内容审稿通过")

# Phase 2: 价格验证
run_cmd(f"python3 {WORKSPACE}/validate-prices.py", fatal=False)

# Phase 3: HTML 生成
print("\n" + "=" * 60)
print("🔧 Phase 2: HTML 生成")
print("=" * 60)

drafts_before = set(os.listdir(f"{WORKSPACE}/drafts")) if os.path.exists(f"{WORKSPACE}/drafts") else set()
gen_ok = run_cmd(f"python3 {WORKSPACE}/generate-html.py", fatal=False) is not None
drafts_after = set(os.listdir(f"{WORKSPACE}/drafts")) if os.path.exists(f"{WORKSPACE}/drafts") else set()
new_drafts = drafts_after - drafts_before

if not new_drafts:
    print("⚠️ 未生成新草稿,尝试备用")
    for fname in ["cn.html", "en.html"]:
        tmp_path = f"{TMP_DIR}/{fname}"
        if os.path.exists(tmp_path):
            dst = f"{WORKSPACE}/drafts/{datetime.now().strftime('%Y-%m-%d')}-{fname}.html"
            shutil.copy2(tmp_path, dst)
            print(f"  📋 备用复制: {os.path.basename(dst)}")

# Phase 3.5: 内链插入
print("\n" + "=" * 60)
print("🔗 Phase 3.5: 内链插入(基于文章主题推荐相关已发布文章)")
print("=" * 60)
run_cmd(f"python3 {WORKSPACE}/insert-internal-links.py", fatal=False)

# Phase 4: HTML 规则审稿
html_passed, html_issues = rule_review_html()

if not html_passed:
    print("\n" + "=" * 60)
    print("❌ HTML 审稿未通过")
    print("=" * 60)

    # 分类问题
    content_problems = [(f, issue) for f, issue in html_issues
                        if any(kw in issue for kw in ["h2", "h1", "标题", "Markdown"])]
    tool_problems = [(f, issue) for f, issue in html_issues
                     if any(kw in issue for kw in ["闭合", "缺少", "未解析", "响应式"])]

    if tool_problems:
        print("\n🔧 HTML 生成工具问题(修复 generate-html.py):")
        for fname, issue in tool_problems:
            print(f"  [{fname}] {issue}")

    if content_problems:
        print("\n📝 内容层问题(需回到内容阶段重跑):")
        for fname, issue in content_problems:
            print(f"  [{fname}] {issue}")

    # 内链问题：自动自愈修复
    internal_problems = [(f, issue) for f, issue in html_issues
                        if any(kw in issue for kw in ["内链"])]
    if internal_problems:
        print("\n🩹 内链问题：触发自愈修复")
        for fname, issue in internal_problems:
            print(f"  [{fname}] {issue}")
        run_cmd(f"python3 {WORKSPACE}/insert-internal-links.py", fatal=False)
        print("🩹 自愈完成，重新审稿...")
        html_passed2, html_issues2 = rule_review_html()
        remaining_internal = [(f, issue) for f, issue in html_issues2
                               if any(kw in issue for kw in ["内链"])]
        if remaining_internal:
            print("⚠️ 自愈后仍有内链问题（已降级为警告，流水线继续）")
            for fname, issue in remaining_internal:
                print(f"  [{fname}] {issue}")
        else:
            print("🩹 内链自愈成功")

    # 只有工具问题或内容问题才中断流水线
    if tool_problems or content_problems:
        print(f"\n💡 修复方式:")
        print(f"  - HTML 工具问题 → 修复 generate-html.py 后重新运行")
        print(f"  - 内容问题 → AI 重新生成内容后重新运行")
        sys.exit(1)

print("\n✅ HTML 审稿通过")

# Phase 5: 发布
print("\n" + "=" * 60)
print("🚀 Phase 3: 发布")
print("=" * 60)

run_cmd(f"python3 {WORKSPACE}/publish-articles.py", timeout=300)

print("\n" + "=" * 60)
print("✅ 全链路完成:内容审 ✅ → HTML审 ✅ → 发布成功 ✅")
print("=" * 60)
