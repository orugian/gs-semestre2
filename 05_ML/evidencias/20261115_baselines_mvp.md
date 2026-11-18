# Baselines do MVP R29 — execução de 15/11/2026

## Escopo e natureza dos resultados

**Verificado por execução do orquestrador**, a partir de `main` após o merge `d807e10`. Estes resultados substituem a configuração anterior **somente para o MVP reduzido**, sem apagar ou relabelar as evidências dos seis destinos de 13/11.

- Fonte: Novo Caged, painel de desenvolvimento previamente construído na S7b; série principal de admissões formais com superior completo ou mais.
- População operacional: **Dados/BI, Monitoramento/IoT e Processos**, cada destino com conjunto CBO disjunto; 27 UFs, 81 séries potenciais.
- Unidade do alvo e do MAE: **admissões por trimestre futuro** (`A(t+1)+A(t+2)+A(t+3)`). Não são vagas disponíveis nem probabilidade individual de contratação.
- Natureza: previsões retrospectivas dos baselines, comparadas ao alvo observado consolidado no painel; não são métricas de modelos ML/RNA já treinados.
- Treino: origens **202101–202409**, 45 meses. Linhas de 2020 preservadas apenas como histórico, sem entrar no ajuste/densidade/folds.
- Validação externa: origens **202501–202509**. Nenhuma EDA dessa partição; somente métricas previstas no protocolo. Holdout de 2026 **não aberto**.
- Elegibilidade global: **55 de 81 séries**, média do alvo no treino ≥10; comparação de validação em **495 linhas**, mesmas linhas para os dois baselines. A densidade foi recalculada em cada fold, sem usar os alvos de validação.
- As três rubricas continuam com revisão humana pendente. O corte de produto não altera a população científica de seis destinos de D11/Estatística.

## Procedência e recorte

O arquivo original de desenvolvimento foi identificado por hash e metadados temporais, **sem reconstruir microdados**:

| Artefato | SHA-256 |
|---|---|
| Painel original, seis destinos | `8e653b0047ceed204d25bf7c0d9d28c8d7944bd4e75c7f65bf4ea09651b4eb9e` |
| Painel projetado, três destinos | `33a898980916c841c325fb9e37b643484ee1d6f8b7017a19f52208de02e922c5` |
| Conjunto de destinos R29 | `991fbc5dbbcc7646de699ef38ef845e4a04f58299a13e04477516918c6cb1f61` |

O recorte tem **5.589 linhas**: histórico2020=972, treino202101–202409=3.645, embargo202410–202412=243 e validação202501–202509=729. Os valores de features/lag foram preservados, não recalculados. Após elegibilidade no treino, a validação efetivamente pontuada tem495linhas.

Manifesto completo: [recorte](<20261115_recorte_mvp.json>). Resultados completos, inclusive métricas por série e folds: [baselines](<20261115_baselines_mvp.json>).

## Comandos executados

Dentro de `app/ml`, com saídas novas fora do repositório:

```powershell
uv run python -m citizentech_ml.recorte --painel <DADOS>\caged\painel\painel_desenvolvimento.parquet --saida <DADOS>\caged\painel\r29_20261115_2041\painel_mvp.parquet
uv run python -m citizentech_ml.baselines --painel <DADOS>\caged\painel\r29_20261115_2041\painel_mvp.parquet --saida <DADOS>\caged\painel\r29_20261115_2041\baselines --escopo-mvp --inicio-treino 202101 --validacao
```

Ambos concluíram com saída0 (`pwsh-35`). O original e as evidências anteriores não foram sobrescritos. Versões do recorte: pandas3.1.1, numpy2.4.6, pyarrow26.0.1.

## Resultados medidos

Desvios entre folds abaixo são amostrais, `ddof=1`; WAPE é exibido em porcentagem.

| Baseline | MAE médio CV treino | Desvio MAE | WAPE médio CV | Desvio WAPE | MAE validação | WAPE validação |
|---|---:|---:|---:|---:|---:|---:|
| Persistência trimestral | 39,94 | 9,85 | 14,75% | 3,77 p.p. | 35,45 | 12,56% |
| Sazonal | 54,06 | 1,66 | 19,92% | 0,54 p.p. | 33,60 | 11,90% |

**Interpretação limitada:** persistência é melhor nos três folds internos desta execução, mas o sazonal tem menor MAE na validação externa. Isso não autoriza ajustar grids/features usando2025 nem abrir o teste. Não há candidato ML/RNA promovido; D10a continua congelado. Modelos clássicos e RNA ainda precisam de execução e avaliação próprias.

## Conferência independente

Outro cálculo, sem importar helpers de baseline, splitter, densidade ou métricas, reabriu **somente o painel de desenvolvimento projetado**, selecionou séries pela média do alvo no treino e recalculou `n`, MAE, RMSE e WAPE:

- Fold0: treino202101–202309; avaliação202401–202403; n165.
- Fold1: treino202101–202312; avaliação202404–202406; n168.
- Fold2: treino202101–202403; avaliação202407–202409; n165.
- Validação externa: treino202101–202409; avaliação202501–202509; n495.

**0 divergências**, tolerância relativa `1e-12`. Saída integral: [conferência](<20261115_conferencia_baselines.txt>).

## Aceite e limitações

- Regressão em `main`: `uv run pytest -q -rs -o addopts=''` → **110passed**; ruff limpo.
- Revisão independente `agy --mode plan` sobre `ac8230f`; adjudicação: return duplicado removido, sobrescrita de baselines bloqueada e população parcial rotulada corretamente. Correções pequenas em `b45b092`, sem segunda revisão independente.
- Limitação histórica: não há RED inicial autoral preservado da projeção. Há REDs dos validadores/CLI e RED/GREEN executados pelo orquestrador para os manifestos.
- **Rejeitar2026 após ler um arquivo não é uma barreira de I/O.** O orquestrador usou somente o painel segregado identificado pelo hash acima. O carregador legado de microdados não deve ser apontado para o diretório misto2020–2026 nesta etapa.
- Não verificados/concluídos aqui: Ridge/RF/HGB, MLP, promoção, teste final, model cards, integração de mercado/API e entregas finais de notebook/slides/vídeo.
