#!/usr/bin/env python3
"""
更新博客索引和 sitemap
扫描 yaohehe.github.io 中的所有文章 HTML，
生成更新后的 index.html、index-en.html 和 sitemap.xml
"""
import os
import re
import glob
import json
import math
from datetime import datetime

BLOG_DIR = os.path.dirname(os.path.abspath(__file__)) or "."

# 统计代码
GOOGLE_ANALYTICS = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-JX42K3RMSC"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-JX42K3RMSC');
</script>'''
CLARITY = '''<!-- Microsoft Clarity -->
<script type="text/javascript">
 (function(c,l,a,r,i,t,y){
 c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
 t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
 y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
 })(window, document, "clarity", "script", "wdy3avd2j9");
</script>'''
BAIDU_STATS = '''<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
</script>'''

INDEX_HEADER_CN = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechPassive - 零成本被动收入实战</title>
    <meta name="description" content="TechPassive 是面向程序员的零成本被动收入实战站点，专注真实测试内容。覆盖亚马逊联盟选购评测、WordPress 自建站全流程、GitHub Actions 自动化部署、Claude Code 与 n8n AI 工作流、VPS 与服务器选型对比等。中文为主，附英文译版，全部文章经人工复核。">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; border-bottom: 2px solid #eee; margin-bottom: 40px; }
        h1 { font-size: 2.5em; color: #2c3e50; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 1.2em; }
        .lang-toggle { margin: 20px 0; }
        .lang-toggle a { color: #3498db; text-decoration: none; margin: 0 10px; }
        .lang-toggle a:hover { text-decoration: underline; }
        .post-list { list-style: none; }
        .post-item { margin-bottom: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; transition: box-shadow 0.3s; }
        .post-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .post-title { font-size: 1.4em; margin-bottom: 10px; }
        .post-title a { color: #3498db; text-decoration: none; }
        .post-title a:hover { text-decoration: underline; }
        .post-meta { color: #999; font-size: 0.9em; margin-bottom: 10px; }
        footer { text-align: center; padding: 40px 0; margin-top: 40px; border-top: 2px solid #eee; color: #666; }
        .affiliate-disclaimer { background: #fff8e1; padding: 15px; border-radius: 8px; margin-bottom: 30px; font-size: 0.9em; color: #666; }
        .popular-section { margin-bottom: 40px; }
        .popular-section h2 { font-size: 1.5em; color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }
        .popular-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .popular-item { padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; transition: box-shadow 0.3s; }
        .popular-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .popular-item .popular-title { font-size: 1em; margin-bottom: 5px; }
        .popular-item .popular-title a { color: #3498db; text-decoration: none; font-weight: 600; }
        .popular-item .popular-title a:hover { text-decoration: underline; }
        .popular-meta { font-size: 0.85em; color: #888; margin-bottom: 8px; }
        .popular-tags { display: flex; gap: 5px; flex-wrap: wrap; }
        .popular-item .tag { background: #e8f4f8; color: #3498db; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
        .popular-excerpt { font-size: 0.85em; color: #666; line-height: 1.5; margin-top: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    </style>
<meta name="google-site-verification" content="aRTYFCdyaEkhMFAdwmfx53qD9csq3FcWdJvnRXx5QUQ" />
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-JX42K3RMSC"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-JX42K3RMSC');
    </script>
    <!-- Microsoft Clarity -->
    <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "wdy3avd2j9");
    </script>
    <!-- 百度统计 -->
    <script>
    var _hmt = _hmt || [];
    (function() {
      var hm = document.createElement("script");
      hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
    })();
    </script>
</head>
<body>
    <header>
        <h1>TechPassive</h1>
        <p class="subtitle">零成本被动收入实战</p>
        <div class="lang-toggle">
            <a href="index.html">中文</a> | <a href="index-en.html">English</a>
        </div>
    </header>

    <style>
      #search {
        margin: 30px auto 40px auto !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box;
      }
      .pagefind-ui__search-input {
        width: 100% !important;
        background-color: #fafafa !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        font-size: 1rem !important;
        padding: 12px 15px 12px 42px !important;
        box-shadow: none !important;
        transition: all 0.2s ease-in-out;
      }
      .pagefind-ui__search-input:focus {
        background-color: #fff !important;
        border-color: #1890ff !important;
        box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.15) !important;
        outline: none;
      }
      /* 🔴 本页未加载官方 pagefind-ui.css，缺以下两条规则 → 不搜索时「空抽屉常驻」+「清除键常显」。
         这里按官方定义原样补上：svelte 在无搜索时会给 drawer 挂 .pagefind-ui__hidden、
         给清除键挂 .pagefind-ui__suppressed，靠这两条隐藏。 */
      .pagefind-ui__hidden { display: none !important; }
      .pagefind-ui__suppressed { opacity: 0 !important; pointer-events: none !important; }
      .pagefind-ui__form {
        position: relative;
      }
      /* ⚠️ 不写 opacity / pointer-events —— 清除键的显隐由官方
         `.pagefind-ui__suppressed { opacity:0; pointer-events:none }` 控制（未搜索时自动隐藏）。
         top 用固定值而非 50%：clear 的包含块是 form（内部还含 drawer），
         用 50% 会被算到整个 form 的中部 → 按钮跑到输入框外面。
         22px ≈ 输入框垂直中心（padding 12px + 1rem 字号 + 边框 ≈ 45px 高）。 */
      .pagefind-ui__search-clear {
        position: absolute;
        top: 22px;
        right: 8px;
        transform: translateY(-50%);
        background-color: #f5f5f5 !important;
        color: #555 !important;
        border-radius: 4px !important;
        padding: 6px 12px !important;
        font-size: 0.85rem !important;
        height: auto !important;
        line-height: 1 !important;
        z-index: 10;
      }
      .pagefind-ui__drawer {
        background: #ffffff !important;
        border: 1px solid #e8e8e8 !important;
        border-radius: 8px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1) !important;
        padding: 20px !important;
        margin-top: 10px !important;
        box-sizing: border-box;
      }
      .pagefind-ui__result-title a {
        color: #1890ff !important;
        font-weight: 600 !important;
        text-decoration: none;
      }
      .pagefind-ui__result-title a:hover { text-decoration: underline; }
      .pagefind-ui__result-excerpt mark {
        background-color: #fff1b8 !important;
        color: #000 !important;
        padding: 0 3px;
        border-radius: 3px;
      }
    </style>
    <div style="position: relative; width: 100%; box-sizing: border-box;">
      <div id="search"></div>
    </div>
    <script src="/_pagefind/pagefind-ui.js"></script>
    <script>
      window.addEventListener('DOMContentLoaded', function() {
        new PagefindUI({
          element: "#search",
          showSubResults: true,
          translations: {
            placeholder: "搜索报错日志、技术关键字或产品...",
            clear_search: "清除",
            zero_results: "未找到与 [SEARCH] 相关的技术踩坑复盘",
            many_results: "找到 [COUNT] 条相关结果"
          }
        });
      });
    </script>

    {{POPULAR_CN}}

    <ul class="post-list">
'''

INDEX_HEADER_EN = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechPassive - Passive Income That Works</title>
    <meta name="description" content="Hands-on passive income testing site for developers. AI, WordPress, Amazon, Claude Code, n8n in 2026. Chinese-first, selected English, human-reviewed.">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 40px 0; border-bottom: 2px solid #eee; margin-bottom: 40px; }
        h1 { font-size: 2.5em; color: #2c3e50; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 1.2em; }
        .lang-toggle { margin: 20px 0; }
        .lang-toggle a { color: #3498db; text-decoration: none; margin: 0 10px; }
        .lang-toggle a:hover { text-decoration: underline; }
        .post-list { list-style: none; }
        .post-item { margin-bottom: 30px; padding: 20px; border: 1px solid #eee; border-radius: 8px; transition: box-shadow 0.3s; }
        .post-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .post-title { font-size: 1.4em; margin-bottom: 10px; }
        .post-title a { color: #3498db; text-decoration: none; }
        .post-title a:hover { text-decoration: underline; }
        .post-meta { color: #999; font-size: 0.9em; margin-bottom: 10px; }
        footer { text-align: center; padding: 40px 0; margin-top: 40px; border-top: 2px solid #eee; color: #666; }
        .affiliate-disclaimer { background: #fff8e1; padding: 15px; border-radius: 8px; margin-bottom: 30px; font-size: 0.9em; color: #666; }
        .popular-section { margin-bottom: 40px; }
        .popular-section h2 { font-size: 1.5em; color: #2c3e50; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #3498db; }
        .popular-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
        .popular-item { padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa; transition: box-shadow 0.3s; }
        .popular-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .popular-item .popular-title { font-size: 1em; margin-bottom: 5px; }
        .popular-item .popular-title a { color: #3498db; text-decoration: none; font-weight: 600; }
        .popular-item .popular-title a:hover { text-decoration: underline; }
        .popular-meta { font-size: 0.85em; color: #888; margin-bottom: 8px; }
        .popular-tags { display: flex; gap: 5px; flex-wrap: wrap; }
        .popular-item .tag { background: #e8f4f8; color: #3498db; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }
        .popular-excerpt { font-size: 0.85em; color: #666; line-height: 1.5; margin-top: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    </style>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-JX42K3RMSC"></script>
    <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-JX42K3RMSC');
    </script>
    <!-- Microsoft Clarity -->
    <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "wdy3avd2j9");
    </script>
    <!-- 百度统计 -->
    <script>
    var _hmt = _hmt || [];
    (function() {
      var hm = document.createElement("script");
      hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
    })();
    </script>
</head>
<body>
    <header>
        <h1>TechPassive</h1>
        <p class="subtitle">Passive Income That Works</p>
        <div class="lang-toggle">
            <a href="index.html">中文</a> | <a href="index-en.html">English</a>
        </div>
    </header>

    <style>
      #search {
        margin: 30px auto 40px auto !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box;
      }
      .pagefind-ui__search-input {
        width: 100% !important;
        background-color: #fafafa !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        font-size: 1rem !important;
        padding: 12px 15px 12px 42px !important;
        box-shadow: none !important;
        transition: all 0.2s ease-in-out;
      }
      .pagefind-ui__search-input:focus {
        background-color: #fff !important;
        border-color: #1890ff !important;
        box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.15) !important;
        outline: none;
      }
      /* 🔴 本页未加载官方 pagefind-ui.css，缺以下两条规则 → 不搜索时「空抽屉常驻」+「清除键常显」。
         这里按官方定义原样补上：svelte 在无搜索时会给 drawer 挂 .pagefind-ui__hidden、
         给清除键挂 .pagefind-ui__suppressed，靠这两条隐藏。 */
      .pagefind-ui__hidden { display: none !important; }
      .pagefind-ui__suppressed { opacity: 0 !important; pointer-events: none !important; }
      .pagefind-ui__form {
        position: relative;
      }
      /* ⚠️ 不写 opacity / pointer-events —— 清除键的显隐由官方
         `.pagefind-ui__suppressed { opacity:0; pointer-events:none }` 控制（未搜索时自动隐藏）。
         top 用固定值而非 50%：clear 的包含块是 form（内部还含 drawer），
         用 50% 会被算到整个 form 的中部 → 按钮跑到输入框外面。
         22px ≈ 输入框垂直中心（padding 12px + 1rem 字号 + 边框 ≈ 45px 高）。 */
      .pagefind-ui__search-clear {
        position: absolute;
        top: 22px;
        right: 8px;
        transform: translateY(-50%);
        background-color: #f5f5f5 !important;
        color: #555 !important;
        border-radius: 4px !important;
        padding: 6px 12px !important;
        font-size: 0.85rem !important;
        height: auto !important;
        line-height: 1 !important;
        z-index: 10;
      }
      .pagefind-ui__drawer {
        background: #ffffff !important;
        border: 1px solid #e8e8e8 !important;
        border-radius: 8px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1) !important;
        padding: 20px !important;
        margin-top: 10px !important;
        box-sizing: border-box;
      }
      .pagefind-ui__result-title a {
        color: #1890ff !important;
        font-weight: 600 !important;
        text-decoration: none;
      }
      .pagefind-ui__result-title a:hover { text-decoration: underline; }
      .pagefind-ui__result-excerpt mark {
        background-color: #fff1b8 !important;
        color: #000 !important;
        padding: 0 3px;
        border-radius: 3px;
      }
    </style>
    <div style="position: relative; width: 100%; box-sizing: border-box;">
      <div id="search"></div>
    </div>
    <script src="/_pagefind/pagefind-ui.js"></script>
    <script>
      window.addEventListener('DOMContentLoaded', function() {
        new PagefindUI({
          element: "#search",
          showSubResults: true,
          translations: {
            placeholder: "Search errors, tech keywords or products...",
            clear_search: "Clear",
            zero_results: "No results for [SEARCH]",
            many_results: "Found [COUNT] results"
          }
        });
      });
    </script>

    {{POPULAR_EN}}

    <ul class="post-list">
'''

INDEX_FOOTER = '''    </ul>
    <footer>
        <p>© 2026 TechPassive. All rights reserved.</p>
        <p style="font-size: 0.8rem; color: #999; margin-top: 8px;">Disclaimer: This site contains affiliate links. Purchases through these links may earn me a small commission at no extra cost to you.</p>
    </footer>
</body>
</html>
'''


def get_date_from_filename(filename):
    """从文件名提取日期 YYYY-MM-DD（从路径或文件名中提取）"""
    # 使用 basename 去掉路径前缀（如 archive/2026-04-12/ 前缀）
    basename = os.path.basename(filename)
    m = re.match(r'^(\d{4}-\d{2}-\d{2})', basename)
    if m:
        return m.group(1)
    return None


def get_title_from_html(filepath):
    """从 HTML 文件中提取标题（h1 或 title）"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        # 优先找 h1（处理嵌套标签情况）
        m = re.search(r'<h1[^>]*>(.*?)</h1>', content)
        if m:
            title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if title:
                return title
        # 其次找 title
        m = re.search(r'<title>([^<]+)</title>', content)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return os.path.splitext(os.path.basename(filepath))[0]


# ── 热门文章：多因子真实热度（2026-10-15 重构）───────────────────
# 旧逻辑的三个问题（2026-10-14 线上实测）：
#   ① 扫 archive/ 副本 + 统计「自己正文的出链数」→ 「热门」名不副实
#      （出链多只说明织网活跃，不说明读者爱看）
#   ② 结果全是 4–6 月旧文 —— archive 副本的内链是历史累积，
#      新文章（9–10 月）内链少，永远进不了热门
#   ③ 混进当前定位的禁区题材（VPS 避坑、Amazon Basics 电池/收纳箱）
# 新逻辑：
#   ① 数据源 = 根目录正位文章全量（archive 副本不再参与）
#   ② 热度分 = 入链数×2.0 + Clarity 真实访问×10.0 + 新近度加成
#   ③ 合规过滤：剔除 TOPIC-POOL §3 禁区题材（VPS横评/纯家居/电池类）
#   ④ 徽章展示真实信号（访问量 / 新发布 / 被引用数），并附一句摘要

# 禁区题材关键词（与 workspace/affiliate-blog/TOPIC-POOL.md §3 禁区清单保持一致）
BANNED_PATTERNS = [
    # VPS / 云服务器横评（当前定位禁区）
    'vps', '云服务器', '主机排行', 'cloud-hosting', 'hosting-review',
    # 纯日用家居（去家居化定位）——含 Amazon Basics 家居线的复数/变体形态
    '空气炸锅', '空气净化', '浴帘', '收纳', '沙发', '床垫', '马桶', '拖把',
    'storage-bin', 'storage-organizer', 'organizer', 'kitchen',
    'batteries', 'battery', 'trash', 'baking', 'reusable-mat', 'food-container',
    'dutch-oven', '珐琅锅', 'measuring-cup', '量杯', '刀具', 'knife',
    '闭眼入',  # Amazon Basics 家居混合线合集（实测摘要含电池/床品/风扇）
    # 跨境电商泛行业（当前定位禁区）
    '跨境电商',
    # 电池类
    '电池',
]

# 壳页 / 合并页 / 已撤回页（标题含这些字样的一律不进热门）
SHELL_PATTERNS = ['已合并', '已撤回', 'moved', '请阅读原版', '本文已']


def _is_banned(filename, title):
    """标题或文件名命中禁区/壳页 → 不进热门。"""
    text = (filename + ' ' + title).lower()
    if any(p in text for p in SHELL_PATTERNS):
        return True
    return any(p in text for p in BANNED_PATTERNS)


def _collect_inbound_links():
    """全站遍历一次，统计每篇文章被多少站内页面链接（入链数）。
    返回 {basename: count}，只统计根目录正位文章之间的 internal-link。
    """
    inbound = {}
    for f in glob.glob(os.path.join(BLOG_DIR, '*.html')):
        base = os.path.basename(f)
        if base.startswith('.') or base in ('index.html', 'index-en.html'):
            continue
        try:
            with open(f, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
        except Exception:
            continue
        # ⚠️ 属性顺序不固定：实测站内两种写法都有（href 在前 / class 在前），
        #    只按一种顺序匹配会漏掉大半（第一版只匹配 class 在前 → 1037 篇只扫到 1 条入链）。
        for tag in re.findall(r'<a\s[^>]*class="internal-link"[^>]*>', content):
            hm = re.search(r'href="([^"]+)"', tag)
            if hm:
                href = os.path.basename(hm.group(1))
                if href and href != base:
                    inbound[href] = inbound.get(href, 0) + 1
    return inbound


def _collect_clarity_traffic():
    """聚合 Clarity 真实访问量，返回 {basename: sessions}。
    数据源：reports/clarity-weekly-summary.json + clarity-daily-*.json。
    ⚠️ Clarity 样本稀疏（日均 30–50 会话、每天仅 top5 页面），
       只作热度信号之一：权重给高（×10）但量级小，不会压倒其他因子。
    """
    traffic = {}
    here = os.path.dirname(os.path.abspath(__file__))
    files = []
    for c in [
        os.path.join(here, 'reports'),                                  # 脚本在 workspace/affiliate-blog/
        os.path.join(here, 'workspace', 'affiliate-blog', 'reports'),   # 脚本在仓库根（workflow 场景）
        os.path.join(here, '..', 'reports'),
    ]:
        if os.path.isdir(c):
            files = sorted(glob.glob(os.path.join(c, 'clarity-daily-*.json')))
            weekly = os.path.join(c, 'clarity-weekly-summary.json')
            if os.path.exists(weekly):
                files.append(weekly)
            if files:
                break
    for p in files:
        try:
            with open(p, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            continue
        entries = data if isinstance(data, list) else [data]
        for e in entries:
            if not isinstance(e, dict):
                continue
            for tp in (e.get('topPages') or []):
                url = (tp.get('url') or '').split('?')[0]
                base = os.path.basename(url)
                if base:
                    traffic[base] = traffic.get(base, 0) + int(tp.get('sessions') or 0)
    return traffic


def get_popular_articles(limit=8, lang='cn'):
    """多因子热度选 TopN（2026-10-15 重构）。

    返回 [(score, date_str, rel_path, title, inbound, clarity, age_days, excerpt)]
    """
    today = datetime.now()
    inbound = _collect_inbound_links()
    traffic = _collect_clarity_traffic()
    articles = []
    seen_slugs = set()

    for f in glob.glob(os.path.join(BLOG_DIR, '*.html')):
        base = os.path.basename(f)
        if base.startswith('.') or base in ('index.html', 'index-en.html', '404.html'):
            continue
        is_en = base.endswith('-en.html')
        if lang == 'en' and not is_en:
            continue
        if lang == 'cn' and is_en:
            continue
        try:
            with open(f, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
        except Exception:
            continue
        m = re.search(r'<h1[^>]*>(.*?)</h1>', content)
        title = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''
        # H1 兜底：剥标签后过短（如只剩「显示器臂」）→ 用 <title> 去站点后缀
        # H1 兜底：过短或关键词罗列（≥3 个逗号）→ 用 <title> 去站点后缀
        comma_count = title.count(',') + title.count('，')
        if len(title) < 8 or comma_count >= 3:
            tm = re.search(r'<title>(.*?)</title>', content, re.S)
            if tm:
                t = re.sub(r'<[^>]+>', '', tm.group(1)).strip()
                t = re.sub(r'\s*[-—|]\s*TechPassive\s*$', '', t).strip()
                if len(t) > len(title):
                    title = t
        if not title:
            title = base
        if _is_banned(base, title):
            continue
        # 同题多版本去重（保留先扫到的一篇）
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}[-_]', '', base)
        slug = re.sub(r'-en\.html$', '', slug)
        slug = re.sub(r'\.html$', '', slug)
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        dm = re.search(r'^(\d{4}-\d{2}-\d{2})', base)
        date_str = dm.group(1) if dm else '2026-01-01'
        inb = inbound.get(base, 0)
        clr = traffic.get(base, 0)
        try:
            pub = datetime.strptime(date_str, '%Y-%m-%d')
            age_days = (today - pub).days
        except ValueError:
            age_days = 999
        recency = 30.0 if age_days <= 30 else (15.0 if age_days <= 60 else 0.0)
        # ⚠️ 入链必须**对数压缩**：实测线性权重下老文 367 入链×2=734 分，
        #    新文上限只有 30 分（新近度）→ 热门永远被 4–6 月老文霸占，
        #    新文章零机会（这正是旧逻辑「结果全是旧文」的根因）。
        #    log10 压缩后 367→62.5 / 76→48.6 / 10→27.6，流量与新近度得以竞争。
        score = math.log10(1 + inb) * 25.0 + clr * 12.0 + recency
        # 摘要：优先 meta description，正文首段兜底
        desc = ''
        md = re.search(r'<meta name="description" content="([^"]*)"', content)
        if md:
            desc = md.group(1)
        if not desc:
            pm = re.search(r'<p[^>]*>(.*?)</p>', content, re.S)
            if pm:
                desc = re.sub(r'<[^>]+>', '', pm.group(1))
        desc = re.sub(r'\s+', ' ', desc).strip()[:80]
        articles.append((score, date_str, base, title, inb, clr, age_days, desc))

    articles.sort(key=lambda x: -x[0])
    return articles[:limit]


def _popular_badges_cn(inb, clr, age_days):
    """中文徽章：最多 2 个，优先展示读者向信号。"""
    badges = []
    if clr > 0:
        badges.append(('clarity', f'👁 {clr} 次访问'))
    if age_days <= 30:
        badges.append(('new', '🆕 新发布'))
    if inb >= 8:
        badges.append(('inbound', f'⭐ {inb} 篇引用'))
    return badges[:2]


def _popular_badges_en(inb, clr, age_days):
    badges = []
    if clr > 0:
        badges.append(('clarity', f'👁 {clr} visits'))
    if age_days <= 30:
        badges.append(('new', '🆕 New'))
    if inb >= 8:
        badges.append(('inbound', f'⭐ {inb} references'))
    return badges[:2]


def _badge_style(kind):
    if kind == 'clarity':
        return ('background:#fff7e6;color:#d46b08;border:1px solid #ffd591;')
    if kind == 'new':
        return ('background:#f6ffed;color:#389e0d;border:1px solid #b7eb8f;')
    return ('background:#e6f7ff;color:#096dd9;border:1px solid #91d5ff;')


def generate_popular_html_cn(limit=8):
    """生成中文热门文章 HTML（多因子真实热度版）"""
    articles = get_popular_articles(limit=limit, lang='cn')
    if not articles:
        return ''
    items_html = []
    for score, date_str, rel_path, title, inb, clr, age_days, desc in articles:
        parts = date_str.split('-')
        date_display = f"{parts[0]}年{int(parts[1])}月{int(parts[2])}日"
        badges = _popular_badges_cn(inb, clr, age_days)
        badge_html = ''.join(
            f'<span style="{_badge_style(k)}padding:2px 6px;border-radius:4px;'
            f'font-size:0.75rem;margin-left:8px;font-weight:500;">{txt}</span>'
            for k, txt in badges)
        excerpt_html = (f'<div class="popular-excerpt">{desc}</div>'
                        if desc else '')
        items_html.append(
            f'            <div class="popular-item">\n'
            f'                <div class="popular-title"><a href="{rel_path}">{title}</a></div>\n'
            f'                <div class="popular-meta">'
            f'                    <span style="color: #666; font-size: 0.85rem;">发布于 {date_display}</span>'
            f'{badge_html}'
            f'                </div>\n'
            f'{excerpt_html}'
            f'            </div>'
        )
    return (
        '    <div class="popular-section">\n'
        '        <h2>&#x1F525; 热门文章</h2>\n'
        '        <div class="popular-grid">\n'
        + '\n'.join(items_html) +
        '\n        </div>\n'
        '    </div>\n\n'
    )


def generate_popular_html_en(limit=8):
    """生成英文热门文章 HTML（多因子真实热度版）"""
    articles = get_popular_articles(limit=limit, lang='en')
    if not articles:
        return ''
    items_html = []
    month_names = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun',
                  '07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}
    for score, date_str, rel_path, title, inb, clr, age_days, desc in articles:
        parts = date_str.split('-')
        date_display = f"{month_names.get(parts[1],parts[1])} {int(parts[2])}, {parts[0]}"
        badges = _popular_badges_en(inb, clr, age_days)
        badge_html = ''.join(
            f'<span style="{_badge_style(k)}padding:2px 6px;border-radius:4px;'
            f'font-size:0.75rem;margin-left:8px;font-weight:500;">{txt}</span>'
            for k, txt in badges)
        excerpt_html = (f'<div class="popular-excerpt">{desc}</div>'
                        if desc else '')
        items_html.append(
            f'            <div class="popular-item">\n'
            f'                <div class="popular-title"><a href="{rel_path}">{title}</a></div>\n'
            f'                <div class="popular-meta">'
            f'                    <span style="color: #666; font-size: 0.85rem;">Published {date_display}</span>'
            f'{badge_html}'
            f'                </div>\n'
            f'{excerpt_html}'
            f'            </div>'
        )
    return (
        '    <div class="popular-section">\n'
        '        <h2>&#x1F525; Popular Articles</h2>\n'
        '        <div class="popular-grid">\n'
        + '\n'.join(items_html) +
        '\n        </div>\n'
        '    </div>\n\n'
    )


def generate_index(articles, header, footer, lang='cn'):
    """生成索引 HTML，动态注入热门文章模块"""
    # 替换占位符为动态生成的热门文章
    placeholder = '{{POPULAR_CN}}' if lang == 'cn' else '{{POPULAR_EN}}'
    popular_html = generate_popular_html_cn() if lang == 'cn' else generate_popular_html_en()
    header = header.replace(placeholder, popular_html)
    # 生成文章列表
    items = []
    for date, filename, title in articles:
        href = os.path.basename(filename)  # 物理文件在根目录，href 必须是 basename
        if lang == 'cn':
            items.append(
                f'        <li class="post-item">\n'
                f'            <h2 class="post-title"><a href="{href}">{title}</a></h2>\n'
                f'            <p class="post-meta">发布于 {date}</p>\n'
                f'        </li>'
            )
        else:
            items.append(
                f'        <li class="post-item">\n'
                f'            <h2 class="post-title"><a href="{href}">{title}</a></h2>\n'
                f'            <p class="post-meta">Published {date}</p>\n'
                f'        </li>'
            )
    return header + '\n'.join(items) + '\n' + footer


def generate_sitemap(articles, today):
    """生成 sitemap XML — 极简格式，仅保留 Google 实际读取的 <loc> + <lastmod>"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
             '  <url>',
             '    <loc>https://yaohehe.github.io/</loc>',
             f'    <lastmod>{today}</lastmod>',
             '  </url>',
             '  <url>',
             '    <loc>https://yaohehe.github.io/index-en.html</loc>',
             f'    <lastmod>{today}</lastmod>',
             '  </url>']
    for date, filename, title in articles:
        url = f'https://yaohehe.github.io/{os.path.basename(filename)}'
        lines.append('  <url>')
        lines.append(f'    <loc>{url}</loc>')
        lines.append(f'    <lastmod>{date}</lastmod>')
        lines.append('  </url>')
    lines.append('</urlset>')
    return '\n'.join(lines) + '\n'


def main():
    today = datetime.now().strftime('%Y-%m-%d')

    # 扫描所有 HTML 文件（去重：同一文件名优先使用 archive/ 版本）
    # 根因：同时扫描 root 和 archive/ 时，未追踪的根目录文件会生成错误链接
    # 解决：同一 basename 文件同时存在于 root 和 archive 时，优先使用 archive 版本（规范发布位置）
    # 防护：检测根目录孤立 HTML 文件（不在 git 追踪中）并报警，防止 publish-articles.py 复制残留
    import collections
    root_files = glob.glob(os.path.join(BLOG_DIR, '*.html'))
    archive_files = glob.glob(os.path.join(BLOG_DIR, 'archive', '**', '*.html'), recursive=True)

    # 检测根目录孤立文件（不在 git 追踪的 HTML，排除索引文件本身）
    import subprocess
    r = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '-I', '*.html',
                        '--ignore-case'], capture_output=True, text=True, cwd=BLOG_DIR)
    orphaned_html = [f.strip() for f in r.stdout.splitlines() if f.strip().endswith('.html')]
    if orphaned_html:
        print(f"⚠️ 检测到 {len(orphaned_html)} 个根目录孤立 HTML 文件（不在 git 追踪中），已从索引扫描中排除:")
        for f in orphaned_html[:5]:
            print(f"  排除: {f}")
        if len(orphaned_html) > 5:
            print(f"  ... 还有 {len(orphaned_html) - 5} 个")

    # basename -> filepath, archive 版本优先
    file_by_basename = {}
    for f in archive_files:
        bn = os.path.basename(f)
        if bn not in file_by_basename:
            file_by_basename[bn] = f
    for f in root_files:
        bn = os.path.basename(f)
        if bn in orphaned_html:
            continue  # 跳过孤立文件，不加入索引
        if bn not in file_by_basename:
            file_by_basename[bn] = f
    
    html_files = [f for bn, f in file_by_basename.items() if bn not in (
        'index.html', 'index-en.html', 'sitemap.xml'
    )]

    cn_articles = []
    en_articles = []

    for filepath in html_files:
        filename = filepath.replace(BLOG_DIR + '/', '')  # keep archive/ prefix
        date = get_date_from_filename(filename)
        if not date:
            continue
        title = get_title_from_html(filepath)
        if filename.endswith('-en.html') or '-en.' in filename:
            en_articles.append((date, filename, title))
        else:
            cn_articles.append((date, filename, title))

    # 按日期降序排序
    cn_articles.sort(key=lambda x: x[0], reverse=True)
    en_articles.sort(key=lambda x: x[0], reverse=True)
    all_articles = cn_articles + en_articles

    print(f"📊 扫描完成：{len(cn_articles)} 篇中文文章，{len(en_articles)} 篇英文文章")

    # 生成 index.html
    index_cn = generate_index(cn_articles, INDEX_HEADER_CN, INDEX_FOOTER, lang='cn')
    with open(os.path.join(BLOG_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_cn)
    print(f"✅ index.html 已更新（{len(cn_articles)} 篇）")

    # 生成 index-en.html
    index_en = generate_index(en_articles, INDEX_HEADER_EN, INDEX_FOOTER, lang='en')
    with open(os.path.join(BLOG_DIR, 'index-en.html'), 'w', encoding='utf-8') as f:
        f.write(index_en)
    print(f"✅ index-en.html 已更新（{len(en_articles)} 篇）")

    # 生成 sitemap.xml
    sitemap = generate_sitemap(all_articles, today)
    with open(os.path.join(BLOG_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print(f"✅ sitemap.xml 已更新（{len(all_articles)} 篇）")

    print(f"📅 更新日期：{today}")


if __name__ == '__main__':
    main()
