-- Lugano Parking: driver reports ("I parked here, there was space").
-- Paste this whole file into Supabase > SQL Editor > New query, then press Run.
-- Stores only which garage and when. No account, no location, no device id.

create table if not exists public.reports (
  id bigint generated always as identity primary key,
  garage_id text not null check (garage_id in ('centralpark','sangiuseppe','ospedale','prailsud','fornaci')),
  created_at timestamptz not null default now()
);

alter table public.reports enable row level security;

-- Anyone using the app may add a report and read the reports of the last 3 hours. Nothing older is readable,
-- and nobody can change or delete reports through the app.
drop policy if exists "app can add reports" on public.reports;
create policy "app can add reports" on public.reports for insert to anon with check (true);
drop policy if exists "app can read recent reports" on public.reports;
create policy "app can read recent reports" on public.reports for select to anon using (created_at > now() - interval '3 hours');

grant select, insert on public.reports to anon;

-- Flood guard: at most one report per garage every 2 minutes, and the server sets the time (no backdating).
create or replace function public.reports_guard() returns trigger language plpgsql as $$
begin
  new.created_at := now();
  if exists (select 1 from public.reports where garage_id = new.garage_id and created_at > now() - interval '2 minutes') then
    return null; -- quietly ignore the duplicate
  end if;
  return new;
end $$;
drop trigger if exists reports_guard on public.reports;
create trigger reports_guard before insert on public.reports for each row execute function public.reports_guard();

-- Housekeeping: old reports are useless, keep the table small (runs whenever someone reports).
create or replace function public.reports_cleanup() returns trigger language plpgsql security definer as $$
begin
  delete from public.reports where created_at < now() - interval '7 days';
  return null;
end $$;
drop trigger if exists reports_cleanup on public.reports;
create trigger reports_cleanup after insert on public.reports for each statement execute function public.reports_cleanup();
