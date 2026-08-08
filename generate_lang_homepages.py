#!/usr/bin/env python3
"""Generate index.html for each language from the English homepage.
No API calls — pulls translated post titles/excerpts from translated post files."""

import re
from pathlib import Path

SITE_ROOT = Path(__file__).parent

LANGS = {
    'it': {
        'html_lang': 'it',
        'title': 'Home — S/V Oroboro',
        'nav_home': 'Home', 'nav_blog': 'Blog', 'nav_map': 'Rotta', 'nav_about': 'Chi siamo',
        'nav_aria': 'Navigazione principale', 'toggle_aria': 'Apri menu',
        'hero_eyebrow': 'Città del Capo · Atlantico · Caraibi · Mediterraneo',
        'hero_h1': 'Viaggiando a vela,<br>a bordo di<br><em>S/V Oroboro</em>',
        'hero_tagline': 'Il viaggio di Francesco e Yuka intorno al mondo su un catamarano Leopard 40, partiti da Città del Capo nel 2018 e ancora in navigazione.',
        'hero_cta': 'Leggi il diario di bordo →',
        'hero_lang_label': 'Lingua:',
        'stat_years': 'Anni in mare', 'stat_oceans': 'Oceani attraversati',
        'stat_countries': 'Paesi visitati', 'stat_posts': 'Articoli',
        'route_eyebrow': 'La Rotta',
        'route_title': 'Da Città del Capo alla Grecia',
        'route_subtitle': "Un viaggio in barca a vela di 7 anni attraverso l'Atlantico del Sud, la costa del Brasile, i Caraibi, l'Atlantico del Nord e il Mediterraneo.",
        'route_overlay': 'Città del Capo → Namibia → Atlantico Sud → Brasile → Caraibi → Mediterraneo → Grecia',
        'route_overlay_sub': '44 tappe principali in 4 continenti',
        'route_cta': 'Esplora la mappa interattiva completa →',
        'latest_eyebrow': 'Il Diario',
        'latest_title': 'Post più recenti',
        'latest_subtitle': 'Segui il viaggio di Oroboro attraverso il nostro dettagliato diario di bordo.',
        'view_all': 'Mostra tutti gli 89 post →',
        'about_eyebrow': 'L\'Equipaggio & la Barca',
        'about_title': 'S/V Oroboro',
        'about_text': "Oroboro — il cui nome deriva dall'antico simbolo dell'ouroboros che rappresenta il rinnovo eterno — è un catamarano Leopard 40 costruito nel 2018. Porta Francesco e Yuka in un viaggio interminabile, fermandosi ovunque la curiosità li porti.",
        'about_boat': 'Barca', 'about_built': 'Anno', 'about_crew': 'Equipaggio', 'about_departed': 'Partenza',
        'about_us': 'Chi siamo →',
        'footer_home': 'Home', 'footer_blog': 'Blog', 'footer_map': 'Rotta', 'footer_about': 'Chi siamo',
        'read_more': 'Leggi di più →',
    },
    'ja': {
        'html_lang': 'ja',
        'title': 'ホーム — S/V Oroboro',
        'nav_home': 'ホーム', 'nav_blog': 'ブログ', 'nav_map': 'ルート', 'nav_about': '私たちについて',
        'nav_aria': 'メインナビゲーション', 'toggle_aria': 'メニューを開く',
        'hero_eyebrow': 'ケープタウン · 大西洋 · カリブ海 · 地中海',
        'hero_h1': 'S/V Oroboroで<br><em>世界を航海する</em>',
        'hero_tagline': 'フランチェスコとゆかのレオパード40カタマランでの世界一周の旅。2018年にケープタウンを出発し、今も航海中。',
        'hero_cta': '旅の記録を読む →',
        'hero_lang_label': '言語：',
        'stat_years': '海での年数', 'stat_oceans': '渡った海洋',
        'stat_countries': '訪れた国', 'stat_posts': 'ブログ記事',
        'route_eyebrow': '航路',
        'route_title': 'ケープタウンからギリシャへ',
        'route_subtitle': '南大西洋、ブラジル、カリブ海、地中海をたどる7年間の世界一周。',
        'route_overlay': 'ケープタウン → ナミビア → 南大西洋 → ブラジル → カリブ海 → 地中海 → ギリシャ',
        'route_overlay_sub': '4大陸にわたる44の主要寄港地',
        'route_cta': 'インタラクティブマップを探索する →',
        'latest_eyebrow': '航海日誌',
        'latest_title': '旅の最新記事',
        'latest_subtitle': '詳細な航海日誌でOroboroの航海を追いかけよう。',
        'view_all': '全89記事を見る →',
        'about_eyebrow': 'クルーと船',
        'about_title': 'S/V Oroboroについて',
        'about_text': 'Oroboroは、永遠の再生を象徴する古代のウロボロスにちなんで名付けられた、2018年建造のレオパード40カタマラン。フランチェスコとゆかは、終わりの日程を決めずに、好奇心の向くままに世界を旅しています。',
        'about_boat': '船', 'about_built': '建造年', 'about_crew': 'クルー', 'about_departed': '出発',
        'about_us': '私たちについて →',
        'footer_home': 'ホーム', 'footer_blog': 'ブログ', 'footer_map': 'ルート', 'footer_about': '私たちについて',
        'read_more': '続きを読む →',
    },
    'fr': {
        'html_lang': 'fr',
        'title': 'Accueil — S/V Oroboro',
        'nav_home': 'Accueil', 'nav_blog': 'Blog', 'nav_map': 'Carte', 'nav_about': 'À propos',
        'nav_aria': 'Navigation principale', 'toggle_aria': 'Ouvrir le menu',
        'hero_eyebrow': 'Le Cap · Atlantique · Caraïbes · Méditerranée',
        'hero_h1': 'Navigation à bord de<br><em>S/V Oroboro</em>',
        'hero_tagline': 'Le voyage de Francesco et Yuka à travers le monde sur un catamaran Leopard 40, partis du Cap en 2018 et encore en mer.',
        'hero_cta': 'Lire le journal de bord →',
        'hero_lang_label': 'Langue :',
        'stat_years': 'Ans en mer', 'stat_oceans': 'Océans traversés',
        'stat_countries': 'Pays visités', 'stat_posts': 'Articles',
        'route_eyebrow': 'La Route',
        'route_title': 'Du Cap à la Grèce',
        'route_subtitle': "Une circumnavigation de 7 ans qui trace l'Atlantique Sud, le Brésil, les Caraïbes et la Méditerranée.",
        'route_overlay': 'Le Cap → Namibie → Atlantique Sud → Brésil → Caraïbes → Méditerranée → Grèce',
        'route_overlay_sub': '44 étapes majeures sur 4 continents',
        'route_cta': 'Explorer la carte interactive →',
        'latest_eyebrow': 'Le Journal',
        'latest_title': 'Derniers articles du voyage',
        'latest_subtitle': "Suivez le voyage d'Oroboro à travers notre journal de bord détaillé.",
        'view_all': 'Voir tous les 89 articles →',
        'about_eyebrow': "L'Équipage & le Bateau",
        'about_title': 'Rencontrez S/V Oroboro',
        'about_text': "Oroboro — nommé d'après l'ancien symbole de l'ouroboros du renouveau éternel — est un catamaran Leopard 40 construit en 2018. Il emporte Francesco et Yuka dans un voyage sans date de fin, s'arrêtant partout où la curiosité les mène.",
        'about_boat': 'Bateau', 'about_built': 'Construit', 'about_crew': 'Équipage', 'about_departed': 'Départ',
        'about_us': 'À propos →',
        'footer_home': 'Accueil', 'footer_blog': 'Blog', 'footer_map': 'Carte', 'footer_about': 'À propos',
        'read_more': 'Lire la suite →',
    },
    'pt': {
        'html_lang': 'pt-BR',
        'title': 'Início — S/V Oroboro',
        'nav_home': 'Início', 'nav_blog': 'Blog', 'nav_map': 'Mapa', 'nav_about': 'Sobre nós',
        'nav_aria': 'Navegação principal', 'toggle_aria': 'Abrir menu',
        'hero_eyebrow': 'Cidade do Cabo · Atlântico · Caribe · Mediterrâneo',
        'hero_h1': 'Navegando a bordo de<br><em>S/V Oroboro</em>',
        'hero_tagline': 'A jornada de Francesco e Yuka ao redor do mundo em um catamarã Leopard 40, partindo da Cidade do Cabo em 2018 e ainda navegando.',
        'hero_cta': 'Leia o diário de bordo →',
        'hero_lang_label': 'Idioma:',
        'stat_years': 'Anos no mar', 'stat_oceans': 'Oceanos cruzados',
        'stat_countries': 'Países visitados', 'stat_posts': 'Postagens',
        'route_eyebrow': 'A Rota',
        'route_title': 'Da Cidade do Cabo à Grécia',
        'route_subtitle': 'Uma circum-navegação de 7 anos traçando o Atlântico Sul, o Brasil, o Caribe e o Mediterrâneo.',
        'route_overlay': 'Cidade do Cabo → Namíbia → Atlântico Sul → Brasil → Caribe → Mediterrâneo → Grécia',
        'route_overlay_sub': '44 paradas principais em 4 continentes',
        'route_cta': 'Explorar mapa interativo completo →',
        'latest_eyebrow': 'O Diário',
        'latest_title': 'Últimas publicações da viagem',
        'latest_subtitle': 'Acompanhe a viagem do Oroboro através do nosso diário de navegação detalhado.',
        'view_all': 'Ver todos os 89 artigos →',
        'about_eyebrow': 'A Tripulação & o Barco',
        'about_title': 'Conheça o S/V Oroboro',
        'about_text': 'Oroboro — nomeado em homenagem ao antigo símbolo do ouroboros de renovação eterna — é um catamarã Leopard 40 construído em 2018. Ele leva Francesco e Yuka em uma jornada sem data de término, parando onde quer que a curiosidade os leve.',
        'about_boat': 'Barco', 'about_built': 'Construído', 'about_crew': 'Tripulação', 'about_departed': 'Partida',
        'about_us': 'Sobre nós →',
        'footer_home': 'Início', 'footer_blog': 'Blog', 'footer_map': 'Mapa', 'footer_about': 'Sobre nós',
        'read_more': 'Leia mais →',
    },
    'es': {
        'html_lang': 'es',
        'title': 'Inicio — S/V Oroboro',
        'nav_home': 'Inicio', 'nav_blog': 'Blog', 'nav_map': 'Mapa', 'nav_about': 'Nosotros',
        'nav_aria': 'Navegación principal', 'toggle_aria': 'Abrir menú',
        'hero_eyebrow': 'Ciudad del Cabo · Atlántico · Caribe · Mediterráneo',
        'hero_h1': 'Navegando a bordo de<br><em>S/V Oroboro</em>',
        'hero_tagline': 'El viaje de Francesco y Yuka alrededor del mundo en un catamarán Leopard 40, partiendo de Ciudad del Cabo en 2018 y aún navegando.',
        'hero_cta': 'Lee el diario de a bordo →',
        'hero_lang_label': 'Idioma:',
        'stat_years': 'Años en el mar', 'stat_oceans': 'Océanos cruzados',
        'stat_countries': 'Países visitados', 'stat_posts': 'Entradas',
        'route_eyebrow': 'La Ruta',
        'route_title': 'De Ciudad del Cabo a Grecia',
        'route_subtitle': 'Una circunnavegación de 7 años trazando el Atlántico Sur, Brasil, el Caribe y el Mediterráneo.',
        'route_overlay': 'Ciudad del Cabo → Namibia → Atlántico Sur → Brasil → Caribe → Mediterráneo → Grecia',
        'route_overlay_sub': '44 paradas principales en 4 continentes',
        'route_cta': 'Explorar el mapa interactivo completo →',
        'latest_eyebrow': 'El Diario',
        'latest_title': 'Lo último del viaje',
        'latest_subtitle': 'Sigue el viaje del Oroboro a través de nuestro detallado diario de navegación.',
        'view_all': 'Ver todos los 89 artículos →',
        'about_eyebrow': 'La Tripulación & el Barco',
        'about_title': 'Conoce el S/V Oroboro',
        'about_text': 'Oroboro — nombrado por el antiguo símbolo del ouroboros de renovación eterna — es un catamarán Leopard 40 construido en 2018. Lleva a Francesco y Yuka en un viaje sin fecha de finalización, deteniéndose donde la curiosidad los guíe.',
        'about_boat': 'Barco', 'about_built': 'Construido', 'about_crew': 'Tripulación', 'about_departed': 'Partida',
        'about_us': 'Sobre nosotros →',
        'footer_home': 'Inicio', 'footer_blog': 'Blog', 'footer_map': 'Mapa', 'footer_about': 'Nosotros',
        'read_more': 'Leer más →',
    },
    'ca': {
        'html_lang': 'ca',
        'title': 'Inici — S/V Oroboro',
        'nav_home': 'Inici', 'nav_blog': 'Blog', 'nav_map': 'Mapa', 'nav_about': 'Sobre nosaltres',
        'nav_aria': 'Navegació principal', 'toggle_aria': 'Obrir menú',
        'hero_eyebrow': 'Cap de Bona Esperança · Atlàntic · Carib · Mediterrani',
        'hero_h1': 'Navegant a bord de<br><em>S/V Oroboro</em>',
        'hero_tagline': "El viatge de Francesco i Yuka arreu del món en un catamarà Leopard 40, partint del Cap de Bona Esperança el 2018 i encara navegant.",
        'hero_cta': 'Llegeix el diari de bord →',
        'hero_lang_label': 'Idioma:',
        'stat_years': 'Anys al mar', 'stat_oceans': 'Oceans travessats',
        'stat_countries': 'Països visitats', 'stat_posts': 'Articles',
        'route_eyebrow': 'La Ruta',
        'route_title': 'Del Cap de Bona Esperança a Grècia',
        'route_subtitle': "Una circumnavegació de 7 anys traçant l'Atlàntic Sud, el Brasil, el Carib i el Mediterrani.",
        'route_overlay': 'Cap de Bona Esperança → Namíbia → Atlàntic Sud → Brasil → Carib → Mediterrani → Grècia',
        'route_overlay_sub': '44 parades principals a 4 continents',
        'route_cta': 'Explora el mapa interactiu complet →',
        'latest_eyebrow': 'El Diari',
        'latest_title': 'El més recent del viatge',
        'latest_subtitle': "Segueix el viatge de l'Oroboro a través del nostre detallat diari de navegació.",
        'view_all': 'Veure els 89 articles →',
        'about_eyebrow': 'La Tripulació & el Vaixell',
        'about_title': 'Coneix el S/V Oroboro',
        'about_text': "Oroboro — anomenat pel símbol antic de l'ouroboros del renaixement etern — és un catamarà Leopard 40 construït el 2018. Porta Francesco i Yuka en un viatge sense data de fi, aturant-se allà on la curiositat els porta.",
        'about_boat': 'Vaixell', 'about_built': 'Construït', 'about_crew': 'Tripulació', 'about_departed': 'Sortida',
        'about_us': 'Sobre nosaltres →',
        'footer_home': 'Inici', 'footer_blog': 'Blog', 'footer_map': 'Mapa', 'footer_about': 'Sobre nosaltres',
        'read_more': 'Llegir més →',
    },
}

HREFLANG = '''  <link rel="alternate" hreflang="en" href="https://sailingoroboro.com/">
  <link rel="alternate" hreflang="it" href="https://sailingoroboro.com/it/">
  <link rel="alternate" hreflang="ja" href="https://sailingoroboro.com/ja/">
  <link rel="alternate" hreflang="fr" href="https://sailingoroboro.com/fr/">
  <link rel="alternate" hreflang="pt-BR" href="https://sailingoroboro.com/pt/">
  <link rel="alternate" hreflang="es" href="https://sailingoroboro.com/es/">
  <link rel="alternate" hreflang="ca" href="https://sailingoroboro.com/ca/">
  <link rel="alternate" hreflang="x-default" href="https://sailingoroboro.com/">
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
    path = SITE_ROOT / lang / 'posts' / f'{slug}.html'
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8')
    art = re.search(r'<article[^>]*>(.*?)</article>', text, re.DOTALL)
    if not art:
        return None
    body = art.group(1)
    for m in re.finditer(r'<p>(.*?)</p>', body, re.DOTALL):
        content = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if len(content) < 40:
            continue
        if len(content) > max_len:
            content = content[:max_len].rsplit(' ', 1)[0] + '…'
        return content
    return None

def generate_homepage(lang, cfg):
    src = (SITE_ROOT / 'index.html').read_text(encoding='utf-8')

    # ── Head ──
    src = src.replace('<html lang="en">', f'<html lang="{cfg["html_lang"]}">')
    src = src.replace('<title>Home — S/V Oroboro</title>', f'<title>{cfg["title"]}</title>')
    # Remove existing hreflang and inject new block
    src = re.sub(r'\s*<link rel="alternate" hreflang[^>]+>\n?', '', src)
    src = src.replace('</head>', HREFLANG + '</head>', 1)

    # ── Nav ──
    src = src.replace('aria-label="Main navigation"', f'aria-label="{cfg["nav_aria"]}"')
    src = src.replace('class="nav-logo" href="/"', f'class="nav-logo" href="/{lang}/"')
    src = src.replace('<li><a href="/">Home</a></li>',
                      f'<li><a href="/{lang}/" class="active">{cfg["nav_home"]}</a></li>')
    src = re.sub(r'<li><a href="/blog\.html"(?:[^>]*)>Blog</a></li>',
                 f'<li><a href="/{lang}/blog.html">{cfg["nav_blog"]}</a></li>', src)
    src = src.replace('<li><a href="/map.html">Map</a></li>',
                      f'<li><a href="/map.html">{cfg["nav_map"]}</a></li>')
    src = src.replace('<li><a href="/about.html">About</a></li>',
                      f'<li><a href="/about.html">{cfg["nav_about"]}</a></li>')
    src = src.replace('aria-label="Toggle menu"', f'aria-label="{cfg["toggle_aria"]}"')

    # ── Hero ──
    src = src.replace(
        'Cape Town · Atlantic · Caribbean · Mediterranean',
        cfg['hero_eyebrow'])
    src = src.replace(
        'Sailing aboard<br><em>S/V Oroboro</em>',
        cfg['hero_h1'])
    src = src.replace(
        "Francesco and Yuka's journey around the world on a Leopard 40 catamaran, departing Cape Town in 2018 and still sailing.",
        cfg['hero_tagline'])
    src = src.replace(
        '<a class="hero-cta" href="/blog.html">Read the Journey →</a>',
        f'<a class="hero-cta" href="/{lang}/blog.html">{cfg["hero_cta"]}</a>')
    # Hero mobile language selector label + set selected option
    src = src.replace('<label for="hero-lang-sel">Language:</label>',
                      f'<label for="hero-lang-sel">{cfg["hero_lang_label"]}</label>')
    src = src.replace('<option value="en" selected>', '<option value="en">')
    src = src.replace(f'<option value="{lang}">', f'<option value="{lang}" selected>')

    # ── Stats ──
    src = src.replace('<div class="stat-label">Years at Sea</div>',
                      f'<div class="stat-label">{cfg["stat_years"]}</div>')
    src = src.replace('<div class="stat-label">Oceans Crossed</div>',
                      f'<div class="stat-label">{cfg["stat_oceans"]}</div>')
    src = src.replace('<div class="stat-label">Countries Visited</div>',
                      f'<div class="stat-label">{cfg["stat_countries"]}</div>')
    src = src.replace('<div class="stat-label">Blog Posts</div>',
                      f'<div class="stat-label">{cfg["stat_posts"]}</div>')

    # ── Route section ──
    src = src.replace('<span class="section-eyebrow">The Route</span>',
                      f'<span class="section-eyebrow">{cfg["route_eyebrow"]}</span>')
    src = src.replace('<h2 class="section-title">From Cape Town to Greece</h2>',
                      f'<h2 class="section-title">{cfg["route_title"]}</h2>')
    src = src.replace(
        '<p class="section-subtitle">A 7-year circumnavigation tracing the South Atlantic, Brazil, the Caribbean, and the Mediterranean.</p>',
        f'<p class="section-subtitle">{cfg["route_subtitle"]}</p>')
    src = src.replace(
        '<strong>Cape Town → Namibia → South Atlantic → Brazil → Caribbean → Mediterranean → Greece</strong>',
        f'<strong>{cfg["route_overlay"]}</strong>')
    src = src.replace('<p>44 major stops across 4 continents</p>',
                      f'<p>{cfg["route_overlay_sub"]}</p>')
    src = src.replace('<a class="route-cta" href="/map.html">Explore full interactive map →</a>',
                      f'<a class="route-cta" href="/map.html">{cfg["route_cta"]}</a>')

    # ── Latest posts section ──
    src = src.replace('<span class="section-eyebrow">The Log</span>',
                      f'<span class="section-eyebrow">{cfg["latest_eyebrow"]}</span>')
    src = src.replace('<h2 class="section-title">Latest from the Journey</h2>',
                      f'<h2 class="section-title">{cfg["latest_title"]}</h2>')
    src = src.replace(
        "<p class=\"section-subtitle\">Follow Oroboro's voyage through our detailed sailing log.</p>",
        f'<p class="section-subtitle">{cfg["latest_subtitle"]}</p>')

    def replace_card(m):
        card = m.group(0)
        slug_m = re.search(r'href="/posts/([^"]+)\.html"', card)
        if not slug_m:
            return card
        slug = slug_m.group(1)
        card = card.replace(f'href="/posts/{slug}.html"', f'href="/{lang}/posts/{slug}.html"')
        title = get_translated_title(lang, slug)
        if title:
            card = re.sub(r'<h3>.*?</h3>', f'<h3>{title}</h3>', card, flags=re.DOTALL)
        excerpt = get_translated_excerpt(lang, slug)
        if excerpt:
            card = re.sub(r'<p class="post-card-excerpt">.*?</p>',
                          f'<p class="post-card-excerpt">{excerpt}</p>', card, flags=re.DOTALL)
        card = card.replace('>Read more →<', f'>{cfg["read_more"]}<')
        return card

    src = re.sub(r'<a class="post-card".*?</a>', replace_card, src, flags=re.DOTALL)
    src = src.replace('<a class="btn-outline" href="/blog.html">View all 89 posts →</a>',
                      f'<a class="btn-outline" href="/{lang}/blog.html">{cfg["view_all"]}</a>')

    # ── About section ──
    src = src.replace('<span class="section-eyebrow">The Crew & Boat</span>',
                      f'<span class="section-eyebrow">{cfg["about_eyebrow"]}</span>')
    src = src.replace('<h2 class="section-title">Meet S/V Oroboro</h2>',
                      f'<h2 class="section-title">{cfg["about_title"]}</h2>')
    src = src.replace(
        "Oroboro — named for the ancient ouroboros symbol of eternal renewal — is a Leopard 40 catamaran built in 2018. She carries Francesco and Yuka on a journey without a fixed end date, stopping wherever curiosity leads.",
        cfg['about_text'])
    src = src.replace('<div class="about-detail-label">Boat</div>',
                      f'<div class="about-detail-label">{cfg["about_boat"]}</div>')
    src = src.replace('<div class="about-detail-label">Built</div>',
                      f'<div class="about-detail-label">{cfg["about_built"]}</div>')
    src = src.replace('<div class="about-detail-label">Crew</div>',
                      f'<div class="about-detail-label">{cfg["about_crew"]}</div>')
    src = src.replace('<div class="about-detail-label">Departed</div>',
                      f'<div class="about-detail-label">{cfg["about_departed"]}</div>')
    src = src.replace('<a class="about-link about-link-app" href="/about.html">About Us →</a>',
                      f'<a class="about-link about-link-app" href="/about.html">{cfg["about_us"]}</a>')

    # ── Footer ──
    src = src.replace('<li><a href="/">Home</a></li>',
                      f'<li><a href="/{lang}/">{cfg["footer_home"]}</a></li>')
    src = re.sub(r'<li><a href="/blog\.html">Blog</a></li>',
                 f'<li><a href="/{lang}/blog.html">{cfg["footer_blog"]}</a></li>', src)
    src = src.replace('<li><a href="/map.html">Map</a></li>',
                      f'<li><a href="/map.html">{cfg["footer_map"]}</a></li>')
    src = src.replace('<li><a href="/about.html">About</a></li>',
                      f'<li><a href="/about.html">{cfg["footer_about"]}</a></li>')

    out = SITE_ROOT / lang / 'index.html'
    out.write_text(src, encoding='utf-8')
    print(f'  {lang}/index.html — done')

def main():
    print('Generating language homepages...')
    for lang, cfg in LANGS.items():
        generate_homepage(lang, cfg)
    print('Done.')

if __name__ == '__main__':
    main()
