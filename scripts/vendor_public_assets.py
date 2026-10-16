"""Vendor only already-public website assets; never read private Supabase data."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"https://[^\s\"<>'()]+\.supabase\.co/[^\s\"<>'()]+")
TEXT = {'.html', '.css', '.js', '.svg', '.txt'}
PUBLIC_BUCKETS = {'luluka-public-media', 'luluka-public-fonts'}

def assets():
    manifest = json.loads((ROOT / 'scripts/public-files.json').read_text(encoding='utf-8'))
    sources = {name: (ROOT / name).read_text(encoding='utf-8') for name in manifest if Path(name).suffix in TEXT}
    urls = sorted({u for content in sources.values() for u in PATTERN.findall(content)})
    return manifest, sources, urls

def destination(url):
    parts = urlsplit(url)
    prefix = '/storage/v1/object/public/'
    if parts.hostname != 'umstsvobrqgstsjdvpza.supabase.co' or not parts.path.startswith(prefix) or parts.query:
        raise ValueError('Unexpected URL: ' + url)
    relative = unquote(parts.path[len(prefix):])
    segments = relative.split('/')
    if segments[0] not in PUBLIC_BUCKETS or '..' in segments or len(segments) != 3:
        raise ValueError('Not an approved public object: ' + url)
    return 'brands/assets/vendor/' + relative

def download(url):
    relative = destination(url)
    target = ROOT / relative
    expected = relative.split('/')[-2]
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
        data = target.read_bytes()
    else:
        for attempt in range(4):
            try:
                with urlopen(Request(url, headers={'User-Agent': 'LULUKA-public-asset-migration'}), timeout=60) as response:
                    if response.status != 200:
                        raise ValueError('Unexpected HTTP response')
                    data = response.read()
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(1 + attempt)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise ValueError('Content hash mismatch: ' + relative)
    return {'source': url, 'path': relative, 'bytes': len(data), 'sha256': digest}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest, sources, urls = assets()
    print(json.dumps({'public_source_files': len(sources), 'public_remote_objects': len(urls),
                      'credential_presence': {name: bool(os.environ.get(name)) for name in
                       ['SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SECRET_KEY', 'SUPABASE_ACCESS_TOKEN', 'GITHUB_TOKEN', 'GH_TOKEN']}}), flush=True)
    if not args.apply:
        return
    rows = []
    for name in manifest:
        if name.startswith('brands/assets/vendor/'):
            data = (ROOT / name).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            source = 'https://umstsvobrqgstsjdvpza.supabase.co/storage/v1/object/public/' + name.removeprefix('brands/assets/vendor/')
            if digest != name.split('/')[-2]:
                rows.append(download(source))
            else:
                rows.append({'source': source, 'path': name, 'bytes': len(data), 'sha256': digest})
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(download, url) for url in urls]
        for future in as_completed(futures):
            row = future.result()
            rows = [previous for previous in rows if previous['path'] != row['path']]
            rows.append(row)
    # Text references inside downloaded SVGs and licenses are also localized.
    mapping = {r['source']: '/' + r['path'] for r in rows}
    downloaded_text = {r['path']: (ROOT / r['path']).read_text(encoding='utf-8') for r in rows if Path(r['path']).suffix in TEXT}
    for name, content in {**sources, **downloaded_text}.items():
        original = content
        for old, new in mapping.items():
            content = content.replace(old, new)
        unresolved = PATTERN.findall(content)
        if unresolved:
            raise ValueError('Unresolved nested remote asset in ' + name)
        if Path(name).suffix == '.html':
            content = content.replace('content="/brands/assets/vendor/', 'content="https://luluka.org/brands/assets/vendor/')
            content = content.replace(' https://umstsvobrqgstsjdvpza.supabase.co', '')
            content = re.sub(r'(\.(?:css|js))\?v=[^\"\s]+', r'\1?v=github-assets-20261016', content)
            inline_scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', content, re.S)
            hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode() + "'" for script in inline_scripts]
            content = re.sub(r"script-src[^;]*", "script-src 'self'" + (' ' + ' '.join(hashes) if hashes else ''), content)
        if content != original:
            (ROOT / name).write_text(content, encoding='utf-8', newline='\n')
    additions = [r['path'] for r in rows]
    (ROOT / 'scripts/public-files.json').write_text(json.dumps(sorted(set(manifest + additions)), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = ROOT / 'docs/public-assets-localized.json'
    report.write_text(json.dumps(sorted(rows, key=lambda r: r['path']), indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'downloaded': len(rows), 'bytes': sum(r['bytes'] for r in rows), 'report': str(report)}), flush=True)

if __name__ == '__main__':
    main()
