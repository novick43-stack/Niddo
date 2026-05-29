-- ============================================================
--  Niddo — Supabase Schema
--  Correr en: Supabase Dashboard → SQL Editor
-- ============================================================

-- ── Tabla: administradores ────────────────────────────────
create table if not exists administradores (
  id          uuid primary key default gen_random_uuid(),
  auth0_id    text unique not null,        -- "sub" del JWT de Auth0
  email       text unique not null,
  nombre      text,
  created_at  timestamptz default now(),
  last_login  timestamptz
);

-- Row Level Security: cada admin solo ve su propio perfil
alter table administradores enable row level security;

create policy "Admin ve su propio perfil"
  on administradores for select
  using (auth0_id = current_setting('request.jwt.claims', true)::json->>'sub');

create policy "Admin actualiza su propio perfil"
  on administradores for update
  using (auth0_id = current_setting('request.jwt.claims', true)::json->>'sub');


-- ── Tabla: vecinos ────────────────────────────────────────
create table if not exists vecinos (
  id            uuid primary key default gen_random_uuid(),
  auth0_id      text unique not null,
  email         text unique not null,
  nombre        text,
  unidad        text,                      -- ej: "3B", "PH1"
  consorcio_id  uuid,                      -- FK a tabla consorcios (futura)
  created_at    timestamptz default now(),
  last_login    timestamptz
);

alter table vecinos enable row level security;

create policy "Vecino ve su propio perfil"
  on vecinos for select
  using (auth0_id = current_setting('request.jwt.claims', true)::json->>'sub');

create policy "Vecino actualiza su propio perfil"
  on vecinos for update
  using (auth0_id = current_setting('request.jwt.claims', true)::json->>'sub');


-- ── Índices ───────────────────────────────────────────────
create index if not exists idx_admin_auth0_id on administradores(auth0_id);
create index if not exists idx_vecino_auth0_id on vecinos(auth0_id);
create index if not exists idx_vecino_email on vecinos(email);
