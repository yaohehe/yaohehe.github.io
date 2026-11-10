#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 SEO postprocess for GitHub Pages build (2026-11-10).

Idempotent. Standard library only. Runs after update-blog-index.py has
regenerated index.html / index-en.html / sitemap.xml, so those regenerated
files keep their SEO tags and noindex pages never leak back into sitemaps.
"""
import os, re, sys, glob, json

SITE = 'https://yaohehe.github.io/'
MARK = b'P1-SEO-1110'
HOME = {'index.html', 'index-en.html'}
STATIC = {'about.html', 'privacy-policy.html'}
SKIP_PREFIX = ('tmp_', 'tmp-', 'bak-', 'backup-', 'prev-', 'google', '404')
CAN = re.compile(rb'<link[^>]+rel=["\']canonical["\'][^>]*>', re.I)
HREF = re.compile(rb'href=["\']([^"\']*)["\']', re.I)
TITLE = re.compile(rb'<title>(.*?)</title>', re.S | re.I)
NOINDEX = re.compile(rb'<meta[^>]+name=["\'](?:robots|googlebot)["\'][^>]*content=["\'][^"\']*noindex', re.I)


def url_of(fn):
    return SITE if fn == 'index.html' else SITE + fn


def esc(s):
    return s.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def jsonld(fn, lang, title):
    url = url_of(fn)
    date = fn[:10] if re.match(r'^\d{4}-\d{2}-\d{2}', fn) else None
    if fn in HOME:
        ld = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'TechPassive',
              'url': url, 'inLanguage': 'zh-CN' if fn == 'index.html' else 'en'}
    elif fn in STATIC:
        ld = {'@context': 'https://schema.org', '@type': 'WebPage', 'name': title,
              'url': url, 'inLanguage': lang}
    else:
        ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': title,
              'url': url, 'mainEntityOfPage': url, 'inLanguage': lang,
              'author': {'@type': 'Organization', 'name': 'TechPassive'},
              'publisher': {'@type': 'Organization', 'name': 'TechPassive'}}
        if date:
            ld['datePublished'] = date
            ld['dateModified'] = date
    return '<script type="application/ld+json">' + esc(
        json.dumps(ld, ensure_ascii=False, separators=(',', ':'))) + '</script>'


def inject(fn, b, eol):
    head, rest = b.split(b'</head>', 1)
    can_tag = CAN.search(head)
    tm = TITLE.search(head)
    title = tm.group(1).decode('utf-8', 'ignore').strip() if tm else fn
    title = re.sub(r'\s*-\s*TechPassive\s*$', '', title)[:110]
    lang = 'en' if fn.endswith('-en.html') or fn == 'index-en.html' else 'zh-CN'
    lines = ['<!-- P1-SEO-1110 -->']
    need_can = can_tag is None
    if can_tag:
        m = HREF.search(can_tag.group(0))
        if m and b'/archive/' in m.group(1):
            need_can = True
            head = head.replace(can_tag.group(0), b'', 1)
    if need_can:
        lines.append('<link rel="canonical" href="%s" />' % url_of(fn))
    if fn in HOME:
        lines.append('<link rel="alternate" hreflang="zh-Hans" href="%s" />' % SITE)
        lines.append('<link rel="alternate" hreflang="en" href="%s" />' % (SITE + 'index-en.html'))
        lines.append('<link rel="alternate" hreflang="x-default" href="%s" />' % SITE)
    if b'application/ld+json' not in head:
        lines.append(jsonld(fn, lang, title))
    return head + eol.join(x.encode('utf-8') for x in lines) + eol + b'</head>' + rest


def clean_sitemap(path, noindex):
    if not os.path.exists(path):
        return 0
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()
    blocks = re.findall(r'<url>.*?</url>', raw, re.S)
    if not blocks:
        return 0
    kept, removed = [], 0
    for blk in blocks:
        m = re.search(r'<loc>(.*?)</loc>', blk)
        fn = m.group(1).rstrip('/').split('/')[-1] if m else ''
        if fn in noindex:
            removed += 1
        else:
            kept.append(blk)
    if not removed:
        return 0
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + '\n'.join(kept) + '\n</urlset>\n')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(xml)
    return removed


def main(root='.'):
    noindex = set()
    paths = sorted(glob.glob(os.path.join(root, '*.html')))
    for p in paths:
        with open(p, 'rb') as f:
            b = f.read()
        if NOINDEX.search(b.split(b'</head>')[0]):
            noindex.add(os.path.basename(p))
    added = 0
    for p in paths:
        fn = os.path.basename(p)
        if fn in noindex or fn.startswith(SKIP_PREFIX):
            continue
        with open(p, 'rb') as f:
            b = f.read()
        if MARK in b or b'</head>' not in b:
            continue
        eol = b'\r\n' if b.count(b'\r\n') == b.count(b'\n') and b.count(b'\n') else b'\n'
        new = inject(fn, b, eol)
        with open(p, 'wb') as f:
            f.write(new)
        added += 1
    r1 = clean_sitemap(os.path.join(root, 'sitemap.xml'), noindex)
    r2 = clean_sitemap(os.path.join(root, 'sitemap-en.xml'), noindex)
    print('P1-SEO: noindex=%d injected=%d sitemap_removed=%d/%d'
          % (len(noindex), added, r1, r2))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
