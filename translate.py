#!/usr/bin/env python3
"""
Sailing Oroboro — Translation Script
Translates English HTML posts to Italian, Japanese, French, or Portuguese
using Claude (claude-opus-4-8) for high-quality narrative translation.

Usage:
  python3 translate.py <lang> <file_or_dir> [file_or_dir ...]
  python3 translate.py it posts/ilha-grande.html
  python3 translate.py it posts/          # translate all posts
  python3 translate.py it posts/ --force  # re-translate existing files

Requires:
  pip install anthropic
  export ANTHROPIC_API_KEY=sk-ant-...
"""

import os, re, sys, time
import anthropic

SITE_ROOT = os.path.dirname(os.path.abspath(__file__))

LANG_CONFIG = {
    'it': {'name': 'Italian',             'html_lang': 'it',    'back': '← Torna ai post'},
    'ja': {'name': 'Japanese',            'html_lang': 'ja',    'back': '← ブログ一覧へ'},
    'fr': {'name': 'French',              'html_lang': 'fr',    'back': '← Retour aux articles'},
    'pt': {'name': 'Brazilian Portuguese','html_lang': 'pt-BR', 'back': '← Voltar para os posts'},
}

SYSTEM_PROMPT = """\
You are a professional translator specialising in sailing, travel writing, and personal narrative.
You are translating a sailing blog written in the first person by Francesco (Italian-American) and \
Yuka (Japanese), a couple sailing around the world on their Leopard 40 catamaran Oroboro.

RULES — follow these exactly:
1. Translate only visible text content between HTML tags. Preserve all HTML tags, attributes, \
class names, ids, style values, and structure exactly as-is.
2. DO NOT translate: URLs, href/src values, class/id/style attributes, proper nouns for \
geographic places (Rio de Janeiro, Ilha Grande, Paraty, Cape Town, St Helena…), person names \
(Francesco, Yuka, Alex Thomson, Joaquin, Monica, Ricardo, Isabel, Philippe, Federique…), \
boat names (Oroboro, Hugo Boss, Plan B…), brand/race names (Vendée Globe, IMOCA, B&G…), \
HTML entities (&mdash; &amp; &nbsp; etc.).
3. DO translate: alt="" attributes on <img> tags when they contain descriptive English phrases.
4. In <figcaption>: keep "Photo N ·" and "Video N ·" numbering, location names in their \
original language, and dates unchanged. Translate only the descriptive sentence after the date.
5. Maintain the personal, warm, first-person narrative voice with occasional humour.
6. Use accurate sailing and nautical terminology in the target language.
7. Preserve all HTML entities, special characters, and line breaks.
8. Return ONLY the translated HTML block with no preamble, explanation, or markdown fences.\
"""


def call_claude(client: anthropic.Anthropic, content: str, lang: str) -> str:
    """Single Claude API call — translate `content` to `lang`."""
    lang_name = LANG_CONFIG[lang]['name']
    response = client.messages.create(
        model='claude-opus-4-8',
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{
            'role': 'user',
            'content': (
                f'Translate the following HTML to {lang_name}. '
                f'Return only the translated HTML:\n\n{content}'
            )
        }]
    )
    return response.content[0].text.strip()


def extract(html: str, pattern: str, flags: int = 0) -> str:
    m = re.search(pattern, html, flags)
    return m.group(1).strip() if m else ''


def process_post(src_path: str, lang: str, client: anthropic.Anthropic, force: bool = False) -> str:
    fname = os.path.basename(src_path)
    out_dir = os.path.join(SITE_ROOT, lang, 'posts')
    out_path = os.path.join(out_dir, fname)

    if os.path.exists(out_path) and not force:
        return f'SKIP (exists): {fname}'

    with open(src_path, 'r', encoding='utf-8') as f:
        html = f.read()

    cfg = LANG_CONFIG[lang]

    # ── Fix asset paths (posts/ is one level deeper in lang/posts/) ──────────
    html = html.replace('href="../css/style.css"', 'href="/css/style.css"')
    html = html.replace('src="../js/main.js"',   'src="/js/main.js"')

    # ── Set html[lang] attribute ──────────────────────────────────────────────
    html = re.sub(r'<html lang="en">', f'<html lang="{cfg["html_lang"]}">', html)

    # ── Extract translatable sections ─────────────────────────────────────────
    title_en  = extract(html, r'<title>(.*?)</title>')
    title_bare = re.sub(r'\s*[—–]\s*S/V Oroboro\s*$', '', title_en).strip()

    meta_en   = extract(html, r'<meta name="description" content="([^"]*)"')
    h1_en     = extract(html, r'<h1[^>]*>(.*?)</h1>', re.DOTALL)

    article_m = re.search(r'(<article[^>]*>)(.*?)(</article>)', html, re.DOTALL)
    article_en = article_m.group(2) if article_m else ''

    # Wrap everything in custom tags so Claude returns a single structured block
    bundle = (
        f'<t_title>{title_bare}</t_title>\n'
        f'<t_meta>{meta_en}</t_meta>\n'
        f'<t_h1>{h1_en}</t_h1>\n'
        f'<t_article>{article_en}</t_article>'
    )

    print(f'  → translating {len(bundle):,} chars to {cfg["name"]}…')
    translated = call_claude(client, bundle, lang)

    # ── Extract translated parts ──────────────────────────────────────────────
    title_tr   = extract(translated, r'<t_title>(.*?)</t_title>', re.DOTALL)
    meta_tr    = extract(translated, r'<t_meta>(.*?)</t_meta>',   re.DOTALL)
    h1_tr      = extract(translated, r'<t_h1>(.*?)</t_h1>',       re.DOTALL)
    article_tr = extract(translated, r'<t_article>(.*?)</t_article>', re.DOTALL)

    # ── Patch HTML ────────────────────────────────────────────────────────────
    if title_tr:
        full_title = f'{title_tr} — S/V Oroboro'
        html = re.sub(r'<title>.*?</title>', f'<title>{full_title}</title>', html)
        html = re.sub(r'(<meta property="og:title" content=")[^"]*(")',
                      f'\\g<1>{full_title}\\2', html)
        html = re.sub(r'(<meta name="twitter:title" content=")[^"]*(")',
                      f'\\g<1>{full_title}\\2', html)

    if meta_tr:
        for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
            html = re.sub(
                f'(<meta {attr} content=")[^"]*(")',
                f'\\g<1>{meta_tr}\\2', html
            )

    if h1_tr:
        html = re.sub(r'<h1([^>]*)>.*?</h1>', f'<h1\\1>{h1_tr}</h1>', html,
                      count=1, flags=re.DOTALL)

    if article_tr:
        html = html.replace(article_en, article_tr, 1)

    # ── Update og:url for language path ──────────────────────────────────────
    html = re.sub(
        r'(<meta property="og:url" content="https://sailingoroboro\.com)/posts/',
        f'\\1/{lang}/posts/', html
    )

    # ── Add hreflang links ────────────────────────────────────────────────────
    hreflang = (
        f'  <link rel="alternate" hreflang="en"'
        f' href="https://sailingoroboro.com/posts/{fname}">\n'
    )
    for l, lc in LANG_CONFIG.items():
        hreflang += (
            f'  <link rel="alternate" hreflang="{lc["html_lang"]}"'
            f' href="https://sailingoroboro.com/{l}/posts/{fname}">\n'
        )
    html = html.replace('</head>', hreflang + '</head>', 1)

    # ── Update "← Back to all posts" link ────────────────────────────────────
    # The article translation will have translated this text; just fix the href
    # so it points to the language blog page when we eventually create one.
    # For now we leave it pointing to /blog.html (English) — acceptable for v1.

    # ── Write output ──────────────────────────────────────────────────────────
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return f'OK: {out_path}'


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    lang = sys.argv[1]
    if lang not in LANG_CONFIG:
        print(f'Unknown language "{lang}". Choose from: {", ".join(LANG_CONFIG)}')
        sys.exit(1)

    force = '--force' in sys.argv
    args  = [a for a in sys.argv[2:] if not a.startswith('--')]

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('Error: ANTHROPIC_API_KEY environment variable not set.')
        print('  export ANTHROPIC_API_KEY=sk-ant-...')
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Collect HTML files
    paths = []
    for arg in args:
        if os.path.isdir(arg):
            paths.extend(sorted(
                os.path.join(arg, f) for f in os.listdir(arg)
                if f.endswith('.html')
            ))
        elif os.path.isfile(arg):
            paths.append(arg)
        else:
            print(f'Warning: {arg} not found, skipping.')

    if not paths:
        print('No HTML files found.')
        sys.exit(1)

    print(f'Translating {len(paths)} file(s) → {LANG_CONFIG[lang]["name"]}')
    print(f'Output dir: {SITE_ROOT}/{lang}/posts/\n')

    ok = skipped = errors = 0
    for i, path in enumerate(paths, 1):
        fname = os.path.basename(path)
        print(f'[{i}/{len(paths)}] {fname}')
        try:
            result = process_post(path, lang, client, force=force)
            print(f'  {result}')
            if result.startswith('SKIP'):
                skipped += 1
            else:
                ok += 1
            time.sleep(0.3)   # gentle on the API
        except anthropic.RateLimitError:
            print('  Rate limited — waiting 60 s…')
            time.sleep(60)
            try:
                result = process_post(path, lang, client, force=force)
                print(f'  {result}')
                ok += 1
            except Exception as e2:
                print(f'  ERROR (retry): {e2}')
                errors += 1
        except Exception as e:
            print(f'  ERROR: {e}')
            errors += 1

    print(f'\nDone — {ok} translated, {skipped} skipped, {errors} errors.')


if __name__ == '__main__':
    main()
