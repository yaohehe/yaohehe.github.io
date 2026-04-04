#!/bin/bash
# 一键部署脚本：生成内容并推送到 GitHub Pages

set -e

echo "=== 1. 生成文章 ==="
node generate.js --count 5

echo "=== 2. 清理旧公共文件 ==="
rm -rf public
mkdir -p public

echo "=== 3. 生成静态文件 ==="
npx hexo generate

echo "=== 4. 推送到 GitHub ==="
git add -A
git commit -m "auto-update: $(date +%Y-%m-%d)" || echo "无更改"
git push origin main

echo "=== 完成 ==="
echo "网站将在几分钟内更新：https://你的用户名.github.io"