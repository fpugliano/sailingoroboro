#!/usr/bin/env python3
"""
Add hreflang links to all English pages and generate sitemap.xml.
Run whenever new posts are added or translations change.
"""

import os, re
from pathlib import Path
from datetime import date

SITE_ROOT = Path(__file__).parent
BASE_URL   = 'https://sailingoroboro.com'
TODAY      = date.today().isoformat()

LANG_CODES = {
    'it': 'it',
    'ja': 'ja',
    'fr': 'fr',
    'pt': 'pt-BR',
    'es': 'es',
    'ca': 'ca',
}


# ── Hreflang helpers ─────────────────────────────────────────────────────────

def make_hreflang(en_path):
    """Return <link rel=alternate hreflang=...> block for a given English URL path."""
    lines = [f'  <link rel="alternate" hreflang="en" href="{BASE_URL}{en_path}">']
    for folder, code in LANG_CODES.items():
        # derive translated path: / → /it/, /blog.html → /it/blog.html,
        # /posts/foo.html → /it/posts/foo.html
        if en_path == '/':
            lang_path = f'/{folder}/'
        else:
            lang_path = f'/{folder}{en_path}'
        # only add if the translated file actually exists
        local = SITE_ROOT / lang_path.lstrip('/')
        # directories: check index.html inside
        if lang_path.endswith('/'):
            local = local / 'index.html'
        if local.exists():
            lines.append(f'  <link rel="alternate" hreflang="{code}" href="{BASE_URL}{lang_path}">')
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="{BASE_URL}{en_path}">')
    return '\n'.join(lines) + '\n'

def inject_hreflang(file_path, en_url_path):
    text = file_path.read_text(encoding='utf-8')
    # remove any existing hreflang block
    text = re.sub(r'\s*<link rel="alternate" hreflang[^>]+>\n?', '', text)
    block = make_hreflang(en_url_path)
    text = text.replace('</head>', block + '</head>', 1)
    file_path.write_text(text, encoding='utf-8')


# ── Sitemap helpers ──────────────────────────────────────────────────────────

def sitemap_url(loc, priority='0.8', changefreq='monthly'):
    return (f'  <url>\n'
            f'    <loc>{loc}</loc>\n'
            f'    <lastmod>{TODAY}</lastmod>\n'
            f'    <changefreq>{changefreq}</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            f'  </url>')


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    urls = []

    # 1. index.html
    print('index.html')
    inject_hreflang(SITE_ROOT / 'index.html', '/')
    urls.append(sitemap_url(f'{BASE_URL}/', priority='1.0', changefreq='weekly'))

    # 2. blog.html
    print('blog.html')
    inject_hreflang(SITE_ROOT / 'blog.html', '/blog.html')
    urls.append(sitemap_url(f'{BASE_URL}/blog.html', priority='0.9', changefreq='weekly'))

    # 3. about.html, map.html
    for page in ['about.html', 'map.html']:
        p = SITE_ROOT / page
        if p.exists():
            print(page)
            inject_hreflang(p, f'/{page}')
            urls.append(sitemap_url(f'{BASE_URL}/{page}', priority='0.6'))

    # 4. posts/*.html
    posts_dir = SITE_ROOT / 'posts'
    post_files = sorted(posts_dir.glob('*.html'))
    print(f'{len(post_files)} English posts')
    for post in post_files:
        en_path = f'/posts/{post.name}'
        inject_hreflang(post, en_path)
        urls.append(sitemap_url(f'{BASE_URL}{en_path}', priority='0.8'))

    # 5. Language homepages and blog pages
    for folder in LANG_CODES:
        for page, priority in [('index.html', '0.7'), ('blog.html', '0.8')]:
            p = SITE_ROOT / folder / page
            if p.exists():
                slug = '' if page == 'index.html' else '/blog.html'
                loc = f'{BASE_URL}/{folder}{slug}' if slug else f'{BASE_URL}/{folder}/'
                urls.append(sitemap_url(loc, priority=priority))

    # 6. Translated posts
    for folder in LANG_CODES:
        lang_posts = sorted((SITE_ROOT / folder / 'posts').glob('*.html'))
        print(f'{len(lang_posts)} {folder} posts')
        for post in lang_posts:
            urls.append(sitemap_url(f'{BASE_URL}/{folder}/posts/{post.name}', priority='0.6'))

    # Write sitemap.xml
    sitemap_path = SITE_ROOT / 'sitemap.xml'
    sitemap_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls) + '\n'
        '</urlset>\n',
        encoding='utf-8'
    )
    print(f'\nsitemap.xml → {len(urls)} URLs')


if __name__ == '__main__':
    main()
