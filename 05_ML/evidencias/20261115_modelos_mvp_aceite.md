# ML/RNA — aceite dos experimentos reais do MVP

**Execução:** 15/11/2026, horário de São Paulo. **Natureza:** avaliação retrospectiva na validação2025; não é avaliação final, demonstração de serving ou previsão de contratação individual.

## População e desenho congelado

- Novo Caged, admissões formais de pessoas com superior/pós nos três grupos R29: Dados/BI, Monitoramento/IoT e Processos, por UF. Alvo: total de admissões do trimestre futuro, com origens mensais sobrepostas.
- Painel DEV segregado: SHA-256 `33a898980916c841c325fb9e37b643484ee1d6f8b7017a19f52208de02e922c5`. Histórico2020 somente para lags; fit202101–202409; validação externa202501–202509, com embargo temporal.
- Seleção por densidade≥10 somente no treino de cada fold; transformações ajustadas dentro do fit. Na validação global: **55 das81 séries elegíveis,495 linhas =55×9 origens**, mesma máscara para todos os modelos e referências.
- Clássicos: Ridge, Random Forest e HistGradientBoosting; RandomizedSearchCV temporal,6 iterações/família,3 folds, seed42, CPU≤6 threads.
- MLP PyTorch CPU: A64/32,dropout0,1,lr0,001; B128/64,dropout0,2,lr0,0005; batch128,até200 épocas,patience15,min_delta0,00001,seed42. Early stopping interno com janela3meses e embargo3meses; pré-processador ajustado só no fit interno. **A foi escolhida no CV do treino; refit com55 épocas**, sem escolher pela validação2025.
- Código no início dos treinos: `a3a6866`. O holdout2026 permaneceu fechado. Nenhum parâmetro foi ajustado após estes resultados de2025.

## Validação2025 — conferida independentemente

MAE e RMSE em **admissões formais/trimestre por grupo×UF**; WAPE em percentual, calculado sobre495 linhas elegíveis. Não são números de anúncios nem medidas individuais de empregabilidade.

| Modelo/referência | MAE | RMSE | WAPE | Ganho relativo de MAE vs sazonal |
|---|---:|---:|---:|---:|
| Persistência |35,4525|103,5830|12,5588%|−5,53%|
| Sazonal |33,5960|91,3838|11,9011%|referência|
| Ridge |34,2577|84,4189|12,1355%|−1,97%|
| Random Forest |35,6339|135,6003|12,6230%|−6,07%|
| HistGradientBoosting |39,7394|132,1033|14,0774%|−18,29%|
| MLP A |**31,6545**|**73,6720**|**11,2133%**|**+5,78%**|

**Leitura crítica:** os três clássicos não superaram a referência sazonal em MAE. Isso é um resultado válido, não motivo para alterar o split ou retunar com2025. A MLP reduziu o MAE em5,78% e o RMSE nesta amostra; o ganho agregado não demonstra benefício em toda UF/série, estabilidade futura, causalidade ou adequação ao uso individual.

**Nenhum modelo foi promovido.** O ganho mínimo de MAE é apenas parte de D10a. Promoção completa, model cards no MongoDB, serving/fallback, painel técnico, notebooks, slides e avaliação final continuam pendentes. O holdout não foi aberto para resolver essa escolha.

## Evidência executada

1. Regressão integrada ML/RNA/Estatística em `main`: `uv run pytest -q -rs -o addopts=''` → **206passed**, seguido de `uv run ruff check .` → **All checks passed**; job `pwsh-98`.
2. Treino clássico real: CLI `citizentech_ml.treinar_classicos`, com `--validacao --n-iter 6 --seed 42 --n-splits 3` → saída0, job `pwsh-99`.
3. Treino MLP real: CLI `citizentech_ml.treinar_rna`, com `--validacao --max-epochs 200 --patience 15 --min-delta 0.00001 --seed 42 --limite-densidade 10 --n-splits 3 --escopo-mvp` → saída0, job `pwsh-100`.
4. Aceite independente do orquestrador: comparação dos alvos exportados com o painel original por chave; recálculo direto de n/MAE/RMSE/WAPE de cada fold e validação, sem helpers de métricas/split/densidade; reabertura dos artefatos próprios e reprodução das previsões de validação **sem fornecer o alvo aos estimadores** → todas as asserções passaram, saída0, job `pwsh-105`.
5. O recálculo preserva previsões brutas, sem clipagem. O aviso de depreciação pandas sobre `float_precision` afetou apenas o leitor CSV do script de conferência, não o cálculo nem o treino.

Os valores completos e os recálculos de CV estão no [JSON de aceite](<20261115_modelos_mvp_aceite.json>). Artefatos grandes permanecem fora do git, sob os diretórios próprios `.dados/artefatos/classicos/20261115_r29_aceite` e `.dados/artefatos/rna/20261115_r29_aceite`, com hashes nos respectivos manifestos.

## Limites e dívidas explícitos

- CV foi usado para seleção: suas métricas não são uma estimativa independente de generalização; a validação2025 não é o teste final.
- A métrica de495 origens não transforma os trimestres sobrepostos em495 observações independentes. Não foi calculado intervalo de confiança por reamostragem temporal.
- Hashes demonstram integridade local, não autenticidade de um diretório controlado por atacante. Somente artefatos próprios foram carregados; reabertura direta não mede latência HTTP/carga de produção.
- Permanecem ajustes de schema comparativo da RNA (`_medio`/`_media`, resumo MASE das referências), validação defensiva de `melhor_config` em manifestos externos e ancoragem externa de hashes para o serving S8.
- As três rubricas do MVP ainda exigem revisão humana. Esta evidência não substitui notebooks executados, slides, relatório acadêmico nem vídeos obrigatórios.
