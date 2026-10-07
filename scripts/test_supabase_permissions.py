"""Local PostgreSQL policy tests; never connects to a real Supabase project."""
from pathlib import Path
import os
import secrets
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'postgres@sha256:ae69c452f483507a6b99fb654cf93aad7fe156ffd2c56247707eef4e36d3c12b'


def run():
    name = 'luluka-rls-test-' + uuid.uuid4().hex[:12]
    local_env = dict(os.environ, POSTGRES_PASSWORD=secrets.token_urlsafe(32))
    subprocess.run(['docker', 'run', '--detach', '--rm', '--network', 'none',
                    '--name', name, '-e', 'POSTGRES_PASSWORD', IMAGE],
                   env=local_env, check=True, stdout=subprocess.DEVNULL)
    try:
        for _ in range(40):
            ready = subprocess.run(['docker','exec',name,'pg_isready','-U','postgres'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if ready.returncode == 0:
                break
            time.sleep(.5)
        else:
            raise RuntimeError('Local PostgreSQL did not become ready')
        # Wait for the final server rather than the temporary initialization server.
        time.sleep(1)
        for file in ['supabase/tests/bootstrap.sql',
                     'supabase/migrations/202610070001_private_brands.sql',
                     'supabase/tests/permissions.sql']:
            result = subprocess.run(['docker','exec','-i',name,'psql','-U','postgres',
                                     '-v','ON_ERROR_STOP=1','-q'],
                                    input=(ROOT/file).read_text(), text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode:
                raise RuntimeError(f'{file}:\n{result.stderr}')
            passes = [line for line in result.stderr.splitlines() if 'PASS:' in line]
            for line in passes:
                print(line)
            if passes:
                print(f'{len(passes)} permission checks passed on PostgreSQL 17')
    finally:
        subprocess.run(['docker','rm','--force',name], check=True, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    run()
