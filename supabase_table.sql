-- Tabela para armazenar registro de leituras individuais de medidores
create table medicoes
(
  id uuid primary key default gen_random_uuid(),
  collection_id text not null,
  equipe text not null,
  operador text not null,
  medidor text not null,
  tipo text not null,
  status text not null,
  observacoes text,
  collection_start timestamp
  with time zone,
  recorded_at timestamp
  with time zone default now
  ()
);

  -- Criar índices para melhor performance
  create index idx_medicoes_collection_id on medicoes(collection_id);
  create index idx_medicoes_equipe on medicoes(equipe);
  create index idx_medicoes_recorded_at on medicoes(recorded_at);

  -- Tabela para armazenar colecoes (sessões de coleta)
  create table colecoes
  (
    id text primary key,
    equipe text not null,
    operador text not null,
    start_time timestamp
    with time zone not null,
  updated_time timestamp
    with time zone not null,
  end_time timestamp
    with time zone,
  status text not null default 'aberta',
  items jsonb not null default '[]'::jsonb,
  created_at timestamp
    with time zone default now
    ()
);

    -- Criar índices para melhor performance
    create index idx_colecoes_status on colecoes(status);
    create index idx_colecoes_created_at on colecoes(created_at);
