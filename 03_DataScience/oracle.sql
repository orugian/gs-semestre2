-- GS 2026.2 - Data Science - Modelo relacional (Oracle)
-- Núcleo mínimo do fluxo integrado (dispositivo -> leitura -> alerta ao cidadão).
-- TODO: acrescentar as tabelas específicas da ideia e ajustar colunas.

-- ------------------------------------------------------------------ DDL
CREATE TABLE cidadao (
    id_cidadao      NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    nome            VARCHAR2(120) NOT NULL,
    email           VARCHAR2(120) UNIQUE,
    telefone        VARCHAR2(20),
    dt_cadastro     DATE DEFAULT SYSDATE NOT NULL
);

CREATE TABLE local_monitorado (
    id_local        NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    nome            VARCHAR2(120) NOT NULL,
    bairro          VARCHAR2(80),
    cidade          VARCHAR2(80),
    uf              CHAR(2),
    latitude        NUMBER(9,6),
    longitude       NUMBER(9,6)
);

CREATE TABLE dispositivo (
    id_dispositivo  VARCHAR2(40) PRIMARY KEY,           -- mesmo dispositivo_id do JSON
    tipo            VARCHAR2(20) NOT NULL CHECK (tipo IN ('esp32', 'drone', 'app')),
    id_local        NUMBER NOT NULL REFERENCES local_monitorado (id_local),
    dt_instalacao   DATE DEFAULT SYSDATE
);

CREATE TABLE metrica (
    cd_metrica      VARCHAR2(40) PRIMARY KEY,           -- mesmo "metrica" do JSON
    unidade         VARCHAR2(20),
    limite_atencao  NUMBER(10,2),
    limite_critico  NUMBER(10,2)
);

CREATE TABLE leitura (
    id_leitura      NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    id_dispositivo  VARCHAR2(40) NOT NULL REFERENCES dispositivo (id_dispositivo),
    cd_metrica      VARCHAR2(40) NOT NULL REFERENCES metrica (cd_metrica),
    valor           NUMBER(10,2) NOT NULL,
    nivel_risco     VARCHAR2(10) NOT NULL CHECK (nivel_risco IN ('normal', 'atencao', 'critico')),
    dt_leitura      TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE TABLE alerta (
    id_alerta       NUMBER GENERATED AS IDENTITY PRIMARY KEY,
    id_leitura      NUMBER NOT NULL REFERENCES leitura (id_leitura),
    id_cidadao      NUMBER NOT NULL REFERENCES cidadao (id_cidadao),
    canal           VARCHAR2(20),                        -- sms, push, whatsapp...
    dt_envio        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

-- ------------------------------------------------------------------ DML (TODO: dados do cenário)
INSERT INTO cidadao (nome, email, telefone) VALUES ('TODO', 'todo@exemplo.com', '0000');
INSERT INTO local_monitorado (nome, bairro, cidade, uf, latitude, longitude) VALUES ('TODO', 'TODO', 'TODO', 'SP', 0, 0);
INSERT INTO dispositivo (id_dispositivo, tipo, id_local) VALUES ('esp32-01', 'esp32', 1);
INSERT INTO metrica VALUES ('TODO_metrica_1', 'TODO', 50, 70);
INSERT INTO leitura (id_dispositivo, cd_metrica, valor, nivel_risco) VALUES ('esp32-01', 'TODO_metrica_1', 75, 'critico');
INSERT INTO alerta (id_leitura, id_cidadao, canal) VALUES (1, 1, 'sms');
COMMIT;

-- ------------------------------------------------------------------ consultas
-- 1) leituras com local e dispositivo (JOIN)
SELECT l.id_leitura, d.id_dispositivo, lm.nome AS local, l.cd_metrica, l.valor, l.nivel_risco, l.dt_leitura
  FROM leitura l
  JOIN dispositivo d       ON d.id_dispositivo = l.id_dispositivo
  JOIN local_monitorado lm ON lm.id_local = d.id_local
 ORDER BY l.dt_leitura DESC;

-- 2) resumo por local e métrica (agregação)
SELECT lm.nome AS local, l.cd_metrica, COUNT(*) AS leituras,
       ROUND(AVG(l.valor), 2) AS media, MAX(l.valor) AS pico,
       SUM(CASE WHEN l.nivel_risco = 'critico' THEN 1 ELSE 0 END) AS criticas
  FROM leitura l
  JOIN dispositivo d       ON d.id_dispositivo = l.id_dispositivo
  JOIN local_monitorado lm ON lm.id_local = d.id_local
 GROUP BY lm.nome, l.cd_metrica;

-- 3) alertas enviados a cada cidadão
SELECT c.nome, a.canal, a.dt_envio, l.cd_metrica, l.valor
  FROM alerta a
  JOIN cidadao c ON c.id_cidadao = a.id_cidadao
  JOIN leitura l ON l.id_leitura = a.id_leitura
 ORDER BY a.dt_envio DESC;
