-- Static hosting for the dashboard frontend, served by the `site` Edge Function.
-- File contents are seeded/updated with plain SQL (dollar-quoted), no redeploys.
create table site_files (
  path         text primary key,
  content      text not null,
  content_type text not null,
  updated_at   timestamptz not null default now()
);
alter table site_files enable row level security;
-- deny-all: only the service role (inside the site function) reads it.
