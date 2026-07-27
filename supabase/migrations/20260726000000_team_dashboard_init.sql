-- Zenthra dev team task dashboard: members, tasks, server-only config, proof storage.
-- Security model: RLS enabled with NO policies (deny-all for anon/authenticated).
-- Only Edge Functions using the service role touch these tables.

create table members (
  id               uuid primary key default gen_random_uuid(),
  discord_username text not null,
  display_name     text,
  timezone         text not null default 'America/Chicago',
  schedule         jsonb not null default '{}'::jsonb,
  role             text,
  access_code_hash text not null,
  active           boolean not null default true,
  created_at       timestamptz not null default now()
);
create unique index members_username_uidx on members (lower(discord_username));

create table tasks (
  id               uuid primary key default gen_random_uuid(),
  member_id        uuid not null references members(id) on delete cascade,
  title            text not null,
  description      text,
  due_date         date,
  sort_order       int not null default 0,
  status           text not null default 'open' check (status in ('open','done')),
  proof_image_path text,
  proof_image_url  text,
  completed_at     timestamptz,
  ping_sent_at     timestamptz,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create index tasks_member_status_idx on tasks (member_id, status, sort_order);
create index tasks_completed_idx on tasks (completed_at desc) where completed_at is not null;

create or replace function set_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at = now();
  return new;
end $$;
create trigger tasks_updated_at before update on tasks
for each row execute function set_updated_at();

-- Server-only config. Rows are seeded manually (admin_code_hash,
-- discord_webhook_url, chris_discord_id) and never committed to git.
create table app_config (
  key   text primary key,
  value text not null
);

alter table members enable row level security;
alter table tasks enable row level security;
alter table app_config enable row level security;

-- Public bucket for proof screenshots. Paths are unguessable
-- (proofs/{task_id}/{uuid}.ext); Discord embeds need stable public URLs.
insert into storage.buckets (id, name, public) values ('proofs', 'proofs', true);
