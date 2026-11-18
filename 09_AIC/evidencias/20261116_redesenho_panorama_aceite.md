# Aceite documental — reconstrução visual do panorama

## Resultado e limite

**Decisão do orquestrador: publicar a reconstrução documental**, integrada em `53f4c50` (autoria `de18cf4`). Não é aprovação da aplicação ponta a ponta nem aceite humano do novo visual. A versão anterior foi rejeitada pelo usuário apesar de seus testes técnicos terem passado; suas provas históricas foram preservadas.

Documento: [panorama](<../../docs/historico/panorama_projeto.html>). SHA-256: `d2f6073e701f3957be8e1cebe96995fafc1bac21d9d6357450acbb27cfece01c`.

O conteúdo é um retrato de **16/11/2026 ~11h34, base funcional18e72aa**, não monitoramento ao vivo. S9 backend integrado; S10/S4 em andamento nesse checkpoint; S11 domínio integrado, rotas pendentes. Atlas e empacotamento E09 existentes; rubricas aprovadas; pacotes gerados não equivalem a envio.

## Mudança de compreensão

- Cinco áreas navegáveis, uma exposta de cada vez: visão geral, sistema, disciplinas, próximos passos e fontes.
- Propósito curto, ação principal antecipada e separação entre já funciona, em construção e para entregar.
- Nove matérias por seleção mestre/detalhe; feito, falta, arquivos e ação da equipe. Eliminada a matriz larga.
- Sistema com conexões, detalhes progressivos e gate humano antes da LLM; ciência offline separada do serving sazonal.
- Sem JavaScript: nove painéis legíveis e nove âncoras reais; controles inertes ocultos.

## Evidência executada pelo orquestrador

Em `app/web`, Node nativo + CDP/Edge headless, sem dependências nem servidor:

```powershell
pnpm exec node C:\Users\orugi\Documents\Projetos\FIAP\GS\.kaiser\tmp\verificar_redesenho_browser.mjs C:\Users\orugi\Documents\Projetos\FIAP\GS\info-gs-diciplinas\docs\panorama_projeto.html C:\Users\orugi\Documents\Projetos\FIAP\GS\.kaiser\tmp\redesenho-qa-main
```

Comando histórico; o temporário foi limpo depois do aceite. [Verificador arquivado na trilha externa ao Git](<../../../.kaiser/reports/DOC-redesenho-verificador.md>).

- **RED:** versão antiga → `AssertionError: Visao geral excessivamente densa:5376 palavras visiveis; limite400` (job484, antes da autoria).
- R1 percorreu as áreas/matérias mas falhou por tipografia e contraste. R2 exigiu ainda ajuste local do contador ativo/separadores. Não foram aceitas apenas por funcionarem.
- **GREEN no worktree e em main:** jobs7 e11, ambos saída0; execução em main encerrada em **2026-11-16T15:52:52.953Z**.
- Cinco larguras reais:1440,1280,768,390,360px, sem expansão de `innerWidth` para acomodar conteúdo.
- Cinco áreas exercitadas em desktop/mobile; nove matérias selecionadas em cada modalidade, com atualização de conteúdo.
- Home/End+Enter sincronizando seleção e URL; deep link, Back/Forward, primeiroTab/skiplink; disclosures de sistema/fontes abertos.
- Texto inicial:285 palavras no desktop e262 no mobile, em vez de5376 expostas continuamente. Não é percentual de conclusão do projeto.
- Contraste computado nos estados exercitados: mínimo4,79:1; fonte mínima12px. Zero erros de contraste/tamanho nas verificações finais.
-35 destinos de link verificados; nenhuma requisição HTTP(S) e nenhum erro JavaScript registrado.
- JavaScript desativado: **9 painéis visíveis +9 âncoras funcionais**, não apenas texto genérico não vazio.
- [Resultado bruto](<20261116_redesenho_panorama_browser.json>).

## Revisão independente e adjudicação

Exploração nativa somente leitura, fresca, sem relatório autoral; leu fontes e capturas. A R1 foi classificada como relatório em cartões, com cinco achados materiais aceitos. Após a R2, a conclusão foi: **a reconstrução agora reduz materialmente a carga cognitiva; não requer novo redesign**. Estatística, arquitetura, mobile e sincronização foram considerados corrigidos pela leitura.

Restaram dois FIXs aceitos e corrigidos localmente:
1. Cloud: simulador **do dispositivo** enviando leituras à Function URL (POST válido201), CloudWatch com payload/classificação e consulta com ocorrências; não basta teste da Lambda retornando200.
2. Fallback: expor as nove matérias semJS, com âncoras; demonstrado pela execução final9/9.

Outras correções: AICSS sem vídeo obrigatório inventado; rosto de quem narra/YouTube não listado/UML/live em AIC; Z para médias, logística binária e unidade do MAE; Oracle local com DDL19c; texto redigido, não currículo bruto, no Mongo. Nenhum modelo foi promovido ou reavaliado aqui.

Detector Impeccable executado uma vez nesta reconstrução: saída2 com avisos de bordas/fontes. Achados incorporados ao loteR2 e conferidos por CSS/render/computados; não se afirma detector final sem avisos. O exame heurístico e os testes não substituem teste de compreensão com o usuário.

## Proveniência das capturas

Capturas reais do HTML integrado, Edge headless, escala1, perfis temporários próprios, movimento reduzido; nenhuma composição ou imagem gerada:

- [Abertura desktop1440×1000](<20261116_redesenho_panorama_desktop.png>) · [Mobile390×844](<20261116_redesenho_panorama_mobile.png>).
- [Matérias desktop](<20261116_redesenho_panorama_disciplinas.png>) · [Arquitetura](<20261116_redesenho_panorama_arquitetura.png>).
- [Gate de confirmação expandido](<20261116_redesenho_panorama_confirmacao.png>) · [Fallback semJS](<20261116_redesenho_panorama_fallback.png>).

## Não feito / riscos residuais

Não executados: regressão do produto, Oracle/AWS/LLM reais, holdout, avaliação de modelos, axe integral, toque físico, impressão/PDF ou estudo de usabilidade com participantes. Execuções de ML/API/Web mencionadas no panorama são registradas de outras frentes, não reexecuções desta tarefa. Nenhuma alteração em `app/`, dado, segredo, enunciado ou recurso remoto foi feita para este redesenho.
