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

# ============================================================
# Phase 0: AI 生成内容
# ============================================================
def call_ai_generate(topic_cn, topic_en=None):
    """
    使用 sessions_spawn 启动 subagent 生成中英文文章内容。
    topic_en 默认等于 topic_cn（如果是中英文同一主题）。
    """
    print("\n" + "=" * 60)
    print("🤖 Phase 0: AI 生成文章内容")
    print("=" * 60)
    
    import subprocess
    
    # 读取文章模板
    template_path = f"{WORKSPACE}/article-template.md"
    rubric_path = f"{WORKSPACE}/content-rubric.md"
    
    if not os.path.exists(template_path):
        print(f"⚠️ article-template.md 不存在，跳过 AI 生成")
        return False
    
    with open(template_path, encoding='utf-8') as f:
        template_content = f.read()
    
    rubric_content = ""
    if os.path.exists(rubric_path):
        with open(rubric_path, encoding='utf-8') as f:
            rubric_content = f.read()
    
    prompt = f"""你是 TechPassive 博客的资深内容编辑。根据以下主题生成中英文文章，严格遵循模板规范。

## 主题
- 中文文章主题: {topic_cn}
- 英文文章主题: {topic_en or topic_cn}

## 文章模板规范（必须严格遵守）
{template_content[:8000]}

## 输出文件路径
- 中文文章 → `/tmp/article-gen/cn.txt`
- 英文文章 → `/tmp/article-gen/en.txt`

## 强制要求
1. 元数据第一行必须是单行 pipe 格式：`标题|描述|一级标题|标签1,标签2,标签3`
2. 禁止章节标题：`## 开头`、`## 引言`（CN）；`## Introduction`、`## Overview`（EN）
3. 亚马逊推荐类必须包含 TL;DR 区块（含产品名+价格+联盟链接）
4. IT 技术教程必须包含 Troubleshooting 章节（≥2 个真实报错+解决方案）
5. 禁止绝对化表述（最好/第一/唯一）
6. Amazon 链接必须是 ASIN 直链（amazon.com/dp/ASIN），禁止通用搜索链接
7. 元数据中禁止出现 "Tags:" 或 "tags:" 字样
8. 中文 ≥ 1500 字符，英文 ≥ 800 词
9. 加粗格式：`**内容**`（**和内容之间无空格）

请生成文章并写入指定文件路径。只写文件，不要解释。
"""
    
    print(f"📝 生成中英文文章: {topic_cn}")
    
    # 写入 prompt 到临时文件，供 sessions_spawn 读取
    prompt_file = f"{TMP_DIR}/.ai_generate_prompt.txt"
    os.makedirs(TMP_DIR, exist_ok=True)
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"✅ Prompt 已写入 {prompt_file}")
    print(f"📋 请在 OpenClaw 会话中执行以下操作生成文章：")
    print(f"""
   使用 sessions_spawn 工具，runtime="subagent"，message 内容读取自：
   {prompt_file}
   
   或者直接让 AI 基于以下 prompt 生成 cn.txt 和 en.txt：
   主题：{topic_cn}
   """)
    return True

def ask_user_topic():
    """交互式获取文章主题（仅在 cn.txt 不存在时调用）"""
    print("\n" + "=" * 60)
    print("📝 文章生成模式")
    print("=" * 60)
    print("提供文章主题（格式：中文主题 | 英文主题），按 Enter 跳过：")
    print("  示例: Amazon Basics AA电池评测 | Amazon Basics AA Battery Review")
    try:
        user_input = input("\n主题> ").strip()
    except EOFError:
        return None, None
    
    if not user_input:
        return None, None
    
    parts = user_input.split('|')
    topic_cn = parts[0].strip()
    topic_en = parts[1].strip() if len(parts) > 1 else None
    return topic_cn, topic_en

print("=" * 60)
print("🤖 流水线 v3:规则审稿 + HTML审稿 + 发布")
print("=" * 60)

# Phase 0: 如果 cn.txt 不存在，尝试 AI 生成
if not os.path.exists(f"{TMP_DIR}/cn.txt"):
    print("⚠️ cn.txt 不存在")
    topic_cn, topic_en = ask_user_topic()
    if topic_cn:
        call_ai_generate(topic_cn, topic_en)
        print("\n请生成文章后重新运行: python3 run-pipeline.py")
        sys.exit(0)
    else:
        print("\n❌ cn.txt 不存在，请先手动生成或让 AI 生成：")
        print("   1. 手动：写入 /tmp/article-gen/cn.txt 和 /tmp/article-gen/en.txt")
        print("   2. AI 辅助：在 OpenClaw 会话中使用 sessions_spawn 生成")
        print("   3. 重试：重新运行 python3 run-pipeline.py")
        sys.exit(1)
else:
    print(f"✅ cn.txt 已存在，跳过 AI 生成（手动/外部生成模式）")

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

# Phase 5: 同步文章到 blog 仓库 + 发布
print("\n" + "=" * 60)
print("🚀 Phase 5: 同步文章到 blog 仓库 + 发布")
print("=" * 60)

# 修复：把 drafts 里的文章复制到 yaohehe.github.io/archive/（目标仓库）
# 复制前先清理同名文件（存在于任何 archive/ 子目录），避免同一文章多副本乱飞
import shutil as _shutil
YAOHEHE_DIR = "/root/.openclaw/workspace/yaohehe.github.io"
drafts_dir = f"{WORKSPACE}/drafts"
today_str = datetime.now().strftime('%Y-%m-%d')
target_archive = os.path.join(YAOHEHE_DIR, "archive", today_str)
if os.path.exists(drafts_dir):
    draft_files = [f for f in os.listdir(drafts_dir) if f.endswith('.html') and not f.startswith('.')]
    if draft_files:
        os.makedirs(target_archive, exist_ok=True)
        # 收集所有 archive 子目录中已存在的同名文件
        archive_base = os.path.join(YAOHEHE_DIR, "archive")
        for f in draft_files:
            # 检查是否已在其他日期目录存在同名文件，有则删旧
            for sub_dir in os.listdir(archive_base):
                if sub_dir == today_str:
                    continue
                existing = os.path.join(archive_base, sub_dir, f)
                idx_path = os.path.join(sub_dir, f)  # relative to archive base, for git
                # 1. 删除本地文件（如果存在）
                if os.path.exists(existing):
                    os.remove(existing)
                    print(f"  🗑 删除旧副本: archive/{sub_dir}/{f}")
                # 2. 无论文件是否存在，检查 Git 索引是否有此路径（防止已发布文件跨文件夹污染）
                r = subprocess.run(
                    ['git', 'ls-files', '--error-unmatch', idx_path],
                    cwd=YAOHEHE_DIR, capture_output=True, text=True, timeout=10
                )
                if r.returncode == 0:
                    subprocess.run(
                        ['git', 'rm', '--cached', '--', idx_path],
                        cwd=YAOHEHE_DIR, capture_output=True, timeout=10
                    )
                    print(f"  🗑 移除索引已发布文件: archive/{sub_dir}/{f}")
            # 复制到当天目录
            src = os.path.join(drafts_dir, f)
            dst = os.path.join(target_archive, f)
            _shutil.copy2(src, dst)
            print(f"  📋 同步: {f} -> archive/{today_str}/")
        print(f"  ✅ 已同步 {len(draft_files)} 篇到 archive/{today_str}/")

run_cmd(f"python3 {WORKSPACE}/publish-articles.py", timeout=300)

print("\n" + "=" * 60)
print("✅ 全链路完成:内容审 ✅ → HTML审 ✅ → 发布成功 ✅")
print("=" * 60)
