#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 SEO postprocess for GitHub Pages build (2026-11-11).

Idempotent. Standard library only. Runs after update-blog-index.py has
regenerated index.html / index-en.html / sitemap.xml.

Responsibilities
  1. Restore canonical / JSON-LD on regenerated pages (legacy P1 behaviour).
  2. Rebuild ALL hreflang tags from the FINAL file set on every build.
     Pairs come from seo-pairs.json (explicit, locked) plus conservative
     auto-matching for articles published after auto_after. Any stale,
     dangling or mis-paired hreflang is removed. Wrong hreflang is worse
     than none, so unmatched pages get zero hreflang tags.
  3. Strip noindex URLs and dangling <loc> entries from both sitemaps.
"""
import os, re, sys, glob, json, collections

SITE = 'https://yaohehe.github.io/'
MARK = b'P1-SEO-1110'
PAIR_FILE = 'seo-pairs.json'
PAIR_START = b'<!-- P1-HREFLANG-1111 -->'
PAIR_END = b'<!-- /P1-HREFLANG-1111 -->'
LEGACY_COMMENTS = (b'<!-- CN-EN-PAIR-1110 -->', b'<!-- /CN-EN-PAIR-1110 -->')
HOME = {'index.html', 'index-en.html'}
STATIC = {'about.html', 'privacy-policy.html'}
SKIP_PREFIX = ('tmp_', 'tmp-', 'bak-', 'backup-', 'prev-', 'google', '404')
CAN = re.compile(rb'<link[^>]+rel=["\']canonical["\'][^>]*>', re.I)
HREF = re.compile(rb'href=["\']([^"\']*)["\']', re.I)
TITLE = re.compile(rb'<title>(.*?)</title>', re.S | re.I)
NOINDEX = re.compile(rb'<meta[^>]+name=["\'](?:robots|googlebot)["\'][^>]*content=["\'][^"\']*noindex', re.I)
LANG = re.compile(rb'<html[^>]+lang=["\']([^"\']+)', re.I)
HL_LINE = re.compile(rb'<link\b[^>]*hreflang=[^>]*>', re.I)
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}')

# P1 token rules (kept verbatim so explicit baseline and auto matching agree)
STOP = set('the and for with from that this 2026 guide complete real vs how why what new best '
           'a an to of in on is are my i 5 3 4 坑 实战 完全 指南 横评 哪款 值得买 2026年'.split())


def url_of(fn):
    return SITE if fn == 'index.html' else SITE + fn


def esc(s):
    return s.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def jsonld(fn, lang, title):
    url = url_of(fn)
    date = fn[:10] if DATE.match(fn) else None
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
    """Legacy P1 injection: canonical + JSON-LD only (hreflang owned by rebuild)."""
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
    if b'application/ld+json' not in head:
        lines.append(jsonld(fn, lang, title))
    return head + eol.join(x.encode('utf-8') for x in lines) + eol + b'</head>' + rest


def eol_of(b):
    return b'\r\n' if b.count(b'\r\n') == b.count(b'\n') and b.count(b'\n') else b'\n'


def norm_lang(raw):
    s = raw.decode('ascii', 'ignore').lower()
    if s.startswith('zh'):
        return 'zh-Hans'
    if s.startswith('ja'):
        return 'ja'
    if s.startswith('en'):
        return 'en'
    return None


def tokens(fn):
    s = fn[:-5]
    if s.endswith('-en'):
        s = s[:-3]
    if DATE.match(s):
        s = s[11:]
    parts = [p for p in re.split(r'[-_]+', s.lower()) if p]
    return set(p for p in parts if p not in STOP and len(p) > 1)


def stem(fn):
    s = fn[:-5]
    if s.endswith('-en'):
        s = s[:-3]
    return s[11:] if DATE.match(s) else s


def load_explicit(root, present, noindex):
    """seo-pairs.json pairs; drop any group whose target vanished or is noindex."""
    path = os.path.join(root, PAIR_FILE)
    if not os.path.exists(path):
        return [], '1970-01-01'
    try:
        d = json.load(open(path, encoding='utf-8'))
    except Exception as ex:
        print('P1-HREFLANG: bad %s (%s)' % (PAIR_FILE, str(ex)[:60]))
        return [], '1970-01-01'
    out, seen = [], set()
    for item in d.get('pairs', []):
        g = {k: v for k, v in item.get('langs', {}).items()
             if k in ('zh-Hans', 'en', 'ja')}
        vals = set(g.values())
        if len(g) < 2 or len(vals) != len(g):
            continue
        if not vals <= present or vals & noindex:
            continue
        key = tuple(sorted(g.items()))
        if key in seen:
            continue
        seen.add(key)
        out.append(g)
    return out, d.get('auto_after', '1970-01-01')


def auto_pairs(present, langs, noindex, used, after):
    """Conservative matching. Only articles dated >= after; never guess history."""
    cn, en = [], []
    for fn in present:
        if not DATE.match(fn) or fn in used or fn in noindex or fn[:10] < after:
            continue
        lg = langs.get(fn)
        if lg == 'zh-Hans':
            cn.append(fn)
        elif lg == 'en':
            en.append(fn)
    by_day = collections.defaultdict(list)
    for c in cn:
        by_day[c[:10]].append(c)
    score = {}
    for e in en:
        te = tokens(e)
        if len(te) < 2:
            continue
        for c in by_day.get(e[:10], ()):
            tc = tokens(c)
            if len(tc) < 2:
                continue
            inter = te & tc
            if len(inter) < 2:
                continue
            ov = len(inter) / min(len(te), len(tc))
            jac = len(inter) / len(te | tc)
            numeric = sum(1 for x in inter if any(ch.isdigit() for ch in x))
            prefix = len(os.path.commonprefix([stem(e), stem(c)]))
            if ov < 0.60:
                continue
            if not (prefix >= 8 or numeric >= 1 or ov >= 0.75):
                continue
            score[(e, c)] = (round(ov + min(jac, .5) * .3 + min(numeric, 3) * .02
                                   + (.05 if prefix >= 8 else 0), 4), ov, inter)
    best_e, best_c = {}, {}
    for (e, c), v in score.items():
        if e not in best_e or v[0] > best_e[e][1][0]:
            best_e[e] = (c, v)
        if c not in best_c or v[0] > best_c[c][1][0]:
            best_c[c] = (e, v)
    out, taken = [], set()
    for e, (c, v) in best_e.items():
        if best_c.get(c, (None,))[0] != e or e in taken or c in taken:
            continue
        second = sorted((x[0] for (ee, cc), x in score.items() if ee == e and cc != c),
                        reverse=True)
        if second and v[0] - second[0] < 0.15:
            continue
        out.append({'zh-Hans': c, 'en': e})
        taken.update((e, c))

    # Same-day last-resort: exactly one unmatched CN and one unmatched EN left,
    # and every token of the CN slug appears in the EN slug (e.g. "rol0").
    left_c = collections.defaultdict(list)
    left_e = collections.defaultdict(list)
    for c in cn:
        if c not in taken:
            left_c[c[:10]].append(c)
    for e in en:
        if e not in taken:
            left_e[e[:10]].append(e)
    for day, cs in left_c.items():
        es = left_e.get(day, [])
        if len(cs) != 1 or len(es) != 1:
            continue
        c, e = cs[0], es[0]
        tc, te = tokens(c), tokens(e)
        if tc and tc <= te:
            out.append({'zh-Hans': c, 'en': e})
            taken.update((e, c))
    return out


def strip_hreflang(head):
    """Delete every hreflang <link> line and our marker lines. Line-wise, so
    repeated runs do not accumulate blank lines (byte-level idempotence)."""
    out = []
    for line in head.splitlines(keepends=True):
        s = line.strip()
        if s in (PAIR_START, PAIR_END) or s in LEGACY_COMMENTS:
            continue
        new = HL_LINE.sub(b'', line)
        if new is line:
            out.append(line)
        elif new.strip() == b'':
            continue
        else:
            out.append(new)
    return b''.join(out)


def apply_hreflang(b, tags, eol):
    head, rest = b.split(b'</head>', 1)
    head = strip_hreflang(head)
    if tags:
        lines = [PAIR_START] + [t.encode('utf-8') for t in tags] + [PAIR_END]
        if not head.endswith((b'\n', b'\r')):
            head += eol
        head += eol.join(lines) + eol
    return head + b'</head>' + rest


def rebuild_hreflang(root, cur, noindex):
    present = set(cur)
    langs = {}
    for fn, b in cur.items():
        head = b.split(b'</head>')[0]
        m = LANG.search(head)
        langs[fn] = norm_lang(m.group(1)) if m else None
        if not langs[fn]:
            langs[fn] = 'en' if fn.endswith('-en.html') or fn == 'index-en.html' else 'zh-Hans'
    explicit, after = load_explicit(root, present, noindex)
    used = {fn for g in explicit for fn in g.values()}
    auto = auto_pairs(present, langs, noindex, used, after)
    groups = explicit + auto
    wanted = {}
    active = 0
    for i, g in enumerate(groups):
        vals = set(g.values())
        if len(g) < 2 or not vals <= present or vals & noindex:
            continue
        # Explicit groups are authoritative (locked from live hreflang). Some
        # legacy CN pages have a wrong <html lang="en">, so do NOT re-validate
        # them here. Auto-matched groups keep the language guard.
        if i >= len(explicit) and any(langs.get(fn) != lg for lg, fn in g.items()):
            continue
        active += 1
        items = sorted(g.items())
        tags = ['<link rel="alternate" hreflang="%s" href="%s" />' % (lg, url_of(fn))
                for lg, fn in items]
        xd = g.get('zh-Hans') or items[0][1]
        tags.append('<link rel="alternate" hreflang="x-default" href="%s" />' % url_of(xd))
        for fn in vals:
            wanted[fn] = tags
    written = cleared = 0
    for fn, b in cur.items():
        if b'</head>' not in b:
            continue
        eol = eol_of(b)
        new = apply_hreflang(b, wanted.get(fn, []), eol)
        if new == b:
            continue
        with open(os.path.join(root, fn), 'wb') as f:
            f.write(new)
        if wanted.get(fn):
            written += 1
        else:
            cleared += 1
    return {'explicit': len(explicit), 'auto': len(auto), 'groups': active,
            'written': written, 'cleared': cleared,
            'auto_detail': [g['en'] for g in auto]}


def clean_sitemap(path, noindex, present=None):
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
        elif present is not None and fn.endswith('.html') and fn not in present:
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
    paths = sorted(glob.glob(os.path.join(root, '*.html')))
    cur = {}
    for p in paths:
        with open(p, 'rb') as f:
            cur[os.path.basename(p)] = f.read()
    noindex = {fn for fn, b in cur.items()
               if NOINDEX.search(b.split(b'</head>')[0])}
    added = 0
    for fn, b in cur.items():
        if fn in noindex or fn.startswith(SKIP_PREFIX) or MARK in b or b'</head>' not in b:
            continue
        with open(os.path.join(root, fn), 'wb') as f:
            f.write(inject(fn, b, eol_of(b)))
        added += 1
    # Re-read: inject() may have just added canonical / JSON-LD.
    for fn in cur:
        with open(os.path.join(root, fn), 'rb') as f:
            cur[fn] = f.read()
    st = rebuild_hreflang(root, cur, noindex)
    present = set(cur)
    r1 = clean_sitemap(os.path.join(root, 'sitemap.xml'), noindex, present)
    r2 = clean_sitemap(os.path.join(root, 'sitemap-en.xml'), noindex, present)
    print('P1-SEO: noindex=%d injected=%d sitemap_removed=%d/%d'
          % (len(noindex), added, r1, r2))
    print('P1-HREFLANG: explicit=%d auto=%d groups=%d written=%d cleared=%d'
          % (st['explicit'], st['auto'], st['groups'], st['written'], st['cleared']))
    for fn in st['auto_detail']:
        print('P1-HREFLANG-AUTO: %s' % fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
