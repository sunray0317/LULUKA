"""Generate SDG navigation/categories and apply pre-encoded responsive media.

No network, JavaScript runtime, or image encoder is required for publication.
"""
from pathlib import Path
from html import escape, unescape
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261031-catalog'


def projects():
    rows = json.loads((ROOT / 'data/visual-design-projects.json').read_text(encoding='utf-8'))
    for row in rows:
        assert re.fullmatch(r'[a-z0-9-]+', row['id'])
        assert row['url'] == f"/visual-design/{row['id']}/"
        assert all(isinstance(goal, int) and 1 <= goal <= 17 for goal in row['goals'])
    return rows


def goals():
    return json.loads((ROOT / 'data/sdg-goals.json').read_text(encoding='utf-8'))


def strip_header(html):
    return re.sub(r'<!-- SDG_HEADER_START -->[\s\S]*?<!-- SDG_HEADER_END -->', '', html)


def header(html, scope, related, current=None):
    html = strip_header(html)
    html = re.sub(r'<link rel="stylesheet" href="/brands/assets/sdg-(?:header|navigation)\.css[^\"]*">', '', html)
    html = re.sub(r'<script src="/brands/assets/(?:sdg-header|banner-trial)\.js[^\"]*" defer></script>', '', html)
    home_version = hashlib.sha256((ROOT / 'brands/assets/sdg-overview.svg').read_bytes()).hexdigest()[:12]
    links = [f'<a class="sdg-button sdg-home" href="/visual-design/" aria-label="0／返回視覺設計總覽" title="視覺設計總覽"><img src="/brands/assets/sdg-overview.svg?v={home_version}" alt="" width="160" height="160" loading="eager" decoding="async"></a>']
    for goal in goals():
        number = goal['id']
        active = number in related
        selected = ' aria-current="page"' if number == current else ''
        links.append(f'<a class="sdg-button{" is-related" if active else ""}" href="/visual-design/sdgs/{number}/" data-goal="{number}" data-related="{str(active).lower()}" aria-label="SDG {number} {goal["name"]}：瀏覽對應設計作品" title="SDG {number}｜{goal["name"]}"{selected}><img src="/brands/assets/sdg/sdg-{number:02}.png" alt="" width="160" height="160" loading="eager" decoding="async"></a>')
    values = '.68 .68 .68 .68 .68 .68 .68 .68 .68 1 1'
    functions = ''.join(f'<feFunc{c} type="table" tableValues="{values}"/>' for c in 'RGB')
    filter_svg = f'<svg xmlns="http://www.w3.org/2000/svg" class="sdg-filter-defs" width="0" height="0" aria-hidden="true"><defs><filter id="sdg-neutral" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/><feComponentTransfer>{functions}</feComponentTransfer></filter></defs></svg>'
    navigation = f'<!-- SDG_HEADER_START --><nav class="sdg-navigation" data-sdg-scope="{scope}" aria-label="永續發展目標作品分類">{filter_svg}<div class="sdg-strip">{"".join(links)}</div></nav><!-- SDG_HEADER_END -->'
    def body(match):
        attrs = match.group(1)
        if 'class="' in attrs:
            attrs = re.sub(r'class="([^\"]*)"', lambda m: 'class="' + ' '.join(dict.fromkeys(m[1].split() + ['has-sdg-header'])) + '"', attrs)
        else:
            attrs += ' class="has-sdg-header"'
        return '<body' + attrs + '>' + navigation
    html = re.sub(r'<body\b([^>]*)>', body, html, count=1)
    return html.replace('</head>', f'<link rel="stylesheet" href="/brands/assets/sdg-navigation.css?v={VERSION}"></head>')


def attrs(tag):
    return {key: unescape(value) for key, value in re.findall(r'([\w:-]+)="([^\"]*)"', tag)}


def optimize_html(html, relative, delivery):
    """Native srcset selection, eager first-screen images, no delayed JS reveal."""
    html = re.sub(r'<link\b[^>]*data-portfolio-preload="true"[^>]*>', '', html)
    image_index = 0
    preload = None
    overview = relative == 'visual-design/index.html'
    def image(match):
        nonlocal image_index, preload
        a = attrs(match[0])
        original = unescape(a.get('data-original-src', a.get('src', '')))
        entry = delivery.get(original)
        if not entry:
            return match[0]
        variants = entry['variants']
        icon = original.startswith('/brands/assets/sdg/')
        if icon:
            sizes = '(max-width:600px) 80px, 112px' if a.get('class') == 'sdg-lead-icon' else '(max-width:900px) 64px, 5.5556vw'
        elif relative.startswith('visual-design/sdgs/') and '<article class="project ' not in html:
            ratio = entry['width'] / entry['height']
            sizes = f'(max-width:600px) min(calc(100vw - 40px), {240*ratio:.1f}px), (max-width:900px) min(calc((100vw - 96px)/2), {280*ratio:.1f}px), min(544px, calc((100vw - 128px)/2), {280*ratio:.1f}px)'
        elif overview or relative.startswith('visual-design/sdgs/'):
            # Twice the visible width is needed for the existing quarter-view crops.
            before = html[:match.start()]
            article = before.rsplit('<article', 1)[-1]
            factor = 2 if 'artwork-crop' in before.rsplit('<figure', 1)[-1] else 1
            ratio = float(a.get('width', 1)) / float(a.get('height', 1))
            if 'lifeline-project' in article:
                total, gaps = 5.396158809300389, 3
            elif 'scouts-project' in article:
                total, gaps = 6.297436358904954, 3
            else:
                total, gaps = 4.232518568179475, 5
            share = ratio / total * factor
            sizes = f'(min-width:1776px) {(1680-gaps*12)*share:.1f}px, (max-width:600px) calc((100vw - {40+gaps*8}px)*{share:.6f}), (max-width:900px) calc((100vw - {64+gaps*12}px)*{share:.6f}), calc((100vw - {96+gaps*12}px)*{share:.6f})'
        elif original.endswith(('election-2026-poster.png', 'election-2026-entrance.png')):
            sizes = '(max-width:600px) 120px, 160px'
        elif original.endswith('election-2026-seating.png'):
            sizes = '(max-width:600px) 240px, 380px'
        elif original.endswith(('election-2026-delegation.png', 'election-2026-credential.png')):
            sizes = '(max-width:600px) 160px, 360px'
        elif 'banner-centered' in original or 'project-views' in original:
            factor = 2 if 'project-views' in original else 1
            sizes = f'(max-width:600px) calc((100vw - 40px)*{factor}), (max-width:900px) calc((100vw - 64px)*{factor}), (min-width:1216px) {1120*factor}px, calc((100vw - 96px)*{factor})'
        else:
            sizes = '(max-width:600px) calc(100vw - 40px), (min-width:1216px) 686px, 60vw'
        default_width = 160 if icon else 640 if overview else 960
        selected = min(variants, key=lambda row: abs(row['width'] - default_width))
        a['width'] = 160 if icon else entry['width']
        a['height'] = 160 if icon else entry['height']
        a['src'] = selected['url']
        a['srcset'] = ', '.join(f'{row["url"]} {row["width"]}w' for row in variants)
        a['sizes'] = sizes
        a['data-original-src'] = original
        a['decoding'] = 'async'
        if icon:
            a['loading'] = 'eager'
            a.pop('fetchpriority', None)
        else:
            first = image_index == 0
            a['loading'] = 'eager' if overview or relative.startswith('visual-design/sdgs/') or first or a.get('fetchpriority') == 'high' else 'lazy'
            a['fetchpriority'] = 'high' if first else 'auto'
            image_index += 1
            if first:
                preload = {key: a[key] for key in ('src', 'srcset', 'sizes')}
        return '<img ' + ' '.join(f'{key}="{escape(str(value), quote=True)}"' for key, value in a.items()) + '>'
    html = re.sub(r'<img\b[^>]*>', image, html)
    if preload:
        link = f'<link rel="preload" as="image" href="{escape(preload["src"], quote=True)}" imagesrcset="{escape(preload["srcset"], quote=True)}" imagesizes="{escape(preload["sizes"], quote=True)}" fetchpriority="high" data-portfolio-preload="true">'
        html = html.replace('</head>', link + '</head>')
    return html


def category(goal, matching):
    number, name = goal['id'], goal['name']
    canonical = f'https://luluka.org/visual-design/sdgs/{number}/'
    description = f'SDG {number} {name}：瀏覽 LULUKA 對應此永續發展目標的設計作品。'
    schema = json.dumps({'@context':'https://schema.org','@type':'CollectionPage','name':description,'url':canonical,'inLanguage':'zh-TW','mainEntity':{'@type':'ItemList','numberOfItems':len(matching),'itemListElement':[{'@type':'ListItem','position':i+1,'url':'https://luluka.org'+row['url'],'name':row['title']} for i,row in enumerate(matching)]}}, ensure_ascii=False, separators=(',', ':'))
    digest = hashlib.sha256(schema.encode()).digest()
    import base64
    sha = base64.b64encode(digest).decode()
    overview = (ROOT / 'visual-design/index.html').read_text(encoding='utf-8')
    articles = re.findall(r'<article class="project\b[\s\S]*?</article>', overview)
    cards = ''.join(next(article for article in articles if f'href="{row["url"]}"' in article) for row in matching)
    results = f'<div class="sdg-project-rows">{cards}</div>' if matching else ''
    html = f'<!doctype html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SDG {number} {name}｜LULUKA 設計作品</title><meta name="description" content="{description}"><meta name="theme-color" content="#ffffff"><link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:title" content="SDG {number} {name}｜LULUKA"><meta property="og:description" content="{description}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="https://luluka.org/brands/assets/sdg/sdg-{number:02}.png"><meta name="twitter:card" content="summary"><link rel="stylesheet" href="/brands/assets/visual-design.css?v={VERSION}"><link rel="stylesheet" href="/brands/assets/sdg-projects.css?v={VERSION}"><script type="application/ld+json">{schema}</script><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'sha256-{sha}\'; style-src \'self\'; img-src \'self\'; object-src \'none\'; base-uri \'none\'; form-action \'none\'"></head><body class="sdg-project-page" id="top"><main class="sdg-results"><header class="sdg-intro"><img class="sdg-lead-icon" src="/brands/assets/sdg/sdg-{number:02}.png" alt="SDG {number} {name}" width="160" height="160" loading="eager"><div><p class="sdg-number">SDG {number:02}</p><h1>{name}</h1><p>{goal["summary"]}</p></div></header>{results}<footer><a href="https://sdgs.un.org/goals/goal{number}" target="_blank" rel="noopener noreferrer">聯合國目標說明 ↗</a></footer></main></body></html>'
    return header(html, 'goal', [number], current=number)


def build(root=None):
    global ROOT
    if root is not None:
        ROOT = Path(root)
    if not (ROOT / 'data/visual-design-projects.json').is_file():
        return
    registry = projects()
    delivery_file = ROOT / 'docs/portfolio-image-delivery.json'
    delivery = json.loads(delivery_file.read_text(encoding='utf-8'))['images'] if delivery_file.is_file() else {}
    manifest_file = ROOT / 'scripts/public-files.json'
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    pages = [('visual-design/index.html', 'collection', sorted({n for row in registry for n in row['goals']}))]
    pages += [(row['url'].lstrip('/')+'index.html', row['id'], row['goals']) for row in registry]
    for relative, scope, active in pages:
        file = ROOT / relative
        html = header(file.read_text(encoding='utf-8'), scope, active)
        file.write_text(optimize_html(html, relative, delivery), encoding='utf-8')
    for goal in goals():
        relative = f'visual-design/sdgs/{goal["id"]}/index.html'
        file = ROOT / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(optimize_html(category(goal, [row for row in registry if goal['id'] in row['goals']]), relative, delivery), encoding='utf-8')
        if relative not in manifest:
            manifest.append(relative)
    if 'brands/assets/sdg-projects.css' not in manifest:
        manifest.append('brands/assets/sdg-projects.css')
    if 'brands/assets/sdg-overview.svg' not in manifest:
        manifest.append('brands/assets/sdg-overview.svg')
    manifest = [file for file in manifest if file not in ('brands/assets/sdg-header.js', 'brands/assets/sdg-header.css')]
    if 'brands/assets/sdg-navigation.css' not in manifest:
        manifest.append('brands/assets/sdg-navigation.css')
    if delivery_file.is_file():
        media_data = json.loads(delivery_file.read_text(encoding='utf-8'))
        for entry in media_data['images'].values():
            for variant in entry['variants']:
                file = variant['url'].lstrip('/')
                if file not in manifest:
                    manifest.append(file)
        for css_file in ROOT.glob('brands/assets/*.css'):
            css = css_file.read_text(encoding='utf-8')
            for original, replacement in media_data.get('backgrounds', {}).items():
                css = css.replace(original, replacement)
            css_file.write_text(css, encoding='utf-8')
        # Reuse the same image delivery on every public page, including the logo.
        # Version CSS by content after replacing backgrounds, so new styles load immediately.
        for relative in manifest:
            if relative.endswith('.html'):
                file = ROOT / relative
                html = optimize_html(file.read_text(encoding='utf-8'), relative, delivery)
                def stylesheet(match):
                    url = match.group(2)
                    css_file = ROOT / url.lstrip('/')
                    digest = hashlib.sha256(css_file.read_bytes()).hexdigest()[:12]
                    return match.group(1) + url + '?v=' + digest + '"'
                html = re.sub(r'(<link\b[^>]*rel="stylesheet"[^>]*href=")(/brands/assets/[^\"?]+\.css)(?:\?[^\"]*)?"', stylesheet, html)
                file.write_text(html, encoding='utf-8')
    manifest_file.write_text(json.dumps(sorted(manifest), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    sitemap_file = ROOT / 'sitemap.xml'
    sitemap = sitemap_file.read_text(encoding='utf-8')
    sitemap = re.sub(r'<url><loc>https://luluka.org/visual-design/sdgs/\d+/</loc></url>\s*', '', sitemap)
    sitemap = sitemap.replace('</urlset>', ''.join(f'<url><loc>https://luluka.org/visual-design/sdgs/{n}/</loc></url>\n' for n in range(1,18))+'</urlset>')
    sitemap_file.write_text(sitemap, encoding='utf-8')


if __name__ == '__main__':
    if '--header' in sys.argv:
        scope = sys.argv[sys.argv.index('--header')+1]
        row = next((row for row in projects() if row['id'] == scope or scope == 'girl-scouts' and row['id'] == 'girl-scouts-2026'), None)
        print(header(sys.stdin.read(), scope, row['goals'] if row else []), end='')
    else:
        build()
        print('SDG categories and responsive visual-design pages prepared.')
