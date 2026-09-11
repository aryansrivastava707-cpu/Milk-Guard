-- Paste this in Supabase: SQL Editor > New query > Run
create table if not exists public.milk_tests (
  id uuid primary key,
  sample_id text not null,
  test_time timestamp not null,
  ph numeric not null,
  tds numeric not null,
  temperature numeric not null,
  result text not null,
  suspicious_probability numeric not null
);

-- The Flask server reads/writes using the private service-role key.
-- Do not put that key in GitHub, JavaScript, or a QR code.
alter table public.milk_tests enable row level security;
