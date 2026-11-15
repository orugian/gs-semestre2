-- CitizenTech: DDL de Usuario e Consentimento (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem dominios)

CREATE TABLE usuario (
    id VARCHAR2(32) NOT NULL,
    email VARCHAR2(254) NOT NULL,
    senha_hash VARCHAR2(255) NOT NULL,
    sessao_versao NUMBER(10) DEFAULT 0 NOT NULL,
    persona_demo CHAR(1) DEFAULT 'N' NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_usuario PRIMARY KEY (id),
    CONSTRAINT uq_usuario_email UNIQUE (email),
    CONSTRAINT ck_usuario_persona_demo CHECK (persona_demo IN ('S', 'N'))
);

CREATE TABLE consentimento (
    id VARCHAR2(32) NOT NULL,
    usuario_id VARCHAR2(32) NOT NULL,
    finalidade VARCHAR2(30) NOT NULL,
    versao_termo VARCHAR2(20) NOT NULL,
    concedido_em TIMESTAMP WITH TIME ZONE NOT NULL,
    revogado_em TIMESTAMP WITH TIME ZONE,
    CONSTRAINT pk_consentimento PRIMARY KEY (id),
    CONSTRAINT fk_consentimento_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    CONSTRAINT ck_consentimento_finalidade CHECK (finalidade IN ('perfil', 'curriculo_llm', 'laboratorio_nuvem'))
);

CREATE INDEX ix_consentimento_usuario_id ON consentimento(usuario_id);
