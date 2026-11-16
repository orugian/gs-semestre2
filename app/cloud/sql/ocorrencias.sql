-- DDL PostgreSQL >= 13 para CitizenTech Cloud
-- Tabela de ocorrencias e ingestao de dados de monitoramento e simuladores.

CREATE TABLE IF NOT EXISTS ocorrencias (
    id SERIAL PRIMARY KEY,
    dispositivo_id TEXT NOT NULL,
    tipo_dispositivo TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    metrica TEXT NOT NULL,
    valor DOUBLE PRECISION NOT NULL,
    relato TEXT,
    sentimento TEXT,
    confianca NUMERIC(5,4),
    nivel_risco TEXT NOT NULL,
    medido_em TIMESTAMPTZ,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evento_id TEXT UNIQUE,
    autenticado BOOLEAN NOT NULL DEFAULT FALSE,
    unidade TEXT,
    sessao_laboratorio_id TEXT,
    ciclo_id TEXT,
    alerta BOOLEAN NOT NULL DEFAULT FALSE,
    analise_status TEXT,
    hash_conteudo TEXT,
    CONSTRAINT chk_nivel_risco CHECK (nivel_risco IN ('normal', 'atencao', 'critico', 'desconhecido')),
    CONSTRAINT chk_relato_tam CHECK (relato IS NULL OR char_length(relato) <= 280),
    CONSTRAINT chk_latitude CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
    CONSTRAINT chk_longitude CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180))
);

-- Migracao caso tabela antiga do professor ja exista
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS evento_id TEXT UNIQUE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS autenticado BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS unidade TEXT;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS sessao_laboratorio_id TEXT;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS ciclo_id TEXT;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS alerta BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS analise_status TEXT;
ALTER TABLE ocorrencias ADD COLUMN IF NOT EXISTS hash_conteudo TEXT;

-- Indices do professor e indice composto para rate limit
CREATE INDEX IF NOT EXISTS idx_ocorrencias_dispositivo_id ON ocorrencias(dispositivo_id);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_criado_em ON ocorrencias(criado_em);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_nivel_risco ON ocorrencias(nivel_risco);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_disp_criado ON ocorrencias(dispositivo_id, criado_em);

-- Consultas de evidencia do professor
-- 1. Ultimas 10 ocorrencias
-- SELECT id, dispositivo_id, tipo_dispositivo, metrica, valor, nivel_risco, alerta, autenticado, criado_em FROM ocorrencias ORDER BY id DESC LIMIT 10;

-- 2. Ocorrencias criticas
-- SELECT id, dispositivo_id, tipo_dispositivo, metrica, valor, nivel_risco, relato, sentimento, confianca, criado_em FROM ocorrencias WHERE nivel_risco = 'critico' ORDER BY id DESC;

-- 3. Resumo por dispositivo
-- SELECT dispositivo_id, tipo_dispositivo, COUNT(*) AS total_ocorrencias, COUNT(*) FILTER (WHERE nivel_risco = 'critico') AS total_criticas, MAX(criado_em) AS ultima_ocorrencia FROM ocorrencias GROUP BY dispositivo_id, tipo_dispositivo ORDER BY total_ocorrencias DESC;

-- 4. Resumo de nao autenticadas por dispositivo
-- SELECT dispositivo_id, COUNT(*) AS total_nao_autenticadas, MAX(criado_em) AS ultima_nao_autenticada FROM ocorrencias WHERE autenticado = FALSE GROUP BY dispositivo_id ORDER BY total_nao_autenticadas DESC;

-- FIM_DDL (marca de separacao para testes automatizados)

-- Role app_ingest de menor privilegio (executado via psql com variavel :'senha_app_ingest')
-- O psql nao interpola variaveis dentro de blocos $$; por isso o comando e montado e
-- executado com \gexec. Uso: psql ... -v senha_app_ingest='<senha>' -f ocorrencias.sql
SELECT format('CREATE ROLE app_ingest WITH LOGIN PASSWORD %L', :'senha_app_ingest')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_ingest')
\gexec

GRANT USAGE ON SCHEMA public TO app_ingest;
GRANT INSERT, SELECT ON ocorrencias TO app_ingest;
GRANT USAGE, SELECT ON SEQUENCE ocorrencias_id_seq TO app_ingest;
