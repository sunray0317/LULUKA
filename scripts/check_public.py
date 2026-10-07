"""Validate publication boundaries, local links and brand SEO metadata."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import xml.etree.ElementTree as ET
import tempfile
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '.site'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.meta = {}
        self.canonical = None
        self.h1 = 0
        self.schema = []
        self.collect_schema = False
        self.language = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, f'Duplicate ID: {a["id"]}'
            self.ids.add(a['id'])
        if tag == 'html':
            self.language = a.get('lang')
        if tag == 'h1':
            self.h1 += 1
        if tag == 'meta':
            self.meta[a.get('name', a.get('property'))] = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical = a.get('href')
        if tag == 'script':
            self.collect_schema = a.get('type') == 'application/ld+json'
        if tag in {'a', 'img', 'script', 'link'}:
            url = a.get('href') if tag in {'a', 'link'} else a.get('src')
            if url:
                self.links.append(url)

    def handle_data(self, data):
        if self.collect_schema and data.strip():
            self.schema.append(json.loads(data))

    def handle_endtag(self, tag):
        if tag == 'script':
            self.collect_schema = False


def check():
    expected = set(json.loads((ROOT / 'scripts/public-files.json').read_text()))
    actual = {p.relative_to(SITE).as_posix() for p in SITE.rglob('*') if p.is_file()}
    assert actual == expected, f'Unexpected deployment files: {actual ^ expected}'
    pages = {}
    for path in SITE.rglob('*.html'):
        parser = Page()
        parser.feed(path.read_text())
        pages[path] = parser
        assert parser.language == 'zh-TW' and parser.h1 == 1, str(path)
        assert parser.meta.get('description') and parser.canonical, str(path)
    for path, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = (SITE / unquote(url.path).lstrip('/')) if url.path.startswith('/') else path.parent / unquote(url.path)
            if not url.path:
                target = path
            if target.is_dir():
                target /= 'index.html'
            assert target.is_file(), f'{path.name}: missing {link}'
            if url.fragment and target in pages:
                assert url.fragment in pages[target].ids, f'Broken anchor: {link}'
    for slug in ['xiaomai', 'kaiaote', 'yongbindata']:
        p = pages[SITE / slug / 'index.html']
        canonical = f'https://luluka.org/{slug}/'
        assert p.canonical == canonical == p.meta['og:url']
        assert p.schema and p.meta['og:description'] and p.meta['twitter:card'] == 'summary_large_image'
        image_url = urlsplit(p.meta['og:image'])
        if image_url.hostname == 'luluka.org':
            image = SITE / image_url.path.lstrip('/')
            assert image.is_file() and image.read_bytes().startswith(b'\x89PNG')
        else:
            import re
            assert image_url.scheme == 'https' and image_url.hostname == 'umstsvobrqgstsjdvpza.supabase.co'
            assert re.fullmatch(r'/storage/v1/object/public/luluka-public-media/[a-f0-9]{64}/'+slug+r'-social\.png',image_url.path)
    locations = {x.text for x in ET.parse(SITE / 'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
    assert locations == {p.canonical for p in pages.values()}, 'Sitemap does not match canonical pages'
    assert 'Sitemap: https://luluka.org/sitemap.xml' in (SITE / 'robots.txt').read_text()
    # Exercise the builder in an isolated fixture, including unlisted sensitive files.
    spec = importlib.util.spec_from_file_location('public_builder', ROOT / 'scripts/build_public.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    with tempfile.TemporaryDirectory() as folder:
        fixture = Path(folder)
        (fixture / 'scripts').mkdir()
        (fixture / 'index.html').write_text('public')
        (fixture / '.env').write_text('TEST_ONLY_NOT_A_REAL_SECRET')
        (fixture / 'private').mkdir()
        (fixture / 'private/record.txt').write_text('TEST_ONLY_PRIVATE_RECORD')
        manifest = fixture / 'scripts/public-files.json'
        manifest.write_text('["index.html"]')
        builder.ROOT, builder.DEST = fixture, fixture / '.site'
        builder.build()
        assert {p.name for p in builder.DEST.iterdir()} == {'index.html'}
        builder.build()  # Repeatability must not introduce more files.
        for bad in ['../escape.html', '.env', 'private/record.txt']:
            manifest.write_text(json.dumps(['index.html', bad]))
            try:
                builder.build()
            except ValueError:
                pass
            else:
                raise AssertionError(f'Builder accepted unsafe path: {bad}')
        (fixture / 'leak.html').symlink_to(fixture / '.env')
        manifest.write_text('["leak.html"]')
        try:
            builder.build()
        except ValueError:
            pass
        else:
            raise AssertionError('Builder published a symlink')
    print(f'Passed: {len(pages)} pages, local links, brand SEO, sitemap and deployment isolation tests')


if __name__ == '__main__':
    check()
