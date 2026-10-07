"""Exercise upload, private visibility and checksum failures without credentials."""
from pathlib import Path
import contextlib
import base64
import hashlib
import importlib.util
import io
import json
import os
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlsplit, unquote, parse_qs

spec = importlib.util.spec_from_file_location('migration',Path(__file__).with_name('migrate_media.py'))
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)
final_spec = importlib.util.spec_from_file_location('finalizer',Path(__file__).with_name('finalize_media_migration.py'))
finalizer = importlib.util.module_from_spec(final_spec)
final_spec.loader.exec_module(finalizer)


class StorageMock:
    def __init__(self, corrupt=False, leak=False):
        self.objects = {}
        self.records = {}
        self.corrupt = corrupt
        self.leak = leak
        self.resumable = None

    class Reply(io.BytesIO):
        def __init__(self,data=b'',headers=None):
            super().__init__(data)
            self.headers=headers or {}

    def open(self, request, timeout=60):
        if isinstance(request,str):
            from urllib.request import Request
            request=Request(request)
        if request.has_header('Authorization'):
            raise AssertionError('Modern secret keys must use apikey, not Bearer JWT')
        url = request.full_url
        path = unquote(urlsplit(url).path)
        method = request.get_method()
        if path == '/storage/v1/upload/resumable' and method == 'POST':
            metadata = dict(item.strip().split(' ',1) for item in request.get_header('Upload-metadata').split(','))
            decoded = {k:base64.b64decode(v).decode() for k,v in metadata.items()}
            self.resumable={'key':decoded['bucketName']+'/'+decoded['objectName'],'data':b'',
                            'length':int(request.get_header('Upload-length'))}
            return self.Reply(headers={'Location':'https://umstsvobrqgstsjdvpza.supabase.co/storage/v1/upload/resumable/test-id'})
        if path == '/storage/v1/upload/resumable/test-id' and method == 'PATCH':
            if len(request.data)>6*1024*1024:
                raise AssertionError('Chunk exceeds supported size')
            if int(request.get_header('Upload-offset'))!=len(self.resumable['data']):
                raise AssertionError('Wrong offset')
            self.resumable['data']+=request.data
            size=len(self.resumable['data'])
            if size==self.resumable['length']:
                self.objects[self.resumable['key']]=self.resumable['data']
            return self.Reply(headers={'Upload-Offset':str(size)})
        if path == '/storage/v1/bucket':
            return io.BytesIO(json.dumps([{'id':'luluka-content-archive','public':False},{'id':'luluka-public-media','public':True}]).encode())
        if path.startswith('/storage/v1/object/'):
            tail = path.removeprefix('/storage/v1/object/')
            if tail.startswith('public/'):
                key = tail.removeprefix('public/')
                if key.startswith('luluka-content-archive/') and not self.leak:
                    raise HTTPError(url,403,'private',None,None)
            elif tail.startswith('authenticated/'):
                key = tail.removeprefix('authenticated/')
            else:
                key = tail
            if method == 'POST':
                self.objects[key] = request.data
                return io.BytesIO(b'{}')
            if key not in self.objects:
                raise HTTPError(url,404,'absent',None,None)
            return io.BytesIO(b'CORRUPTED' if self.corrupt else self.objects[key])
        if path == '/rest/v1/luluka_content_archive':
            if method == 'POST':
                row = json.loads(request.data)
                self.records[row['source_path']] = row
                return io.BytesIO(b'')
            source = parse_qs(urlsplit(url).query)['source_path'][0].removeprefix('eq.')
            row = self.records[source]
            return io.BytesIO(json.dumps([{'sha256':row['sha256'],'bytes':row['bytes']}]).encode())
        raise AssertionError('Unexpected request')


class MigrationTests(unittest.TestCase):
    def exercise(self, fake, expected_error=None, finalize_mode=None, large=False):
        with tempfile.TemporaryDirectory() as folder:
            backup = Path(folder)
            contents = {'website/test.gif':b'GIF89a_TEST_ONLY',
                        'website/中文 空白.jpg':b'JPEG_TEST_ONLY',
                        'brands/assets/xiaomai-social.png':b'\x89PNG_TEST_ONLY',
                        'index.html':b'<html><style>hidden css</style><p>Public words</p><script>hidden js</script></html>',
                        'legacy-index.html':b'<p>Legacy words</p>'}
            if large:
                contents['website/large.gif']=b'GIF89a'+b'x'*(7*1024*1024)
            inventory=[]
            with tarfile.open(backup/'content.tar.gz','w:gz') as archive:
                for path,data in contents.items():
                    info=tarfile.TarInfo(path);info.size=len(data);archive.addfile(info,io.BytesIO(data))
                    if path!='legacy-index.html':
                        inventory.append({'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            (backup/'inventory.json').write_text(json.dumps(inventory))
            argv=['migrate_media.py','--backup-dir',folder,'--project-url','https://umstsvobrqgstsjdvpza.supabase.co']
            with patch('sys.argv',argv),patch.dict(os.environ,{'SUPABASE_SERVICE_ROLE_KEY':'TEST_ONLY_NOT_REAL'}),patch.object(migration.urllib.request,'urlopen',fake.open),contextlib.redirect_stdout(io.StringIO()):
                if expected_error:
                    with self.assertRaisesRegex(RuntimeError,expected_error):
                        migration.main()
                    self.assertTrue((backup/'content.tar.gz').exists())
                    if (backup/'supabase-receipt.json').exists():
                        self.assertFalse(json.loads((backup/'supabase-receipt.json').read_text())['complete'])
                    return
                migration.main()
                receipt=json.loads((backup/'supabase-receipt.json').read_text())
                self.assertTrue(receipt['complete'])
                self.assertEqual(len(receipt['files']),len(contents))
                self.assertEqual(sum(bool(r['public_url']) for r in receipt['files']),1)
                self.assertEqual(fake.records['index.html']['plain_text'],'Public words')
                self.assertTrue(fake.records['website/中文 空白.jpg']['object_key'].endswith('/original.jpg'))
                before=len(fake.objects)
                migration.main()
                self.assertEqual(len(fake.objects),before,'Retry must reuse content-addressed objects')
            if finalize_mode:
                with tempfile.TemporaryDirectory() as checkout:
                    root=Path(checkout)
                    for path,data in contents.items():
                        if path!='legacy-index.html':
                            local=root/path;local.parent.mkdir(parents=True,exist_ok=True);local.write_bytes(data)
                    for slug in ['xiaomai','kaiaote','yongbindata','privacy']:
                        (root/slug).mkdir()
                        (root/slug/'index.html').write_text('<link href="/brands/assets/xiaomai-social.png"><meta content="img-src \'self\'">')
                    (root/'scripts').mkdir()
                    (root/'scripts/public-files.json').write_text(json.dumps([r['path'] for r in inventory]))
                    if finalize_mode=='changed':
                        (root/'website/test.gif').write_bytes(b'CHANGED_SINCE_BACKUP')
                    if finalize_mode=='corrupt':
                        fake.corrupt=True
                    original_page=(root/'xiaomai/index.html').read_text()
                    with patch.object(finalizer,'ROOT',root),patch('sys.argv',['finalize_media_migration.py','--backup-dir',folder]),patch.dict(os.environ,{'SUPABASE_SERVICE_ROLE_KEY':'TEST_ONLY_NOT_REAL'}),patch.object(finalizer.urllib.request,'urlopen',fake.open),contextlib.redirect_stdout(io.StringIO()):
                        if finalize_mode!='success':
                            with self.assertRaises(RuntimeError):finalizer.main()
                            self.assertTrue((root/'website/test.gif').exists())
                            self.assertTrue((root/'brands/assets/xiaomai-social.png').exists())
                            self.assertEqual((root/'xiaomai/index.html').read_text(),original_page)
                        else:
                            finalizer.main()
                            self.assertFalse((root/'website/test.gif').exists())
                            self.assertFalse((root/'brands/assets/xiaomai-social.png').exists())
                            self.assertIn('supabase.co/storage/v1/object/public/',(root/'xiaomai/index.html').read_text())
                            self.assertTrue((root/'index.html').exists(),'Public HTML/code must be retained')

    def test_verified_upload_and_repeatability(self):
        self.exercise(StorageMock())

    def test_corrupt_download_prevents_completion(self):
        self.exercise(StorageMock(corrupt=True),'checksum mismatch')

    def test_public_original_prevents_completion(self):
        self.exercise(StorageMock(leak=True),'accessible anonymously')

    def test_verified_cleanup_preserves_public_code(self):
        self.exercise(StorageMock(),finalize_mode='success')

    def test_changed_local_file_prevents_cleanup(self):
        self.exercise(StorageMock(),finalize_mode='changed')

    def test_corrupt_remote_file_prevents_cleanup(self):
        self.exercise(StorageMock(),finalize_mode='corrupt')

    def test_large_file_uses_verified_resumable_chunks(self):
        fake=StorageMock()
        self.exercise(fake,large=True)
        self.assertIsNotNone(fake.resumable)


if __name__=='__main__':
    unittest.main()
