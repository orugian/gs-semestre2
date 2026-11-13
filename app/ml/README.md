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

