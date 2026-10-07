"""Upload a verified external backup; verify every download before any cleanup.

Never stores credentials. Writes the verification receipt outside the checkout.
Does not delete local files, change Git history or push.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import quote
import argparse
import base64
import hashlib
import json
import mimetypes
import os
import re
import sys
import tarfile
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATHS = {f'brands/assets/{s}-social.png' for s in ['luluka','xiaomai','kaiaote','yongbindata']} | {'brands/assets/favicon.svg'}


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.words = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script','style'}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {'script','style'} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.words.append(data.strip())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def storage_filename(path):
    name = Path(path).name
    return name if re.fullmatch(r'[A-Za-z0-9._-]+',name) else 'original'+Path(path).suffix.lower()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup-dir', required=True)
    parser.add_argument('--project-url', required=True)
    parser.add_argument('--verify-backup', action='store_true')
    parser.add_argument('--key-mode', choices=['secret','legacy-jwt'], default='secret')
    args = parser.parse_args()
    backup = Path(args.backup_dir).resolve()
    if backup.is_relative_to(ROOT):
        raise RuntimeError('Backup and receipts must remain outside the checkout')
    url = args.project_url.rstrip('/')
    if not re.fullmatch(r'https://[a-z0-9]{20}\.supabase\.co',url):
        raise RuntimeError('Invalid project URL')
    inventory = json.loads((backup/'inventory.json').read_text())
    with tarfile.open(backup/'content.tar.gz','r:gz') as archive:
        entries = []
        for row in inventory:
            path = row['path']
            if Path(path).is_absolute() or '..' in Path(path).parts:
                raise RuntimeError('Unsafe backup path')
            data = archive.extractfile(path).read()
            if digest(data) != row['sha256'] or len(data) != row['bytes']:
                raise RuntimeError('Backup checksum mismatch')
            entries.append((path,data))
        legacy = archive.extractfile('legacy-index.html').read()
        entries.append(('legacy-index.html',legacy))
    print(f'Backup verified: {len(entries)} content files')
    if args.verify_backup:
        return
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if not key:
        raise RuntimeError('Missing secure SUPABASE_SERVICE_ROLE_KEY binding; no upload attempted')

    def request(path, method='GET', body=None, content_type=None, headers=None, anonymous=False, return_headers=False):
        h = {} if anonymous else {'apikey':key}
        if not anonymous and args.key_mode == 'legacy-jwt':
            h['Authorization'] = 'Bearer ' + key
        if content_type:
            h['Content-Type'] = content_type
        h.update(headers or {})
        try:
            with urllib.request.urlopen(urllib.request.Request(url+path,data=body,headers=h,method=method),timeout=60) as response:
                data = response.read()
                return (data,dict(response.headers)) if return_headers else data
        except urllib.error.HTTPError as error:
            # Parse only a short error CODE, never headers or response records.
            category = ''
            try:
                details = json.loads(error.read())
                code = details.get('error', details.get('code', ''))
                if isinstance(code,str) and re.fullmatch(r'[A-Za-z0-9_ -]{1,60}',code):
                    category = '; error code: ' + code
            except (ValueError,AttributeError):
                pass
            raise RuntimeError(f'{method} operation failed (HTTP {error.code}{category})') from None
        except urllib.error.URLError:
            raise RuntimeError('Supabase Storage connection failed; check network and TLS trust') from None

    bucket_info = json.loads(request('/storage/v1/bucket'))
    if not isinstance(bucket_info,list):
        raise RuntimeError('Unexpected bucket response')
    bucket_flags = {x.get('id'):x.get('public') for x in bucket_info}
    if bucket_flags.get('luluka-content-archive') is not False or bucket_flags.get('luluka-public-media') is not True:
        raise RuntimeError('Required archive/public bucket configuration is missing')

    def upload_verified(bucket, object_key, data, content_type, public=False):
        object_path = quote(bucket+'/'+object_key,safe='/')
        # Content-addressed keys make retries safe. Download first, then upload
        # only when absent; never replace an object with different contents.
        get_path = '/storage/v1/object/'+('public/' if public else 'authenticated/')+object_path
        existing = None
        try:
            existing = request(get_path,anonymous=public)
        except RuntimeError as error:
            if 'HTTP 400' not in str(error) and 'HTTP 404' not in str(error):
                raise
        if existing is None:
            if len(data) > 6*1024*1024:
                metadata = ','.join(k+' '+base64.b64encode(v.encode()).decode() for k,v in
                                    [('bucketName',bucket),('objectName',object_key),
                                     ('contentType',content_type),('cacheControl','3600')])
                _,response_headers = request('/storage/v1/upload/resumable','POST',b'',headers={
                    'Tus-Resumable':'1.0.0','Upload-Length':str(len(data)),
                    'Upload-Metadata':metadata,'x-upsert':'false'},return_headers=True)
                location = next((v for k,v in response_headers.items() if k.lower()=='location'),None)
                if not location:
                    raise RuntimeError('Resumable upload did not return its location')
                if location.startswith(url+'/'):
                    location=location[len(url):]
                if not location.startswith('/storage/v1/upload/resumable/'):
                    raise RuntimeError('Unexpected resumable upload destination')
                for offset in range(0,len(data),6*1024*1024):
                    chunk=data[offset:offset+6*1024*1024]
                    _,response_headers=request(location,'PATCH',chunk,'application/offset+octet-stream',
                        {'Tus-Resumable':'1.0.0','Upload-Offset':str(offset)},return_headers=True)
                    returned=next((v for k,v in response_headers.items() if k.lower()=='upload-offset'),None)
                    if returned is None or int(returned)!=offset+len(chunk):
                        raise RuntimeError('Resumable upload offset mismatch')
            else:
                request('/storage/v1/object/'+object_path,'POST',data,content_type,{'x-upsert':'false'})
            existing = request(get_path,anonymous=public)
        if digest(existing) != digest(data) or len(existing) != len(data):
            raise RuntimeError('Remote download checksum mismatch; no cleanup allowed')
        return url+get_path

    receipt = {'project_url':url,'complete':False,'files':[]}
    receipt_path = backup/'supabase-receipt.json'
    for index,(path,data) in enumerate(entries,1):
        sha = digest(data)
        content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        # This inventory currently contains supported images and HTML only.
        if content_type == 'application/octet-stream':
            raise RuntimeError('Unsupported content type; review the inventory before upload')
        object_key = sha+'/'+storage_filename(path)
        private_url = upload_verified('luluka-content-archive',object_key,data,content_type)
        # Test that originals are not anonymously downloadable.
        public_probe = '/storage/v1/object/public/'+quote('luluka-content-archive/'+object_key,safe='/')
        try:
            request(public_probe,anonymous=True)
        except RuntimeError as error:
            if not any(f'HTTP {status}' in str(error) for status in [400,401,403,404]):
                raise
        else:
            raise RuntimeError('Private original was accessible anonymously; no cleanup allowed')
        public_url = None
        if path in PUBLIC_PATHS:
            public_url = upload_verified('luluka-public-media',object_key,data,content_type,public=True)
        plain_text = None
        if path.endswith('.html'):
            text = Text(); text.feed(data.decode('utf-8')); plain_text='\n'.join(text.words)
        record = {'source_path':path,'sha256':sha,'bytes':len(data),'object_key':object_key,'content_type':content_type,'plain_text':plain_text}
        request('/rest/v1/luluka_content_archive?on_conflict=source_path','POST',json.dumps(record,ensure_ascii=False).encode(),'application/json',{'Prefer':'resolution=merge-duplicates,return=minimal'})
        check = json.loads(request('/rest/v1/luluka_content_archive?source_path=eq.'+quote(path,safe='')+'&select=sha256,bytes'))
        if len(check)!=1 or check[0]['sha256']!=sha or check[0]['bytes']!=len(data):
            raise RuntimeError('Database archive receipt mismatch')
        receipt['files'].append({'path':path,'sha256':sha,'bytes':len(data),'archive_verified':True,'anonymous_archive_denied':True,'public_url':public_url})
        receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
        print(f'Verified file {index}/{len(entries)}')
    receipt['complete']=True
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(f'All {len(entries)} files verified; receipt saved outside checkout')


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        print(str(error),file=sys.stderr)
        sys.exit(1)
