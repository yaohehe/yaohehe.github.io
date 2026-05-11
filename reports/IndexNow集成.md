# IndexNow 集成 - 快速让搜索引擎索引你的新文章

## 什么是 IndexNow？

IndexNow 是一个开放的协议，让你一次性通知多个搜索引擎（Bing、Yandex）有新文章发布。相比传统的 sitemap 被动等待，IndexNow 能让文章在几小时内被 Bing/Yandex 发现和索引。

**官网**：[indexnow.org](https://www.indexnow.org)

---

## 本网站配置

| 项目 | 值 |
|------|-----|
| API Key | `cc8394e322884ba58f5db3acfcf3e2a7` |
| Key 文件 | `https://yaohehe.github.io/cc8394e322884ba58f5db3acfcf3e2a7.txt` |
| Key 文件状态 | ✅ 已生效 |
| 提交端点 | `api.indexnow.org` + `www.bing.com/IndexNow` |
| 脚本 | `submit-indexnow.py` |

---

## 使用方法

### 提交最近 N 篇新文章
```bash
cd /root/.openclaw/workspace/yaohehe.github.io
python3 submit-indexnow.py --recent 5
```

### 提交所有 sitemap 文章
```bash
python3 submit-indexnow.py --all
```

### 提交指定文件
```bash
python3 submit-indexnow.py 2026-05-10-xxx.html 2026-05-09-yyy.html
```

---

## 集成到流水线（自动提交）

每次流水线发布新文章后，自动提交到 IndexNow：

```python
# 在 run-pipeline.py 或 publish-articles.py 末尾添加：
import subprocess
result = subprocess.run(
    ['python3', 'submit-indexnow.py', '--recent', '1'],
    cwd='/root/.openclaw/workspace/yaohehe.github.io',
    capture_output=True, text=True
)
print(result.stdout)
```

---

## 验证 Key 文件

```bash
curl -s https://yaohehe.github.io/cc8394e322884ba58f5db3acfcf3e2a7.txt
# 输出应为: cc8394e322884ba58f5db3acfcf3e2a7
```

---

## 测试结果（2026-05-10）

```
📡 IndexNow: Submitting 5 recent articles...
  https://api.indexnow.org/IndexNow: 202
  https://www.bing.com/IndexNow: 200
✅ Submitted 5 URL(s) successfully
```

两个端点均返回 200/202，成功通知到 Bing 搜索引擎。

---

## 注意事项

- Key 文件名需与 API Key 完全一致，且必须在域名根目录
- GitHub Pages 默认忽略不含 `.html` 扩展名的纯文本文件 → **已通过 git ls-files 验证文件在仓库中**
- 每分钟最多提交 1 次，单次最多 10,000 个 URL
- Bing/Yandex 会将 URL 立即加入索引排队，不保证立即展示

## 主动提交 vs Sitemap

| 方式 | 速度 | 适用场景 |
|------|------|---------|
| IndexNow | 数小时 | 新文章/更新/删除 |
| Sitemap | 数天~数周 | 被动等待全站索引 |