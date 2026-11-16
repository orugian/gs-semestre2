-- CitizenTech: DDL de Plano de Transicao e Checkpoints (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem dominios, sem tipo JSON nativo)

CREATE TABLE caminho_escolhido (
    id VARCHAR2(32) NOT NULL,
    usuario_id VARCHAR2(32) NOT NULL,
    destino_id VARCHAR2(64) NOT NULL,
    comparacao_id VARCHAR2(32),
    versao_catalogo VARCHAR2(40),
    status VARCHAR2(12) NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_caminho_escolhido PRIMARY KEY (id),
    CONSTRAINT fk_caminho_usuario FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE,
    CONSTRAINT fk_caminho_comparacao FOREIGN KEY (comparacao_id) REFERENCES comparacao(id) ON DELETE SET NULL,
    CONSTRAINT ck_caminho_status CHECK (status IN ('ativo', 'substituido'))
);

CREATE INDEX ix_caminho_usuario_status ON caminho_escolhido(usuario_id, status);

CREATE TABLE plano (
    id VARCHAR2(32) NOT NULL,
    caminho_id VARCHAR2(32) NOT NULL,
    regra VARCHAR2(60),
    base_json CLOB NOT NULL,
    observacoes_json VARCHAR2(2000),
    gerado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_plano PRIMARY KEY (id),
    CONSTRAINT uq_plano_caminho_id UNIQUE (caminho_id),
    CONSTRAINT fk_plano_caminho FOREIGN KEY (caminho_id) REFERENCES caminho_escolhido(id) ON DELETE CASCADE,
    CONSTRAINT ck_plano_base_json CHECK (base_json IS JSON),
    CONSTRAINT ck_plano_obs_json CHECK (observacoes_json IS JSON)
);

CREATE TABLE checkpoint (
    id VARCHAR2(32) NOT NULL,
    plano_id VARCHAR2(32) NOT NULL,
    ordem NUMBER(3) NOT NULL,
    tipo VARCHAR2(12) NOT NULL,
    titulo VARCHAR2(300) NOT NULL,
    descricao VARCHAR2(1500),
    criterio_conclusao VARCHAR2(1000),
    requisito_id_local VARCHAR2(80),
    estado_origem VARCHAR2(15),
    motivo_origem VARCHAR2(60),
    obrigatorio CHAR(1) NOT NULL,
    exercicio_id VARCHAR2(64),
    status VARCHAR2(15) NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_checkpoint PRIMARY KEY (id),
    CONSTRAINT fk_checkpoint_plano FOREIGN KEY (plano_id) REFERENCES plano(id) ON DELETE CASCADE,
    CONSTRAINT ck_checkpoint_tipo CHECK (tipo IN ('estudar', 'praticar', 'demonstrar', 'laboratorio', 'exercicio')),
    CONSTRAINT ck_checkpoint_obrigatorio CHECK (obrigatorio IN ('S', 'N')),
    CONSTRAINT ck_checkpoint_status CHECK (status IN ('pendente', 'em_andamento', 'concluido')),
    CONSTRAINT uq_checkpoint_plano_ordem UNIQUE (plano_id, ordem)
);
