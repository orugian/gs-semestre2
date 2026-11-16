-- CitizenTech: DDL de Competencias do Usuario (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem dominios)

CREATE TABLE competencia_usuario (
    id VARCHAR2(32) NOT NULL,
    usuario_id VARCHAR2(32) NOT NULL,
    esco_id VARCHAR2(64) NOT NULL,
    trecho_origem VARCHAR2(1200),
    origem VARCHAR2(20) DEFAULT 'extracao_llm' NOT NULL,
    estado_evidencia VARCHAR2(20) DEFAULT 'declarada' NOT NULL,
    revisao VARCHAR2(20) NOT NULL,
    curriculo_id VARCHAR2(32),
    extracao_id VARCHAR2(32),
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_competencia_usuario PRIMARY KEY (id),
    CONSTRAINT fk_competencia_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
    CONSTRAINT ck_competencia_origem CHECK (origem IN ('extracao_llm', 'manual')),
    CONSTRAINT ck_competencia_estado CHECK (estado_evidencia IN ('declarada', 'demonstrada')),
    CONSTRAINT ck_competencia_revisao CHECK (revisao IN ('pendente', 'confirmada', 'rejeitada', 'nao_possuo'))
);

CREATE INDEX ix_competencia_usuario_esco ON competencia_usuario(usuario_id, esco_id);
