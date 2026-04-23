#!/usr/bin/env python3
"""
价格真实性验证器 v3
检测 cn.txt/en.txt 中的价格是否为真实搜索结果
免费方案（curl）优先，失败时使用 browser.cash（备用）
"""
import re
import os
import sys
import subprocess
import json
from datetime import datetime
from html.parser import HTMLParser

TMP_DIR = "/tmp/article-gen"
MEMORY_DIR = os.path.expanduser("~/self-improving/domains")

# browser.cash 配置（仅当免费方案失败时使用）
BROWSER_CASH_KEY = None  # 从 clawdbot config 读取

# 可疑价格模式（可能是占位符或 hallucinate）
SUSPICIOUS_PRICE_PATTERNS = [
    (r'\$\s*\d+\.?\d*(?!\w)', '美元价格'),
    (r'\$\s*\d+', '美元价格'),
    (r'人民币\s*¥?\s*\d+', '人民币价格'),
    (r'¥\s*\d+', '人民币价格'),
    (r'USD\s*\$?\s*\d+', 'USD价格'),
    (r'CNY\s*¥?\s*\d+', 'CNY价格'),
    (r'\d+%\s*折扣', '折扣百分比'),
    (r'省\s*\d+%|优惠\s*\d+%', '优惠百分比'),
    (r'/?\s*年|/?\s*月|/?\s*日|/?\s*小时', '时长定价'),
]

# 可信价格指示器
TRUST_INDICATORS = [
    '建议自行确认', '搜索来源', 'asin=', 'amazon.com/s',
    'tag=techpassive', '截至', '根据',
]

# 稳定品类（价格相对固定）
STABLE_CATEGORIES = [
    'VPS', '云服务器', '虚拟主机', '域名', 'Cloudflare', 'CDN',
]


class PriceExtractor(HTMLParser):
    """从 HTML 中提取价格"""
    def __init__(self):
        super().__init__()
        self.prices = []
        self.in_price_context = False
        
    def handle_starttag(self, tag, attrs):
        attrs_str = str(attrs).lower()
        if any(k in attrs_str for k in ['price', 'amount', 'cost', 'data-a-color']):
            self.in_price_context = True
        
    def handle_data(self, data):
        if self.in_price_context:
            data = data.strip()
            if data:
                found = re.findall(r'[\$¥][\d,]+\.?\d*', data)
                self.prices.extend(found)
                found2 = re.findall(r'[\d,]+\.\d{2}\s*(?:USD|CNY|JPY|EUR)', data)
                self.prices.extend(found2)
        self.in_price_context = False


def get_browser_cash_key():
    """从 clawdbot config 获取 browser.cash API key"""
    global BROWSER_CASH_KEY
    if BROWSER_CASH_KEY:
        return BROWSER_CASH_KEY
    
    try:
        result = subprocess.run(
            ['clawdbot', 'config', 'get', 'skills.entries.browser-cash.apiKey'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            BROWSER_CASH_KEY = result.stdout.strip()
            return BROWSER_CASH_KEY
    except:
        pass
    return None


def extract_urls(text):
    """从文本中提取产品链接"""
    urls = []
    
    for match in re.finditer(r'amazon\.com/[^\s"]*?/dp/([A-Z0-9]{10})', text, re.IGNORECASE):
        asin = match.group(1)
        url = f'https://www.amazon.com/dp/{asin}?tag=techpassive-20'
        if url not in urls:
            urls.append(url)
    
    for match in re.finditer(r'amazon\.com/dp/([A-Z0-9]{10})', text, re.IGNORECASE):
        asin = match.group(1)
        url = f'https://www.amazon.com/dp/{asin}?tag=techpassive-20'
        if url not in urls:
            urls.append(url)
    
    for match in re.finditer(r'https?://[^\s<>"\']+', text):
        url = match.group(0)
        if any(domain in url.lower() for domain in ['amazon.com', 'digitalocean', 'vultr.com', 'linode']):
            if url not in urls:
                urls.append(url)
    
    return urls[:5]


def fetch_price_curl(url):
    """用 curl 抓取页面提取价格（免费方案）"""
    try:
        cmd = [
            'curl', '-s', '-L', '--max-time', '10',
            '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        html = result.stdout
        
        if not html or len(html) < 100:
            return None, "页面内容为空"
        
        parser = PriceExtractor()
        try:
            parser.feed(html)
        except:
            pass
        
        prices = parser.prices
        
        html_lower = html.lower()
        price_zones = re.findall(r'(?:price|amount|cost)[^<]{0,200}', html_lower)
        for zone in price_zones:
            found = re.findall(r'[\$¥][\d,]+\.?\d*', zone)
            prices.extend(found)
        
        seen = set()
        unique_prices = []
        for p in prices:
            p_clean = p.replace('$', '').replace('¥', '').replace(',', '').strip()
            if p_clean and p_clean not in seen:
                seen.add(p_clean)
                unique_prices.append(p)
        
        if unique_prices:
            return unique_prices[:3], None
        else:
            return None, "未找到价格"
            
    except subprocess.TimeoutExpired:
        return None, "抓取超时"
    except Exception as e:
        return None, f"抓取失败"


def fetch_price_browser_cash(url, timeout=60):
    """用 browser.cash 抓取页面提取价格（备用方案，约$0.0015/次）"""
    api_key = get_browser_cash_key()
    if not api_key:
        return None, "browser.cash 未配置"
    
    session = None
    browser = None
    try:
        # 1. 创建 session
        create_cmd = [
            'curl', '-s', '-X', 'POST',
            'https://api.browser.cash/v1/browser/session',
            '-H', f'Authorization: Bearer {api_key}',
            '-H', 'Content-Type: application/json',
            '-d', '{"country": "US", "windowSize": "800x600"}'
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None, "browser.cash session 创建失败"
        
        session_data = json.loads(result.stdout)
        session_id = session_data.get('sessionId')
        cdp_url = session_data.get('cdpUrl')
        
        if not session_id or not cdp_url:
            return None, "browser.cash session 无效"
        
        session = session_id
        
        # 2. 用 puppeteer-core 连接并抓取
        script = f'''
const puppeteer = require('puppeteer-core');
(async () => {{
    const browser = await puppeteer.connect({{
        browserWSEndpoint: '{cdp_url}',
        timeout: 30000
    }});
    const pages = await browser.pages();
    const page = pages[0] || await browser.newPage();
    await page.goto('{url}', {{ waitUntil: 'domcontentloaded', timeout: 20000 }});
    await new Promise(r => setTimeout(r, 3000));
    
    // 提取价格
    const result = await page.evaluate(() => {{
        const selectors = [
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price-whole',
            '#corePrice_feature_div .a-price .a-offscreen'
        ];
        for (const sel of selectors) {{
            const el = document.querySelector(sel);
            if (el) return {{ price: el.textContent.trim(), selector: sel }};
        }}
        return {{ price: null, selector: null }};
    }});
    
    console.log(JSON.stringify(result));
    await browser.disconnect();
}})();
'''
        
        script_path = '/tmp/bc-scrape.js'
        with open(script_path, 'w') as f:
            f.write(script)
        
        # 设置 NODE_PATH
        env = os.environ.copy()
        env['NODE_PATH'] = os.path.expanduser('~/clawd/node_modules')
        
        result = subprocess.run(
            ['node', script_path],
            capture_output=True, text=True, timeout=timeout,
            env=env
        )
        
        try:
            data = json.loads(result.stdout.strip())
            if data.get('price'):
                return [data['price']], None
            return None, "browser.cash 未找到价格"
        except:
            return None, f"browser.cash 解析失败: {result.stdout[:100]}"
        
    except subprocess.TimeoutExpired:
        return None, "browser.cash 超时"
    except Exception as e:
        return None, f"browser.cash 错误: {str(e)[:50]}"
    finally:
        # 3. 停止 session
        if session:
            try:
                subprocess.run(
                    ['curl', '-s', '-X', 'DELETE',
                     f'https://api.browser.cash/v1/browser/session?sessionId={session}',
                     '-H', f'Authorization: Bearer {api_key}'],
                    timeout=5
                )
            except:
                pass


def fetch_price(url, use_browser_cash_fallback=True):
    """抓取页面提取价格，curl 失败时自动使用 browser.cash"""
    # 先尝试 curl（免费）
    prices, error = fetch_price_curl(url)
    if prices:
        return prices, 'curl', None
    
    # curl 失败，检查是否使用 browser.cash
    if use_browser_cash_fallback:
        api_key = get_browser_cash_key()
        if api_key:
            print(f"       🔄 curl 失败，使用 browser.cash 备用...")
            prices, error = fetch_price_browser_cash(url)
            if prices:
                return prices, 'browser.cash', None
    
    return None, 'curl', error


def check_price_authenticity(text, lang='cn'):
    """检查文本中的价格是否可疑"""
    warnings = []
    lines = text.split('\n')
    
    has_trust_indicator = any(
        indicator.lower() in text.lower() for indicator in TRUST_INDICATORS
    )
    
    is_stable_category = any(
        cat.lower() in text.lower()
        for cat in STABLE_CATEGORIES
    )
    
    for line_num, line in enumerate(lines, 1):
        for pattern, price_type in SUSPICIOUS_PRICE_PATTERNS:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                price_str = match.group(0)
                
                if any(decl in line for decl in ['建议自行确认', '建议您自行', '请以实际为准']):
                    continue
                
                context_start = max(0, line_num - 3)
                context_end = min(len(lines), line_num + 2)
                context = '\n'.join(lines[context_start:context_end])
                
                has_local_trust = any(
                    indicator.lower() in context.lower()
                    for indicator in TRUST_INDICATORS
                )
                
                if has_local_trust or has_trust_indicator or is_stable_category:
                    continue
                
                warnings.append({
                    'line': line_num,
                    'price': price_str,
                    'type': price_type,
                    'context': line.strip()[:80]
                })
    
    return warnings


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 价格真实性验证 v3")
    
    # 检查 browser.cash 配置
    bc_key = get_browser_cash_key()
    if bc_key:
        print(f"  ✅ browser.cash 已配置（备用方案）")
    else:
        print(f"  ⚠️ browser.cash 未配置（仅使用免费方案）")
    
    cn_file = f"{TMP_DIR}/cn.txt"
    en_file = f"{TMP_DIR}/en.txt"
    
    all_warnings = []
    url_verification_results = []
    total_browser_cash_used = 0
    
    for txt_file, lang in [(cn_file, 'cn'), (en_file, 'en')]:
        if not os.path.exists(txt_file):
            print(f"  ⏭️  {lang}.txt 不存在，跳过")
            continue
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        warnings = check_price_authenticity(content, lang)
        
        if warnings:
            print(f"  ⚠️  {lang}.txt: 发现 {len(warnings)} 处可疑价格")
            for w in warnings[:3]:
                print(f"     第{w['line']}行: {w['price']} ({w['type']})")
            if len(warnings) > 3:
                print(f"     ... 还有 {len(warnings) - 3} 处")
            all_warnings.append((lang, warnings))
            
            # 提取 URL 进行验证
            urls = extract_urls(content)
            if urls:
                print(f"  🔗 发现 {len(urls)} 个产品链接，验证价格...")
                for url in urls:
                    short_url = url[:60] + '...' if len(url) > 60 else url
                    print(f"     → {short_url}")
                    
                    prices, method, error = fetch_price(url)
                    
                    if prices:
                        print(f"       ✅ [{method}] 抓取到: {', '.join(prices[:2])}")
                        if method == 'browser.cash':
                            total_browser_cash_used += 1
                        url_verification_results.append({
                            'url': url,
                            'found_prices': prices,
                            'method': method,
                            'error': None
                        })
                    else:
                        print(f"       ⚠️ {error}")
                        url_verification_results.append({
                            'url': url,
                            'found_prices': None,
                            'method': method,
                            'error': error
                        })

        # ASIN 可用性检查（验证推广链接是否有效）
        asin_results = check_asins_in_article(txt_file, lang)
        invalid_asins = [(a, s) for a, v, s in asin_results if not v]
        if invalid_asins:
            print(f"  ❌ {lang}.txt: 发现 {len(invalid_asins)} 个无效 ASIN（产品已下架或不可用）")
            for asin, status in invalid_asins:
                print(f"     ❌ ASIN {asin} (HTTP {status}) → https://www.amazon.com/dp/{asin}")
                url_verification_results.append({
                    'url': f'https://www.amazon.com/dp/{asin}',
                    'found_prices': None,
                    'method': 'asin_check',
                    'error': f'ASIN无效 (HTTP {status})'
                })
        else:
            print(f"  ✅ {lang}.txt: ASIN 验证通过')
    
    # 输出总结
    print(f"\n{'='*50}")
    
    if total_browser_cash_used > 0:
        est_cost = total_browser_cash_used * 0.0015  # 约$0.0015/次
        print(f"💰 browser.cash 消耗: {total_browser_cash_used} 次，估算成本 ~${est_cost:.4f}")
    
    if all_warnings or url_verification_results:
        print(f"📊 验证摘要:")
        if all_warnings:
            total_warn = sum(len(w) for _, w in all_warnings)
            print(f"   - 可疑价格: {total_warn} 处")
        if url_verification_results:
            success = sum(1 for r in url_verification_results if r['found_prices'])
            print(f"   - URL验证: {success}/{len(url_verification_results)} 成功")
        
        print(f"\n💡 建议:")
        print(f"   - 如果价格来自真实搜索，建议添加「建议自行确认」声明")
        print(f"   - 亚马逊推广文请确保 ASIN 已通过搜索验证")
        print(f"   - 稳定品类（VPS/CDN）可忽略此警告")
        
        # 记录到 memory
        os.makedirs(MEMORY_DIR, exist_ok=True)
        log_file = f"{MEMORY_DIR}/price-warnings.log"
        with open(log_file, 'a') as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 价格验证\n")
            for lang, warns in all_warnings:
                f.write(f"  {lang}.txt: {len(warns)} 处可疑价格\n")
            for r in url_verification_results:
                if r['found_prices']:
                    f.write(f"  ✅ [{r['method']}] {r['url'][:50]}: {', '.join(r['found_prices'][:2])}\n")
                else:
                    f.write(f"  ⚠️ {r['url'][:50]}: {r['error']}\n")
        
        print(f"\n⚠️  价格验证有警告，流程继续（不阻断）")
    else:
        print(f"✅ 价格真实性验证通过")
    
    sys.exit(0)


if __name__ == '__main__':
    main()


def check_asin_availability(asin):
    """检查 ASIN 是否有效（HTTP 200）"""
    url = f"https://www.amazon.com/dp/{asin}"
    try:
        result = subprocess.run(
            ['curl', '-so', '/dev/null', '-w', '%{http_code}',
             '--max-time', '8',
             '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
             url],
            capture_output=True, text=True, timeout=12
        )
        return result.stdout.strip() == '200', result.stdout.strip()
    except:
        return False, 'error'


def extract_asins(text):
    """从文本中提取所有 ASIN"""
    asins = set()
    for m in re.finditer(r'amazon\.com/[^/]*/dp/([A-Z0-9]{10})', text, re.IGNORECASE):
        asins.add(m.group(1))
    return list(asins)


def check_asins_in_article(txt_file, lang):
    """检查草稿中 ASIN 的可用性"""
    if not os.path.exists(txt_file):
        return []

    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    asins = extract_asins(content)
    if not asins:
        return []

    results = []
    for asin in asins:
        valid, status = check_asin_availability(asin)
        results.append((asin, valid, status))

    invalid = [(a, s) for a, v, s in results if not v]
    return results
