# Aceite do caderno visual — documento, não aplicação

**16/11/2026,09h42 UTC−3.** Artefato: [panorama_projeto.html](<../../docs/historico/panorama_projeto.html>). Integração documental `c6ee6e1`; checkpoint funcional `13cb0a2`, regressão registrada em `5d311e7`, contexto reconciliado com `dd55e48`(09h15). O panorama é estático/offline e **não prova jornadaE2E, implantação ou submissão acadêmica**.

## Escopo executado

- Handoff inicial e prompt entregues antes da implementação visual. Quando a árvore principal avançou em outra sessão, um novo handoff09h15 substituiu o inicial: S8/E08/S15a/E05 já integrados; próxima implementaçãoS9. Nenhuma dessas fatias foi refeita por esta linha documental.
- Autoria isolada via agy em worktree, com snapshots; reconciliação posterior só no HTML e PRODUCT.md. Nenhuma mudança em `app/` no diff `dd55e48..c6ee6e1`.
- A rodada inicial passou em6checagens estruturais, mas foi rejeitada por leitura/render: falsos feitos de firmware/PII/Cloud, SVG ilegível no mobile e viewport expandido. A correção não foi tratada como aprovação por autorrelato.
- RED de publicação: arquivo ausente→`AssertionError`,1failed. Aceite final emmain: `uv run pytest <test_panorama_documental.py> -q -o addopts=''` → **8passed em0,19s**. O script de aceite é trilha do orquestrador em `.kaiser/tmp`, não código do produto. Verifica publicação/idioma/landmarks, offline, âncoras, destinos locais,9enunciados, limites,checkpoint e hierarquia de títulos.

## Browser real, versão publicada

`pnpm exec node <verificar_panorama_browser.mjs> <HTML-em-main> <pasta-provas>` → saída0 (`pwsh-300`). Edge headless, perfil temporário separado, arquivo local; sem servidor da aplicação e sem pacote novo.

| Largura solicitada | innerWidth | scrollWidth | Resultado |
|---:|---:|---:|---|
|1440|1440|1425|sem expansão horizontal do documento|
|768|768|753|sem expansão horizontal do documento|
|390|390|390|sem expansão horizontal do documento|
|360|360|360|sem expansão horizontal do documento|

A diferença15px desktop/tablet é a barra de rolagem vertical. Tabelas largas mantêm rolagem local nomeada,tabindex e aviso visível; a rolagem local não é overflow do corpo.

- Corpo17px/27,2px; menor rótulo/código12px; tracking mínimo−0,01em.
-698 trechos HTML avaliados por cor/fundo computados: menor contraste6,917:1, nenhuma violação detectada nesse recorte. Não equivale a auditoriaWCAG integral.
- Tab colocou foco no skip link; outline2px/offset2px. Hover do skip link mantém texto branco. Enter(com evento de texto correto) expandiu o sumário mobile nativo.
- Zero requisiçõesHTTP(S) de recursos da página. Imagens/fontes/CDN/JS não são necessários para abrir o documento.
- [Relatório bruto do browser](<20261116_panorama_browser.json>), [início desktop](<20261116_panorama_desktop-inicio.png>), [arquitetura desktop](<20261116_panorama_desktop-arquitetura.png>) e [início mobile](<20261116_panorama_mobile-inicio.png>).

## Impeccable e revisão independente

Contexto, direçãoRead confirmada, craftfloor, detector mecânico e inspeção de capturas reais foram usados. O detector **não retornou zero**: alertou hover, níveis de títulos, fontes pequenas,tracking e padding. Foram corrigidos hover preto-sobre-preto do skip link, saltoH2→H4 e código herdado abaixo12px. Os alertas de tracking/padding foram confrontados com Edge:−0,01em e células9,35/12,75px, não os valores inferidos pelo detector. Não houve suppressão/allowlist de alertas.

Revisor novo somente leitura examinou HTML completo/fontes e seis capturas. Disposição inicial **FIX**,1achadoP2: revisão das rubricas estava tarde na ordem dos gates. Corrigido: homologação das três rubricas antes deS10/S13; Gate6 apenas remete ao pré-requisito. Revisor confirmou **P2resolvido**, restrito à leitura desse trecho, sem aprovação geral de runtime. As verificações finais emmain ocorreram depois das correções.

## Não verificado / não feito

Não executados nesta linha documental: suítes de produto ML/API/Web,28testesOracle pósS8,Cloud/Tools,axe/Playwright da aplicação,leitor de tela,zoom200%,toque físico ou impressão/PDF deste panorama. As contagens de produto exibidas são registros identificados de outra frente. Não abriram holdout, não retunaram modelos, não acessaram segredos/dados de mercado para esta página, não houve push nem exclusão de dados/schemas/volumes. Worktree documental limpo/integrado removido; S5 original e RED preservados.
