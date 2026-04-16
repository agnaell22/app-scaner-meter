-- Tabela para armazenar registro de leituras individuais de medidores
CREATE TABLE medicoes
(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id TEXT NOT NULL,
  equipe TEXT NOT NULL,
  operador TEXT NOT NULL,
  medidor TEXT NOT NULL,
  tipo TEXT NOT NULL,
  status TEXT NOT NULL,
  observacoes TEXT,
  collection_start TIMESTAMP
  WITH TIME ZONE,
  recorded_at TIMESTAMP
  WITH TIME ZONE DEFAULT now
  ()
);

  -- Criar índices para melhor performance
  CREATE INDEX idx_medicoes_collection_id ON medicoes(collection_id);
  CREATE INDEX idx_medicoes_equipe ON medicoes(equipe);
  CREATE INDEX idx_medicoes_recorded_at ON medicoes(recorded_at);

  -- Tabela para armazenar colecoes (sessões de coleta)
  CREATE TABLE colecoes
  (
    id TEXT PRIMARY KEY,
    equipe TEXT NOT NULL,
    operador TEXT NOT NULL,
    start_time TIMESTAMP
    WITH TIME ZONE NOT NULL,
  updated_time TIMESTAMP
    WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP
    WITH TIME ZONE,
  status TEXT NOT NULL DEFAULT 'aberta',
  items JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP
    WITH TIME ZONE DEFAULT now
    ()
);

    -- Criar índices para melhor performance
    CREATE INDEX idx_colecoes_status ON colecoes(status);
    CREATE INDEX idx_colecoes_created_at ON colecoes(created_at);
    );

    -- Criar índices para melhor performance
    CREATE INDEX idx_colecoes_status ON colecoes(status);
    CREATE INDEX idx_colecoes_created_at ON colecoes(created_at);
