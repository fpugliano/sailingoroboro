#!/usr/bin/env python3
"""
generate_media_review.py — Sailing Oroboro local media library
Scans all posts/*.html and writes media-review.html (gitignored).

Usage:  python3 generate_media_review.py
Also auto-runs via .git/hooks/post-commit
"""

import os, re, sys
from pathlib import Path
from html import unescape

SITE_ROOT = Path(__file__).parent
POSTS_DIR = SITE_ROOT / 'posts'
OUTPUT    = SITE_ROOT / 'media-review.html'

SKIP_SRC = re.compile(r'/img/|/images/posts/|logo|favicon', re.I)

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', unescape(s)).strip()

def clean(s):
    return re.sub(r'\s+', ' ', strip_tags(s)).strip()


def load_blog_order():
    """Return ordered list of (slug, region, date) from blog.html."""
    result = []
    try:
        text = (SITE_ROOT / 'blog.html').read_text(encoding='utf-8')
    except FileNotFoundError:
        return result
    for m in re.finditer(r'href="/posts/([^"]+\.html)"[^>]*data-region="([^"]*)"', text):
        slug   = Path(m.group(1)).stem
        region = m.group(2)
        # find the date span near this position
        snippet = text[m.start():m.start()+800]
        dm = re.search(r'post-card-date">([^<]+)', snippet)
        date = dm.group(1).strip() if dm else ''
        result.append((slug, region, date))
    return result


def parse_post(path, region, date):
    text  = path.read_text(encoding='utf-8')
    slug  = path.stem

    m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL)
    title = clean(m.group(1)) if m else slug.replace('-', ' ').title()

    items = []
    for fig in re.finditer(r'<figure[^>]*>(.*?)</figure>', text, re.DOTALL):
        block = fig.group(1)

        cm = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', block, re.DOTALL)
        caption = clean(cm.group(1)) if cm else ''

        # YouTube
        yt = re.search(r'youtube\.com/embed/([A-Za-z0-9_-]+)', block)
        if yt:
            vid = yt.group(1)
            items.append({'kind': 'youtube',
                          'thumb': f'https://img.youtube.com/vi/{vid}/hqdefault.jpg',
                          'url': f'https://www.youtube.com/watch?v={vid}',
                          'caption': caption})
            continue

        # video with poster
        vm = re.search(r'<video[^>]*poster="([^"]+)"', block)
        if vm:
            sm = re.search(r'<source[^>]*src="([^"]+)"', block)
            items.append({'kind': 'video',
                          'thumb': vm.group(1),
                          'url': sm.group(1) if sm else '',
                          'caption': caption})
            continue

        # img
        im = re.search(r'<img[^>]*src="([^"]+)"', block)
        if im:
            src = im.group(1)
            if SKIP_SRC.search(src):
                continue
            kind = 'map' if ('/maps/' in src or src.endswith('.gif')) else 'photo'
            items.append({'kind': kind, 'thumb': src, 'url': src, 'caption': caption})

    return {'slug': slug, 'title': title, 'region': region, 'date': date, 'items': items}


BADGE = {'photo': ('badge-blue', 'photo'), 'video': ('badge-red', 'video'),
         'youtube': ('badge-red', 'YT'), 'map': ('badge-green', 'map')}

def item_html(it, post_title):
    kind    = it['kind']
    thumb   = it['thumb']
    url     = it['url']
    cap_esc = it['caption'].replace('"', '&quot;')
    pt_esc  = post_title.replace('"', '&quot;')
    bc, bl  = BADGE.get(kind, ('badge-blue', kind))
    play = ''
    if kind in ('video', 'youtube'):
        play = '<div class="play"><svg width="38" height="38" viewBox="0 0 38 38"><circle cx="19" cy="19" r="19" fill="rgba(0,0,0,.55)"/><polygon points="15,11 29,19 15,27" fill="white"/></svg></div>'
    return (
        f'<div class="item" data-kind="{kind}" data-url="{url}" '
        f'data-caption="{cap_esc}" data-post="{pt_esc}">'
        f'<div class="tw"><img data-src="{thumb}" src="" alt="">{play}'
        f'<span class="kb {bc}">{bl}</span></div>'
        f'<div class="cap">{it["caption"]}</div></div>'
    )


def write_html(posts, out):
    n_photos  = sum(1 for p in posts for i in p['items'] if i['kind'] == 'photo')
    n_videos  = sum(1 for p in posts for i in p['items'] if i['kind'] in ('video','youtube'))
    n_maps    = sum(1 for p in posts for i in p['items'] if i['kind'] == 'map')

    out.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oroboro Media Library</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:system-ui,sans-serif}}
.bar{{position:sticky;top:0;z-index:50;background:#161b22;border-bottom:1px solid #30363d;
      padding:.65rem 1rem;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap}}
.bar h1{{font-size:.9rem;font-weight:700;color:#58a6ff;white-space:nowrap}}
.stats{{font-size:.72rem;color:#8b949e;white-space:nowrap}}
#q{{flex:1;min-width:140px;max-width:260px;background:#0d1117;border:1px solid #30363d;
    border-radius:6px;color:#e6edf3;padding:.3rem .6rem;font-size:.8rem}}
#q:focus{{outline:none;border-color:#58a6ff}}
.fbs{{display:flex;gap:.35rem;flex-wrap:wrap}}
.fb{{background:#21262d;border:1px solid #30363d;border-radius:6px;color:#8b949e;
     font-size:.7rem;font-weight:700;letter-spacing:.05em;padding:.28rem .6rem;cursor:pointer}}
.fb:hover{{background:#30363d;color:#e6edf3}}
.fb.on{{background:#1f6feb;border-color:#1f6feb;color:#fff}}
.wrap{{padding:1.25rem 1rem;max-width:1600px;margin:0 auto}}
.ps{{margin-bottom:2.25rem}}
.ph{{display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;
     margin-bottom:.75rem;padding-bottom:.45rem;border-bottom:1px solid #21262d}}
.ph h2{{font-size:.95rem;font-weight:700}}
.ph h2 a{{color:#58a6ff;text-decoration:none}}
.ph h2 a:hover{{text-decoration:underline}}
.pm{{font-size:.72rem;color:#8b949e}}
.pc{{font-size:.68rem;color:#6e7681;margin-left:auto}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:.45rem}}
.item{{background:#161b22;border-radius:6px;overflow:hidden;cursor:pointer;
       border:1px solid #21262d;transition:.15s}}
.item:hover{{border-color:#58a6ff;transform:scale(1.013);z-index:2;position:relative}}
.item[hidden]{{display:none}}
.tw{{position:relative;padding-top:75%;background:#0d1117;overflow:hidden}}
.tw img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
          opacity:0;transition:opacity .3s}}
.tw img.show{{opacity:1}}
.play{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}}
.kb{{position:absolute;top:4px;right:4px;font-size:.58rem;font-weight:700;
     letter-spacing:.05em;padding:2px 5px;border-radius:4px}}
.badge-blue{{background:rgba(31,111,235,.8);color:#fff}}
.badge-red{{background:rgba(180,50,30,.85);color:#fff}}
.badge-green{{background:rgba(25,130,90,.85);color:#fff}}
.cap{{padding:.4rem .5rem;font-size:.67rem;line-height:1.4;color:#8b949e;
      background:#0d1117;border-top:1px solid #21262d}}
#lb{{display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.92);
     flex-direction:column;align-items:center;justify-content:center;gap:.85rem;padding:1rem}}
#lb.open{{display:flex}}
#lb img,#lb video{{max-width:96vw;max-height:80vh;border-radius:6px;object-fit:contain;cursor:default}}
#lb video{{background:#000}}
#lbc{{color:#cdd9e5;font-size:.8rem;text-align:center;max-width:680px;line-height:1.5}}
#lbx{{position:fixed;top:.75rem;right:1rem;font-size:1.5rem;color:#8b949e;cursor:pointer}}
#lbx:hover{{color:#fff}}
#lbn{{position:fixed;top:50%;transform:translateY(-50%);display:flex;
      justify-content:space-between;width:100%;padding:0 .6rem;pointer-events:none}}
.arr{{pointer-events:all;background:rgba(255,255,255,.1);border:none;color:#fff;
      font-size:1.5rem;cursor:pointer;border-radius:50%;width:42px;height:42px;
      display:flex;align-items:center;justify-content:center}}
.arr:hover{{background:rgba(255,255,255,.25)}}
</style>
</head>
<body>
<div class="bar">
  <h1>⚓ Oroboro Media</h1>
  <span class="stats">{len(posts)} posts &middot; {n_photos} photos &middot; {n_videos} videos &middot; {n_maps} maps</span>
  <input id="q" type="search" placeholder="Search captions&hellip;" autocomplete="off">
  <div class="fbs">
    <button class="fb on" data-k="all">All</button>
    <button class="fb" data-k="photo">Photos</button>
    <button class="fb" data-k="video">Videos</button>
    <button class="fb" data-k="youtube">YouTube</button>
    <button class="fb" data-k="map">Maps</button>
  </div>
</div>
<div class="wrap">
""")

    for p in posts:
        if not p['items']:
            continue
        slug  = p['slug']
        title = p['title']
        meta  = ' · '.join(x for x in [p['region'], p['date']] if x)
        n     = len(p['items'])
        out.write(
            f'<section class="ps" id="s-{slug}">'
            f'<div class="ph"><h2><a href="/posts/{slug}.html" target="_blank">{title}</a></h2>'
            f'<span class="pm">{meta}</span><span class="pc">{n} items</span></div>'
            f'<div class="grid">'
        )
        for it in p['items']:
            out.write(item_html(it, title))
        out.write('</div></section>\n')

    out.write("""</div>

<div id="lb">
  <span id="lbx" title="Close (Esc)">&#x2715;</span>
  <img id="lbi" src="" alt="" hidden>
  <video id="lbv" controls hidden></video>
  <div id="lbc"></div>
  <div id="lbn">
    <button class="arr" id="lbp">&#8249;</button>
    <button class="arr" id="lbn2">&#8250;</button>
  </div>
</div>

<script>
// lazy load
const io = new IntersectionObserver(es => {
  es.forEach(e => { if(e.isIntersecting){ const i=e.target; i.src=i.dataset.src; i.classList.add('show'); io.unobserve(i); } });
}, {rootMargin:'200px'});
document.querySelectorAll('img[data-src]').forEach(i => io.observe(i));

// filter + search
const all = Array.from(document.querySelectorAll('.item'));
const secs = Array.from(document.querySelectorAll('.ps'));
let ak = 'all';
function run(){
  const q = document.getElementById('q').value.toLowerCase();
  all.forEach(el => {
    const ok = (ak==='all'||el.dataset.kind===ak) &&
               (!q||el.dataset.caption.toLowerCase().includes(q)||el.dataset.post.toLowerCase().includes(q));
    el.hidden = !ok;
  });
  secs.forEach(s => {
    const v = s.querySelectorAll('.item:not([hidden])').length;
    s.hidden = v===0;
    const c = s.querySelector('.pc'); if(c) c.textContent = v ? v+' shown' : '';
  });
}
document.querySelectorAll('.fb').forEach(b => b.addEventListener('click', () => {
  document.querySelectorAll('.fb').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); ak=b.dataset.k; run();
}));
document.getElementById('q').addEventListener('input', run);

// lightbox
const lb=document.getElementById('lb'), lbi=document.getElementById('lbi'),
      lbv=document.getElementById('lbv'), lbc=document.getElementById('lbc');
let li=[], lx=0;
function open2(x){
  const it=li[x]; lx=x;
  lbi.hidden=true; lbv.hidden=true; lbv.pause&&lbv.pause();
  lbc.textContent=it.caption;
  if(it.kind==='video'){lbv.src=it.url;lbv.hidden=false;}
  else if(it.kind==='youtube'){lb.classList.remove('open');window.open(it.url,'_blank');return;}
  else{lbi.src=it.url;lbi.hidden=false;}
  lb.classList.add('open');
}
all.forEach(el => el.addEventListener('click', () => {
  li = all.filter(e=>!e.hidden).map(e=>({kind:e.dataset.kind,url:e.dataset.url,caption:e.dataset.caption}));
  const idx = li.findIndex(i=>i.url===el.dataset.url&&i.caption===el.dataset.caption);
  open2(Math.max(0,idx));
}));
function close2(){ lb.classList.remove('open'); lbv.pause&&lbv.pause(); }
document.getElementById('lbx').onclick = close2;
lb.addEventListener('click', e=>{ if(e.target===lb) close2(); });
document.getElementById('lbp').onclick  = e=>{ e.stopPropagation(); if(lx>0) open2(lx-1); };
document.getElementById('lbn2').onclick = e=>{ e.stopPropagation(); if(lx<li.length-1) open2(lx+1); };
document.addEventListener('keydown', e=>{
  if(!lb.classList.contains('open')) return;
  if(e.key==='Escape') close2();
  if(e.key==='ArrowLeft'&&lx>0) open2(lx-1);
  if(e.key==='ArrowRight'&&lx<li.length-1) open2(lx+1);
});
</script>
</body>
</html>""")


def main():
    print('Scanning posts…', flush=True)
    order = load_blog_order()

    ordered_slugs = [s for s, r, d in order]
    meta_map = {s: (r, d) for s, r, d in order}
    all_slugs = {p.stem for p in POSTS_DIR.glob('*.html')}
    for slug in sorted(all_slugs - set(ordered_slugs)):
        ordered_slugs.append(slug)

    posts = []
    for slug in ordered_slugs:
        path = POSTS_DIR / f'{slug}.html'
        if not path.exists():
            continue
        region, date = meta_map.get(slug, ('', ''))
        print(f'  {slug}', flush=True)
        p = parse_post(path, region, date)
        posts.append(p)

    print(f'Writing {OUTPUT}…', flush=True)
    with OUTPUT.open('w', encoding='utf-8') as f:
        write_html(posts, f)

    total = sum(len(p['items']) for p in posts)
    size  = OUTPUT.stat().st_size // 1024
    print(f'Done — {len(posts)} posts, {total} items, {size} KB', flush=True)


if __name__ == '__main__':
    main()
