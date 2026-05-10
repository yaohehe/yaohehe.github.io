#!/usr/bin/env python3
"""
fix-meta-descriptions.py
修复所有 HTML 文件的 meta description（目标 150-160 字符）
"""
import re, os, base64, subprocess, time

YAOHEHE_DIR = '/root/.openclaw/workspace/yaohehe.github.io'
REPO = 'yaohehe/yaohehe.github.io'

def get_token():
    url = subprocess.run(['git', 'config', '--get', 'remote.origin.url'],
                         capture_output=True, text=True).stdout.strip()
    s = url.index('x-access-token:') + len('x-access-token:')
    e = url.index('@')
    return url[s:e]

TOKEN = get_token()
HEADERS = {'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json'}

def get_file_sha(filepath):
    import requests
    url = f'https://api.github.com/repos/{REPO}/contents/{filepath}'
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json()['sha']
    return None

def push_file(filepath, content, message=None):
    import requests
    url = f'https://api.github.com/repos/{REPO}/contents/{filepath}'
    if message is None:
        message = f'auto: fix meta description ({len(content)} bytes)'
    # Handle both str and bytes input
    content_bytes = content.encode('utf-8') if isinstance(content, str) else content
    data = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode()
    }
    sha = get_file_sha(filepath)
    if sha:
        data["sha"] = sha
    try:
        r = requests.put(url, headers=HEADERS, json=data, timeout=30)
        if r.status_code in (200, 201):
            return True, r.status_code
        else:
            return False, r.status_code
    except Exception as e:
        return False, str(e)

def extract_content(html_content):
    """Extract title and first paragraph for description generation."""
    title_m = re.search(r'<title>([^<]+)</title>', html_content)
    title = title_m.group(1) if title_m else ''
    
    # Get first paragraph text (skip header/metas)
    p_m = re.search(r'<p[^>]*>([^<]{30,})</p>', html_content)
    first_p = p_m.group(1) if p_m else ''
    
    return title, first_p

def generate_description(title, first_p, category=''):
    """Generate a 150-160 char meta description."""
    # Clean up title
    title_clean = re.sub(r'\[.*?\]|\(.*?\)|——.*|：.*', '', title).strip()
    
    # Build base from title + context
    if category == 'amazon-basics':
        base = f"{title_clean}。深度横评，实测数据，帮你选出真正值得买的产品。含价格对比和购买建议。"
    elif category in ('wordpress', 'wp'):
        base = f"{title_clean}。含完整步骤、配置指南和实战技巧，助你快速搭建专业网站。"
    elif category in ('ollama', 'ai', 'lm-studio', 'deepseek', 'jan'):
        base = f"{title_clean}。实测对比，帮你选择最适合本地运行的大模型工具。"
    elif category in ('vps', 'cloud', 'server', 'devops', 'docker'):
        base = f"{title_clean}。实战经验，性能测试，帮你选择最合适的云服务器和配置方案。"
    elif category == 'affiliate':
        base = f"{title_clean}。被动收入实战技巧，帮你用内容创作建立可持续收益流。"
    else:
        base = f"{title_clean}。实战经验，深度分析，帮你做出明智技术决策。"
    
    # Trim to 150-160 chars
    if len(base) > 160:
        base = base[:157] + '...'
    elif len(base) < 120:
        # Extend
        extras = {
            'amazon-basics': '附真实评测和购买建议，帮你省时省钱不踩坑。',
            'wordpress': '新手友好，步骤详细，2026年最新实战经验总结。',
            'ai': '含实测数据和使用场景分析，帮你选择最适合的工具。',
            'vps': '含配置步骤和成本对比，2026年最新云服务器选择指南。',
            'affiliate': '附平台选择技巧和内容策略，帮你建立被动收入。',
        }
        cat_key = next((k for k in extras if k in category), 'general')
        ext = extras.get(cat_key, '含详细步骤和实战经验，帮你做出明智选择。')
        base = base.rstrip('。') + '。' + ext
    
    # Final trim
    if len(base) > 160:
        base = base[:157] + '...'
    
    return base

def get_category(filename):
    """Infer category from filename."""
    f = filename.lower()
    if 'amazon-basics' in f or ('amazon' in f and 'basic' in f):
        return 'amazon-basics'
    elif 'wordpress' in f:
        return 'wordpress'
    elif any(x in f for x in ['ollama', 'lm-studio', 'deepseek', 'jan ai', 'local-ai', 'agent', 'glm-']):
        return 'ai'
    elif any(x in f for x in ['vps', 'cloud-server', 'digitalocean', 'vultr', 'server', 'devops', 'docker', 'nginx', 'github-actions']):
        return 'vps'
    elif any(x in f for x in ['affiliate', '联盟营销', '被动收入', 'monetiz']):
        return 'affiliate'
    elif any(x in f for x in ['woocommerce', 'shopify', '跨境', 'ecommerce']):
        return 'ecommerce'
    elif any(x in f for x in ['n8n', 'automation', 'zapier', 'make']):
        return 'automation'
    else:
        return 'general'

def fix_file(filepath):
    """Fix meta description for a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fname = os.path.basename(filepath)
    category = get_category(fname)
    
    # Extract current title and content
    title, first_p = extract_content(content)
    
    # Generate new description
    new_desc = generate_description(title, first_p, category)
    
    # Replace existing meta description
    if '<meta name="description" content="' in content:
        new_content = re.sub(
            r'<meta name="description" content="[^"]*"',
            f'<meta name="description" content="{new_desc}"',
            content
        )
    else:
        # Insert after description tag or in head
        new_content = content.replace('<head>', f'<head>\n    <meta name="description" content="{new_desc}">', 1)
    
    return new_content, new_desc, len(new_desc)

def main():
    os.chdir(YAOHEHE_DIR)
    
    # Get all root HTML files (not index pages, not archive/)
    all_files = []
    for f in os.listdir('.'):
        if f.endswith('.html') and not f.startswith('index') and 'archive' not in f:
            all_files.append(f)
    
    print(f"Total HTML files: {len(all_files)}")
    
    # Check meta desc lengths
    short_files = []
    for fname in all_files:
        with open(fname) as f:
            content = f.read()
        m = re.search(r'<meta name="description" content="([^"]+)"', content)
        if m and len(m.group(1)) < 120:
            short_files.append((fname, len(m.group(1)), m.group(1)))
    
    print(f"Short meta desc files: {len(short_files)}")
    
    # Fix in batches of 20
    batch_size = 20
    success = 0
    failed = []
    
    for i in range(0, len(short_files), batch_size):
        batch = short_files[i:i+batch_size]
        print(f"\n--- Batch {i//batch_size + 1}: {len(batch)} files ---")
        
        for fname, old_len, old_desc in batch:
            try:
                new_content, new_desc, new_len = fix_file(fname)
                
                ok, code = push_file(fname, new_content,
                                     f'auto: fix meta description ({new_len} chars)')
                
                if ok:
                    print(f"  ✅ {fname}: {old_len} → {new_len} chars")
                    success += 1
                else:
                    print(f"  ❌ {fname}: {code}")
                    failed.append((fname, code))
                
                time.sleep(0.5)  # Rate limit buffer
                
            except Exception as e:
                print(f"  ❌ {fname}: {e}")
                failed.append((fname, str(e)))
        
        if i + batch_size < len(short_files):
            print(f"  Sleeping 3s between batches...")
            time.sleep(3)
    
    print(f"\n✅ Fixed: {success}/{len(short_files)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for fname, code in failed[:5]:
            print(f"   {fname}: {code}")

if __name__ == '__main__':
    main()