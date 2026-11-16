-- CitizenTech: DDL de Sessao de Laboratorio (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem dominios)

CREATE TABLE sessao_laboratorio (
    id VARCHAR2(32) NOT NULL,
    usuario_id VARCHAR2(32) NOT NULL,
    codigo VARCHAR2(16) NOT NULL,
    status VARCHAR2(10) NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    expira_em TIMESTAMP WITH TIME ZONE NOT NULL,
    relato_redigido VARCHAR2(1200),
    relato_status VARCHAR2(10) DEFAULT 'nenhum' NOT NULL,
    relato_evento_id VARCHAR2(64),
    CONSTRAINT pk_sessao_laboratorio PRIMARY KEY (id),
    CONSTRAINT fk_sessao_laboratorio_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
    CONSTRAINT uq_sessao_laboratorio_codigo UNIQUE (codigo),
    CONSTRAINT ck_sessao_lab_status CHECK (status IN ('ativa', 'encerrada')),
    CONSTRAINT ck_sessao_lab_relato_status CHECK (relato_status IN ('nenhum', 'pendente', 'enviado'))
);

CREATE INDEX ix_sessao_lab_usr_status ON sessao_laboratorio(usuario_id, status);
