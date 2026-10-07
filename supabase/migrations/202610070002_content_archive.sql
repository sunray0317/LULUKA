-- Backend-only legacy content archive, separate from brand editing records.
begin;
create table public.luluka_content_archive (
  source_path text primary key,
  sha256 text not null check (sha256 ~ '^[a-f0-9]{64}$'),
  bytes bigint not null check (bytes >= 0),
  object_key text not null,
  content_type text not null,
  plain_text text,
  migrated_at timestamptz not null default now()
);
alter table public.luluka_content_archive enable row level security;
revoke all on public.luluka_content_archive from public, anon, authenticated;
grant select, insert, update on public.luluka_content_archive to service_role;

insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types) values
 ('luluka-content-archive','luluka-content-archive',false,104857600,
  array['image/jpeg','image/png','image/gif','image/svg+xml','image/webp','image/tiff',
        'video/mp4','video/webm','audio/mpeg','audio/wav','text/html','text/plain','application/json']),
 ('luluka-public-media','luluka-public-media',true,10485760,
  array['image/png','image/svg+xml'])
on conflict (id) do nothing;
do $$ begin
  if not exists(select 1 from storage.buckets where id='luluka-content-archive' and public=false)
     or not exists(select 1 from storage.buckets where id='luluka-public-media' and public=true) then
    raise exception 'Existing bucket visibility conflicts with migration';
  end if;
end $$;
-- No authenticated/anonymous policies: only a trusted server credential can
-- write the archive or public derivatives. Bucket public=false protects originals.
commit;
