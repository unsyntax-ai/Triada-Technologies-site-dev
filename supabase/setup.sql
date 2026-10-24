-- Triada jobs: table and access rules. Paste all of this into Supabase > SQL Editor > Run.
create table if not exists public.jobs (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  location text not null default 'Remote (U.S.)',
  employment_type text not null default 'Contract'
    check (employment_type in ('Contract', 'Contract-to-hire', 'Direct hire', 'Temporary')),
  pay text,
  summary text not null default '',
  responsibilities text[] not null default '{}',
  requirements text[] not null default '{}',
  status text not null default 'draft' check (status in ('draft', 'published', 'closed')),
  publish_at timestamptz,
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.jobs enable row level security;

-- Visitors can read only jobs that are published, already started, and not expired.
drop policy if exists "Public can read live jobs" on public.jobs;
create policy "Public can read live jobs" on public.jobs
  for select to anon, authenticated
  using (status = 'published' and publish_at <= now() and (expires_at is null or expires_at > now()));

-- Only the admin email can see everything and add, change or delete jobs.
drop policy if exists "Admin full access" on public.jobs;
create policy "Admin full access" on public.jobs
  for all to authenticated
  using ((auth.jwt() ->> 'email') = 'unsyntax.ai@gmail.com')
  with check ((auth.jwt() ->> 'email') = 'unsyntax.ai@gmail.com');

-- Admin PIN lock (used by the admin-pin Edge Function only).
-- No policies: the public and signed-in users cannot read or change this table; only the function can.
create table if not exists public.admin_pin (
  id int primary key check (id = 1),
  salt text not null,
  hash text not null,
  failed int not null default 0,
  updated_at timestamptz not null default now()
);
alter table public.admin_pin enable row level security;

-- Archived jobs (status 'closed') are deleted for good 365 days after they were archived.
-- The admin page also does this each time it opens. To make it run daily on its own, enable the pg_cron
-- extension (Database > Extensions) and run:
--   select cron.schedule('purge-archived-jobs', '15 3 * * *',
--     $$delete from public.jobs where status = 'closed' and updated_at < now() - interval '365 days'$$);
