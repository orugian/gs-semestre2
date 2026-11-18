# Roteiro de gravação — Machine Learning (até 5 min)

**Exigido pelo enunciado:** problema, decisões de modelagem, resultados e aplicação prática, com demonstração do notebook ou das previsões. Link do YouTube não listado ou Google Drive com acesso liberado.

## Antes de gravar

1. Abra `05_ML\slides.pdf` em tela cheia.
2. Abra `05_ML\notebook.ipynb` no VS Code (ou no GitHub). Ele **já está executado**: só role. **Não reexecute** (o treino lê dados que ficam fora do repositório).
3. Na raiz: `powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\subir_app.ps1`. Em http://localhost:5173, aba **Mercado**, escolha "Analista de Monitoramento/IoT Industrial" e UF **SP**.

## Gravação

| Tempo | O que dizer | Tela |
|---|---|---|
| 0:00–0:30 | Quem está em transição escolhe um destino sem saber quanto o mercado formal absorve. O modelo estima **admissões formais do próximo trimestre** por destino e UF. **Não** é chance individual de contratação. | Slides "Problema e Público" |
| 0:30–1:05 | Dados: microdados públicos do Novo Caged (MTE), admissões com superior completo nas ocupações de 3 destinos, por UF, 202001–202509. 81 séries; 55 com média de treino ≥ 10 entram na avaliação. Treino 202101–202409, embargo de 3 meses, validação 202501–202509 (495 linhas). O teste de 2026 ficou fechado. | Slide "Base de Dados"; notebook §2–3 |
| 1:05–1:45 | Pré-processamento: lags, médias e somas móveis; padronização ajustada **só no treino** de cada fold. Sem o embargo, o treino veria meses do próprio alvo (vazamento). | Notebook §3 |
| 1:45–2:30 | Modelos: dois baselines (persistência e sazonal), Ridge, Random Forest, HistGradientBoosting; ajuste com validação temporal (3 folds, 6 tentativas por família). | Slides "Modelos", "Otimização" |
| 2:30–3:20 | Resultados (MAE, admissões por trimestre): sazonal **33,60**; Ridge 34,26; persistência 35,45; Random Forest 35,63; HGB 39,74. **Nenhum clássico superou o baseline sazonal.** A rede neural (outra disciplina) teve 31,65. | Slide "Métricas"; notebook §7 |
| 3:20–3:50 | Importância (Random Forest): soma de 3 meses (0,18), lag 1 (0,15), média de 3 meses (0,14) — inércia do emprego formal; é relação preditiva, não causal. | Slide "Importância" |
| 3:50–4:30 | Decisão: promover exige ≥ 5% de ganho, estabilidade e o teste de 2026, que está fechado. **Nenhum modelo foi promovido**; o app mostra o baseline sazonal. Exemplo do notebook §8: IoT em SP, origem 202509 — sazonal 329, MLP 420,6, realizado 391. | Slide "Modelo Final"; notebook §8 |
| 4:30–4:50 | Aplicação: na aba Mercado, a pessoa vê admissões observadas e a estimativa, com fonte e limites. | App, Mercado |
| 4:50–5:00 | ODS 4 (meta 4.4), 8 e 10. Nomes e RMs. | Slide "ODS" |

## Não diga
"Vagas", "o modelo final", "em produção", "teste final" para a validação de 2025.

## Checklist
- [ ] até 5 min · [ ] notebook ou previsões aparecem · [ ] "nenhum modelo promovido" dito · [ ] nomes e RMs · [ ] link testado
