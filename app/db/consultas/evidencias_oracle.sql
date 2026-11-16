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
