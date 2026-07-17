#!/usr/bin/env /usr/bin/python3
"""
Build script for Sailing Oroboro static website.
Parses WordPress WXR export and generates HTML files.

Usage:
    python3 build.py

Output files are written to the repo root (GitHub Pages served from main branch root).
"""

import re
import os
import html
from datetime import datetime
from pathlib import Path
import yaml
import markdown as _md

# ─── Config ──────────────────────────────────────────────────────────────────

WP_XML      = Path.home() / "Documents/Blog Documentation/Oroboro Blog Back Up Text.xml"
OUT_DIR     = Path(__file__).parent
POSTS_DIR   = OUT_DIR / "posts"
CONTENT_DIR = OUT_DIR / "content"

R2_BASE = 'https://pub-7f7d07c430fd4c3eb11a4e6eae938ce3.r2.dev/'

# Sort-date overrides for legacy posts whose WordPress pubDate ≠ event date.
# Only affects chronological ordering; display_date is unchanged.
SORT_DATE_OVERRIDES = {
    '2nd-atlantic-crossing': '2021-05-03',  # published Sep 2021; voyage departed May 3 2021
}

# Hand-authored posts that live in posts/ but have no XML or content/ source.
# build.py includes them in blog/index listings but does NOT regenerate their HTML.
PREBUILT_POSTS = [
    {
        'title':           'I Built a Boat Manager App',
        'slug':            'boat-manager-app',
        'display_date':    'June 07, 2026',
        'iso_date':        '2026-06-07',
        'sort_date':       '2026-06-07',
        'region':          'boat',
        'region_display':  'Boat Systems',
        'excerpt':         "After eight years of sailing Oroboro across three oceans, I've fixed a lot of things. I couldn't find a boat management app that worked for real bluewater cruisers — so I built one.",
        'image':           R2_BASE + 'blogpost.jpg',
        'content':         None,
        'pub_date':        '',
        'categories':      ['Boat Systems'],
        'cat_slugs':       [],
        'is_markdown':     False,
        'is_prebuilt':     True,
        'nav_exclude':     True,
        'published_display': None,
    },
    {
        'title':           'I built my own boat dashboard — and it looks better than the €250 Victron screen',
        'slug':            'oroboro-dashboard',
        'display_date':    'June 10, 2026',
        'iso_date':        '2026-06-10',
        'sort_date':       '2026-06-10',
        'region':          'boat',
        'region_display':  'Technology',
        'excerpt':         'After years staring at a 1995-style Victron Remote Console, I built my own on a Raspberry Pi. Plain HTML, CSS, and JavaScript — no frameworks, no cloud, no subscription.',
        'image':           '/images/posts/New Dashboard.jpg',
        'content':         None,
        'pub_date':        '',
        'categories':      ['Technology'],
        'cat_slugs':       [],
        'is_markdown':     False,
        'is_prebuilt':     True,
        'nav_exclude':     True,
        'published_display': None,
    },
]

# Region mapping for markdown post frontmatter region: values
MARKDOWN_REGION_MAP = {
    'azores':          ('atlantic2', 'Azores'),
    'north atlantic':  ('atlantic2', 'North Atlantic'),
    'atlantic':        ('atlantic',  'South Atlantic'),
    'atlantic-crossing': ('atlantic', 'South Atlantic'),
    'europe':          ('europe',    'Europe'),
    'mediterranean':   ('europe',    'Mediterranean'),
    'portugal':        ('europe',    'Europe'),
    'sailing':         ('sailing',   'Sailing'),
    'boat':            ('boat',      'Boat'),
    'technology':      ('boat',      'Technology'),
    'caribbean':       ('caribbean', 'Caribbean'),
    'brazil':          ('brazil',    'Brazil'),
}

# Region mapping: category slug → display name + filter key
REGION_MAP = {
    "south-africa":      ("South Africa",    "south-africa"),
    "namibia":           ("Namibia",         "namibia"),
    "atlantic-crossing": ("South Atlantic",  "atlantic"),
    "brazil":            ("Brazil",          "brazil"),
    "caribbean":         ("Caribbean",       "caribbean"),
    "europe":            ("Europe",          "europe"),
    "sailing":           ("Sailing",         "sailing"),
    "boat":              ("Boat",            "boat"),
    "boat-systems":      ("Boat Systems",    "boat"),
    "catamaran":         ("Catamaran",       "boat"),
    "leopard":           ("Leopard",         "boat"),
}

REGION_DISPLAY = {
    "south-africa": "South Africa",
    "namibia":      "Namibia",
    "atlantic":     "South Atlantic",
    "brazil":       "Brazil",
    "caribbean":    "Caribbean",
    "atlantic2":    "North Atlantic",
    "europe":       "Europe",
    "sailing":      "Sailing",
    "boat":         "Boat",
}

# ─── Parser ───────────────────────────────────────────────────────────────────

def parse_cdata(text):
    """Extract content from CDATA or plain text."""
    m = re.search(r'<!\[CDATA\[(.*?)\]\]>', text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()

def extract_field(item_xml, field):
    """Extract a field value from item XML block."""
    patterns = [
        rf'<{field}><!\[CDATA\[(.*?)\]\]></{field}>',
        rf'<{field}>(.*?)</{field}>',
    ]
    for pat in patterns:
        m = re.search(pat, item_xml, re.DOTALL)
        if m:
            return m.group(1).strip()
    return ''

def extract_categories(item_xml):
    """Return list of (nicename, display_name) tuples for category domain."""
    return re.findall(
        r'<category domain="category" nicename="([^"]+)"><!\[CDATA\[(.*?)\]\]></category>',
        item_xml
    )

def extract_first_image(content_html):
    """Return src of first <img> in post content."""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
    return m.group(1) if m else None

def text_excerpt(html_content, max_chars=180):
    """Strip HTML and return plain text excerpt."""
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = re.sub(r'\s+', ' ', text).strip()
    text = html.unescape(text)
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0] + '…'
    return text

BLOCK_TAGS = re.compile(r'^<(p|div|ul|ol|li|h[1-6]|blockquote|pre|table|figure|img|hr|br)', re.IGNORECASE)

def wpautop(content):
    """Convert double newlines to <p> tags, mirroring WordPress wpautop."""
    # Normalize line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    # Split into blocks on blank lines
    blocks = re.split(r'\n\n+', content.strip())
    result = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if BLOCK_TAGS.match(block):
            result.append(block)
        else:
            # Convert single newlines within a text block to <br>
            block = block.replace('\n', '<br>\n')
            result.append(f'<p>{block}</p>')
    return '\n'.join(result)

def categorize_md_region(region_str, categories):
    """Map markdown frontmatter region/categories to (region_key, region_display)."""
    key = region_str.lower().strip()
    if key in MARKDOWN_REGION_MAP:
        return MARKDOWN_REGION_MAP[key]
    for cat in (categories or []):
        ckey = cat.lower().strip().replace('-', ' ').replace('_', ' ')
        if ckey in MARKDOWN_REGION_MAP:
            return MARKDOWN_REGION_MAP[ckey]
    fallback = region_str.lower().replace(' ', '-')
    return (fallback, region_str)


_IMG_RE = re.compile(r'<img([^>]*)>', re.IGNORECASE)

def rewrite_md_images(html_content):
    """Rewrite bare image paths to full R2 URLs and wrap in wp-caption figure."""
    def _sub(m):
        attrs = m.group(1)
        alt_m = re.search(r'alt="([^"]*)"', attrs)
        src_m = re.search(r'src="([^"]*)"', attrs)
        alt = alt_m.group(1) if alt_m else ''
        src = src_m.group(1) if src_m else ''
        if src and not src.startswith('http'):
            src = R2_BASE + src
        if alt:
            return (
                f'<figure class="wp-caption aligncenter" style="max-width:100%">\n'
                f'<img src="{src}" alt="{html.escape(alt)}" class="aligncenter">\n'
                f'<p class="wp-caption-text">{html.escape(alt)}</p>\n'
                f'</figure>'
            )
        return f'<img src="{src}" alt="">'
    return _IMG_RE.sub(_sub, html_content)


def parse_markdown_posts():
    """Parse all *.md files in content/ (ignoring _ prefixed files)."""
    posts = []
    if not CONTENT_DIR.exists():
        return posts
    for md_file in sorted(CONTENT_DIR.glob('[!_]*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            raw = f.read()
        if not raw.startswith('---'):
            print(f"  WARNING: {md_file.name} missing frontmatter, skipping")
            continue
        parts = raw.split('---', 2)
        if len(parts) < 3:
            print(f"  WARNING: {md_file.name} malformed frontmatter, skipping")
            continue
        try:
            fm = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as e:
            print(f"  WARNING: {md_file.name} YAML error: {e}, skipping")
            continue
        body = parts[2].strip()

        title      = str(fm.get('title', ''))
        slug       = str(fm.get('slug', md_file.stem))
        date_str   = str(fm.get('date', ''))       # event date YYYY-MM-DD
        pub_str    = str(fm.get('published', ''))   # publication date YYYY-MM-DD
        region_raw = str(fm.get('region', ''))
        cats_raw   = fm.get('categories', [])
        if isinstance(cats_raw, str):
            cats_raw = [cats_raw]
        hero = str(fm.get('hero', ''))

        # Event date for display and sorting
        try:
            evt_dt = datetime.strptime(date_str, '%Y-%m-%d')
            display_date = evt_dt.strftime('%B %d, %Y')
        except ValueError:
            display_date = date_str

        # Publication date for dual-date display
        try:
            pub_dt = datetime.strptime(pub_str, '%Y-%m-%d')
            published_display = pub_dt.strftime('%B %Y')
        except ValueError:
            published_display = pub_str if pub_str else None

        region_key, region_display = categorize_md_region(region_raw, cats_raw)

        # Convert markdown → HTML (HTML comments like <!-- IMG: ... --> pass through)
        converter = _md.Markdown(extensions=['fenced_code', 'tables'])
        content_html = converter.convert(body)
        content_html = rewrite_md_images(content_html)

        excerpt = text_excerpt(content_html)
        image   = (R2_BASE + hero) if hero else extract_first_image(content_html)

        posts.append({
            'title':             title,
            'slug':              slug,
            'pub_date':          pub_str,
            'display_date':      display_date,
            'iso_date':          date_str,
            'sort_date':         date_str,
            'published_display': published_display,
            'content':           content_html,
            'categories':        cats_raw,
            'cat_slugs':         [c.lower().replace(' ', '-') for c in cats_raw],
            'region':            region_key,
            'region_display':    region_display,
            'image':             image,
            'excerpt':           excerpt,
            'is_markdown':       True,
            'is_prebuilt':       False,
            'nav_exclude':       False,
        })
        print(f"  Loaded markdown post: {slug} ({date_str})")
    return posts


def parse_date(pub_date_str):
    """Parse WordPress pubDate to a nice display string."""
    if not pub_date_str:
        return '', ''
    try:
        dt = datetime.strptime(pub_date_str.strip(), '%a, %d %b %Y %H:%M:%S %z')
        return dt.strftime('%B %d, %Y'), dt.strftime('%Y-%m-%d')
    except Exception:
        return pub_date_str, ''

def categorize_post(cats_nicenames):
    """Return (region_key, region_display) for a post's categories."""
    priority = ['south-africa', 'namibia', 'atlantic-crossing', 'brazil', 'caribbean', 'europe']
    for p in priority:
        if p in cats_nicenames:
            return REGION_MAP.get(p, (p.replace('-', ' ').title(), p))
    for n in cats_nicenames:
        if n in REGION_MAP:
            return REGION_MAP[n]
    return ('Sailing', 'sailing')

def parse_wordpress_xml(xml_path):
    """Parse WP WXR file and return list of published post dicts."""
    print(f"Parsing {xml_path}...")
    with open(xml_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Split on <item> boundaries
    items_raw = re.split(r'<item>', raw)[1:]  # first chunk is channel header

    posts = []
    for item_xml in items_raw:
        post_type = extract_field(item_xml, r'wp:post_type')
        status    = extract_field(item_xml, r'wp:status')

        if post_type != 'post' or status != 'publish':
            continue

        title   = extract_field(item_xml, 'title')
        if not title:
            continue

        slug    = extract_field(item_xml, r'wp:post_name')
        pub_str = extract_field(item_xml, 'pubDate')
        content = extract_field(item_xml, r'content:encoded')
        if not content:
            # Try alternate namespace form
            m = re.search(r'<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>', item_xml, re.DOTALL)
            content = m.group(1).strip() if m else ''

        cats     = extract_categories(item_xml)
        cat_slugs = [c[0] for c in cats]
        cat_names = [c[1] for c in cats]

        display_date, iso_date = parse_date(pub_str)
        region_display, region_key = categorize_post(cat_slugs)
        content_local = re.sub(
            r'https://sailingoroboro\.com/wp-content/uploads/\d{4}/\d{2}/([^\s"\'<>]+)',
            lambda m: 'https://pub-7f7d07c430fd4c3eb11a4e6eae938ce3.r2.dev/' + m.group(1).lower(),
            content
        )
        image = extract_first_image(content_local)
        excerpt = text_excerpt(content_local)

        posts.append({
            'title':          title,
            'slug':           slug,
            'pub_date':       pub_str,
            'display_date':   display_date,
            'iso_date':       iso_date,
            'content':        content_local,
            'categories':     cat_names,
            'cat_slugs':      cat_slugs,
            'region':         region_key,
            'region_display': region_display,
            'image':          image,
            'excerpt':        excerpt,
        })

    # Sort chronologically
    posts.sort(key=lambda p: p['iso_date'] or '0000')
    print(f"Found {len(posts)} published posts.")
    return posts

# ─── HTML Templates ───────────────────────────────────────────────────────────

NAV_HTML = '''<nav class="nav" role="navigation" aria-label="Main navigation">
  <a class="nav-logo" href="/">
    <img src="/img/logo-white.png" alt="Oroboro logo">
    S/V Oroboro
  </a>
  <ul class="nav-links">
    <li><a href="/">Home</a></li>
    <li><a href="/blog.html">Blog</a></li>
    <li><a href="/map.html">Map</a></li>
    <li><a href="/about.html">About</a></li>
    <li><a href="https://www.instagram.com/sailingoroboro/" target="_blank" rel="noopener" class="nav-instagram">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
      @sailingoroboro
    </a></li>
  </ul>
  <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
</nav>'''

FOOTER_HTML = '''<footer class="footer">
  <div class="footer-logo">
    <img src="/img/logo-white.png" alt="">
    <span>S/V Oroboro</span>
  </div>
  <ul class="footer-links">
    <li><a href="/">Home</a></li>
    <li><a href="/blog.html">Blog</a></li>
    <li><a href="/map.html">Map</a></li>
    <li><a href="/about.html">About</a></li>
    <li><a href="https://www.instagram.com/sailingoroboro/" target="_blank" rel="noopener">Instagram</a></li>
    <li><a href="https://boat.sailingoroboro.com" target="_blank" rel="noopener">Boat Manager</a></li>
  </ul>
  <p class="footer-copy">© {year} Francesco &amp; Yuka</p>
</footer>'''

HEAD_COMMON = '''  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="{css_path}css/style.css">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" href="/img/favicon-32x32.png" type="image/png" sizes="32x32">
  <link rel="icon" href="/img/favicon-16x16.png" type="image/png" sizes="16x16">
  <link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">'''


def html_page(title, body, css_path='/', extra_head='', extra_scripts='', body_class=''):
    year = datetime.now().year
    body_attr = f' class="{body_class}"' if body_class else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <title>{title} — S/V Oroboro</title>
{HEAD_COMMON.replace("{css_path}", css_path)}
{extra_head}
</head>
<body{body_attr}>
{NAV_HTML}
{body}
{FOOTER_HTML.replace("{year}", str(year))}
<script src="{css_path}js/main.js"></script>
{extra_scripts}
</body>
</html>'''


# ─── Index Page ───────────────────────────────────────────────────────────────

def build_index(posts):
    # Latest 6 posts
    latest = posts[-6:][::-1]

    cards_html = ''
    for p in latest:
        img_html = ''
        if p['image']:
            img_html = f'<img src="{html.escape(p["image"])}" alt="{html.escape(p["title"])}" loading="lazy">'
        else:
            img_html = '<div class="post-card-no-image">⛵</div>'

        cats_display = p['region_display']
        cards_html += f'''
    <a class="post-card" href="/posts/{html.escape(p["slug"])}.html" data-region="{html.escape(p["region"])}">
      <div class="post-card-image">{img_html}</div>
      <div class="post-card-body">
        <div class="post-card-meta">
          <span class="post-card-region">{html.escape(cats_display)}</span>
          <span class="post-card-date">{html.escape(p["display_date"])}</span>
        </div>
        <h3>{html.escape(p["title"])}</h3>
        <p class="post-card-excerpt">{html.escape(p["excerpt"])}</p>
        <span class="post-card-link">Read more →</span>
      </div>
    </a>'''

    body = f'''
<main>
  <!-- Hero -->
  <section class="hero" aria-label="Hero">
    <video class="hero-media" autoplay muted loop playsinline preload="none"
           aria-hidden="true" poster="/OroboroHeroPhoto.jpeg">
      <source src="/img/hero-video.mp4" type="video/mp4">
    </video>
    <img class="hero-media" src="/OroboroHeroPhoto.jpeg"
         alt="" aria-hidden="true"
         style="display:none"
         onerror="this.style.display='none'"
         id="hero-photo-fallback">
    <div class="hero-bg" aria-hidden="true"></div>
    <div class="hero-content">
      <img class="hero-logo" src="/img/logo-white.png" alt="Oroboro — serpent eating its tail">
      <span class="hero-eyebrow">Cape Town · Atlantic · Caribbean · Mediterranean</span>
      <h1>Sailing aboard<br><em>S/V Oroboro</em></h1>
      <p class="hero-tagline">Francesco and Yuka's journey around the world on a Leopard 40 catamaran, departing Cape Town in 2018 and still sailing.</p>
      <a class="hero-cta" href="/blog.html">Read the Journey →</a>
    </div>
    <div class="hero-scroll" aria-hidden="true">Scroll</div>
    <div class="hero-waves" aria-hidden="true">
      <svg viewBox="0 0 1440 120" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
        <path d="M0,60 C180,100 360,20 540,60 C720,100 900,20 1080,60 C1260,100 1350,40 1440,60 L1440,120 L0,120 Z" fill="#FAFAF8"/>
      </svg>
    </div>
  </section>

  <!-- Stats -->
  <section class="stats-bar" aria-label="Journey statistics">
    <div class="stats-inner">
      <div class="stat-item">
        <div class="stat-number">7+</div>
        <div class="stat-label">Years at Sea</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">3</div>
        <div class="stat-label">Oceans Crossed</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">30+</div>
        <div class="stat-label">Countries Visited</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{len(posts)}</div>
        <div class="stat-label">Blog Posts</div>
      </div>
    </div>
  </section>

  <!-- Route Map -->
  <section class="section route-section" aria-label="Journey route">
    <div class="section-inner">
      <div class="section-header">
        <span class="section-eyebrow">The Route</span>
        <h2 class="section-title">From Cape Town to Greece</h2>
        <p class="section-subtitle">A 7-year circumnavigation tracing the South Atlantic, Brazil, the Caribbean, and the Mediterranean.</p>
      </div>
      <div class="route-map-preview">
        <div id="mini-map"></div>
        <div class="route-overlay">
          <strong>Cape Town → Namibia → South Atlantic → Brazil → Caribbean → Mediterranean → Greece</strong>
          <p>44 major stops across 4 continents</p>
        </div>
      </div>
      <a class="route-cta" href="/map.html">Explore full interactive map →</a>
    </div>
  </section>

  <!-- Latest Posts -->
  <section class="section" aria-label="Latest posts">
    <div class="section-inner">
      <div class="section-header">
        <span class="section-eyebrow">The Log</span>
        <h2 class="section-title">Latest from the Journey</h2>
        <p class="section-subtitle">Follow Oroboro's voyage through our detailed sailing log.</p>
      </div>
      <div class="posts-grid">
        {cards_html}
      </div>
      <div class="section-footer">
        <a class="btn-outline" href="/blog.html">View all {len(posts)} posts →</a>
      </div>
    </div>
  </section>

  <!-- About -->
  <section class="section about-section" aria-label="About Oroboro">
    <div class="section-inner">
      <div class="about-grid">
        <div>
          <span class="section-eyebrow">The Crew & Boat</span>
          <h2 class="section-title">Meet S/V Oroboro</h2>
          <p class="about-text">Oroboro — named for the ancient ouroboros symbol of eternal renewal — is a Leopard 40 catamaran built in 2018. She carries Francesco and Yuka on a journey without a fixed end date, stopping wherever curiosity leads.</p>
          <div class="about-details">
            <div class="about-detail">
              <div class="about-detail-label">Boat</div>
              <div class="about-detail-value">Leopard 40 Catamaran</div>
            </div>
            <div class="about-detail">
              <div class="about-detail-label">Built</div>
              <div class="about-detail-value">2018</div>
            </div>
            <div class="about-detail">
              <div class="about-detail-label">Crew</div>
              <div class="about-detail-value">Francesco &amp; Yuka</div>
            </div>
            <div class="about-detail">
              <div class="about-detail-label">Departed</div>
              <div class="about-detail-value">Cape Town, Sep 2018</div>
            </div>
          </div>
          <div class="about-links">
            <a class="about-link about-link-instagram" href="https://www.instagram.com/sailingoroboro/" target="_blank" rel="noopener">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
              @sailingoroboro
            </a>
            <a class="about-link about-link-app" href="https://boat.sailingoroboro.com" target="_blank" rel="noopener">
              Boat Manager App ↗
            </a>
            <a class="about-link about-link-app" href="/about.html">About Us →</a>
          </div>
        </div>
        <div class="about-image-wrap">
          <img class="about-logo" src="/img/logo-stacked.png"
               alt="Oroboro logo — wind rose, serpent and compass"
               style="filter: brightness(0) invert(1);">
        </div>
      </div>
    </div>
  </section>
</main>'''

    extra_head = '''  <!-- Leaflet for mini-map -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">'''
    extra_scripts = '''<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="/js/map.js"></script>
<script>
// Show photo fallback if video fails to load
(function(){
  var v = document.querySelector('.hero-media[autoplay]');
  var p = document.getElementById('hero-photo-fallback');
  if (!v || !p) return;
  v.addEventListener('error', function(){ p.style.display='block'; }, true);
  v.addEventListener('stalled', function(){ if(v.readyState===0){ p.style.display='block'; } });
})();
</script>'''

    return html_page('Home', body, css_path='/', extra_head=extra_head, extra_scripts=extra_scripts)


# ─── Blog Index Page ──────────────────────────────────────────────────────────

def build_blog(posts):
    # Build filter buttons
    regions_seen = []
    for p in posts:
        rk = p['region']
        if rk not in regions_seen:
            regions_seen.append(rk)

    filter_buttons = '<button class="filter-btn active" data-filter="all">All Posts</button>\n'
    region_labels = {
        'south-africa': 'South Africa',
        'namibia':      'Namibia',
        'atlantic':     'South Atlantic',
        'brazil':       'Brazil',
        'caribbean':    'Caribbean',
        'atlantic2':    'North Atlantic',
        'europe':       'Europe / Med',
        'sailing':      'Sailing',
        'boat':         'Boat',
    }
    for rk in regions_seen:
        label = region_labels.get(rk, rk.replace('-', ' ').title())
        filter_buttons += f'<button class="filter-btn" data-filter="{html.escape(rk)}">{html.escape(label)}</button>\n'

    cards_html = ''
    for p in reversed(posts):
        img_html = ''
        if p['image']:
            img_html = f'<img src="{html.escape(p["image"])}" alt="{html.escape(p["title"])}" loading="lazy">'
        else:
            img_html = '<div class="post-card-no-image">⛵</div>'

        cards_html += f'''
    <a class="post-card" href="/posts/{html.escape(p["slug"])}.html"
       data-region="{html.escape(p["region"])}">
      <div class="post-card-image">{img_html}</div>
      <div class="post-card-body">
        <div class="post-card-meta">
          <span class="post-card-region">{html.escape(p["region_display"])}</span>
          <span class="post-card-date">{html.escape(p["display_date"])}</span>
        </div>
        <h2>{html.escape(p["title"])}</h2>
        <p class="post-card-excerpt">{html.escape(p["excerpt"])}</p>
        <span class="post-card-link">Read more →</span>
      </div>
    </a>'''

    body = f'''
<main>
  <header class="page-header">
    <span class="page-header-eyebrow">The Sailing Log</span>
    <h1>Journey Posts</h1>
    <p>{len(posts)} posts from Cape Town to Greece</p>
  </header>

  <div class="filters" role="navigation" aria-label="Filter posts">
    <div class="filters-inner">
      {filter_buttons}
    </div>
  </div>

  <div class="blog-grid">
    <div class="blog-grid-inner">
      {cards_html}
    </div>
  </div>
</main>'''

    return html_page('Blog', body, css_path='/')


# ─── Single Post Page ─────────────────────────────────────────────────────────

def build_post(post, prev_post, next_post):
    if post.get('is_markdown'):
        # Markdown posts: content is already rendered HTML; skip WP cleanup
        content = post['content']
    else:
        # WordPress posts: clean shortcodes, rewrite image URLs, apply wpautop
        content = post['content']
        content = re.sub(r'\[caption[^\]]*\](.*?)\[/caption\]', r'\1', content, flags=re.DOTALL)
        content = re.sub(r'\[/?[a-z_]+[^\]]*\]', '', content)
        content = re.sub(
            r'https://sailingoroboro\.com/wp-content/uploads/\d{4}/\d{2}/([^\s"\'<>]+)',
            lambda m: R2_BASE + m.group(1).lower(),
            content
        )
        content = wpautop(content)

    cats_html = ''
    for cat in post['categories'][:3]:
        cats_html += f'<span class="post-header-region">{html.escape(cat)}</span>'

    # Date display: new markdown posts show event date + publication date
    if post.get('published_display'):
        date_html = (f'{html.escape(post["display_date"])} · '
                     f'<span style="opacity:0.7">published {html.escape(post["published_display"])}</span>')
    else:
        date_html = html.escape(post["display_date"])

    # Prev/next nav — skip nav_excluded posts (tech posts not in voyage sequence)
    eff_prev = prev_post if (prev_post and not prev_post.get('nav_exclude')) else None
    eff_next = next_post if (next_post and not next_post.get('nav_exclude')) else None

    nav_html = ''
    if eff_prev or eff_next:
        nav_html = '<nav class="post-nav" aria-label="Post navigation">'
        if eff_prev:
            nav_html += f'''
      <a class="post-nav-item" href="/posts/{html.escape(eff_prev["slug"])}.html">
        <div class="post-nav-label">← Previous</div>
        <div class="post-nav-title">{html.escape(eff_prev["title"])}</div>
      </a>'''
        else:
            nav_html += '<div></div>'
        if eff_next:
            nav_html += f'''
      <a class="post-nav-item post-nav-next" href="/posts/{html.escape(eff_next["slug"])}.html">
        <div class="post-nav-label">Next →</div>
        <div class="post-nav-title">{html.escape(eff_next["title"])}</div>
      </a>'''
        nav_html += '</nav>'

    body = f'''
<main>
  <header class="post-header">
    <div class="post-header-meta">
      {cats_html}
      <span class="post-header-date">{date_html}</span>
    </div>
    <h1>{html.escape(post["title"])}</h1>
  </header>

  <div class="post-body">
    <div class="post-body-inner">
      <a href="/blog.html" style="display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:0.85rem;margin-bottom:2.5rem;">
        ← Back to all posts
      </a>
      <article class="post-content clearfix">
        {content}
      </article>
      {nav_html}
    </div>
  </div>
</main>'''

    # Per-post og: / twitter: social preview
    title_full = html.escape(post['title']) + ' — S/V Oroboro'
    slug_esc   = html.escape(post['slug'])

    # ~150-char plain-text description from the already-extracted excerpt
    desc_raw = post['excerpt']
    if len(desc_raw) > 150:
        desc_raw = desc_raw[:150].rsplit(' ', 1)[0] + '…'
    desc_esc = html.escape(desc_raw)

    # Image: hero (already resolved to absolute R2 URL in post['image'] for
    # markdown posts) → first image (same field for legacy posts) → site default
    og_image = html.escape(post.get('image') or R2_BASE + 'oroboro-logo-21.jpg')
    og_url   = f'https://sailingoroboro.com/posts/{slug_esc}.html'

    og_head = (
        f'\n  <meta name="description" content="{desc_esc}">'
        f'\n  <meta property="og:type" content="article">'
        f'\n  <meta property="og:title" content="{title_full}">'
        f'\n  <meta property="og:description" content="{desc_esc}">'
        f'\n  <meta property="og:image" content="{og_image}">'
        f'\n  <meta property="og:url" content="{og_url}">'
        f'\n  <meta name="twitter:card" content="summary_large_image">'
        f'\n  <meta name="twitter:title" content="{title_full}">'
        f'\n  <meta name="twitter:description" content="{desc_esc}">'
        f'\n  <meta name="twitter:image" content="{og_image}">'
    )
    return html_page(post['title'], body, css_path='../', extra_head=og_head)


# ─── Static Pages ─────────────────────────────────────────────────────────────

def build_about():
    body = '''
<main>
  <header class="page-header">
    <span class="page-header-eyebrow">The Crew & Boat</span>
    <h1>About S/V Oroboro</h1>
    <p>Two adventurers. One catamaran. An open ocean.</p>
  </header>

  <div class="about-full">
    <div class="about-full-inner">

      <div class="boat-section">
        <h2>The Boat</h2>
        <p>Oroboro is a <strong>Leopard 40 catamaran</strong> built in 2018 by Robertson &amp; Caine in South Africa.
        She combines performance, comfort, and reliability — the ideal vessel for extended bluewater sailing.
        Named for the ancient <em>ouroboros</em> symbol (a serpent devouring its own tail, meaning eternal renewal),
        Oroboro is also a palindrome.</p>
        <div class="boat-specs">
          <div class="spec-item">
            <div class="spec-value">40′</div>
            <div class="spec-label">Length</div>
          </div>
          <div class="spec-item">
            <div class="spec-value">2018</div>
            <div class="spec-label">Year Built</div>
          </div>
          <div class="spec-item">
            <div class="spec-value">2</div>
            <div class="spec-label">Crew</div>
          </div>
          <div class="spec-item">
            <div class="spec-value">3</div>
            <div class="spec-label">Oceans</div>
          </div>
          <div class="spec-item">
            <div class="spec-value">Leopard</div>
            <div class="spec-label">Make</div>
          </div>
          <div class="spec-item">
            <div class="spec-value">Cat</div>
            <div class="spec-label">Type</div>
          </div>
        </div>
      </div>

      <div class="crew-grid">
        <div class="crew-card">
          <h3>Francesco</h3>
          <p>Italian-born, left a career in big tech in Silicon Valley to sail the world with Yuka.
          Handles navigation, weather routing, and keeps the boat manager app running at
          <a href="https://boat.sailingoroboro.com" style="color:var(--teal)">boat.sailingoroboro.com</a>.</p>
        </div>
        <div class="crew-card">
          <h3>Yuka</h3>
          <p>Left a career in big tech in Silicon Valley to sail the world with Francesco.
          Designed the Oroboro logo — a blend of wind rose, serpent, and compass —
          and handles photography and creativity on board.</p>
        </div>
      </div>

      <div style="background:var(--white);border-radius:14px;padding:2.5rem;box-shadow:var(--shadow-sm);margin:2rem 0;">
        <h2 style="font-family:var(--font-serif);color:var(--navy);font-size:1.8rem;margin-bottom:1rem;">The Name</h2>
        <p style="color:var(--text);line-height:1.8;">
          During a summer 2017 charter in the Aeolian Islands, Francesco's sister Marina suggested "Oroboro" on the spot.
          The word refers to the <em>ouroboros</em> — an ancient symbol of a serpent eating its own tail,
          representing the eternal cycle of renewal. It's also a palindrome (reads the same backward as forward).
          Yuka immediately sketched the logo: a wind rose, a serpent head indicating north, and three small
          triangles at 90°, 180°, and 270°. Easy to spell in NATO phonetic: Oscar Romeo Oscar Bravo Oscar Romeo Oscar.
        </p>
        <img src="/img/logo-stacked.png"
             alt="Oroboro logo"
             style="max-width:280px;margin:2rem auto;border-radius:0;">
      </div>

      <div style="text-align:center;margin-top:3rem;">
        <p style="color:var(--muted);margin-bottom:1.5rem;">Follow the journey</p>
        <div style="display:flex;gap:1rem;justify-content:center;flex-wrap:wrap;">
          <a class="about-link about-link-instagram"
             href="https://www.instagram.com/sailingoroboro/"
             target="_blank" rel="noopener"
             style="display:inline-flex;align-items:center;gap:8px;padding:12px 24px;border-radius:24px;font-weight:600;background:linear-gradient(135deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888);color:white;">
            Instagram @sailingoroboro
          </a>
          <a href="https://boat.sailingoroboro.com" target="_blank" rel="noopener"
             style="display:inline-flex;align-items:center;gap:8px;padding:12px 24px;border-radius:24px;font-weight:600;border:2px solid var(--teal);color:var(--teal);">
            Boat Manager App ↗
          </a>
        </div>
      </div>

    </div>
  </div>
</main>'''

    return html_page('About', body, css_path='/')


def build_map(posts):
    # Sidebar waypoint list (populated by map.js from WAYPOINTS array)

    # We'll populate the sidebar from map.js data via JS
    sidebar_script = '''
<script>
document.addEventListener('DOMContentLoaded', function() {
  const list = document.querySelector('.waypoint-list');
  if (!list || typeof WAYPOINTS === 'undefined') return;
  list.innerHTML = '';
  WAYPOINTS.forEach(function(wp, i) {
    const li = document.createElement('li');
    li.className = 'waypoint-item';
    li.dataset.waypoint = i;
    li.innerHTML = '<div class="waypoint-name">' + wp.name + '</div><div class="waypoint-date">' + wp.date + '</div>';
    list.appendChild(li);
  });
});
</script>'''

    body = f'''
<a class="map-back" href="/blog.html">← Blog</a>
<div class="map-page">
  <div id="journey-map" aria-label="Interactive route map of S/V Oroboro"></div>
  <aside class="map-sidebar" aria-label="Journey waypoints">
    <h2>Route — {len(posts)} stops</h2>
    <ul class="waypoint-list" aria-label="Waypoints"></ul>
  </aside>
</div>'''

    extra_head = '''  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
  <style>body { overflow: hidden; }</style>'''
    extra_scripts = f'''<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="/js/map.js"></script>
{sidebar_script}'''

    return html_page('Journey Map', body, css_path='/', extra_head=extra_head,
                     extra_scripts=extra_scripts, body_class='map-page-body')


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    POSTS_DIR.mkdir(exist_ok=True)
    CONTENT_DIR.mkdir(exist_ok=True)

    # ── Legacy WordPress posts ────────────────────────────────────────────────
    legacy_posts = parse_wordpress_xml(WP_XML)
    if not legacy_posts:
        print("ERROR: No posts found. Check the XML path.")
        return

    # Apply sort-date overrides (event date ≠ pubDate for some legacy posts)
    for p in legacy_posts:
        p['sort_date']        = SORT_DATE_OVERRIDES.get(p['slug'], p['iso_date'])
        p['published_display'] = None
        p['is_markdown']      = False
        p['is_prebuilt']      = False
        p['nav_exclude']      = False

    # ── Markdown posts from content/ ─────────────────────────────────────────
    md_posts = parse_markdown_posts()

    # ── Markdown overrides legacy: drop XML post when same slug exists in content/ ──
    md_slugs = {p['slug'] for p in md_posts}
    filtered = []
    for p in legacy_posts:
        if p['slug'] in md_slugs:
            print(f"  slug '{p['slug']}': markdown overrides legacy, skipping XML version")
        else:
            filtered.append(p)
    legacy_posts = filtered

    # ── Merge all sources and sort chronologically by sort_date ──────────────
    all_posts = legacy_posts + md_posts + PREBUILT_POSTS
    all_posts.sort(key=lambda p: p.get('sort_date') or p.get('iso_date') or '0000')

    voyage_posts = [p for p in all_posts if not p.get('is_prebuilt')]
    total_generated = len([p for p in all_posts if not p.get('is_prebuilt')])

    # ── Static pages ─────────────────────────────────────────────────────────
    print("Building index.html...")
    (OUT_DIR / 'index.html').write_text(build_index(all_posts), encoding='utf-8')

    print("Building blog.html...")
    (OUT_DIR / 'blog.html').write_text(build_blog(all_posts), encoding='utf-8')

    print("Building about.html...")
    (OUT_DIR / 'about.html').write_text(build_about(), encoding='utf-8')

    print("Building map.html...")
    (OUT_DIR / 'map.html').write_text(build_map(all_posts), encoding='utf-8')

    # ── Post pages (skip prebuilt — their HTML is hand-authored) ─────────────
    print(f"Building {total_generated} post pages...")
    for i, post in enumerate(all_posts):
        if post.get('is_prebuilt'):
            continue
        prev_post = all_posts[i - 1] if i > 0 else None
        next_post = all_posts[i + 1] if i < len(all_posts) - 1 else None
        post_html = build_post(post, prev_post, next_post)
        out_path  = POSTS_DIR / f'{post["slug"]}.html'
        out_path.write_text(post_html, encoding='utf-8')

    print(f"\n✓ Built {total_generated + 4} HTML files successfully.")
    print(f"  Voyage posts : {total_generated}  ({len(legacy_posts)} legacy + {len(md_posts)} markdown)")
    print(f"  Tech posts   : {len(PREBUILT_POSTS)}  (pre-built, not regenerated)")
    print(f"  Site         : {OUT_DIR}")
    print("\nTo deploy:")
    print("  git add -A && git commit -m 'Build site' && git push")


if __name__ == '__main__':
    main()
