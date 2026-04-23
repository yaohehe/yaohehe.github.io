import re

for lang in ['index.html', 'index-en.html']:
    with open(lang, 'r', encoding='utf-8') as f:
        content = f.read()

    old_link = '2026-04-23-wordpress-security-plugin-showdown-2026-wordfence--en.html'
    new_link = 'archive/2026-04-23/2026-04-23-wordpress-security-plugin-showdown-2026-wordfence--en.html'
    old_title = 'WPScan 2025 data shows 43% of WordPress security incidents are directly linked to outdated plugins and themes. Wordfence\'s threat intelligence reports indicate brute force attacks can peak at millions of requests per minute. These numbers tell me one thing: running WordPress without a security plugin is like walking naked. 18 months ago, I also thought "install a plugin and relax." I was wrong. Three major pitfalls later, here\'s what I\'ve learned — comparing three plugins: Wordfence, Solid Security (formerly iThemes Security), and Sucuri. Not to sell you anything, but to help you understand which one fits before you commit.'
    new_title = 'WordPress Security Plugin Showdown: Wordfence vs Solid Security vs Sucuri (2026 In-Depth Comparison)'

    if old_link in content:
        content = content.replace(f'href="{old_link}">{old_title}', f'href="{new_link}">{new_title}')
        print(f'{lang}: replaced 1 link(s)')
    else:
        # Check what's there
        if old_link in content:
            print(f'{lang}: link found but title mismatch')
        else:
            print(f'{lang}: old link NOT FOUND')
        # Try simple replacement
        if new_link in content:
            print(f'{lang}: already uses archive path')

    with open(lang, 'w', encoding='utf-8') as f:
        f.write(content)