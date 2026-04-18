#!/usr/bin/env python3
"""
AI 驱动文章审稿脚本 - 质量门控 v2
支持内容审稿和 HTML 审稿，自动判断问题来源并指导重跑阶段
"""
import subprocess
import os
import sys
import json
import re
import tempfile
from datetime import datetime

TMP_DIR = "/tmp/article-gen"
WORKSPACE = "/root/.openclaw/workspace/affiliate-blog"
REVIEW_SESSION_LABEL = "article-reviewer"

# ============================================================
# AI 审稿 Prompt（内容层）
# ============================================================
CONTENT_REVIEW_PROMPT = """你是 TechPassive 博客的资深编辑。严格审稿，发现问题要直接指出。

## 审稿文章（{lang}）

---
{content}
---

## 审稿标准

### 致命问题（任何一项存在即为不通过）
1. **元数据格式错误**：第一行不是 `标题|描述|一级标题|标签` 单行pipe格式，而是 `标题：...` 多行格式
2. **禁止章节标题**：正文包含 `## 开头`、`## 引言`、`## 前言`、`## 导语`（英文：`## Introduction`、`## Overview`、`## Beginning`）
3. **加粗格式错误**：`** 内容 **` 中 ** 和内容之间有空格（注意：**Hello World** 是正确的，内容可以有空格）
4. **字数严重不足**：中文<1200字，英文<650词
5. **幻觉信息**：明显不合理的价格（$1.5 买电池套装）、不存在的 ASIN、或未标注"建议自行确认"的不确定信息

### 警告问题（存在则扣分，但不一定阻断）
1. 缺少第一人称体验描述（"我测试了..."、"I tested..."）
2. 缺少具体价格/数据支撑
3. 链接格式不标准（用了 amazon.com/s?k= 而非真实 ASIN）
4. 缺少联盟链接声明
5. 字数偏低（中文1200-1500字，英文650-800词）
6. 泛泛而谈，缺少深度分析

### 优点（加分项）
1. 有具体的使用场景描述
2. 有优缺点对比表格
3. 有适用/不适用人群说明
4. 有真实 ASIN 和可查证的数据

## 输出格式（必须严格遵守）

```
## 审稿结果

### 致命问题
{none | 1. ... | 2. ...}

### 警告问题  
{none | 1. ... | 2. ...}

### 优点
1. ...
2. ...

### E-E-A-T 自评
- Experience（经验）：X/5（描述：...）
- Expertise（专业）：X/5（描述：...）
- Authoritativeness（权威）：X/5（描述：...）
- Trustworthiness（可信）：X/5（描述：...）

### 结论
[PASS | NEEDS_REVISION | FAIL]
- 总分：X/35
- 问题来源：CONTENT（内容层问题）
- 改进建议：
  1. ...
  2. ...
```

## 重要规则
- 仔细数一下实际字数（中文约1字=1字符，英文约1词=5字符），不要估计错误
- 仔细检查第一行格式
- 仔细检查全文是否有禁止的章节标题（包括出现在正文中间的）
- 如果文章非常好，没有或只有微不足道的问题，给 PASS
- 发现了问题必须诚实说出来，不要为了通过而降低标准"""

# ============================================================
# AI 审稿 Prompt（HTML层）
# ============================================================
HTML_REVIEW_PROMPT = """你是 TechPassive 博客的前端质量审核员。严格审查 HTML 渲染质量。

## 审稿 HTML 文件信息
- 文件名：{filename}
- 文件路径：{filepath}
- 语言：{lang}

## 审稿标准

### 致命问题（任何一项存在即为不通过）
1. **禁止的 h2 标题**：HTML 中存在 `<h2>开头</h2>`、`<h2>引言</h2>`、`<h2>前言</h2>`、`<h2>导语</h2>` 等（英文：`Introduction`、`Overview`、`Beginning`）
   - 这些词只能作为普通段落文本，不能作为 h2 标签
2. **元数据污染**：`index.html` 或 `index-en.html` 被错误更新的内容混入
3. **链接失效**：href 中包含未定义的变量（如 `{tag}`、`{asin}`）或空链接
4. **严重结构问题**：缺少 `<h1>` 或出现多个 `<h1>`、`<html>` 标签不完整

### 警告问题
1. h2/h3 层级不清晰（应该有多个 h2 作为主章节）
2. 缺少 `<h2>` 章节标题（整篇只有一个 h1？）
3. 响应式 CSS 缺失（没有 `max-width`、`padding`、`font-size` 响应式设置）
4. 联盟链接不够明显（购买链接应该清晰可见）
5. 缺少 Skip link 或 ARIA landmark（无障碍）
6. 购买链接格式：`amazon.com/s?k=xxx` 而非 `amazon.com/dp/ASIN`

### 优点（加分）
1. 有面包屑导航
2. 有返回首页链接
3. 有相关阅读区块
4. 结构清晰，h2/h3 层次分明

## 输出格式（必须严格遵守）

```
## HTML 审稿结果：{filename}

### 致命问题
{none | 1. ... | 2. ...}

### 警告问题
{none | 1. ... | 2. ...}

### HTML 质量亮点
1. ...

### 结论
[PASS | NEEDS_REVISION | FAIL]
- 问题来源：HTML（HTML生成层问题）或 CONTENT（内容层问题，需回到内容阶段重跑）
- 如果是 HTML 问题：说明修复方向（如"修复 generate-html.py 中的 h2 降级逻辑"）
- 改进建议：
  1. ...
```

## 重要
- 直接读取 `{filepath}` 文件内容进行审稿
- 重点关注那些只有经过 HTML 转换才会暴露的问题
- 如果 HTML 看起来完全正常，给 PASS"""


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def call_ai_review(prompt, model="minimax/MiniMax-M2.7", timeout=180):
    """通过 sessions_spawn 隔离 AI 审稿，返回结构化报告"""
    session_key = f"agent:isolated:{REVIEW_SESSION_LABEL}"
    
    # 写 prompt 到临时文件避免特殊字符问题
    prompt_file = f"/tmp/.review_prompt_{os.getpid()}.txt"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    try:
        result = subprocess.run(
            [
                "openclaw", "sessions", "spawn",
                "--label", REVIEW_SESSION_LABEL,
                "--runtime", "subagent",
                "--model", model,
                "--timeout", str(timeout),
                "--run-timeout", str(timeout + 30),
                "reviewer",
                "cat", prompt_file
            ],
            capture_output=True, text=True, timeout=timeout + 60
        )
        output = result.stdout if result.stdout else result.stderr
        return output[:8000]
    except subprocess.TimeoutExpired:
        return f"[审稿超时 {timeout}s]"
    except Exception as e:
        return f"[审稿异常: {e}]"
    finally:
        if os.path.exists(prompt_file):
            os.remove(prompt_file)


def parse_review_result(report_text, review_type="content"):
    """解析 AI 审稿报告，返回结构化结果"""
    result = {
        "passed": False,
        "conclusion": "UNKNOWN",
        "source": "CONTENT" if review_type == "content" else "HTML",
        "critical": [],
        "warnings": [],
        "score": 0,
        "suggestions": []
    }
    
    text = report_text or ""
    
    # 解析结论
    if "FAIL" in text:
        result["conclusion"] = "FAIL"
        result["passed"] = False
    elif "PASS" in text and "NEEDS_REVISION" not in text:
        result["conclusion"] = "PASS"
        result["passed"] = True
    elif "NEEDS_REVISION" in text:
        result["conclusion"] = "NEEDS_REVISION"
        result["passed"] = False
    
    # 解析总分
    score_match = re.search(r'总分[：:]?\s*(\d+)/35|总分[：:]?\s*(\d+)', text)
    if not score_match:
        score_match = re.search(r'总分[：:]?\s*(\d+)', text)
    if score_match:
        result["score"] = int(score_match.group(1))
    
    # 解析问题来源
    if "问题来源：HTML" in text or "source.*HTML" in text.lower():
        result["source"] = "HTML"
    elif "问题来源：CONTENT" in text or "source.*CONTENT" in text.upper():
        result["source"] = "CONTENT"
    
    # 解析致命问题（提取列表项）
    critical_section = re.search(r'### 致命问题\n([\s\S]+?)(?=###|##|$)', text)
    if critical_section:
        lines = critical_section.group(1).strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and line not in ("none", "无", "无致命问题", "✅", "✔️", "没有"):
                # 去掉列表标记
                cleaned = re.sub(r'^\d+[.)、]\s*', '', line)
                if cleaned and len(cleaned) > 3:
                    result["critical"].append(cleaned)
    
    # 解析警告问题
    warnings_section = re.search(r'### 警告问题\n([\s\S]+?)(?=###|##|优点|E-E-A-T|结论|$)', text)
    if warnings_section:
        lines = warnings_section.group(1).strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and line not in ("none", "无", "无警告问题", "✅", "✔️"):
                cleaned = re.sub(r'^\d+[.)、]\s*', '', line)
                if cleaned and len(cleaned) > 3:
                    result["warnings"].append(cleaned)
    
    # 解析改进建议
    suggestions_section = re.search(r'改进建议[：:\n]([\s\S]+?)$', text)
    if suggestions_section:
        lines = suggestions_section.group(1).strip().split("\n")
        for line in lines[:5]:
            line = line.strip()
            if line:
                cleaned = re.sub(r'^\d+[.)、]\s*', '', line)
                if cleaned:
                    result["suggestions"].append(cleaned)
    
    return result


def review_content(cn_content, en_content, max_retries=2):
    """审稿内容层，最多重试 max_retries 次"""
    print("\n" + "=" * 60)
    print("📝 Phase 1: AI 内容审稿")
    print("=" * 60)
    
    for attempt in range(1, max_retries + 1):
        print(f"\n--- 内容审稿第 {attempt}/{max_retries} 次 ---")
        
        # 并行审稿中英文
        print("🤖 CN 审稿中...")
        cn_prompt = CONTENT_REVIEW_PROMPT.format(lang="中文", content=cn_content)
        cn_report = call_ai_review(cn_prompt)
        cn_result = parse_review_result(cn_report, "content")
        
        print(f"🤖 EN 审稿中...")
        en_prompt = CONTENT_REVIEW_PROMPT.format(lang="英文", content=en_content)
        en_report = call_ai_review(en_prompt)
        en_result = parse_review_result(en_report, "content")
        
        # 打印报告
        print(f"\n📄 CN 审稿结果: {cn_result['conclusion']} ({cn_result['score']}/35)")
        if cn_result['critical']:
            for i, issue in enumerate(cn_result['critical'], 1):
                print(f"  ❌ {i}. {issue[:100]}")
        if cn_result['warnings']:
            for i, issue in enumerate(cn_result['warnings'][:3], 1):
                print(f"  ⚠️  {i}. {issue[:100]}")
        
        print(f"\n📄 EN 审稿结果: {en_result['conclusion']} ({en_result['score']}/35)")
        if en_result['critical']:
            for i, issue in enumerate(en_result['critical'], 1):
                print(f"  ❌ {i}. {issue[:100]}")
        if en_result['warnings']:
            for i, issue in enumerate(en_result['warnings'][:3], 1):
                print(f"  ⚠️  {i}. {issue[:100]}")
        
        # 判断是否通过
        both_pass = cn_result["passed"] and en_result["passed"]
        
        if both_pass:
            print(f"\n✅ 内容审稿通过")
            return {"passed": True, "phase": "content", "attempt": attempt}
        
        # 失败，打印 AI 给的改进建议
        all_critical = cn_result["critical"] + en_result["critical"]
        if all_critical and attempt < max_retries:
            print(f"\n⚠️  内容审稿未通过，AI 建议：")
            for suggestion in (cn_result["suggestions"] + en_result["suggestions"])[:5]:
                if suggestion:
                    print(f"  → {suggestion[:150]}")
            print(f"\n🔄 将问题反馈给内容生成阶段，重新生成...")
        
        if attempt == max_retries:
            print(f"\n❌ 内容审稿已达最大重试次数 ({max_retries})")
            print(f"   致命问题：")
            for issue in all_critical[:5]:
                print(f"   - {issue[:150]}")
            return {
                "passed": False,
                "phase": "content",
                "attempt": attempt,
                "cn_result": cn_result,
                "en_result": en_result,
                "report": f"CN:\n{cn_report}\n\nEN:\n{en_report}"
            }
    
    return {"passed": False, "phase": "content", "attempt": max_retries}


def review_html(html_path, lang="CN"):
    """审稿 HTML 层"""
    filename = os.path.basename(html_path)
    
    print("\n" + "=" * 60)
    print(f"📝 Phase 2: AI HTML 审稿 ({filename})")
    print("=" * 60)
    
    # 读取 HTML
    if not os.path.exists(html_path):
        print(f"❌ HTML 文件不存在: {html_path}")
        return {
            "passed": False,
            "phase": "HTML",
            "source": "HTML",
            "critical": [f"文件不存在: {html_path}"]
        }
    
    # 只读取部分内容（前500行，避免过大）
    with open(html_path, "r", encoding="utf-8") as f:
        lines = f.readlines()[:500]
    html_content = "".join(lines)
    
    if len(lines) >= 500:
        html_content += f"\n... (文件过大，已截取前500行共{sum(1 for _ in lines)}行，实际{sum(1 for _ in open(html_path))}行)"
    
    # 调用 AI 审稿
    lang_label = "中文" if lang == "CN" else "英文"
    prompt = HTML_REVIEW_PROMPT.format(
        filename=filename,
        filepath=html_path,
        lang=lang_label,
        content=html_content
    )
    
    report = call_ai_review(prompt)
    result = parse_review_result(report, "html")
    
    print(f"\n📄 {filename} 审稿结果: {result['conclusion']}")
    if result["critical"]:
        for i, issue in enumerate(result["critical"], 1):
            print(f"  ❌ {i}. {issue[:150]}")
    if result["warnings"]:
        for i, issue in enumerate(result["warnings"][:3], 1):
            print(f"  ⚠️  {i}. {issue[:150]}")
    
    result["report"] = report
    result["filename"] = filename
    return result


def save_review_report(cn_result, en_result, html_results, phase, attempt):
    """保存完整审稿报告"""
    report_path = f"{TMP_DIR}/.ai_review_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"📋 AI 驱动审稿报告\n")
        f.write(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"阶段：{phase}（第{attempt}次尝试）\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("## 内容审稿\n")
        f.write(f"CN: {cn_result.get('conclusion','N/A')} ({cn_result.get('score',0)}/35)\n")
        for issue in cn_result.get('critical', []):
            f.write(f"  ❌ {issue}\n")
        for issue in cn_result.get('warnings', []):
            f.write(f"  ⚠️  {issue}\n")
        
        f.write(f"\nEN: {en_result.get('conclusion','N/A')} ({en_result.get('score',0)}/35)\n")
        for issue in en_result.get('critical', []):
            f.write(f"  ❌ {issue}\n")
        for issue in en_result.get('warnings', []):
            f.write(f"  ⚠️  {issue}\n")
        
        f.write("\n## HTML 审稿\n")
        for hr in html_results:
            f.write(f"{hr.get('filename','?')}: {hr.get('conclusion','N/A')}\n")
            for issue in hr.get('critical', []):
                f.write(f"  ❌ {issue}\n")
    
    print(f"\n📄 审稿报告已保存: {report_path}")
    return report_path


def main():
    if len(sys.argv) < 2:
        print("用法: python3 ai-review.py <phase>")
        print("  phase: content  - 仅审稿内容层")
        print("  phase: html     - 仅审稿 HTML 层")
        print("  phase: full     - 完整审稿（内容+HTML）")
        print("  phase: status   - 查询上次审稿状态")
        sys.exit(1)
    
    phase = sys.argv[1]
    
    if phase == "status":
        report_path = f"{TMP_DIR}/.ai_review_report.txt"
        if os.path.exists(report_path):
            print(read_file(report_path))
        else:
            print("暂无审稿报告")
        sys.exit(0)
    
    cn_path = f"{TMP_DIR}/cn.txt"
    en_path = f"{TMP_DIR}/en.txt"
    
    if phase in ("content", "full"):
        if not os.path.exists(cn_path) or not os.path.exists(en_path):
            print("❌ cn.txt 或 en.txt 不存在，跳过内容审稿")
            sys.exit(1)
        
        cn_content = read_file(cn_path)
        en_content = read_file(en_path)
        
        result = review_content(cn_content, en_content)
        
        if result["passed"]:
            print(f"\n✅ 内容审稿通过，进入 HTML 生成阶段")
            # 写通过标记
            with open(f"{TMP_DIR}/.content_review_passed", "w") as f:
                f.write(f"passed=1, attempt={result['attempt']}, time={datetime.now().isoformat()}\n")
            sys.exit(0)
        else:
            print(f"\n❌ 内容审稿未通过")
            print(f"致命问题摘要：")
            for key in ["cn_result", "en_result"]:
                if key in result:
                    for issue in result[key].get("critical", [])[:3]:
                        print(f"  - {issue[:150]}")
            sys.exit(1)
    
    elif phase == "html":
        # 审稿所有生成的 HTML
        html_files = []
        for f in os.listdir(WORKSPACE + "/drafts"):
            if f.endswith(".html"):
                html_files.append(WORKSPACE + "/drafts/" + f)
        
        if not html_files:
            print("⚠️  drafts 目录为空，跳过 HTML 审稿")
            sys.exit(0)
        
        html_results = []
        all_passed = True
        
        for hf in html_files:
            lang = "EN" if "-en.html" in hf else "CN"
            result = review_html(hf, lang)
            html_results.append(result)
            if not result["passed"]:
                all_passed = False
        
        if all_passed:
            print(f"\n✅ 所有 HTML 审稿通过")
            with open(f"{TMP_DIR}/.html_review_passed", "w") as f:
                f.write(f"passed=1, time={datetime.now().isoformat()}\n")
            sys.exit(0)
        else:
            print(f"\n❌ 部分 HTML 审稿未通过")
            for hr in html_results:
                if not hr["passed"]:
                    print(f"  {hr.get('filename','?')}: {hr.get('source','?')}问题")
                    for issue in hr.get("critical", [])[:2]:
                        print(f"    - {issue[:150]}")
            sys.exit(1)
    
    else:
        print(f"未知 phase: {phase}")
        sys.exit(1)


if __name__ == "__main__":
    main()
