#!/usr/bin/env python3
"""Generate blog.html for each language from the English blog.html.
Pulls translated post titles from the translated post files.
Run again after translations complete to pick up any new titles."""

import os, re
from pathlib import Path

SITE_ROOT = Path(__file__).parent

LANGS = {
    'it': {
        'html_lang': 'it',
        'title': 'Blog — S/V Oroboro',
        'nav_home': 'Home', 'nav_blog': 'Blog', 'nav_map': 'Rotta', 'nav_about': 'Chi siamo',
        'nav_aria': 'Navigazione principale', 'toggle_aria': 'Apri menu',
        'eyebrow': 'Il diario di bordo', 'h1': 'Diario di bordo',
        'count': '87 articoli dal Sudafrica alla Grecia',
        'filters': {'All Posts': 'Tutti', 'Boat': 'Barca', 'Sailing': 'Navigazione',
                    'South Africa': 'Sud Africa', 'South Atlantic': 'Atlantico Sud',
                    'Brazil': 'Brasile', 'Caribbean': 'Caraibi', 'North Atlantic': 'Atlantico Nord'},
        'read_more': 'Leggi di più →',
    },
    'ja': {
        'html_lang': 'ja',
        'title': 'ブログ — S/V Oroboro',
        'nav_home': 'ホーム', 'nav_blog': 'ブログ', 'nav_map': 'ルート', 'nav_about': '私たちについて',
        'nav_aria': 'メインナビゲーション', 'toggle_aria': 'メニューを開く',
        'eyebrow': '航海日誌', 'h1': '旅の記事',
        'count': '南アフリカからギリシャまで87本の記事',
        'filters': {'All Posts': 'すべて', 'Boat': 'ボート', 'Sailing': '航海',
                    'South Africa': '南アフリカ', 'South Atlantic': '南大西洋',
                    'Brazil': 'ブラジル', 'Caribbean': 'カリブ海', 'North Atlantic': '北大西洋'},
        'read_more': '続きを読む →',
    },
    'fr': {
        'html_lang': 'fr',
        'title': 'Blog — S/V Oroboro',
        'nav_home': 'Accueil', 'nav_blog': 'Blog', 'nav_map': 'Carte', 'nav_about': 'À propos',
        'nav_aria': 'Navigation principale', 'toggle_aria': 'Ouvrir le menu',
        'eyebrow': 'Journal de bord', 'h1': 'Articles de voyage',
        'count': '87 articles du Cap à la Grèce',
        'filters': {'All Posts': 'Tous', 'Boat': 'Bateau', 'Sailing': 'Navigation',
                    'South Africa': 'Afrique du Sud', 'South Atlantic': 'Atlantique Sud',
                    'Brazil': 'Brésil', 'Caribbean': 'Caraïbes', 'North Atlantic': 'Atlantique Nord'},
        'read_more': 'Lire la suite →',
    },
    'pt': {
        'html_lang': 'pt-BR',
        'title': 'Blog — S/V Oroboro',
        'nav_home': 'Início', 'nav_blog': 'Blog', 'nav_map': 'Mapa', 'nav_about': 'Sobre nós',
        'nav_aria': 'Navegação principal', 'toggle_aria': 'Abrir menu',
        'eyebrow': 'Diário de bordo', 'h1': 'Artigos de viagem',
        'count': '87 artigos do Cabo à Grécia',
        'filters': {'All Posts': 'Todos', 'Boat': 'Barco', 'Sailing': 'Navegação',
                    'South Africa': 'África do Sul', 'South Atlantic': 'Atlântico Sul',
                    'Brazil': 'Brasil', 'Caribbean': 'Caribe', 'North Atlantic': 'Atlântico Norte'},
        'read_more': 'Leia mais →',
    },
    'es': {
        'html_lang': 'es',
        'title': 'Blog — S/V Oroboro',
        'nav_home': 'Inicio', 'nav_blog': 'Blog', 'nav_map': 'Mapa', 'nav_about': 'Nosotros',
        'nav_aria': 'Navegación principal', 'toggle_aria': 'Abrir menú',
        'eyebrow': 'Diario de a bordo', 'h1': 'Artículos de viaje',
        'count': '87 artículos desde Ciudad del Cabo hasta Grecia',
        'filters': {'All Posts': 'Todos', 'Boat': 'Barco', 'Sailing': 'Navegación',
                    'South Africa': 'Sudáfrica', 'South Atlantic': 'Atlántico Sur',
                    'Brazil': 'Brasil', 'Caribbean': 'Caribe', 'North Atlantic': 'Atlántico Norte'},
        'read_more': 'Leer más →',
    },
    'ca': {
        'html_lang': 'ca',
        'title': 'Blog — S/V Oroboro',
        'nav_home': 'Inici', 'nav_blog': 'Blog', 'nav_map': 'Mapa', 'nav_about': 'Sobre nosaltres',
        'nav_aria': 'Navegació principal', 'toggle_aria': 'Obrir menú',
        'eyebrow': 'Diari de bord', 'h1': 'Articles de viatge',
        'count': '87 articles des del Cap fins a Grècia',
        'filters': {'All Posts': 'Tots', 'Boat': 'Vaixell', 'Sailing': 'Navegació',
                    'South Africa': 'Sud-àfrica', 'South Atlantic': 'Atlàntic Sud',
                    'Brazil': 'Brasil', 'Caribbean': 'Carib', 'North Atlantic': 'Atlàntic Nord'},
        'read_more': 'Llegir més →',
    },
}

HREFLANG = '''  <link rel="alternate" hreflang="en" href="https://sailingoroboro.com/blog.html">
  <link rel="alternate" hreflang="it" href="https://sailingoroboro.com/it/blog.html">
  <link rel="alternate" hreflang="ja" href="https://sailingoroboro.com/ja/blog.html">
  <link rel="alternate" hreflang="fr" href="https://sailingoroboro.com/fr/blog.html">
  <link rel="alternate" hreflang="pt-BR" href="https://sailingoroboro.com/pt/blog.html">
  <link rel="alternate" hreflang="es" href="https://sailingoroboro.com/es/blog.html">
  <link rel="alternate" hreflang="ca" href="https://sailingoroboro.com/ca/blog.html">
'''

def get_translated_title(lang, slug):
    path = SITE_ROOT / lang / 'posts' / f'{slug}.html'
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8')
    m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL)
    if not m:
        return None
    return re.sub(r'<[^>]+>', '', m.group(1)).strip()

def get_translated_excerpt(lang, slug, max_len=200):
    """Extract first real paragraph from translated post (skip caption-only paragraphs)."""
    path = SITE_ROOT / lang / 'posts' / f'{slug}.html'
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8')
    # Find the article body
    art = re.search(r'<article[^>]*>(.*?)</article>', text, re.DOTALL)
    if not art:
        return None
    body = art.group(1)
    for m in re.finditer(r'<p>(.*?)</p>', body, re.DOTALL):
        content = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        # skip short caption-style paragraphs (just bold date/location)
        if len(content) < 40:
            continue
        if len(content) > max_len:
            content = content[:max_len].rsplit(' ', 1)[0] + '…'
        return content
    return None

def generate_blog(lang, cfg):
    src = (SITE_ROOT / 'blog.html').read_text(encoding='utf-8')

    src = src.replace('<html lang="en">', f'<html lang="{cfg["html_lang"]}">')
    src = src.replace('<title>Blog — S/V Oroboro</title>', f'<title>{cfg["title"]}</title>')
    src = src.replace('aria-label="Main navigation"', f'aria-label="{cfg["nav_aria"]}"')
    src = src.replace('class="nav-logo" href="/"', f'class="nav-logo" href="/{lang}/"')
    src = src.replace('<li><a href="/">Home</a></li>', f'<li><a href="/{lang}/">{cfg["nav_home"]}</a></li>')
    src = re.sub(r'<li><a href="/blog\.html"(?:[^>]*)>Blog</a></li>',
                 f'<li><a href="/{lang}/blog.html" class="active">{cfg["nav_blog"]}</a></li>', src)
    src = src.replace('<li><a href="/map.html">Map</a></li>', f'<li><a href="/map.html">{cfg["nav_map"]}</a></li>')
    src = src.replace('<li><a href="/about.html">About</a></li>', f'<li><a href="/about.html">{cfg["nav_about"]}</a></li>')
    src = src.replace('aria-label="Toggle menu"', f'aria-label="{cfg["toggle_aria"]}"')
    src = src.replace('<span class="page-header-eyebrow">The Sailing Log</span>',
                      f'<span class="page-header-eyebrow">{cfg["eyebrow"]}</span>')
    src = src.replace('<h1>Journey Posts</h1>', f'<h1>{cfg["h1"]}</h1>')
    src = src.replace('<p>87 posts from Cape Town to Greece</p>', f'<p>{cfg["count"]}</p>')

    for en_text, lang_text in cfg['filters'].items():
        src = src.replace(f'>{en_text}<', f'>{lang_text}<')

    def replace_card(m):
        card = m.group(0)
        slug_m = re.search(r'href="/posts/([^"]+)\.html"', card)
        if not slug_m:
            return card
        slug = slug_m.group(1)
        card = card.replace(f'href="/posts/{slug}.html"', f'href="/{lang}/posts/{slug}.html"')
        title = get_translated_title(lang, slug)
        if title:
            card = re.sub(r'<h2>.*?</h2>', f'<h2>{title}</h2>', card, flags=re.DOTALL)
        excerpt = get_translated_excerpt(lang, slug)
        if excerpt:
            card = re.sub(r'<p class="post-card-excerpt">.*?</p>',
                          f'<p class="post-card-excerpt">{excerpt}</p>', card, flags=re.DOTALL)
        card = card.replace('>Read more →<', f'>{cfg["read_more"]}<')
        return card

    src = re.sub(r'<a class="post-card".*?</a>', replace_card, src, flags=re.DOTALL)
    src = src.replace('</head>', HREFLANG + '</head>', 1)

    out = SITE_ROOT / lang / 'blog.html'
    out.write_text(src, encoding='utf-8')
    n_translated = sum(1 for _ in (SITE_ROOT / lang / 'posts').glob('*.html'))
    print(f'  {lang}/blog.html — {n_translated}/89 post titles translated')

def main():
    print('Generating language blog pages...')
    for lang, cfg in LANGS.items():
        generate_blog(lang, cfg)
    print('Done.')

if __name__ == '__main__':
    main()
