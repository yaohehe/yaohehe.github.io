# 稳定发布流程重建计划

## 问题诊断（2026-04-25）

### 症状
6AM 文章生成成功，但文章未发布到 GitHub Pages（HTTP 404）
用户反馈：运行了这么多天，发布流程很不稳定

### 根因链条

1. **4AM verify-publish.py 误判 staged changes 为错误**（2026-04-25 04:03 失败）
   - `git status --porcelain` 输出中 `M  publish-articles.py` 是 staged change（已 add 未 commit）
   - 旧代码把所有非空输出都当作"有未提交更改"，但 staged changes 不算未提交
   - 验证失败 → 4AM 任务退出码 1 → cron 标记为 failed

2. **6AM 文章生成写错目录？**
   - generate-html.py 写 `DRAFTS_DIR = affiliate-blog/drafts`
   - run-pipeline.py 调用 publish-articles.py
   - publish-articles.py 从 drafts 移到 BLOG_DIR/archive/
   - 但 `yaohehe.github.io` 是独立的 git 仓库，不是 workspace 的子模块
   - 文章在 `affiliate-blog/archive/` 不等于在 `yaohehe.github.io/archive/`

3. **两个仓库的同步依赖人工 push**
   - yaohehe.github.io 有自己的 git 历史
   - 本地变更需要手动 push
   - 4AM verify 失败后，变更堆积在本地

4. **发布流程缺少质量门控和断点续传**
   - 任何一步失败后没有重试机制
   - 文章卡在中间状态无人知晓

### 当前 cron 任务分析

| 时间 | 任务 | 问题 |
|------|------|------|
| 4AM | verify-publish | 只验证不发布，失败后不触发发布 |
| 6AM | SEO文章生成-早 | 生成后调用 pipeline，pipeline 调用 publish-articles |
| 12PM | 亚马逊推广 | 同上 |
| 18PM | 亚马逊推广 | 同上 |
| 22PM | 踩坑复盘系列 | 同上 |

## 修复方案

### 方案：统一发布入口，4AM 作为"兜底发布验证"

**核心原则：**
1. 所有文章只存在于 `yaohehe.github.io/archive/YYYY-MM-DD/`
2. publish-articles.py 统一从 `yaohehe.github.io/archive/` 推送，不依赖 drafts
3. 4AM 任务不再验证 git 状态，而是检查 archive/ 里有没有未推送的文章

### 修改清单

1. **重写 verify-publish.py**
   - 扫描 `yaohehe.github.io/archive/` 的 mtime
   - 检查 GitHub remote 上是否存在同名文件
   - 不存在 → 推送；存在但本地更新 → 推送
   - 不依赖 git status 判断未发布

2. **重写 publish-articles.py**
   - 输入参数：article_dir（默认从 `yaohehe.github.io/archive/` 取当天文章）
   - 不依赖 drafts 目录
   - 先同步 yaohehe.github.io → 运行 update-blog-index.py → 推送所有改动
   - 断点续传：检测上次失败的发布点，从断点继续

3. **修改 4AM cron 任务**
   - verify-and-publish 模式：验证+发布合一
   - 发现未发布文章 → 直接推送，不等 AI 重试

4. **新增 self-heal 自检**
   - 每日 4AM 运行 self_heal.py 后检查 publish 状态
   - 发现异常立即报警，不静默跳过

