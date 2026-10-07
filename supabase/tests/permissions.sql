\set ON_ERROR_STOP on
begin;
create function pg_temp.assert_true(p_value boolean, p_label text)
returns void language plpgsql as $$
begin
  if p_value is distinct from true then raise exception 'FAILED: %', p_label; end if;
  raise notice 'PASS: %', p_label;
end;
$$;
insert into auth.users(id) values
 ('00000000-0000-0000-0000-000000000001'),
 ('00000000-0000-0000-0000-000000000002'),
 ('00000000-0000-0000-0000-000000000003'),
 ('00000000-0000-0000-0000-000000000004'),
 ('00000000-0000-0000-0000-000000000005');
insert into luluka_private.brand_memberships values
 ('yongbindata','00000000-0000-0000-0000-000000000001','editor'),
 ('yongbindata','00000000-0000-0000-0000-000000000002','reviewer'),
 ('yongbindata','00000000-0000-0000-0000-000000000003','viewer'),
 ('kaiaote','00000000-0000-0000-0000-000000000004','admin');

set local role anon;
do $$ begin
  perform * from public.luluka_records;
  raise exception 'Anonymous read unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: anonymous record read denied'; end $$;
do $$ begin
  perform public.luluka_approved_text('yongbindata');
  raise exception 'Anonymous export unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: anonymous export denied'; end $$;
select pg_temp.assert_true((select count(*)=0 from storage.objects), 'anonymous storage returns no records');
reset role;

set local role authenticated;
select set_config('request.jwt.claims','{"aal":"aal2"}',true);
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
insert into public.luluka_records(id,brand,internal_title,private_metadata)
 values ('10000000-0000-0000-0000-000000000001','yongbindata','PRIVATE TEST TITLE','{"private":"TEST_ONLY"}');
select pg_temp.assert_true((select count(*)=1 from public.luluka_records), 'editor can read own brand');
do $$ begin
  insert into public.luluka_records(brand,internal_title) values ('kaiaote','cross-brand');
  raise exception 'Cross-brand insert unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: cross-brand record insert denied'; end $$;
do $$ begin
  insert into luluka_private.brand_memberships values ('yongbindata',auth.uid(),'admin');
  raise exception 'Self-escalation unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: self-assigned admin denied'; end $$;
do $$ begin
  perform public.luluka_approve_publication('10000000-0000-0000-0000-000000000001',1,'sample','public title','public summary');
  raise exception 'Editor approval unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: editor cannot approve publication'; end $$;
insert into storage.objects(bucket_id,name) values ('luluka-private','yongbindata/test.jpg');
reset role;
set local role anon;
select pg_temp.assert_true((select count(*)=0 from storage.objects), 'anonymous cannot read existing private objects');
do $$ begin
  insert into storage.objects(bucket_id,name) values ('luluka-private','yongbindata/anonymous.jpg');
  raise exception 'Anonymous upload unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: anonymous upload denied'; end $$;
reset role;
set local role authenticated;
do $$ begin
  insert into storage.objects(bucket_id,name) values ('luluka-private','kaiaote/test.jpg');
  raise exception 'Cross-brand upload unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: cross-brand upload denied'; end $$;
select pg_temp.assert_true((select count(*)=1 from storage.objects), 'editor can read own private objects');

select set_config('request.jwt.claims','{"aal":"aal1"}',true);
select pg_temp.assert_true((select count(*)=0 from public.luluka_records), 'password-only login cannot read private records');
select pg_temp.assert_true((select count(*)=0 from storage.objects), 'password-only login cannot read private files');
do $$ begin
  insert into public.luluka_records(brand,internal_title) values ('yongbindata','no MFA');
  raise exception 'Non-MFA insert unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: password-only login cannot write'; end $$;
select set_config('request.jwt.claims','{"aal":"aal2"}',true);

select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000003',true);
select pg_temp.assert_true((select count(*)=1 from public.luluka_records), 'viewer can read own brand');
do $$ begin
  insert into public.luluka_records(brand,internal_title) values ('yongbindata','viewer write');
  raise exception 'Viewer write unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: viewer cannot write'; end $$;
do $$ begin
  insert into storage.objects(bucket_id,name) values ('luluka-private','yongbindata/viewer.jpg');
  raise exception 'Viewer upload unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: viewer cannot upload'; end $$;

select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000004',true);
select pg_temp.assert_true((select count(*)=0 from public.luluka_records), 'other-brand admin cannot read records');
select pg_temp.assert_true((select count(*)=0 from storage.objects), 'other-brand admin cannot read files');
do $$ begin
  perform public.luluka_approve_publication('10000000-0000-0000-0000-000000000001',1,'sample','public title','public summary');
  raise exception 'Cross-brand approval unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: cross-brand approval denied'; end $$;

select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000005',true);
select pg_temp.assert_true((select count(*)=0 from public.luluka_records), 'unassigned authenticated user cannot read');
select pg_temp.assert_true((select count(*)=0 from storage.objects), 'unassigned user cannot read files');

select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
select pg_temp.assert_true(public.luluka_approve_publication('10000000-0000-0000-0000-000000000001',1,'sample','public title','public summary') is not null, 'reviewer approval succeeds');
select pg_temp.assert_true((select title='public title' and summary='public summary' from public.luluka_approved_text('yongbindata')), 'export contains only approved text');
select set_config('request.jwt.claims','{"aal":"aal1"}',true);
do $$ begin
  perform public.luluka_approve_publication('10000000-0000-0000-0000-000000000001',1,'sample','title','summary');
  raise exception 'Non-MFA approval unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: reviewer without MFA cannot approve'; end $$;
select set_config('request.jwt.claims','{"aal":"aal2"}',true);
do $$ begin
  perform * from luluka_private.publication_snapshots;
  raise exception 'Direct private snapshot access unexpectedly allowed';
exception when insufficient_privilege then raise notice 'PASS: direct private snapshot access denied'; end $$;

select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
update public.luluka_records set private_metadata='{"private":"UPDATED_TEST_ONLY"}', version=500
 where id='10000000-0000-0000-0000-000000000001';
select pg_temp.assert_true((select version=2 from public.luluka_records), 'version is controlled by trigger');
do $$ begin
  update public.luluka_records set created_by='00000000-0000-0000-0000-000000000003';
  raise exception 'Identity mutation unexpectedly allowed';
exception when raise_exception then
  if sqlerrm <> 'Record identity and brand are immutable' then raise; end if;
  raise notice 'PASS: record creator is immutable';
end $$;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
do $$ begin
  perform public.luluka_approve_publication('10000000-0000-0000-0000-000000000001',1,'sample','title','summary');
  raise exception 'Stale approval unexpectedly allowed';
exception when raise_exception then
  if sqlerrm <> 'Record changed; review its current version before approval' then raise; end if;
  raise notice 'PASS: stale approval denied';
end $$;
reset role;
select pg_temp.assert_true((select public=false from storage.buckets where id='luluka-private'), 'bucket is private');
rollback;
