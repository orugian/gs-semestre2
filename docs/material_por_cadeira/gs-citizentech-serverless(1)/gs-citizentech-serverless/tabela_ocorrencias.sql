-- Global Solution - CitizenTech
-- Tabela que recebe as leituras enviadas pelos dispositivos de campo
-- (ESP32, drone ou app do cidadao) para o RDS PostgreSQL.

CREATE TABLE IF NOT EXISTS ocorrencias (
    id                SERIAL PRIMARY KEY,
    dispositivo_id    TEXT        NOT NULL,
    tipo_dispositivo  TEXT        NOT NULL,              -- esp32 | drone | app
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    metrica           TEXT        NOT NULL,              -- nivel_rio_cm, fumaca_ppm, ...
    valor             DOUBLE PRECISION NOT NULL,
    relato            TEXT,                              -- texto do cidadao (entra no modelo de IA)
    sentimento        TEXT,                              -- rotulo devolvido pelo modelo
    confianca         NUMERIC(5,4),                      -- score do rotulo
    nivel_risco       TEXT        NOT NULL,              -- normal | atencao | critico | desconhecido
    medido_em         TIMESTAMPTZ,                       -- hora no dispositivo
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT NOW() -- hora da gravacao na nuvem
);

CREATE INDEX IF NOT EXISTS idx_ocorrencias_dispositivo ON ocorrencias (dispositivo_id);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_risco       ON ocorrencias (nivel_risco);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_criado      ON ocorrencias (criado_em DESC);

-- Opcional: catalogo dos pontos monitorados, se o grupo quiser normalizar
-- o cadastro em vez de repetir latitude/longitude em cada leitura.
--
-- CREATE TABLE locais_monitorados (
--     id         SERIAL PRIMARY KEY,
--     nome       TEXT NOT NULL,
--     bairro     TEXT,
--     latitude   DOUBLE PRECISION,
--     longitude  DOUBLE PRECISION
-- );
-- ALTER TABLE ocorrencias ADD COLUMN local_id INT REFERENCES locais_monitorados (id);


-- Consultas para o print da entrega -----------------------------------------

-- 1) ultimas leituras que chegaram na nuvem
SELECT id, dispositivo_id, tipo_dispositivo, metrica, valor,
       nivel_risco, sentimento, confianca, criado_em
  FROM ocorrencias
 ORDER BY id DESC
 LIMIT 10;

-- 2) ocorrencias criticas (as que gerariam alerta ao cidadao)
SELECT dispositivo_id, metrica, valor, relato, sentimento, criado_em
  FROM ocorrencias
 WHERE nivel_risco = 'critico'
 ORDER BY criado_em DESC;

-- 3) resumo por dispositivo
SELECT dispositivo_id,
       COUNT(*)                                   AS leituras,
       ROUND(AVG(valor)::numeric, 2)              AS media,
       MAX(valor)                                 AS pico,
       SUM((nivel_risco = 'critico')::int)        AS criticas
  FROM ocorrencias
 GROUP BY dispositivo_id
 ORDER BY criticas DESC, leituras DESC;
