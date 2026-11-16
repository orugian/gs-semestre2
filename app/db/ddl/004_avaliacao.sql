-- CitizenTech: DDL de Avaliacao e Tentativas de Exercicio Diagnostico (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem dominios, sem tipo JSON nativo)

CREATE TABLE tentativa (
    id VARCHAR2(32) NOT NULL,
    usuario_id VARCHAR2(32) NOT NULL,
    destino_id VARCHAR2(64) NOT NULL,
    exercicio_id VARCHAR2(64) NOT NULL,
    exercicio_versao VARCHAR2(20) NOT NULL,
    respostas_objetivas_json VARCHAR2(2000) NOT NULL,
    acertos NUMBER(2) NOT NULL,
    total_objetivas NUMBER(2) NOT NULL,
    nota_objetiva NUMBER(5,4) NOT NULL,
    status_aberta VARCHAR2(10) NOT NULL,
    nota_llm NUMBER(5,4),
    nota_final NUMBER(5,4),
    resultado VARCHAR2(15) NOT NULL,
    avaliacao_id VARCHAR2(64),
    sha256_resposta CHAR(64) NOT NULL,
    discordo_em TIMESTAMP WITH TIME ZONE,
    discordo_motivo VARCHAR2(1200),
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_tentativa PRIMARY KEY (id),
    CONSTRAINT fk_tentativa_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
    CONSTRAINT ck_tentativa_resp_obj_json CHECK (respostas_objetivas_json IS JSON),
    CONSTRAINT ck_tentativa_status_aberta CHECK (status_aberta IN ('avaliada', 'parcial')),
    CONSTRAINT ck_tentativa_resultado CHECK (resultado IN ('demonstrada', 'insuficiente', 'parcial'))
);

CREATE INDEX ix_tentativa_usr_ex_criado ON tentativa(usuario_id, exercicio_id, criado_em);
