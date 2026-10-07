"""Reverify a complete receipt, replace public references, remove local media.

Requires a verified archive outside the checkout and a server credential.
Does not rewrite Git history or push. Always rejects changed local media.
"""
from pathlib import Path
from urllib.parse import quote
import argparse
import hashlib
import json
import os
import re
import sys
import tarfile
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HOST = 'https://umstsvobrqgstsjdvpza.supabase.co'
MEDIA_EXTENSIONS = {'.png','.jpg','.jpeg','.gif','.svg','.webp','.mp4','.webm','.mp3','.wav'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def storage_filename(path):
    name = Path(path).name
    return name if re.fullmatch(r'[A-Za-z0-9._-]+',name) else 'original'+Path(path).suffix.lower()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup-dir',required=True)
    parser.add_argument('--key-mode', choices=['secret','legacy-jwt'], default='secret')
    args = parser.parse_args()
    backup = Path(args.backup_dir).resolve()
    if backup.is_relative_to(ROOT):
        raise RuntimeError('Backup must remain outside checkout')
    receipt = json.loads((backup/'supabase-receipt.json').read_text())
    inventory = json.loads((backup/'inventory.json').read_text())
    if receipt.get('complete') is not True or receipt.get('project_url') != EXPECTED_HOST:
        raise RuntimeError('Receipt is incomplete or belongs to another project')
    entries = {r['path']:r for r in receipt['files']}
    if len(entries) != len(receipt['files']) or set(entries) != {x['path'] for x in inventory} | {'legacy-index.html'}:
        raise RuntimeError('Receipt does not match complete backup inventory')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if not key:
        raise RuntimeError('Missing secure Storage credential')
    removals = []
    replacements = {}
    with tarfile.open(backup/'content.tar.gz','r:gz') as archive:
        for row in inventory:
            path = row['path']
            if Path(path).is_absolute() or '..' in Path(path).parts:
                raise RuntimeError('Unsafe inventory path')
            original = archive.extractfile(path).read()
            record = entries[path]
            if digest(original) != row['sha256'] or row['sha256'] != record['sha256'] or len(original) != record['bytes']:
                raise RuntimeError('Backup or receipt checksum mismatch')
            if record.get('archive_verified') is not True or record.get('anonymous_archive_denied') is not True:
                raise RuntimeError('Private archive verification missing')
            object_key = row['sha256']+'/'+storage_filename(path)
            headers = {'apikey':key}
            if args.key_mode == 'legacy-jwt':
                headers['Authorization'] = 'Bearer ' + key
            request = urllib.request.Request(EXPECTED_HOST+'/storage/v1/object/authenticated/'+quote('luluka-content-archive/'+object_key,safe='/'),headers=headers)
            try:
                with urllib.request.urlopen(request,timeout=60) as response:
                    remote = response.read()
            except (urllib.error.HTTPError,urllib.error.URLError):
                raise RuntimeError('Remote re-verification failed; local files retained') from None
            if digest(remote) != row['sha256']:
                raise RuntimeError('Remote checksum mismatch; local files retained')
            if Path(path).suffix.lower() in MEDIA_EXTENSIONS:
                local = ROOT/path
                if local.is_symlink() or not local.resolve().is_relative_to(ROOT):
                    raise RuntimeError('Local media path is unsafe')
                if local.exists() and digest(local.read_bytes()) != row['sha256']:
                    raise RuntimeError('Local media changed since backup; refusing to delete it')
                if local.exists():
                    removals.append(local)
                if record.get('public_url'):
                    expected = EXPECTED_HOST+'/storage/v1/object/public/'+quote('luluka-public-media/'+object_key,safe='/')
                    if record['public_url'] != expected:
                        raise RuntimeError('Unexpected public object URL')
                    with urllib.request.urlopen(expected,timeout=60) as response:
                        if digest(response.read()) != row['sha256']:
                            raise RuntimeError('Public derivative checksum mismatch')
                    replacements['https://luluka.org/'+path] = expected
                    replacements['/'+path] = expected
    # Validate everything before changing pages or deleting any originals.
    pages = [ROOT/'index.html',*[ROOT/s/'index.html' for s in ['xiaomai','kaiaote','yongbindata','privacy']]]
    changed = {}
    for page in pages:
        content = page.read_text()
        for old,new in sorted(replacements.items(),key=lambda x:len(x[0]),reverse=True):
            content = content.replace(old,new)
        content = content.replace("img-src 'self'", "img-src 'self' "+EXPECTED_HOST)
        changed[page] = content
    manifest_file = ROOT/'scripts/public-files.json'
    manifest = json.loads(manifest_file.read_text())
    removal_paths = {p.relative_to(ROOT).as_posix() for p in removals}
    manifest = [x for x in manifest if x not in removal_paths]
    for page,content in changed.items():
        page.write_text(content)
    manifest_file.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    for local in removals:
        local.unlink()
    for folder in sorted((ROOT/'website').rglob('*'),reverse=True) if (ROOT/'website').exists() else []:
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    if (ROOT/'website').exists() and not any((ROOT/'website').iterdir()):
        (ROOT/'website').rmdir()
    print(f'Re-verified archive; removed {len(removals)} unchanged local media files')
    print('Public HTML/code remains in Git; old media may still exist in Git history')


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        print(str(error),file=sys.stderr)
        sys.exit(1)
