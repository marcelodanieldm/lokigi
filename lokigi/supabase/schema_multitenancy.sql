-- Supabase Multi-tenancy: Tablas y RLS para agencias

-- Tabla de agencias
create table if not exists agencies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  custom_domain text unique,
  created_at timestamptz default now()
);

-- Branding de agencia
create table if not exists agency_branding (
  agency_id uuid references agencies(id) on delete cascade,
  primary_color text,
  logo_url text,
  agency_name text,
  constraint agency_branding_pkey primary key (agency_id)
);

-- Reportes y archivos privados
create table if not exists agency_reports (
  id uuid primary key default gen_random_uuid(),
  agency_id uuid references agencies(id) on delete cascade,
  report_url text,
  created_at timestamptz default now()
);

-- RLS: Cada agencia solo ve sus datos
alter table agency_branding enable row level security;
create policy "Agencia solo ve su branding" on agency_branding
  using (auth.uid() = agency_id);

alter table agency_reports enable row level security;
create policy "Agencia solo ve sus reportes" on agency_reports
  using (auth.uid() = agency_id);

-- Storage: Cada agencia tiene su bucket/carpeta privada
-- (Configura en Supabase Storage UI: un bucket por agencia o prefijo por agency_id)
