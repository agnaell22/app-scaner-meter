-- Tabela Supabase para armazenar registros de coleta de medidores
create table medicoes (
  id uuid primary key default gen_random_uuid(),
  collection_id text not null,
  equipe text not null,
  operador text not null,
  medidor text not null,
  tipo text not null,
  status text not null,
  observacoes text,
  collection_start timestamp with time zone,
  recorded_at timestamp with time zone default now()
);
