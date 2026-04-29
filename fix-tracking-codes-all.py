#!/usr/bin/env python3
"""
全站统计代码修复脚本
修复所有缺失 GA / Clarity / 百度统计 的文章页
"""
import re
import os
import glob

BLOG_DIR = "/root/.openclaw/workspace/yaohehe.github.io"

GA_CODE = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-YQZQY6XDXN"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-YQZQY6XDXN');
</script>'''

CLARITY_CODE = '''<!-- Microsoft Clarity -->
<script type="text/javascript">
(function(c,l,a,r,i,t,y){
c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
})(window, document, "clarity", "script", "wdy3avd2j9");
</script>'''

BAIDU_CODE = '''<!-- 百度统计 -->
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?5217d6a8f8299c6b114858ac6e719e2b";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
</script>'''

GA_ID = "G-YQZQY6XDXN"
CLARITY_ID = "wdy3avd2j9"
BAIDU_ID = "5217d6a8f8299c6b114858ac6e719e2b"

# 静态页面（无<head>）不处理
STATIC_KW = ['contact/', 'privacy-policy/', 'about/', 'disclaimer/', 'google12386b896297faca.html']


def needs_code(content, code_id):
    """检查文件是否缺失某个统计代码"""
    return code_id not in content


def add_codes_to_head(html):
    """向HTML文件<head>后添加缺失的统计代码，返回是否修改"""
    if '</head>' not in html.lower():
        return html, False

    head_end = re.search(r'</head>', html, re.IGNORECASE)
    pos = head_end.start()
    modified = False

    # GA
    if needs_code(html, GA_ID):
        html = html[:pos] + GA_CODE + '\n' + html[pos:]
        pos += len(GA_CODE) + 1
        modified = True

    # Clarity
    if needs_code(html, CLARITY_ID):
        html = html[:pos] + CLARITY_CODE + '\n' + html[pos:]
        pos += len(CLARITY_CODE) + 1
        modified = True

    # Baidu
    if needs_code(html, BAIDU_ID):
        html = html[:pos] + BAIDU_CODE + '\n' + html[pos:]
        modified = True

    return html, modified


def main():
    files_fixed = {'ga': 0, 'clarity': 0, 'baidu': 0, 'skipped': 0}
    files_total = 0

    html_files = glob.glob(os.path.join(BLOG_DIR, '**', '*.html'), recursive=True)
    html_files += glob.glob(os.path.join(BLOG_DIR, '*.html'))

    for fpath in set(html_files):
        # 跳过静态页面
        if any(kw in fpath for kw in STATIC_KW):
            continue
        # 跳过索引页（另有脚本处理）
        if fpath.endswith('index.html') or fpath.endswith('index-en.html'):
            continue

        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                html = f.read()
        except Exception:
            continue

        files_total += 1

        # 检查缺失情况
        miss_ga = needs_code(html, GA_ID)
        miss_clar = needs_code(html, CLARITY_ID)
        miss_baidu = needs_code(html, BAIDU_ID)

        if not (miss_ga or miss_clar or miss_baidu):
            continue

        # 处理无<head>的文件（早期文章）
        if '</head>' not in html.lower():
            files_fixed['skipped'] += 1
            continue

        new_html, modified = add_codes_to_head(html)

        if modified:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_html)
            msgs = []
            if miss_ga: msgs.append('GA')
            if miss_clar: msgs.append('Clarity')
            if miss_baidu: msgs.append('Baidu')
            print(f"  ✅ {os.path.basename(fpath)}: 补全 {', '.join(msgs)}")
            if miss_ga: files_fixed['ga'] += 1
            if miss_clar: files_fixed['clarity'] += 1
            if miss_baidu: files_fixed['baidu'] += 1

    print(f"\n📊 统计: 共扫描 {files_total} 个文件，修复 {sum(v for k,v in files_fixed.items() if k!='skipped')} 个文件")
    print(f"   GA: +{files_fixed['ga']} | Clarity: +{files_fixed['clarity']} | Baidu: +{files_fixed['baidu']}")
    if files_fixed['skipped']:
        print(f"   跳过（无<head>）: {files_fixed['skipped']} 个")


if __name__ == "__main__":
    main()
