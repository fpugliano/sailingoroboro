#!/usr/bin/env python3
"""
generate_media_review.py — Sailing Oroboro local media library
Scans all posts/*.html and outputs media-review.html (gitignored).

Usage:  python3 generate_media_review.py
Also runs automatically via .git/hooks/post-commit
"""

import os, re
from pathlib import Path
from html import unescape

SITE_ROOT  = Path(__file__).parent
POSTS_DIR  = SITE_ROOT / 'posts'
OUTPUT     = SITE_ROOT / 'media-review.html'
R2_PREFIX  = 'pub-7f7d07c430fd4c3eb11a4e6eae938ce3.r2.dev'


# ── helpers ──────────────────────────────────────────────────────────────────

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', unescape(s)).strip()

def clean(s):
    return re.sub(r'\s+', ' ', strip_tags(s)).strip()


# ── parse blog.html for post order + region ───────────────────────────────────

def load_blog_meta():
    """Return {slug: {region, date, excerpt}} from blog.html post-card list."""
    meta = {}
    try:
        text = (SITE_ROOT / 'blog.html').read_text(encoding='utf-8')
    except FileNotFoundError:
        return meta
    for card in re.finditer(
        r'<a class="post-card"[^>]*href="/posts/([^"]+\.html)"[^>]*data-region="([^"]*)"[^>]*>'
        r'(.*?)</a>',
        text, re.DOTALL
    ):
        slug   = Path(card.group(1)).stem
        region = card.group(2)
        body   = card.group(3)
        date_m = re.search(r'<span class="post-card-date">([^<]+)', body)
        exc_m  = re.search(r'<p class="post-card-excerpt">([^<]+)', body)
        meta[slug] = {
            'region':  region,
            'date':    date_m.group(1).strip() if date_m else '',
            'excerpt': exc_m.group(1).strip()  if exc_m  else '',
        }
    return meta


# ── parse one post ────────────────────────────────────────────────────────────

SKIP_SRC = re.compile(r'/img/|/images/posts/|logo|favicon|site\.webmanifest', re.I)

def parse_post(path, blog_meta):
    text  = path.read_text(encoding='utf-8')
    slug  = path.stem
    bm    = blog_meta.get(slug, {})

    # title
    m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL)
    title = clean(m.group(1)) if m else slug.replace('-', ' ').title()

    items = []

    # Walk every <figure>…</figure> block
    for fig in re.finditer(r'<figure[^>]*>(.*?)</figure>', text, re.DOTALL):
        block = fig.group(1)

        cap_m   = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', block, re.DOTALL)
        caption = clean(cap_m.group(1)) if cap_m else ''

        # ── YouTube iframe ────────────────────────────────────────────────────
        yt = re.search(r'youtube\.com/embed/([A-Za-z0-9_-]+)', block)
        if yt:
            vid_id = yt.group(1)
            items.append({
                'kind':    'youtube',
                'thumb':   f'https://img.youtube.com/vi/{vid_id}/hqdefault.jpg',
                'url':     f'https://www.youtube.com/watch?v={vid_id}',
                'caption': caption,
            })
            continue

        # ── <video poster="…"> ────────────────────────────────────────────────
        vm = re.search(r'<video[^>]*poster="([^"]+)"', block)
        if vm:
            poster = vm.group(1)
            sm     = re.search(r'<source[^>]*src="([^"]+)"', block)
            src    = sm.group(1) if sm else ''
            items.append({
                'kind':    'video',
                'thumb':   poster,
                'url':     src,
                'caption': caption,
            })
            continue

        # ── <img src="…"> ────────────────────────────────────────────────────
        im = re.search(r'<img[^>]*src="([^"]+)"', block)
        if im:
            src = im.group(1)
            if SKIP_SRC.search(src):
                continue
            kind = 'map' if ('/maps/' in src or src.endswith('.gif')) else 'photo'
            items.append({
                'kind':    kind,
                'thumb':   src,
                'url':     src,
                'caption': caption,
            })

    return {
        'slug':    slug,
        'title':   title,
        'region':  bm.get('region', ''),
        'date':    bm.get('date', ''),
        'excerpt': bm.get('excerpt', ''),
        'items':   items,
    }


# ── HTML generation ───────────────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d1117; color: #e6edf3; font-family: system-ui, -apple-system, sans-serif;
       min-height: 100vh; }

/* ─ header ─ */
.toolbar { position: sticky; top: 0; z-index: 50; background: #161b22;
           border-bottom: 1px solid #30363d; padding: .75rem 1.25rem;
           display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; }
.toolbar h1 { font-size: .95rem; font-weight: 700; letter-spacing: .04em;
              color: #58a6ff; white-space: nowrap; margin-right: .5rem; }
.stats { font-size: .75rem; color: #8b949e; white-space: nowrap; }
#search { flex: 1; min-width: 160px; max-width: 280px; background: #0d1117;
          border: 1px solid #30363d; border-radius: 6px; color: #e6edf3;
          padding: .35rem .65rem; font-size: .82rem; }
#search:focus { outline: none; border-color: #58a6ff; }
.filters { display: flex; gap: .4rem; flex-wrap: wrap; }
.fbtn { background: #21262d; border: 1px solid #30363d; border-radius: 6px;
        color: #8b949e; font-size: .72rem; font-weight: 700; letter-spacing: .05em;
        padding: .3rem .65rem; cursor: pointer; transition: .15s; }
.fbtn:hover { background: #30363d; color: #e6edf3; }
.fbtn.active { background: #1f6feb; border-color: #1f6feb; color: #fff; }

/* ─ content ─ */
.content { padding: 1.5rem 1.25rem; max-width: 1600px; margin: 0 auto; }

/* ─ post section ─ */
.post-section { margin-bottom: 2.5rem; }
.post-header { display: flex; align-items: baseline; gap: .75rem; flex-wrap: wrap;
               margin-bottom: .85rem; padding-bottom: .5rem;
               border-bottom: 1px solid #21262d; }
.post-header h2 { font-size: 1rem; font-weight: 700; }
.post-header h2 a { color: #58a6ff; text-decoration: none; }
.post-header h2 a:hover { text-decoration: underline; }
.post-meta { font-size: .75rem; color: #8b949e; }
.post-count { font-size: .72rem; color: #6e7681; margin-left: auto; }

/* ─ grid ─ */
.media-grid { display: grid;
              grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
              gap: .5rem; }

/* ─ item ─ */
.item { position: relative; background: #161b22; border-radius: 6px; overflow: hidden;
        cursor: pointer; border: 1px solid #21262d;
        transition: border-color .15s, transform .15s; }
.item:hover { border-color: #58a6ff; transform: scale(1.015); z-index: 2; }
.item[hidden] { display: none; }

.thumb-wrap { position: relative; padding-top: 75%; background: #161b22; }
.thumb-wrap img { position: absolute; inset: 0; width: 100%; height: 100%;
                  object-fit: cover; display: block;
                  transition: opacity .3s; }
.thumb-wrap img.loading { opacity: 0; }

/* kind badge */
.kind-badge { position: absolute; top: 5px; right: 5px; font-size: .6rem;
              font-weight: 700; letter-spacing: .06em; padding: 2px 5px;
              border-radius: 4px; text-transform: uppercase; pointer-events: none; }
.badge-photo   { background: rgba(31,111,235,.75); color: #fff; }
.badge-video   { background: rgba(188,60,30,.85);  color: #fff; }
.badge-youtube { background: rgba(188,60,30,.85);  color: #fff; }
.badge-map     { background: rgba(30,140,100,.85);  color: #fff; }

/* play icon for video/yt */
.play-icon { position: absolute; inset: 0; display: flex; align-items: center;
             justify-content: center; pointer-events: none; }
.play-icon svg { filter: drop-shadow(0 1px 4px rgba(0,0,0,.7)); opacity: .9; }

/* caption */
.item-caption { padding: .45rem .55rem; font-size: .68rem; line-height: 1.45;
                color: #8b949e; background: #0d1117; border-top: 1px solid #21262d; }

/* ─ lightbox ─ */
#lb { display: none; position: fixed; inset: 0; z-index: 200;
      background: rgba(0,0,0,.92); cursor: zoom-out;
      flex-direction: column; align-items: center; justify-content: center; gap: 1rem;
      padding: 1rem; }
#lb.open { display: flex; }
#lb img, #lb video { max-width: 96vw; max-height: 82vh; border-radius: 6px;
                      object-fit: contain; cursor: default; }
#lb video { background: #000; }
#lb-caption { color: #cdd9e5; font-size: .82rem; text-align: center;
              max-width: 680px; line-height: 1.55; }
#lb-caption a { color: #58a6ff; }
#lb-close { position: fixed; top: 1rem; right: 1.25rem; font-size: 1.6rem;
             color: #8b949e; cursor: pointer; line-height: 1; }
#lb-close:hover { color: #fff; }
#lb-nav { position: fixed; top: 50%; transform: translateY(-50%);
          display: flex; justify-content: space-between; width: 100%;
          padding: 0 .75rem; pointer-events: none; }
.lb-arrow { pointer-events: all; background: rgba(255,255,255,.1);
            border: none; color: #fff; font-size: 1.6rem; cursor: pointer;
            border-radius: 50%; width: 44px; height: 44px; display: flex;
            align-items: center; justify-content: center; }
.lb-arrow:hover { background: rgba(255,255,255,.25); }

/* ─ empty state ─ */
.no-results { text-align: center; color: #6e7681; padding: 4rem 0; font-size: .9rem; }
"""

JS = r"""
// ── lazy load ──────────────────────────────────────────────────────────────
const obs = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const img = e.target;
      img.src = img.dataset.src;
      img.classList.remove('loading');
      obs.unobserve(img);
    }
  });
}, { rootMargin: '200px' });
document.querySelectorAll('img[data-src]').forEach(img => {
  img.classList.add('loading');
  obs.observe(img);
});

// ── filter / search ────────────────────────────────────────────────────────
const items   = Array.from(document.querySelectorAll('.item'));
const sections = Array.from(document.querySelectorAll('.post-section'));
let activeKind = 'all';

function applyFilters() {
  const q = document.getElementById('search').value.toLowerCase().trim();
  items.forEach(it => {
    const kind    = it.dataset.kind;
    const caption = it.dataset.caption.toLowerCase();
    const post    = it.dataset.post.toLowerCase();
    const kindOk  = activeKind === 'all' || kind === activeKind;
    const textOk  = !q || caption.includes(q) || post.includes(q);
    it.hidden = !(kindOk && textOk);
  });
  // Hide post sections with no visible items
  sections.forEach(sec => {
    const visible = sec.querySelectorAll('.item:not([hidden])').length;
    sec.hidden = visible === 0;
    const cnt = sec.querySelector('.post-count');
    if (cnt) cnt.textContent = visible ? `${visible} shown` : '';
  });
}

document.querySelectorAll('.fbtn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.fbtn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeKind = btn.dataset.kind;
    applyFilters();
  });
});
document.getElementById('search').addEventListener('input', applyFilters);

// ── lightbox ───────────────────────────────────────────────────────────────
const lb      = document.getElementById('lb');
const lbImg   = document.getElementById('lb-img');
const lbVid   = document.getElementById('lb-vid');
const lbCap   = document.getElementById('lb-caption');
let   lbItems = [], lbIdx = 0;

function openLb(idx) {
  const it = lbItems[idx];
  lbIdx = idx;
  lbImg.hidden = true;
  lbVid.hidden = true;
  lbVid.pause && lbVid.pause();
  lbCap.innerHTML = it.caption;
  if (it.kind === 'video') {
    lbVid.src = it.url;
    lbVid.hidden = false;
  } else if (it.kind === 'youtube') {
    // open in new tab
    lb.classList.remove('open');
    window.open(it.url, '_blank');
    return;
  } else {
    lbImg.src = it.url;
    lbImg.hidden = false;
  }
  lb.classList.add('open');
}

document.querySelectorAll('.item').forEach((el, i) => {
  el.addEventListener('click', () => {
    // Build filtered list for navigation
    lbItems = items.filter(it => !it.hidden).map(it => ({
      kind:    it.dataset.kind,
      url:     it.dataset.url,
      caption: it.dataset.caption,
    }));
    const clickIdx = lbItems.findIndex(it => it.url === el.dataset.url && it.caption === el.dataset.caption);
    openLb(Math.max(0, clickIdx));
  });
});

document.getElementById('lb-close').addEventListener('click', () => {
  lb.classList.remove('open');
  lbVid.pause && lbVid.pause();
});
lb.addEventListener('click', e => {
  if (e.target === lb) { lb.classList.remove('open'); lbVid.pause && lbVid.pause(); }
});
document.getElementById('lb-prev').addEventListener('click', e => {
  e.stopPropagation();
  if (lbIdx > 0) openLb(lbIdx - 1);
});
document.getElementById('lb-next').addEventListener('click', e => {
  e.stopPropagation();
  if (lbIdx < lbItems.length - 1) openLb(lbIdx + 1);
});
document.addEventListener('keydown', e => {
  if (!lb.classList.contains('open')) return;
  if (e.key === 'Escape') { lb.classList.remove('open'); lbVid.pause && lbVid.pause(); }
  if (e.key === 'ArrowLeft'  && lbIdx > 0)               openLb(lbIdx - 1);
  if (e.key === 'ArrowRight' && lbIdx < lbItems.length-1) openLb(lbIdx + 1);
});
"""

BADGE_LABELS = {'photo': 'photo', 'video': 'video', 'youtube': 'YT', 'map': 'map'}

def item_html(it, post_title):
    kind    = it['kind']
    thumb   = it['thumb']
    url     = it['url']
    caption = it['caption'].replace('"', '&quot;')
    ptitle  = post_title.replace('"', '&quot;')

    badge  = f'<span class="kind-badge badge-{kind}">{BADGE_LABELS[kind]}</span>'
    play   = ''
    if kind in ('video', 'youtube'):
        play = '<div class="play-icon"><svg width="40" height="40" viewBox="0 0 40 40"><circle cx="20" cy="20" r="20" fill="rgba(0,0,0,.55)"/><polygon points="16,12 30,20 16,28" fill="white"/></svg></div>'

    return (
        f'<div class="item" data-kind="{kind}" data-url="{url}" '
        f'data-caption="{caption}" data-post="{ptitle}">'
        f'<div class="thumb-wrap">'
        f'<img data-src="{thumb}" src="" alt="" loading="lazy">'
        f'{badge}{play}'
        f'</div>'
        f'<div class="item-caption">{it["caption"]}</div>'
        f'</div>'
    )


def generate(posts):
    total_photos  = sum(1 for p in posts for i in p['items'] if i['kind'] == 'photo')
    total_videos  = sum(1 for p in posts for i in p['items'] if i['kind'] in ('video', 'youtube'))
    total_maps    = sum(1 for p in posts for i in p['items'] if i['kind'] == 'map')
    total_items   = total_photos + total_videos + total_maps
    total_posts   = len(posts)

    filters = (
        '<div class="filters">'
        '<button class="fbtn active" data-kind="all">All</button>'
        '<button class="fbtn" data-kind="photo">Photos</button>'
        '<button class="fbtn" data-kind="video">Videos</button>'
        '<button class="fbtn" data-kind="youtube">YouTube</button>'
        '<button class="fbtn" data-kind="map">Maps</button>'
        '</div>'
    )

    sections_html = []
    for p in posts:
        if not p['items']:
            continue
        slug    = p['slug']
        title   = p['title']
        region  = p['region']
        date    = p['date']
        n       = len(p['items'])
        meta    = ' · '.join(x for x in [region, date] if x)
        post_url = f'/posts/{slug}.html'

        items_html = '\n'.join(item_html(it, title) for it in p['items'])
        sections_html.append(
            f'<section class="post-section" id="post-{slug}">'
            f'<div class="post-header">'
            f'<h2><a href="{post_url}" target="_blank">{title}</a></h2>'
            f'<span class="post-meta">{meta}</span>'
            f'<span class="post-count">{n} items</span>'
            f'</div>'
            f'<div class="media-grid">{items_html}</div>'
            f'</section>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oroboro Media Library</title>
<style>{CSS}</style>
</head>
<body>

<div class="toolbar">
  <h1>⚓ Oroboro Media Library</h1>
  <span class="stats">{total_posts} posts · {total_photos} photos · {total_videos} videos · {total_maps} maps</span>
  <input id="search" type="search" placeholder="Search captions…" autocomplete="off">
  {filters}
</div>

<div class="content">
{''.join(sections_html)}
<p class="no-results" id="no-results" style="display:none">No results</p>
</div>

<!-- lightbox -->
<div id="lb">
  <span id="lb-close" title="Close (Esc)">✕</span>
  <img id="lb-img" src="" alt="" hidden>
  <video id="lb-vid" controls hidden></video>
  <div id="lb-caption"></div>
  <div id="lb-nav">
    <button class="lb-arrow" id="lb-prev">&#8249;</button>
    <button class="lb-arrow" id="lb-next">&#8250;</button>
  </div>
</div>

<script>{JS}</script>
</body>
</html>"""


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print('Scanning posts…')
    blog_meta = load_blog_meta()

    # Preserve blog.html order (newest first), then append any unlisted posts
    ordered_slugs = list(blog_meta.keys())
    all_slugs = {p.stem for p in POSTS_DIR.glob('*.html')}
    extra = sorted(all_slugs - set(ordered_slugs))
    ordered_slugs += extra

    posts = []
    for slug in ordered_slugs:
        path = POSTS_DIR / f'{slug}.html'
        if path.exists():
            p = parse_post(path, blog_meta)
            posts.append(p)

    html = generate(posts)
    OUTPUT.write_text(html, encoding='utf-8')

    total = sum(len(p['items']) for p in posts)
    print(f'Written {OUTPUT}  ({len(posts)} posts, {total} media items)')


if __name__ == '__main__':
    main()
