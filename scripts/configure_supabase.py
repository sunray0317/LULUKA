"""Check/apply the fresh-project migration via Supabase's HTTPS Management API.

Credentials are read from secure environment bindings, never arguments or files.
Use --check first; --apply changes the selected project's database.
"""
from pathlib import Path
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error('Choose exactly one of --check or --apply')
    required = ['SUPABASE_URL', 'SUPABASE_PROJECT_REF', 'SUPABASE_ACCESS_TOKEN']
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError('Missing environment requirements: ' + ', '.join(missing))
    ref = os.environ['SUPABASE_PROJECT_REF']
    if not re.fullmatch(r'[a-z0-9]{20}', ref):
        raise RuntimeError('Invalid Supabase project ref')
    if os.environ['SUPABASE_URL'].rstrip('/') != f'https://{ref}.supabase.co':
        raise RuntimeError('SUPABASE_URL and project ref do not match')

    def query(sql):
        request = urllib.request.Request(
            f'https://api.supabase.com/v1/projects/{ref}/database/query',
            data=json.dumps({'query': sql}).encode(),
            headers={'Authorization': 'Bearer ' + os.environ['SUPABASE_ACCESS_TOKEN'],
                     'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            # Never print API response bodies, request headers or credentials.
            raise RuntimeError(f'Supabase API rejected the operation (HTTP {error.code})') from None
        except urllib.error.URLError:
            raise RuntimeError('Supabase API connection failed; check allowed domain and TLS trust') from None

    preflight = query("""
      select
        exists(select 1 from pg_namespace where nspname='luluka_private') as existing_schema,
        to_regclass('public.luluka_records') is not null as existing_records,
        (select count(*) from pg_policies where schemaname='storage' and tablename='objects') as storage_policy_count,
        exists(select 1 from storage.buckets where id='luluka-private') as existing_bucket;
    """)
    if not isinstance(preflight, list) or len(preflight) != 1:
        raise RuntimeError('Unexpected preflight response; refusing to change the database')
    state = preflight[0]
    if set(state) != {'existing_schema','existing_records','storage_policy_count','existing_bucket'}:
        raise RuntimeError('Incomplete preflight response; refusing to change the database')
    if any(state[name] for name in ['existing_schema','existing_records','existing_bucket']) or state['storage_policy_count'] != 0:
        raise RuntimeError('Project has existing LULUKA objects or Storage policies; inspect and reconcile before applying')
    print('Project access verified; no conflicting LULUKA objects or Storage policies found')
    if not args.apply:
        return
    query((ROOT/'supabase/migrations/202610070001_private_brands.sql').read_text())
    verification = query("""
      select
        (select relrowsecurity from pg_class where oid='public.luluka_records'::regclass) as records_rls,
        not has_table_privilege('anon','public.luluka_records','SELECT') as anon_read_denied,
        not has_function_privilege('anon','public.luluka_approved_text(text)','EXECUTE') as anon_export_denied,
        (select not public from storage.buckets where id='luluka-private') as bucket_private,
        (select count(*) from pg_policies where schemaname='public' and tablename='luluka_records') as record_policies,
        (select count(*) from pg_policies where schemaname='storage' and tablename='objects') as storage_policies;
    """)
    if not isinstance(verification, list) or len(verification) != 1:
        raise RuntimeError('Migration executed, but hosted verification response is unexpected')
    v = verification[0]
    if not all(v.get(x) is True for x in ['records_rls','anon_read_denied','anon_export_denied','bucket_private']) or v.get('record_policies') != 4 or v.get('storage_policies') != 4:
        raise RuntimeError('Migration executed, but hosted protection checks failed; do not upload private data')
    print('Migration applied; hosted RLS, anonymous grants and private bucket checks passed')
    print('Next: invite administrator, assign brand memberships, enroll MFA, and test real Auth/Storage requests')


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
