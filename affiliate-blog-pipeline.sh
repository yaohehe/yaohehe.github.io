#!/bin/bash
# affiliate-blog-pipeline.sh
# AI生成任务一键执行脚本
set -e

WORKSPACE="/root/.openclaw/workspace/affiliate-blog"
TMP_DIR="/tmp/article-gen"

echo "[1/4] 清理目录..."
rm -rf $TMP_DIR && mkdir -p $TMP_DIR

echo "[2/4] 生成文章 (AI已写入cn.txt和en.txt，此处等待AI完成)..."
# AI在这里写入内容到cn.txt和en.txt
# 此脚本由AI调用时，cn.txt和en.txt应已存在
if [ ! -f "$TMP_DIR/cn.txt" ] || [ ! -f "$TMP_DIR/en.txt" ]; then
    echo "❌ cn.txt或en.txt不存在，AI生成步骤未完成"
    exit 1
fi
echo "✅ 文章就绪 ($(wc -c < $TMP_DIR/cn.txt) bytes / $(wc -c < $TMP_DIR/en.txt) bytes)"

echo "[3/4] HTML转换..."
python3 $WORKSPACE/generate-html.py

echo "[4/4] 发布到GitHub..."
python3 $WORKSPACE/publish-articles.py

echo "✅ 流水线完成"
