#!/usr/bin/env python3
"""
IndexNow Submission Script
Submits URLs to Bing/Yandex via IndexNow protocol for fast indexing.
Key: cc8394e322884ba58f5db3acfcf3e2a7
KeyLocation: https://yaohehe.github.io/cc8394e322884ba58f5db3acfcf3e2a7.txt
"""
import sys, json, requests, os, base64, subprocess, datetime

REPO = 'yaohehe/yaohehe.github.io'
KEY = 'cc8394e322884ba58f5db3acfcf3e2a7'
KEY_LOCATION = 'https://yaohehe.github.io/cc8394e322884ba58f5db3acfcf3e2a7.txt'
HOST = 'yaohehe.github.io'

INDEXNOW_ENDPOINTS = [
    'https://api.indexnow.org/IndexNow',
    'https://www.bing.com/IndexNow',
]

def get_github_token():
    url = subprocess.run(['git', 'config', '--get', 'remote.origin.url'],
                         capture_output=True, text=True).stdout.strip()
    s = url.index('x-access-token:') + len('x-access-token:')
    e = url.index('@')
    return url[s:e]

def get_latest_articles(n=10):
    """Get N most recent article filenames from local HTML files (not in archive/)."""
    html_dir = '/root/.openclaw/workspace/yaohehe.github.io'
    files = []
    for f in os.listdir(html_dir):
        if f.endswith('.html') and not f.startswith('index'):
            mtime = os.path.getmtime(os.path.join(html_dir, f))
            files.append((mtime, f))
    files.sort(reverse=True)
    return [f for _, f in files[:n]]

def get_local_articles(n=10):
    """Get recent articles from root dir (published, not archive/)."""
    html_dir = '/root/.openclaw/workspace/yaohehe.github.io'
    files = []
    for f in os.listdir(html_dir):
        if f.endswith('.html') and not f.startswith('index') and not f.startswith('archive'):
            mtime = os.path.getmtime(os.path.join(html_dir, f))
            files.append((mtime, f))
    files.sort(reverse=True)
    return [f for _, f in files[:n]]

def submit_urls(url_list, verbose=True):
    """Submit URLs via IndexNow protocol."""
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": url_list
    }
    
    results = []
    for endpoint in INDEXNOW_ENDPOINTS:
        try:
            r = requests.post(endpoint, json=payload, timeout=15,
                            headers={'Content-Type': 'application/json; charset=utf-8'})
            if verbose:
                print(f"  {endpoint}: {r.status_code}")
            results.append((endpoint, r.status_code, r.text[:100]))
        except Exception as e:
            if verbose:
                print(f"  {endpoint}: ERROR - {e}")
            results.append((endpoint, 'ERROR', str(e)))
    
    return results

def main():
    # Mode: submit last N articles or specific files
    if len(sys.argv) > 1 and sys.argv[1] == '--recent':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        articles = get_local_articles(n)
        print(f"📡 IndexNow: Submitting {len(articles)} recent articles...")
    elif len(sys.argv) > 1 and sys.argv[1] == '--all':
        # Submit sitemap URLs
        sitemap_path = '/root/.openclaw/workspace/yaohehe.github.io/sitemap.xml'
        if os.path.exists(sitemap_path):
            import re
            with open(sitemap_path) as f:
                content = f.read()
            urls = re.findall(r'<loc>([^<]+)</loc>', content)
            articles = [u.replace('https://yaohehe.github.io/', '') for u in urls if u.endswith('.html') and 'archive' not in u]
            print(f"📡 IndexNow: Submitting all {len(articles)} sitemap URLs...")
        else:
            print("❌ sitemap.xml not found")
            return
    else:
        # Submit specific files
        articles = sys.argv[1:] if len(sys.argv) > 1 else []
        print(f"📡 IndexNow: Submitting {len(articles)} article(s)...")

    if not articles:
        print("⚠️ No articles to submit")
        return

    base_url = f'https://{HOST}'
    url_list = [f'{base_url}/{a}' for a in articles]
    
    print(f"\nURLs to submit:")
    for u in url_list:
        print(f"  {u}")
    print()
    
    results = submit_urls(url_list)
    
    # Summary
    success = any(r[1] == 200 for r in results)
    if success:
        print(f"\n✅ Submitted {len(articles)} URL(s) successfully")
    else:
        print(f"\n⚠️ Submission completed but no 200 response")
        for endpoint, code, txt in results:
            print(f"   {endpoint}: {code} - {txt}")

if __name__ == '__main__':
    main()