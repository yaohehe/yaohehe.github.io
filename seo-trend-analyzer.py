#!/usr/bin/env python3
"""
SEO趋势分析器 - 配合cron AI任务
在固定路径写入分析模板，AI读取后填入搜索结果
"""
import os
from datetime import datetime

OUTPUT = "/root/.openclaw/workspace/affiliate-blog/reports/seo-analysis-input.txt"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

template = f"""# SEO趋势分析 - {datetime.now().strftime('%Y-%m-%d')}

## 上周建议回顾（如 seo-analysis-output.txt 存在且<8天）
读取 /root/.openclaw/workspace/affiliate-blog/reports/seo-analysis-output.txt 中的"下周生成建议"，确认是否被采纳：
- 如采纳：确认对应文章已发布（检查 git log）
- 如未采纳：分析原因并记录到 seo.md（"⚠️ 上周建议[X]未被采纳，原因：...")

## 任务
用搜索技能查找以下内容，输出到 `/root/.openclaw/workspace/affiliate-blog/reports/seo-analysis-output.txt`：

1. 用 `agent-reach` 搜索 "VPS hosting 2026 trends" 和 "best cloud hosting for developers" 获取当前SEO机会
2. 读取 `~/self-improving/domains/seo.md` 和 `~/self-improving/corrections.md` 作为上下文
3. 结合 yaohehe.github.io 的主题覆盖（WordPress建站、DevOps自动化、联盟营销、AI自动化、云服务器）判断优先级
4. 输出格式：

## 搜索发现
[2-3个当前热门关键词机会及搜索量估算]

## 主题优先级建议
| 优先级 | 主题 | 理由 |
|--------|------|------|
| 1 | ... | ... |
| 2 | ... | ... |

## 生成建议
[下周生成计划的2-3条具体改进建议]

## 记忆更新
[如果发现新模式，写入 ~/self-improving/domains/seo.md 的条目]
"""

with open(OUTPUT, 'w') as f:
    f.write(template)

print(f"[{datetime.now()}] 📋 SEO分析模板已写入 {OUTPUT}")
print("  AI读取后填入搜索结果，输出到 seo-analysis-output.txt")
print("  heartbeat读取输出文件并推送给用户")
