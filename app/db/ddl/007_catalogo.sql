-- CitizenTech: projeção relacional do catálogo curado (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem domínios).
-- A fonte de verdade do catálogo continua nos YAML de app/catalogo; estas tabelas são carregadas
-- por app/tools/carregar_catalogo_oracle.py para consultas relacionais (Data Science).

CREATE TABLE destino (
    id VARCHAR2(64) NOT NULL,
    nome VARCHAR2(120) NOT NULL,
    versao VARCHAR2(40),
    status_revisao VARCHAR2(20) NOT NULL,
    revisado_em TIMESTAMP WITH TIME ZONE,
    no_escopo_mvp CHAR(1) DEFAULT 'N' NOT NULL,
    descricao VARCHAR2(1000),
    CONSTRAINT pk_destino PRIMARY KEY (id),
    CONSTRAINT ck_destino_status CHECK (status_revisao IN ('aprovado', 'pendente', 'rascunho')),
    CONSTRAINT ck_destino_escopo CHECK (no_escopo_mvp IN ('S', 'N'))
);

CREATE TABLE ocupacao_cbo (
    cbo6 CHAR(6) NOT NULL,
    titulo VARCHAR2(200) NOT NULL,
    fonte_titulo VARCHAR2(40),
    CONSTRAINT pk_ocupacao_cbo PRIMARY KEY (cbo6)
);

CREATE TABLE destino_ocupacao (
    destino_id VARCHAR2(64) NOT NULL,
    cbo6 CHAR(6) NOT NULL,
    CONSTRAINT pk_destino_ocupacao PRIMARY KEY (destino_id, cbo6),
    CONSTRAINT fk_dest_ocup_destino FOREIGN KEY (destino_id) REFERENCES destino(id) ON DELETE CASCADE,
    CONSTRAINT fk_dest_ocup_cbo FOREIGN KEY (cbo6) REFERENCES ocupacao_cbo(cbo6),
    CONSTRAINT uq_dest_ocup_cbo UNIQUE (cbo6)
);

CREATE TABLE competencia_esco (
    esco_id VARCHAR2(64) NOT NULL,
    titulo VARCHAR2(300) NOT NULL,
    tipo VARCHAR2(30),
    uri VARCHAR2(200),
    CONSTRAINT pk_competencia_esco PRIMARY KEY (esco_id)
);

CREATE TABLE requisito_destino (
    destino_id VARCHAR2(64) NOT NULL,
    id_local VARCHAR2(80) NOT NULL,
    esco_id VARCHAR2(64) NOT NULL,
    obrigatorio CHAR(1) NOT NULL,
    ordem NUMBER(3) NOT NULL,
    CONSTRAINT pk_requisito_destino PRIMARY KEY (destino_id, id_local),
    CONSTRAINT fk_req_destino FOREIGN KEY (destino_id) REFERENCES destino(id) ON DELETE CASCADE,
    CONSTRAINT fk_req_esco FOREIGN KEY (esco_id) REFERENCES competencia_esco(esco_id),
    CONSTRAINT ck_req_obrigatorio CHECK (obrigatorio IN ('S', 'N'))
);

CREATE INDEX ix_requisito_esco ON requisito_destino(esco_id);
