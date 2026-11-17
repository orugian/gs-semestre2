# Vídeo pitch — Machine Learning (máx. 5 min)

**Link (YouTube não listado ou Google Drive com acesso habilitado):** [HUMANO — preencher]
**Conteúdo exigido:** problema, decisões de modelagem, resultados e aplicação prática, com demonstração do notebook ou das previsões.

## Preparação (antes de gravar)
1. `05_ML/slides.pdf` aberto em tela cheia.
2. `05_ML/notebook.ipynb` aberto **já executado** (não reexecutar gravando: o treino não é refeito no notebook, ele lê os artefatos de `.dados/artefatos/`). Rolar até as células de métricas (§7), importância das variáveis e demonstração (§8, origem 202509, SP).
3. App web e API locais conforme o [README](<../README.md#rodar-a-aplicação>), com o snapshot de Mercado configurado. Não é preciso login ou LLM para a aba **Mercado**. Selecionar o destino "Analista de Monitoramento/IoT Industrial", UF SP.
4. Não mostrar `app/.env`, terminal com variáveis nem a pasta `.dados/`.

## Roteiro com tempos

| Tempo | Fala (resumo) | Tela |
|---|---|---|
| 0:00–0:30 | Problema e público: profissionais graduados em transição de carreira escolhem destino sem saber quanto o mercado formal absorve. O modelo estima **admissões formais do próximo trimestre** por destino e UF. Não é chance individual de contratação. | Slides "Problema e Público", "Motivação" |
| 0:30–1:05 | Base: microdados públicos do Novo Caged (MTE), admissões com ensino superior completo ou mais nas ocupações CBO de 3 destinos, por UF, 202001–202509. 81 séries; 55 com média de treino ≥ 10 entram na avaliação. Split temporal: treino 202101–202409, embargo de 3 meses, validação 202501–202509 (495 linhas). Holdout 2026 fechado. | Slide "Base de Dados"; notebook §2–§3 |
| 1:05–1:45 | Decisões de pré-processamento: lags, médias e somas móveis; padronização ajustada **só no treino** de cada fold; seleção por densidade calculada só no treino. Por que isso evita vazamento: o alvo soma t+1..t+3, então sem embargo o treino veria meses do alvo. | Notebook §3 |
| 1:45–2:30 | Modelos: dois baselines (persistência e sazonal), Ridge, Random Forest e HistGradientBoosting. Tuning com RandomizedSearchCV em validação temporal (3 folds, 6 iterações por família). | Slides "Modelos Comparados", "Otimização" |
| 2:30–3:20 | Resultados na validação 2025 (MAE em admissões por trimestre): sazonal **33,60**; Ridge 34,26; persistência 35,45; Random Forest 35,63; HGB 39,74. **Nenhum modelo clássico superou o baseline sazonal.** A rede neural (disciplina de Redes Neurais) teve 31,65, 5,78% abaixo do sazonal. | Slide "Métricas"; notebook §7 |
| 3:20–3:50 | Importância das variáveis: no Random Forest dominam soma de 3 meses (0,18), lag 1 (0,15), média de 3 meses (0,14). Leitura: inércia do emprego formal; é relação preditiva, não causal. | Slide "Importância das Variáveis" |
| 3:50–4:30 | Modelo final e decisão: pela regra D10a, promover exige ≥ 5% de ganho, estabilidade entre folds e teste no holdout 2026, que está fechado. **Nenhum modelo foi promovido**; o app mostra o baseline sazonal. Demonstração: notebook §8, IoT em SP, origem 202509: sazonal 329, MLP 420,6, realizado 391. | Slide "Modelo Final"; notebook §8 |
| 4:30–4:50 | Aplicação: na aba Mercado do app, a pessoa vê as admissões observadas e a estimativa do destino na UF, com fonte e limites. | App web, aba Mercado |
| 4:50–5:00 | ODS 4 (meta 4.4), ODS 8 e ODS 10. Nomes e RMs. | Slide "ODS" |

## Cuidados
- Não dizer que um modelo "foi escolhido como final" ou "está em produção". O número exibido no app é o baseline sazonal.
- Não chamar a validação 2025 de teste final: ela orientou a leitura, e o teste final é o holdout 2026, ainda fechado.
- As admissões são registros formais observados, não vagas abertas.
