-- CitizenTech: DDL de Intencao e Comparacao (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem dominios, sem tipo JSON nativo)

CREATE TABLE intencao (
    usuario_id VARCHAR2(32) NOT NULL,
    atividades_json VARCHAR2(4000) NOT NULL,
    motivos_json VARCHAR2(4000) NOT NULL,
    horas_semana NUMBER(2) NOT NULL,
    orcamento_mensal_brl NUMBER(12,2),
    uf CHAR(2) NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_intencao PRIMARY KEY (usuario_id),
    CONSTRAINT fk_intencao_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
    CONSTRAINT ck_intencao_atividades_json CHECK (atividades_json IS JSON),
    CONSTRAINT ck_intencao_motivos_json CHECK (motivos_json IS JSON),
    CONSTRAINT ck_intencao_horas_semana CHECK (horas_semana BETWEEN 1 AND 80),
    CONSTRAINT ck_intencao_orcamento CHECK (orcamento_mensal_brl >= 0)
);

CREATE TABLE comparacao (
    id VARCHAR2(32) NOT NULL,
    usuario_id VARCHAR2(32) NOT NULL,
    uf CHAR(2),
    aviso VARCHAR2(400) NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_comparacao PRIMARY KEY (id),
    CONSTRAINT fk_comparacao_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
);

CREATE INDEX ix_comparacao_usuario_criado ON comparacao(usuario_id, criado_em);

CREATE TABLE comparacao_destino (
    comparacao_id VARCHAR2(32) NOT NULL,
    ordem NUMBER(1) NOT NULL,
    destino_id VARCHAR2(64) NOT NULL,
    situacao_obrigatorios VARCHAR2(40) NOT NULL,
    resultado_json CLOB NOT NULL,
    CONSTRAINT pk_comparacao_destino PRIMARY KEY (comparacao_id, ordem),
    CONSTRAINT fk_comparacao_destino_comp FOREIGN KEY (comparacao_id) REFERENCES comparacao(id) ON DELETE CASCADE,
    CONSTRAINT ck_comp_destino_ordem CHECK (ordem BETWEEN 1 AND 3),
    CONSTRAINT ck_comp_destino_situacao CHECK (situacao_obrigatorios IN ('todos_demonstrados', 'ha_obrigatorios_nao_demonstrados')),
    CONSTRAINT ck_comp_destino_resultado_json CHECK (resultado_json IS JSON),
    CONSTRAINT uq_comparacao_destino_id UNIQUE (comparacao_id, destino_id)
);
