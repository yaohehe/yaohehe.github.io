#!/usr/bin/env python3
"""
文章审稿脚本 - 基于规则的质量门控
在 HTML 生成前对 cn.txt 和 en.txt 进行客观格式审查
致命问题阻止发布，警告问题仅记录
"""
import os
import sys
import re

TMP_DIR = "/tmp/article-gen"
WORKSPACE = "/root/.openclaw/workspace/affiliate-blog"

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def check_file(filepath, lang):
    """审稿单个文件，返回 (critical_issues, warnings)"""
    content = read_file(filepath)
    filename = os.path.basename(filepath)
    critical = []
    warnings = []
    
    lines = content.split("\n")
    first_line = lines[0] if lines else ""
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""
    
    # ========== 格式检查（致命）==========
    
    # 1. 元数据格式：必须是单行 pipe 格式
    if lang == "CN":
        if "标题：" in first_line or "描述：" in first_line or "一级标题：" in first_line:
            critical.append(f"{lang}: 元数据使用了多行格式（标题：/描述：等）而非单行pipe格式")
        if "Tags:" in first_line or "tags:" in first_line:
            critical.append(f"{lang}: 元数据包含 'Tags:' 标记，应为纯pipe格式")
    else:
        if "Title:" in first_line or "Description:" in first_line or "H1:" in first_line:
            critical.append(f"{lang}: 元数据使用了多行格式（Title:/Description:等）而非单行pipe格式")
        if "Tags:" in first_line:
            critical.append(f"{lang}: 元数据包含 'Tags:' 标记，应为纯pipe格式")
    
    # 2. 禁止的章节标题
    forbidden_headers_cn = ["## 开头", "## 引言", "## 前言", "## 导语", "## 开篇", "## Hook"]
    forbidden_headers_en = ["## Introduction", "## Overview", "## Beginning", "## Intro", "## Hook", "## Preface"]
    forbidden_headers = forbidden_headers_cn if lang == "CN" else forbidden_headers_en
    
    for header in forbidden_headers:
        if header in body:
            critical.append(f"{lang}: 正文包含禁止的章节标题 '{header}'")
    
    # 3. 加粗格式（** 和内容之间无空格）- 逐行检查
    for lineno, line in enumerate(lines, 1):
        # 禁用 DOTALL，确保 . 不匹配换行符（避免 ** 跨行匹配）
        for m in re.finditer(r'\*\*(.+?)\*\*', line):
            bold_inner = m.group(1)
            # 加粗内容本身含空格是正常的（如 **Hello World**）
            # 但如果内容以空格开头或结尾，说明格式错误（如 `** content **` ）
            if bold_inner.startswith(' ') or bold_inner.endswith(' '):
                critical.append(f"{lang}: 第{lineno}行加粗格式有空格（'{m.group(0)}'），应为 **内容** 无空格（内容首尾空格需去除）")
    
    # 4. ASIN 链接检查
    asin_pattern = re.compile(r'amazon\.com/(dp|gp/product)/([A-Z0-9]{10})', re.I)
    generic_search = 'amazon.com/s?' in content
    
    if lang == "CN":
        asins_found = asin_pattern.findall(content)
        if not asins_found:
            # 没有 ASIN 链接是警告不是致命（可能产品确实找不到）
            warnings.append(f"{lang}: 未找到真实 ASIN 链接（仅通用搜索链接）")
        elif generic_search and len(asins_found) == 0:
            warnings.append(f"{lang}: 仅使用通用搜索链接，无真实 ASIN")
    
    # 5. 联盟声明
    if lang == "CN":
        if "联盟" not in content and "佣金" not in content and "affiliate" not in content.lower():
            warnings.append(f"{lang}: 缺少联盟链接/佣金声明")
    else:
        if "affiliate" not in content.lower() and "commission" not in content.lower():
            warnings.append(f"{lang}: 缺少 affiliate/commission 声明")
    
    # ========== E-E-A-T 检查（警告）==========
    
    # 第一人称体验
    if lang == "CN":
        if not re.search(r'我(实际|测试|用了|买了|体验了|跑了|用了)', content):
            warnings.append(f"{lang}: 缺少第一人称体验描述（'我实际/测试/用了...'）")
    else:
        if not re.search(r'I (tested|used|bought|actually|found|ran)', content, re.I):
            warnings.append(f"{lang}: 缺少 first-person experience description")
    
    # 具体数据
    has_prices = re.search(r'\$[\d,]+\.?\d*|¥[\d,]+\.?\d*|\d+\s*(美元|人民币|円)', content)
    has_data = has_prices or re.search(r'\d+%|\d+\s*(万|千|亿)', content)
    if not has_data:
        warnings.append(f"{lang}: 缺少具体价格或数据支撑")
    
    # =========== 字数检查（警告）==========
    
    if lang == "CN":
        # 粗略字数（中文）
        char_count = len(content)
        if char_count < 1500:
            critical.append(f"{lang}: 字数不足1500字（当前约{char_count}字）")
        elif char_count < 2000:
            warnings.append(f"{lang}: 字数偏低（{char_count}字），建议≥2000字")
    else:
        # 粗略词数（英文，按空格分）
        word_count = len(re.findall(r'\b\w+\b', content))
        if word_count < 800:
            critical.append(f"{lang}: 词数不足800词（当前约{word_count}词）")
        elif word_count < 1000:
            warnings.append(f"{lang}: 词数偏低（{word_count}词），建议≥1000词")
    
    return critical, warnings

def main():
    cn_path = f"{TMP_DIR}/cn.txt"
    en_path = f"{TMP_DIR}/en.txt"
    
    # 跳过审稿的快捷方式
    if os.path.exists(f"{TMP_DIR}/.review_skip"):
        print("⏭️  审稿已跳过（.review_skip 文件存在）")
        sys.exit(0)
    
    if not os.path.exists(cn_path):
        print(f"⚠️ {cn_path} 不存在，跳过审稿")
        sys.exit(0)
    if not os.path.exists(en_path):
        print(f"⚠️ {en_path} 不存在，跳过审稿")
        sys.exit(0)
    
    print("=" * 60)
    print("📋 文章审稿开始")
    print("=" * 60)
    
    cn_critical, cn_warnings = check_file(cn_path, "CN")
    en_critical, en_warnings = check_file(en_path, "EN")
    
    all_critical = cn_critical + en_critical
    all_warnings = cn_warnings + en_warnings
    
    if all_critical:
        print(f"\n❌ 致命问题 ({len(all_critical)} 项)：")
        for i, issue in enumerate(all_critical, 1):
            print(f"  {i}. {issue}")
    
    if all_warnings:
        print(f"\n⚠️  警告问题 ({len(all_warnings)} 项)：")
        for i, issue in enumerate(all_warnings, 1):
            print(f"  {i}. {issue}")
    
    if not all_critical and not all_warnings:
        print(f"\n✅ 全部检查通过，无致命问题，无警告")
    
    # 写审稿报告文件
    report_path = f"{TMP_DIR}/.review_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("📋 文章审稿报告\n")
        f.write("=" * 60 + "\n\n")
        if all_critical:
            f.write(f"❌ 致命问题 ({len(all_critical)} 项)：\n")
            for issue in all_critical:
                f.write(f"  - {issue}\n")
            f.write("\n")
        if all_warnings:
            f.write(f"⚠️  警告问题 ({len(all_warnings)} 项)：\n")
            for issue in all_warnings:
                f.write(f"  - {issue}\n")
            f.write("\n")
        if not all_critical and not all_warnings:
            f.write("✅ 全部检查通过\n")
        f.write(f"\n审稿时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"\n📄 审稿报告已保存: {report_path}")
    
    # 致命问题 → exit 1（阻断发布）
    # 仅有警告 → exit 0（继续发布）
    if all_critical:
        print(f"\n🚫 审稿不通过，致命问题必须修复")
        print(f"💡 修复后删除 {TMP_DIR}/.review_skip（如果创建过）然后重新运行")
        sys.exit(1)
    else:
        print(f"\n✅ 审稿通过，继续发布")
        sys.exit(0)

if __name__ == "__main__":
    main()
