# CitizenTech ML — Features e Split Temporal (Novo Caged)

Módulo de processamento de microdados, engenharia de features retrospectivas, seleção por densidade e divisão temporal com embargo para a previsão trimestral de admissões formais por ocupação e Unidade Federativa (FIAP Global Solution 2026.2).

---

## 1. Visão Geral da Arquitetura

O componente opera sobre os microdados do Novo Caged (2020–2026) estruturados em arquivos Parquet gerados na etapa de ingestão. As séries temporais são agregadas na unidade canônica:
$$\text{Destino} \times \text{UF (27)} \times \text{Mês (YYYYMM)}$$

As ocupações são divididas em 6 destinos profissionais disjuntos (`app/catalogo/ocupacoes_cbo.json`):
1. `analista_dados_bi`
2. `analista_monitoramento_iot`
3. `analista_processos`
4. `gerente_projetos_produto`
5. `analista_suporte_infra`
6. `desenvolvedor_sistemas`

A reserva CBO6 (`cbo6_reserva`) é estritamente disjunta dos destinos e descartada das séries oficiais. Qualquer sobreposição entre destinos ou entre reserva e destinos dispara `ValueError` imediatamente.

---

## 2. Regras de Disponibilidade as-of e Cobertura

### 2.1 Disponibilidade Conservadora (D04b / R02 / T05 / T18)
Para evitar vazamento temporal (*lookahead bias*), as features no instante $t$ utilizam uma **aproximação retrospectiva por competência** (a publicação real em dia exato não foi observada pela fonte pública do Caged):
- **EXC (Exclusões)**: $t_{\text{disp}} = \max(\text{competencia\_dec}, \text{competencia\_exc}, \text{competencia\_arquivo})$.
  Uma exclusão registrada em 2025 referente a um fato de 2023 **não** pode alterar a visão do passado antes de 2025.
- **MOV / FOR**: $t_{\text{disp}} = \max(\text{competencia\_dec}, \text{competencia\_arquivo})$.
- **Condição de visibilidade**: um registro só entra no cômputo de features no instante $t$ se $t_{\text{disp}} \le t$ **e** $\text{competencia\_mov} \le t$.
- Campos temporais nulos, vazios ou fora do formato YYYYMM geram `ValueError` explícito.
- Tipos de arquivo aceitos: `MOV`, `FOR`, `EXC` (normalizados via strip e case-insensitive, agregando `EXC` estritamente como exclusão negativa).

### 2.2 Cobertura Estrita e Prevenção de Falsos Zeros (T03)
- O status de ingestão por competência e tipo de arquivo é obtido via relatório de cobertura.
- Um mês possui observação inicial completa se `MOV` está presente com `situacao == 'ingerido'` e `FOR`/`EXC` estão presentes com `situacao in {'ingerido', 'ausente_na_fonte'}`.
- Estados como `nao_promovida`, `pendente`, `falha`, `desconhecida` ou ausência de tipo no manifesto invalidam a cobertura do mês.
- Duplicações conflitantes no manifesto de cobertura disparam `ValueError` explícito.
- **Revisões posteriores em intervalo ($m..t$)**: Para afirmar contagem retrospectiva completa do mês de movimento $m$ no momento as-of $t$, validam-se `MOV` em $m$ e as revisões `FOR`/`EXC` em **todo** o intervalo $m..t$. Uma pendência em mês posterior $k \in [m, t]$ produz `NaN` para o lag correspondente em $t$.
- Lacunas anteriores a $m$ não afetam $m$; falhas futuras $> t$ não alteram o passado (não afetam $t$).
- Séries legítimas sem qualquer movimentação em mês comprovadamente coberto recebem `0.0`.
- Janelas temporais incompletas (lags, somas, médias ou alvos com dados ausentes) permanecem `NaN`.
- Contagens negativas resultantes disparam `ValueError` imediatamente, proibindo clipagem silenciosa (`clip(lower=0)`).

### 2.3 Validação Estrita de Dados (Sem Coerção Silenciosa)
- `saldo_movimentacao`: deve ser estritamente `1` (admissão) ou `-1` (desligamento). Valores nulos, booleanos, floats não inteiros (e.g. 1.9) ou fora de $\{\pm 1\}$ disparam `ValueError`.
- `uf`: deve pertencer aos 27 códigos IBGE válidos (11..53).
- `grau_instrucao`: rejeita valores nulos, booleanos ou não inteiros.

---

## 3. Catálogo de Features e Alvos

### 3.1 Identificadores
- `competencia`: Mês de referência as-of ($t$, string YYYYMM).
- `destino`: Identificador do agrupamento CBO6.
- `uf`: Código IBGE de 2 dígitos das 27 UFs brasileiras.
- `mes`: Mês calendário (inteiro de 1 a 12).

### 3.2 Série Principal (Superior Completo ou Mais)
Apenas registros com grau de instrução em $\{9, 10, 11, 80\}$:
- `admissoes`: Admissões no mês $t$.
- `desligamentos`: Desligamentos no mês $t$.
- `admissoes_lag_1`, `admissoes_lag_2`, `admissoes_lag_3`, `admissoes_lag_12`: Lags de admissões em $t-1, t-2, t-3, t-12$.
- `desligamentos_lag_1`, `desligamentos_lag_2`, `desligamentos_lag_3`, `desligamentos_lag_12`: Lags de desligamentos em $t-1, t-2, t-3, t-12$.
- `admissoes_soma_3m`: Soma dos últimos 3 meses conhecidos: $A(t) + A(t-1) + A(t-2)$.
- `admissoes_media_3m`: Média dos últimos 3 meses: $(A(t) + A(t-1) + A(t-2)) / 3$.
- `admissoes_sazonal_ano_anterior`: Referência sazonal do mesmo trimestre no ano anterior: $A(t-11) + A(t-10) + A(t-9)$.

### 3.3 Série de Contexto (Total - Todos os Níveis de Escolaridade)
Abrange todas as movimentações sem filtro de grau de instrução:
- `admissoes_total`, `desligamentos_total`
- Lags 1, 2, 3, 12 para admissões e desligamentos totais.
- `admissoes_total_soma_3m`, `admissoes_total_media_3m`, `admissoes_total_sazonal_ano_anterior`.

### 3.4 Alvo Trimestral Consolidado ($y$)
$$y(g, t) = A(t+1) + A(t+2) + A(t+3)$$
Onde $A(m)$ são as admissões consolidadas da série principal (MOV + FOR − EXC) avaliadas no horizonte de consolidação da cobertura. Se qualquer um dos três meses futuros for incompleto ou não coberto, o alvo é estritamente `NaN`.

---

## 4. Divisão Temporal e Origem Móvel (D10 / T04)

### 4.1 Split Canônico de Calendário e Proteção do Holdout
- **Treino**: $t \le 202409$
- **Embargo 1**: $202410 .. 202412$ (blindagem contra sobreposição dos alvos de 202409)
- **Validação**: $202501 .. 202509$
- **Embargo 2**: $202510 .. 202512$
- **Teste Holdout**: $202601 .. 202606$

Proteção ativa do holdout:
- As APIs de desenvolvimento (`obter_split_calendario(df, incluir_teste=False)`) retornam exclusivamente `(df_treino, df_val)`.
- `construir_painel_features` limita automaticamente as origens a $t \le 202509$ quando `competencias=None` e bloqueia qualquer competência $\ge 202601$ com `ValueError` a menos que explicitamente autorizado com `permitir_teste=True` (restrito a fixtures sintéticas).

### 4.2 Splitter de Origem Móvel (`SplitOrigemMovel`)
Compatível com a interface `split` e `get_n_splits` do scikit-learn:
- Regras congeladas D10: embargo obrigatório $\ge 3$ meses (`meses_embargo >= 3`), limite máximo de treino $\le 202409$, parâmetros inteiros estritos (rejeita float e bool).
- Folds com expansão temporal contidos dentro do treino ($t \le 202409$).
- Expulsa exatamente 3 meses reais de calendário anteriores ao início de cada validação em todas as séries do painel.
- Imune a dados desordenados ou meses faltantes no painel multi-UF: nunca retorna folds com treino ou validação vazios (rejeita explicitamente se houver lacunas que inviabilizem folds válidos).

---

## 5. Seleção por Densidade no Treino (D04a / T19)

- Uma série só é elegível se a média de seu alvo no treino satisfizer:
$$\overline{y}_{\text{treino}} \ge 10.0 \text{ admissões/trimestre (inclusive)}$$
- **Responsabilidade do chamador**: Deve fornecer exclusivamente o conjunto de treino do fold correspondente (ou do treino global). A função valida que não há competências posteriores ao corte de treino e rejeita alvos negativos ou não finitos.
- Outliers ou tendências na validação/teste jamais alteram a seleção de séries elegíveis.

---

## 6. Otimização de Performance e Pré-Agregação

Para processar milhões de registros do Caged sem estouro de memória:
- A validação de disponibilidade as-of é vetorizada via identificação de combinações temporais únicas.
- A função `pre_agregar_microdados` reduz os microdados a agregados por $(destino, uf, superior, mes, disp)$.
- A função pública `concatenar_pre_agregados(dfs)` permite processar arquivos Parquet ou chunks independentes e consolidá-los.
- `construir_painel_features` aceita tanto microdados brutos quanto DataFrames já pré-agregados, produzindo resultados estritamente equivalentes.

---

## 7. Limitações Conhecidas

1. **Aproximação Retrospectiva por Competência**: A publicação real em dia exato não foi observada pela fonte pública do Caged; a disponibilidade utiliza a aproximação conservadora por competência $\max(\text{competencia\_dec}, \text{competencia\_arquivo}, \text{competencia\_exc})$.
2. **Esparsidade Territorial**: Determinados destinos (e.g. `analista_monitoramento_iot`) possuem volume muito baixo em UFs menores, resultando em abstenção conforme a regra de densidade ($\ge 10.0$).
3. **Quebras de Série CBO**: Códigos como 211220 (Cientista de Dados) só aparecem a partir de 2024; códigos 212425 e 212430 a partir de 2022.

---

## 8. Exemplo Sintético Reproduzível

```python
import pandas as pd
from citizentech_ml.features import (
    construir_painel_features,
    calcular_densidade_treino,
    obter_series_elegiveis,
    filtrar_series_elegiveis,
    pre_agregar_microdados,
    concatenar_pre_agregados,
)
from citizentech_ml.split import SplitOrigemMovel, obter_split_calendario

# 1. Cobertura sintética com MOV, FOR e EXC ingeridos
cobertura = pd.DataFrame([
    {"competencia": f"2024{m:02d}", "tipo": t, "situacao": "ingerido"}
    for m in range(1, 10)
    for t in ["MOV", "FOR", "EXC"]
])

# 2. Microdados sintéticos de movimentação
dados = pd.DataFrame([
    {
        "competencia_mov": "202401",
        "competencia_dec": "202401",
        "competencia_arquivo": "202401",
        "arquivo_tipo": "MOV",
        "saldo_movimentacao": 1,
        "cbo2002_ocupacao": "211205",  # analista_dados_bi
        "uf": "35",                    # SP
        "grau_instrucao": 9,           # Superior completo
    }
])

# 3. Construir painel de features as-of (aceita brutos ou pré-agregados)
painel = construir_painel_features(
    dados=dados,
    cobertura=cobertura,
    competencias=["202401", "202402"],
)

# 4. Seleção por densidade calculada estritamente no treino
relatorio = calcular_densidade_treino(painel, limite_minimo=10.0)
series_ok = obter_series_elegiveis(relatorio)
painel_filtrado = filtrar_series_elegiveis(painel, series_ok)

# 5. Divisão por origem móvel com embargo mínimo de 3 meses
splitter = SplitOrigemMovel(n_splits=2, tamanho_minimo_treino_meses=3, meses_embargo=3)
folds = list(splitter.split(painel))
for fold_idx, (idx_tr, idx_val) in enumerate(folds):
    print(f"Fold {fold_idx}: treino={len(idx_tr)} linhas, val={len(idx_val)} linhas")
```

---

## 9. Painel, EDA e Baselines

Esta seção documenta os módulos de construção do painel de desenvolvimento, análise exploratória descritiva do treino e avaliação dos modelos de referência (baselines).

### 9.1 Comandos de Execução

#### 1. Montagem do Painel de Desenvolvimento
Gera a grade consolidada destino × UF × mês até setembro de 2025, atribuindo as partições de treino ($t \le 202409$), embargo ($202410–202412$) e validação ($202501–202509$):
```bash
uv run python -m citizentech_ml.painel --dados <dir_dados> --saida <dir_saida> [--inicio 202001] [--fim 202509]
```

#### 2. Geração da EDA do Treino
Produz o relatório em Markdown e figuras PNG descritivas operando estritamente sobre as origens de treino:
```bash
uv run python -m citizentech_ml.eda --painel <caminho_painel.parquet> --dados <dir_dados> --saida <dir_saida>
```

#### 3. Avaliação dos Baselines (Origem Móvel)
Executa o backtesting com expansão temporal (3 folds) dentro do treino para os baselines de persistência trimestral e sazonal, e opcionalmente avalia a partição de validação ou projeta para o recorte MVP R29:
```bash
uv run python -m citizentech_ml.baselines --painel <caminho_painel.parquet> --saida <dir_saida> [--inicio-treino AAAAMM] [--validacao] [--escopo-mvp]
```

#### 4. Recorte do Escopo MVP (R29)
Filtra o painel de desenvolvimento retendo exclusivamente os 3 destinos aprovados no MVP (`analista_dados_bi`, `analista_monitoramento_iot`, `analista_processos`), preservando todas as colunas, o histórico de lags 2020 e gravando manifesto determinístico sem permitir sobrescrita:
```bash
uv run python -m citizentech_ml.recorte --painel <caminho_painel.parquet> --saida <caminho_saida.parquet> [--escopo <caminho_escopo.json>]
```

### 9.2 Arquivos de Saída Gerados

1. **`painel_desenvolvimento.parquet`**: Painel temporal estruturado contendo identificadores (`competencia`, `destino`, `uf`, `mes`), features retrospectivas as-of, baselines nativos (`admissoes_soma_3m`, `admissoes_sazonal_ano_anterior`), alvo trimestral consolidado $y(g,t) = A(t+1) + A(t+2) + A(t+3)$ e a coluna categórica `particao`.
2. **`painel_desenvolvimento.json`**: Metadados auditáveis da construção contendo contagem de arquivos e linhas lidas, mapa de descarte de UFs inválidas por código, linhas descartadas após o limite temporal, sha256 do Parquet gerado, sha256 do catálogo CBO utilizado, data/hora UTC ISO-8601 e versões das bibliotecas pandas, numpy e pyarrow.
3. **`eda_treino.md`**: Relatório descritivo com tabelas estruturadas (indicando Fonte, População, Unidade, Período e Natureza) e frases factuais sem interpretações inventadas, números formatados no padrão pt-BR, organizado em 7 seções:
   - *Cabeçalho*: data UTC de geração, SHA-256 do painel analisado e nota metodológica obrigatória.
   - *1. Qualidade e cobertura*: volume de microdados, descartes de UF inválida (legível como "UF 99: ..."), origens cobertas, origens com todas as features completas, tabela de ausência por feature, alvos nulos e proporção de células com zero.
   - *2. Densidade (D04a)*: contagem de UFs elegíveis ($\ge 10$ admissões/trimestre), fração de cobertura efetiva de admissões e lista de UFs excluídas por destino.
   - *3. Nível e tendência*: totais e médias de admissões consolidadas por destino (série principal vs total) e comparativo percentual contra a visão as-of.
   - *4. Sazonalidade*: índice sazonal (1,00 = média anual) calculado estritamente sobre anos completos presentes no treino (12 meses, excluindo anos parciais como 2024).
   - *5. 2020 × demais anos*: comparativo anual de admissões consolidadas, meses no treino, média mensal, coeficiente de variação mensal (CV), fração de declarações por arquivo FOR (FOR ÷ (MOV+FOR)) e declaradas após o mês da movimentação, para ambas as séries (principal e total).
   - *6. Defasagem de declaração (R02)*: fração acumulada das admissões brutas declaradas até 0, 1, 2, 3, 6 e 12 meses após a competência da movimentação e fração de exclusões (calculada a partir dos arquivos EXC sem cancelamento interno), para ambas as séries.
   - *7. Distribuição do alvo*: contagem, taxa de zeros, média, desvio e quantis (Q10, Q25, Mediana, Q75, Q90) por destino.
4. **`nivel_tendencia.png` e `sazonalidade.png`**: Gráficos gerados via matplotlib utilizando backend sem tela (`Agg`). `nivel_tendencia.png` apresenta dois subplots verticais (série principal e total) e `sazonalidade.png` apresenta a curva do índice sazonal por destino e o agregado.
5. **`baselines.json`**: Registro da avaliação dos baselines contendo parâmetros utilizados, sha256 do painel, metadados do escopo (`modo`, `destinos`, `hash_recorte`), métricas por fold (`n`, `mae`, `rmse`, `wape`, `macro_mae`, `mase` com escala sazonal de treino, `series_com_escala` e `series_sem_escala`), resumo agregado entre folds (`folds_validos`, médias e desvios padrão amostrais com $ddof=1$, retornando `None` quando não há folds válidos) e métricas da partição de validação (quando solicitada).
6. **`<saida_recorte>.parquet` e `<saida_recorte>.json`**: Parquet contendo os dados projetados exclusivamente nos 3 destinos do MVP R29 acompanhado de manifesto JSON contendo SHA-256 do arquivo de entrada e de saída, SHA-256 e hash determinístico do recorte, contagem de linhas por partição temporal (`historico_2020`, `treino_202101_202409`, `embargo_202410_202412`, `validacao_202501_202509`), carimbo UTC e versões dos componentes. Falha antecipadamente se o arquivo de destino já existir.

### 9.3 Limitações e Regras Congeladas

- **Recorte MVP R29**: Redução de escopo operacional restrita aos destinos `analista_dados_bi`, `analista_monitoramento_iot` e `analista_processos`. Os seis destinos canônicos originais continuam preservados na base e nas estatísticas (D11). A projeção não homologa rubricas e não altera a modelagem temporal.
- **Proteção do Holdout (D10)**: competências $\ge 202601$ são rejeitadas em memória. Isso **não é uma barreira de leitura**: o CLI lê o arquivo indicado antes de validar suas linhas. Use exclusivamente o painel de desenvolvimento segregado e previamente identificado; nunca passe Parquets de microdados ou do holdout. Não reconstrua o painel apontando para o diretório misto de microdados 2020–2026: o carregador legado também filtra depois da leitura.
- **Início do Treino 202101 (D10)**: A partição de treino cobre origens $202101 \le t \le 202409$; dados de 2020 são estritamente utilizados como histórico retrospectivo para o cálculo de lags e sazonais.
- **Isolamento de Partições**: A EDA e a seleção por densidade dentro dos folds utilizam exclusivamente dados de treino ($t \le 202409$). Registros de validação nunca vazam para a seleção de séries ou métricas in-sample.
- **Tratamento de UF 99**: Registros com UF não identificada ou inválida (fora dos 27 códigos IBGE) são descartados no carregamento e registrados com contagem exata por código no relatório, garantindo que o agregador receba apenas UFs válidas.
- **Comparação Justa de Baselines**: As métricas de persistência e sazonal são calculadas sobre o subconjunto idêntico de linhas em cada fold onde ambas as previsões e o alvo consolidado estão simultaneamente presentes.
- **Imunidade a Falsos Zeros**: Janelas temporais com histórico incompleto permanecem estritamente como `NaN` e não são convertidas em zero.
- **População nos manifestos**: sem `--escopo-mvp`, `catalogo_completo` só é usado quando os seis destinos canônicos estão presentes; subconjuntos são `catalogo_parcial`, com IDs efetivamente encontrados. Na chamada de biblioteca sem metadados, o escopo fica `nao_informado`, não inferido.
- **Proteção contra Sobrescrita**: recorte e relatório de baselines rejeitam arquivos de saída existentes, preservando evidências anteriores.


