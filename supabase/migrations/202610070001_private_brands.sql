-- Apply once to a fresh Supabase project. No secrets or actual private records.
begin;

create schema if not exists luluka_private;
revoke all on schema luluka_private from public, anon;
grant usage on schema luluka_private to authenticated;

create table luluka_private.brand_memberships (
  brand text not null check (brand in ('xiaomai', 'kaiaote', 'yongbindata')),
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('viewer', 'editor', 'reviewer', 'admin')),
  primary key (brand, user_id)
);
alter table luluka_private.brand_memberships enable row level security;
revoke all on luluka_private.brand_memberships from public, anon, authenticated;

create function luluka_private.has_brand_role(p_brand text, p_roles text[])
returns boolean language sql stable security definer set search_path = '' as $$
  select coalesce(auth.jwt()->>'aal', '') = 'aal2' and exists (
    select 1 from luluka_private.brand_memberships m
    where m.brand = p_brand and m.user_id = auth.uid() and m.role = any(p_roles)
  );
$$;
revoke all on function luluka_private.has_brand_role(text, text[]) from public, anon;
grant execute on function luluka_private.has_brand_role(text, text[]) to authenticated;

create table public.luluka_records (
  id uuid primary key default gen_random_uuid(),
  brand text not null check (brand in ('xiaomai', 'kaiaote', 'yongbindata')),
  internal_title text not null check (char_length(internal_title) between 1 and 300),
  private_metadata jsonb not null default '{}'::jsonb,
  version bigint not null default 1,
  created_by uuid not null default auth.uid() references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.luluka_records enable row level security;
revoke all on public.luluka_records from public, anon, authenticated;
grant select, insert, update, delete on public.luluka_records to authenticated;
create policy records_read on public.luluka_records for select to authenticated
  using (luluka_private.has_brand_role(brand, array['viewer','editor','reviewer','admin']));
create policy records_insert on public.luluka_records for insert to authenticated
  with check (created_by = auth.uid() and version = 1 and luluka_private.has_brand_role(brand, array['editor','admin']));
create policy records_update on public.luluka_records for update to authenticated
  using (luluka_private.has_brand_role(brand, array['editor','admin']))
  with check (luluka_private.has_brand_role(brand, array['editor','admin']));
create policy records_delete on public.luluka_records for delete to authenticated
  using (luluka_private.has_brand_role(brand, array['admin']));

create function luluka_private.record_version()
returns trigger language plpgsql set search_path = '' as $$
begin
  if new.brand <> old.brand or new.id <> old.id or new.created_by <> old.created_by
     or new.created_at <> old.created_at then
    raise exception 'Record identity and brand are immutable';
  end if;
  new.version := old.version + 1;
  new.updated_at := now();
  return new;
end;
$$;
revoke all on function luluka_private.record_version() from public, anon, authenticated;
create trigger bump_record_version before update on public.luluka_records
  for each row execute function luluka_private.record_version();

-- Approved text snapshots are still PRIVATE until a separate publishing workflow
-- explicitly exports them. Original/private metadata never enters this table.
create table luluka_private.publication_snapshots (
  id uuid primary key default gen_random_uuid(),
  record_id uuid references public.luluka_records(id) on delete set null,
  source_version bigint not null,
  brand text not null,
  slug text not null check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and char_length(slug) <= 80),
  public_title text not null check (char_length(public_title) between 1 and 160),
  public_summary text not null check (char_length(public_summary) between 1 and 2000),
  approved_by uuid not null references auth.users(id),
  approved_at timestamptz not null default now(),
  unique (brand, slug)
);
alter table luluka_private.publication_snapshots enable row level security;
revoke all on luluka_private.publication_snapshots from public, anon, authenticated;

create function public.luluka_approve_publication(
  p_record_id uuid, p_expected_version bigint,
  p_slug text, p_public_title text, p_public_summary text
) returns uuid language plpgsql security definer set search_path = '' as $$
declare
  source public.luluka_records%rowtype;
  publication_id uuid;
begin
  select * into source from public.luluka_records where id = p_record_id for update;
  if not found or not luluka_private.has_brand_role(source.brand, array['reviewer','admin']) then
    raise exception 'Publication access denied' using errcode = '42501';
  end if;
  if source.version <> p_expected_version then
    raise exception 'Record changed; review its current version before approval';
  end if;
  insert into luluka_private.publication_snapshots
    (record_id, source_version, brand, slug, public_title, public_summary, approved_by)
  values
    (source.id, source.version, source.brand, p_slug, p_public_title, p_public_summary, auth.uid())
  on conflict (brand, slug) do update set
    record_id = excluded.record_id, source_version = excluded.source_version,
    public_title = excluded.public_title, public_summary = excluded.public_summary,
    approved_by = excluded.approved_by, approved_at = now()
  returning id into publication_id;
  return publication_id;
end;
$$;
revoke all on function public.luluka_approve_publication(uuid,bigint,text,text,text) from public, anon;
grant execute on function public.luluka_approve_publication(uuid,bigint,text,text,text) to authenticated;

create function public.luluka_approved_text(p_brand text)
returns table (slug text, title text, summary text)
language plpgsql stable security definer set search_path = '' as $$
begin
  if not luluka_private.has_brand_role(p_brand, array['reviewer','admin']) then
    raise exception 'Export access denied' using errcode = '42501';
  end if;
  return query select s.slug, s.public_title, s.public_summary
    from luluka_private.publication_snapshots s
    where s.brand = p_brand order by s.slug;
end;
$$;
revoke all on function public.luluka_approved_text(text) from public, anon;
grant execute on function public.luluka_approved_text(text) to authenticated;

-- A single PRIVATE bucket. Object names begin with an authorized brand folder.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('luluka-private', 'luluka-private', false, 26214400,
  array['image/jpeg','image/png','image/webp','image/tiff','application/pdf'])
on conflict (id) do update set public = false,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create policy luluka_files_read on storage.objects for select to authenticated
  using (bucket_id = 'luluka-private' and luluka_private.has_brand_role(split_part(name,'/',1), array['viewer','editor','reviewer','admin']));
create policy luluka_files_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'luluka-private' and luluka_private.has_brand_role(split_part(name,'/',1), array['editor','admin']));
create policy luluka_files_update on storage.objects for update to authenticated
  using (bucket_id = 'luluka-private' and luluka_private.has_brand_role(split_part(name,'/',1), array['editor','admin']))
  with check (bucket_id = 'luluka-private' and luluka_private.has_brand_role(split_part(name,'/',1), array['editor','admin']));
create policy luluka_files_delete on storage.objects for delete to authenticated
  using (bucket_id = 'luluka-private' and luluka_private.has_brand_role(split_part(name,'/',1), array['admin']));

commit;
