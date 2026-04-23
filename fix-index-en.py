#!/usr/bin/env python3
with open('index-en.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The current title in index-en.html
old = 'WordPress Security Plugin Showdown shows 43% of WordPress security incidents are directly linked to outdated plugins and themes. Wordfence\'s threat intelligence reports indicate brute force attacks can peak at millions of requests per minute. These numbers tell me one thing: running WordPress without a security plugin is like walking naked. 18 months ago, I also thought "install a plugin and relax." I was wrong. Three major pitfalls later, here\'s what I\'ve learned — comparing three plugins: Wordfence, Solid Security (formerly iThemes Security), and Sucuri. Not to sell you anything, but to help you understand which one fits before you commit.'
new = 'WordPress Security Plugin Showdown: Wordfence vs Solid Security vs Sucuri (2026 In-Depth Comparison)'

if old in content:
    content = content.replace(old, new)
    print('Replaced')
    with open('index-en.html', 'w', encoding='utf-8') as f:
        f.write(content)
else:
    idx = content.find('WordPress Security Plugin Showdown shows')
    if idx != -1:
        end_idx = content.find('</a>', idx)
        print('Current title:', repr(content[idx:end_idx]))
    else:
        print('Old pattern NOT FOUND')