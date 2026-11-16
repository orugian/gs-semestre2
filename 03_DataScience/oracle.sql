-- CitizenTech · Data Science · Oracle (dialeto 19c)
-- Arquivo GERADO por app/tools/empacotar_entregas.py: não edite aqui; edite as origens.
-- Ordem: DDL 001–007 e, no fim, as consultas de evidência (resultados em evidencias/).

-- ======================================================================
-- Origem: app/db/ddl/001_usuario_consentimento.sql
-- ======================================================================
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

-- ======================================================================
-- Origem: app/db/ddl/002_competencias.sql
-- ======================================================================
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

-- ======================================================================
-- Origem: app/db/ddl/003_intencao_comparacao.sql
-- ======================================================================
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

-- ======================================================================
-- Origem: app/db/ddl/004_avaliacao.sql
-- ======================================================================
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

-- ======================================================================
-- Origem: app/db/ddl/005_plano.sql
-- ======================================================================
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

-- ======================================================================
-- Origem: app/db/ddl/006_laboratorio.sql
-- ======================================================================
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

-- ======================================================================
-- Origem: app/db/ddl/007_catalogo.sql
-- ======================================================================
-- CitizenTech: projeção relacional do catálogo curado (FIAP GS 2026.2)
-- Dialeto Oracle 19c (sem BOOLEAN, sem IF NOT EXISTS, sem domínios).
-- A fonte de verdade do catálogo continua nos YAML de app/catalogo. Estas tabelas são carregadas
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

-- ======================================================================
-- Origem: app/db/consultas/evidencias_oracle.sql
-- ======================================================================
-- CitizenTech: consultas de evidência (Data Science) — Oracle 19c
-- Executadas no Oracle local (Docker Free 23ai, DDL no dialeto 19c) sobre o schema do app,
-- com dados da persona de demonstração e do catálogo carregado (DDL 007).
-- Execução: app/tools/executar_consultas_oracle.py (grava a saída em 03_DataScience/evidencias/).

-- C1. Catálogo: ocupações CBO de cada destino (JOIN + agregação de texto)
SELECT d.id AS destino,
       d.no_escopo_mvp AS mvp,
       COUNT(o.cbo6) AS ocupacoes,
       LISTAGG(o.cbo6, ', ') WITHIN GROUP (ORDER BY o.cbo6) AS cbo6
FROM destino d
JOIN destino_ocupacao dox ON dox.destino_id = d.id
JOIN ocupacao_cbo o ON o.cbo6 = dox.cbo6
GROUP BY d.id, d.no_escopo_mvp
ORDER BY d.no_escopo_mvp DESC, d.id;

-- C2. Requisitos por destino: obrigatórios × opcionais e quantos são conhecimento (agregação)
SELECT rd.destino_id AS destino,
       SUM(CASE WHEN rd.obrigatorio = 'S' THEN 1 ELSE 0 END) AS obrigatorios,
       SUM(CASE WHEN rd.obrigatorio = 'N' THEN 1 ELSE 0 END) AS opcionais,
       SUM(CASE WHEN ce.tipo = 'conhecimento' THEN 1 ELSE 0 END) AS de_conhecimento
FROM requisito_destino rd
JOIN competencia_esco ce ON ce.esco_id = rd.esco_id
GROUP BY rd.destino_id
ORDER BY rd.destino_id;

-- C3. Competências ESCO compartilhadas por mais de um destino (GROUP BY + HAVING)
SELECT ce.titulo AS competencia,
       COUNT(DISTINCT rd.destino_id) AS destinos
FROM competencia_esco ce
JOIN requisito_destino rd ON rd.esco_id = ce.esco_id
GROUP BY ce.titulo
HAVING COUNT(DISTINCT rd.destino_id) > 1
ORDER BY destinos DESC, competencia;

-- C4. Competências revisadas pela persona de demonstração, com o requisito correspondente em cada destino (JOIN de 4 tabelas)
SELECT ce.titulo AS competencia,
       cu.revisao,
       cu.estado_evidencia,
       rd.destino_id AS destino,
       rd.obrigatorio
FROM competencia_usuario cu
JOIN usuario u ON u.id = cu.usuario_id
JOIN competencia_esco ce ON ce.esco_id = cu.esco_id
LEFT JOIN requisito_destino rd ON rd.esco_id = cu.esco_id
WHERE u.persona_demo = 'S'
ORDER BY cu.revisao, ce.titulo, rd.destino_id;

-- C5. Obrigatórios de cada destino do MVP que a persona ainda não confirmou (subconsulta NOT EXISTS)
SELECT rd.destino_id AS destino,
       rd.id_local AS requisito_obrigatorio
FROM requisito_destino rd
JOIN destino d ON d.id = rd.destino_id AND d.no_escopo_mvp = 'S'
WHERE rd.obrigatorio = 'S'
  AND NOT EXISTS (
        SELECT 1
        FROM competencia_usuario cu
        JOIN usuario u ON u.id = cu.usuario_id
        WHERE u.persona_demo = 'S'
          AND cu.esco_id = rd.esco_id
          AND cu.revisao = 'confirmada')
ORDER BY rd.destino_id, rd.ordem;

-- C6. Tentativas do exercício diagnóstico com classificação da melhor por pessoa e exercício (função analítica RANK)
SELECT t.exercicio_id,
       t.criado_em,
       t.nota_objetiva,
       t.nota_llm,
       t.nota_final,
       t.resultado,
       RANK() OVER (PARTITION BY t.usuario_id, t.exercicio_id
                    ORDER BY t.nota_final DESC NULLS LAST, t.criado_em DESC) AS posicao_melhor
FROM tentativa t
JOIN usuario u ON u.id = t.usuario_id
WHERE u.persona_demo = 'S'
ORDER BY t.exercicio_id, posicao_melhor;

-- C7. Comparações salvas: leitura de campos do JSON de cada destino (JSON_VALUE, 19c)
SELECT c.criado_em,
       cd.ordem,
       cd.destino_id AS destino,
       cd.situacao_obrigatorios,
       JSON_VALUE(cd.resultado_json, '$.dimensoes.requisitos.contagem.declarada') AS declaradas,
       JSON_VALUE(cd.resultado_json, '$.dimensoes.requisitos.contagem.desconhecida') AS desconhecidas,
       JSON_VALUE(cd.resultado_json, '$.dimensoes.mercado.ultimo_observado.valor') AS ultimo_mes_admissoes,
       JSON_VALUE(cd.resultado_json, '$.dimensoes.mercado.referencia_temporal') AS periodo_observado
FROM comparacao c
JOIN comparacao_destino cd ON cd.comparacao_id = c.id
JOIN usuario u ON u.id = c.usuario_id
WHERE u.persona_demo = 'S'
ORDER BY c.criado_em, cd.ordem;

-- C8. Progresso do plano ativo por tipo de checkpoint (JOIN + agregação condicional)
SELECT ce.destino_id AS destino,
       ck.tipo,
       COUNT(*) AS checkpoints,
       SUM(CASE WHEN ck.status = 'concluido' THEN 1 ELSE 0 END) AS concluidos,
       SUM(CASE WHEN ck.obrigatorio = 'S' THEN 1 ELSE 0 END) AS de_requisito_obrigatorio
FROM caminho_escolhido ce
JOIN plano p ON p.caminho_id = ce.id
JOIN checkpoint ck ON ck.plano_id = p.id
JOIN usuario u ON u.id = ce.usuario_id
WHERE u.persona_demo = 'S' AND ce.status = 'ativo'
GROUP BY ce.destino_id, ck.tipo
ORDER BY ce.destino_id, MIN(ck.ordem);

-- C9. Consentimentos ativos por finalidade (LGPD) entre todas as contas do ambiente de demonstração
SELECT finalidade,
       COUNT(*) AS concedidos,
       SUM(CASE WHEN revogado_em IS NULL THEN 1 ELSE 0 END) AS ativos
FROM consentimento
GROUP BY finalidade
ORDER BY finalidade;
