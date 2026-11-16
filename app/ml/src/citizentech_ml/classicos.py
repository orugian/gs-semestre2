"""Módulo de modelagem clássica com Ridge, Random Forest e HistGradientBoosting.

Implementa treinamento com validação cruzada temporal (origem móvel com embargo)
e filtro de densidade por fold (D04a, D10, D10b, R29).
"""

from __future__ import annotations

import platform
import sys
import time
from typing import Any

import numpy as np
import pandas as pd
import threadpoolctl
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from citizentech_ml.baselines import avaliar_baselines, prever_baselines
from citizentech_ml.features.datas import validar_competencia
from citizentech_ml.features.densidade import (
    calcular_densidade_treino,
    obter_series_elegiveis,
)
from citizentech_ml.features.extracao import COLUNAS_FEATURES
from citizentech_ml.metricas import mae, mase, resumir_erros, rmse
from citizentech_ml.recorte import carregar_escopo_mvp, recortar_painel_mvp
from citizentech_ml.split import SplitOrigemMovel

COLUNAS_CATEGORICAS: list[str] = ["destino", "uf"]
COLUNAS_PREDITORES_NUMERICOS: list[str] = [
    c for c in COLUNAS_FEATURES if "_total" not in c and c != "mes"
]


class EstimadorClassicoElegivel(BaseEstimator, RegressorMixin):
    """Wrapper para estimadores clássicos que aplica o filtro de densidade D04a no fit."""

    def __init__(
        self,
        algoritmo: str = "ridge",
        limite_densidade: float = 10.0,
        seed: int = 42,
        # Parâmetros Ridge
        alpha: float = 1.0,
        # Parâmetros Random Forest
        n_estimators: int = 100,
        max_depth: int | None = None,
        min_samples_leaf: int = 1,
        n_jobs: int = 1,
        # Parâmetros HistGradientBoosting
        learning_rate: float = 0.1,
        max_leaf_nodes: int = 31,
        l2_regularization: float = 0.0,
    ) -> None:
        self.algoritmo = algoritmo
        self.limite_densidade = limite_densidade
        self.seed = seed
        self.alpha = alpha
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.n_jobs = n_jobs
        self.learning_rate = learning_rate
        self.max_leaf_nodes = max_leaf_nodes
        self.l2_regularization = l2_regularization

    def fit(self, X: pd.DataFrame, y: Any) -> EstimadorClassicoElegivel:
        """Ajusta o estimador calculando densidade exclusivamente nos dados fornecidos."""
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X deve ser um pandas DataFrame.")

        colunas_id = {"competencia", "destino", "uf"}
        if not colunas_id.issubset(X.columns):
            raise ValueError(f"X deve conter colunas de identificação: {sorted(colunas_id)}")

        competencias = X["competencia"].astype(str).map(validar_competencia)
        if (competencias >= "202601").any():
            raise ValueError("Fit de holdout 2026 proibido nesta fatia (D10).")

        y_serie = pd.Series(y, index=X.index, name="alvo")
        valores_y = y_serie.dropna().to_numpy(dtype=float)
        if len(valores_y) > 0:
            if not np.isfinite(valores_y).all() or (valores_y < 0).any():
                raise ValueError("Coluna de alvo contém valores negativos ou não finitos.")

        # 1. Calcular densidade exclusivamente no conjunto deste fit (D04a)
        df_treino_fit = X[["competencia", "destino", "uf"]].copy()
        df_treino_fit["alvo"] = y_serie

        rel_densidade = calcular_densidade_treino(
            df_treino_fit,
            limite_minimo=self.limite_densidade,
            coluna_alvo="alvo",
            coluna_tempo="competencia",
            limite_competencia_treino=None,
        )
        self.series_elegiveis_ = obter_series_elegiveis(rel_densidade)
        self.relatorio_densidade_ = rel_densidade
        self.series_excluidas_densidade_ = len(rel_densidade) - len(self.series_elegiveis_)

        # 2. Filtrar dados do fit para manter apenas séries elegíveis e alvos válidos
        pares = list(zip(X["destino"], X["uf"], strict=False))
        mascara_elegivel = np.array([p in self.series_elegiveis_ for p in pares], dtype=bool)
        y_vals = y_serie.to_numpy(dtype=float)
        mascara_valida = mascara_elegivel & pd.notna(y_vals) & np.isfinite(y_vals)

        X_elegivel = X.iloc[mascara_valida].copy()
        y_elegivel = y_vals[mascara_valida]

        if len(X_elegivel) == 0:
            raise ValueError(
                "Folds sem amostra válida para treino com "
                f"limite_densidade={self.limite_densidade}."
            )

        # 3. Identificar features numéricas disponíveis
        colunas_num = [c for c in COLUNAS_PREDITORES_NUMERICOS if c in X.columns]
        if "mes" in X.columns and "mes" not in colunas_num:
            colunas_num.append("mes")
        self.colunas_numericas_ = sorted(colunas_num)
        self.colunas_categoricas_ = list(COLUNAS_CATEGORICAS)

        # Registrar ausentes no conjunto de treino ajustado
        self.ausentes_treino_ = {
            col: int(X_elegivel[col].isna().sum()) for col in self.colunas_numericas_
        }

        # 4. Construção do pipeline de pré-processamento e estimador interno
        # Numéricas: mediana + indicador de ausente (+ StandardScaler para Ridge)
        passos_num: list[tuple[str, Any]] = [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True))
        ]
        if self.algoritmo == "ridge":
            passos_num.append(("scaler", StandardScaler()))

        pipeline_num = Pipeline(passos_num)
        pipeline_cat = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", pipeline_num, self.colunas_numericas_),
                ("cat", pipeline_cat, self.colunas_categoricas_),
            ]
        )

        n_jobs_rf = max(1, min(int(self.n_jobs), 6))

        if self.algoritmo == "ridge":
            reg = Ridge(alpha=float(self.alpha), random_state=int(self.seed))
        elif self.algoritmo == "random_forest":
            reg = RandomForestRegressor(
                n_estimators=int(self.n_estimators),
                max_depth=int(self.max_depth) if self.max_depth is not None else None,
                min_samples_leaf=int(self.min_samples_leaf),
                n_jobs=n_jobs_rf,
                random_state=int(self.seed),
            )
        elif self.algoritmo == "hist_gradient_boosting":
            reg = HistGradientBoostingRegressor(
                learning_rate=float(self.learning_rate),
                max_leaf_nodes=int(self.max_leaf_nodes),
                l2_regularization=float(self.l2_regularization),
                early_stopping=False,
                random_state=int(self.seed),
            )
        else:
            raise ValueError(f"Algoritmo desconhecido: {self.algoritmo!r}")

        self.pipeline_ = Pipeline([("preprocessor", preprocessor), ("regressor", reg)])

        with threadpoolctl.threadpool_limits(limits=6):
            self.pipeline_.fit(
                X_elegivel[self.colunas_numericas_ + self.colunas_categoricas_],
                y_elegivel,
            )

        # 5. Extração de nomes de features e importâncias/coeficientes
        transformer_ajustado = self.pipeline_.named_steps["preprocessor"]
        nomes_features = list(transformer_ajustado.get_feature_names_out())
        self.nomes_features_ = nomes_features

        reg_ajustado = self.pipeline_.named_steps["regressor"]
        if self.algoritmo == "ridge":
            self.coeficientes_ = dict(
                zip(nomes_features, [float(c) for c in reg_ajustado.coef_], strict=False)
            )
            self.importancias_ = {}
        elif self.algoritmo == "random_forest":
            self.importancias_ = dict(
                zip(
                    nomes_features,
                    [float(i) for i in reg_ajustado.feature_importances_],
                    strict=False,
                )
            )
            self.coeficientes_ = {}
        else:
            self.importancias_ = {}
            self.coeficientes_ = {}

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Produz previsões numéricas preservando valores brutos (inclusive negativos)."""
        if not hasattr(self, "pipeline_"):
            raise ValueError("O estimador ainda não foi ajustado (fit).")
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X deve ser um pandas DataFrame.")

        colunas_requeridas = self.colunas_numericas_ + self.colunas_categoricas_
        for col in colunas_requeridas:
            if col not in X.columns:
                raise ValueError(f"Coluna obrigatória '{col}' ausente em X.")

        with threadpoolctl.threadpool_limits(limits=6):
            y_pred = self.pipeline_.predict(X[colunas_requeridas])

        return np.asarray(y_pred, dtype=float)


def _obter_mascara_comum(
    df: pd.DataFrame,
    series_elegiveis: set[tuple[str, str]],
) -> np.ndarray:
    """Calcula a máscara justa comum entre baselines e modelos supervisionados.

    Critérios estritos e invariantes ao modelo:
    1. Série (destino, uf) elegível pelo critério de densidade no treino do fold (D04a);
    2. Alvo presente e finito;
    3. Referência de persistência (previsao_persistencia) presente e finita;
    4. Referência sazonal (previsao_sazonal) presente e finita.
    """
    pares = list(zip(df["destino"], df["uf"], strict=False))
    mascara_elegivel = np.array([p in series_elegiveis for p in pares], dtype=bool)

    y_arr = df["alvo"].to_numpy(dtype=float) if "alvo" in df.columns else np.full(len(df), np.nan)
    mascara_valida = mascara_elegivel & pd.notna(y_arr) & np.isfinite(y_arr)

    for col_b in ["previsao_persistencia", "previsao_sazonal"]:
        if col_b in df.columns:
            b_arr = df[col_b].to_numpy(dtype=float)
            mascara_valida = mascara_valida & pd.notna(b_arr) & np.isfinite(b_arr)
        else:
            mascara_valida = np.zeros(len(df), dtype=bool)

    return mascara_valida


def _criar_scorer_elegivel():
    """Cria scorer customizado para o RandomizedSearchCV com máscara justa e filtro D04a."""

    def scorer(estimator: EstimadorClassicoElegivel, X: pd.DataFrame, y: Any) -> float:
        elegiveis = getattr(estimator, "series_elegiveis_", None)
        if elegiveis is None:
            raise ValueError("Estimador sem series_elegiveis_ ajustadas.")

        df_eval_input = X.copy()
        df_eval_input["alvo"] = np.asarray(y, dtype=float)
        mascara_valida = _obter_mascara_comum(df_eval_input, elegiveis)

        if not np.any(mascara_valida):
            raise ValueError(
                "Fold sem amostra válida na validação após aplicação de filtros "
                "de elegibilidade e máscara justa."
            )

        X_val = X.iloc[mascara_valida] if isinstance(X, pd.DataFrame) else X[mascara_valida]
        y_val = df_eval_input.loc[mascara_valida, "alvo"].to_numpy(dtype=float)

        y_pred = estimator.predict(X_val)
        return -float(mae(y_val, y_pred))

    return scorer


class ResultadoTreinamentoClassicos:
    """Encapsula estimadores ajustados, previsões tabulares e relatório auditável."""

    def __init__(
        self,
        estimadores: dict[str, EstimadorClassicoElegivel],
        relatorio: dict[str, Any],
        previsoes: pd.DataFrame,
    ) -> None:
        self.estimadores = estimadores
        self.modelos = estimadores
        self.relatorio = relatorio
        self.previsoes = previsoes

    def __getitem__(self, item: str) -> Any:
        if item in ("estimadores", "modelos"):
            return self.estimadores
        if item == "relatorio":
            return self.relatorio
        if item == "previsoes":
            return self.previsoes
        raise KeyError(item)

    def __contains__(self, item: object) -> bool:
        return item in ("estimadores", "modelos", "relatorio", "previsoes")

    def keys(self) -> list[str]:
        return ["estimadores", "modelos", "relatorio", "previsoes"]


def _calcular_escalas_treino(
    df_treino: pd.DataFrame,
    series_elegiveis: set[tuple[str, str]],
) -> dict[tuple[str, str], float | None]:
    """Calcula a escala de erro ingênuo/sazonal no treino para cálculo do MASE."""
    mapa_escalas: dict[tuple[str, str], float | None] = {}
    col_saz = "previsao_sazonal"
    tem_saz = col_saz in df_treino.columns

    for s in series_elegiveis:
        if not tem_saz:
            mapa_escalas[s] = None
            continue
        df_s = df_treino[(df_treino["destino"] == s[0]) & (df_treino["uf"] == s[1])]
        val_tr = df_s[df_s["alvo"].notna() & df_s[col_saz].notna()]
        if len(val_tr) > 0:
            escala = mae(val_tr["alvo"], val_tr[col_saz])
            mapa_escalas[s] = escala if escala > 0.0 else None
        else:
            mapa_escalas[s] = None

    return mapa_escalas


def _avaliar_previsoes_conjunto(
    df_val_base: pd.DataFrame,
    y_pred: np.ndarray,
    mascara_valida: np.ndarray,
    mapa_escalas: dict[tuple[str, str], float | None],
) -> dict[str, Any]:
    """Calcula métricas detalhadas (MAE, RMSE, WAPE, MASE) com suporte a WAPE/MASE indefinidos."""
    if not np.any(mascara_valida):
        return {
            "n": 0,
            "mae": None,
            "rmse": None,
            "wape": None,
            "wape_motivo": "sem_amostras_validas",
            "macro_mae": None,
            "mase": None,
            "mase_motivo": "sem_amostras_validas",
            "series_com_escala": 0,
            "series_sem_escala": 0,
            "previsoes_negativas": 0,
            "tabela_series": [],
        }

    df_eval = df_val_base.iloc[mascara_valida].copy()
    y_arr = df_val_base["alvo"].to_numpy(dtype=float)
    y_eval = y_arr[mascara_valida]
    y_pred_eval = y_pred[mascara_valida]

    n_neg = int(np.sum(y_pred_eval < 0))
    val_mae = float(mae(y_eval, y_pred_eval))
    val_rmse = float(rmse(y_eval, y_pred_eval))

    # WAPE
    soma_real = float(np.sum(y_eval))
    if soma_real == 0.0:
        val_wape = None
        wape_motivo = "soma_real_zero"
    else:
        val_wape = float(np.sum(np.abs(y_eval - y_pred_eval))) / soma_real
        wape_motivo = None

    # Métricas por série
    df_eval["_y_pred"] = y_pred_eval
    resumo_base = resumir_erros(
        df_eval,
        col_real="alvo",
        col_prev="_y_pred",
        chaves_serie=["destino", "uf"],
    )

    mases_validos: list[float] = []
    for reg in resumo_base["tabela_series"]:
        s_chave = (str(reg["destino"]), str(reg["uf"]))
        esc = mapa_escalas.get(s_chave)
        val_mase_s = mase([reg["mae"]], [0.0], esc) if esc is not None else None
        reg["mase"] = val_mase_s
        if val_mase_s is not None:
            mases_validos.append(val_mase_s)

    if mases_validos:
        mase_agregado = float(np.mean(mases_validos))
        mase_motivo = None
    else:
        mase_agregado = None
        mase_motivo = "escala_invalida_ou_zero"

    return {
        "n": len(df_eval),
        "mae": val_mae,
        "rmse": val_rmse,
        "wape": val_wape,
        "wape_motivo": wape_motivo,
        "macro_mae": resumo_base["macro_mae"],
        "mase": mase_agregado,
        "mase_motivo": mase_motivo,
        "series_com_escala": len(mases_validos),
        "series_sem_escala": len(resumo_base["tabela_series"]) - len(mases_validos),
        "previsoes_negativas": n_neg,
        "tabela_series": resumo_base["tabela_series"],
    }


def treinar_classicos(
    painel: pd.DataFrame,
    seed: int = 42,
    n_iter: int = 6,
    incluir_validacao: bool = False,
    n_splits: int = 3,
    limite_densidade: float = 10.0,
) -> ResultadoTreinamentoClassicos:
    """Treina e avalia Ridge, RandomForest e HistGradientBoosting via CV temporal (D10 / D04a).

    Parâmetros:
    -----------
    painel: pd.DataFrame
        Painel de desenvolvimento contendo colunas de identificadores, features e alvo.
    seed: int
        Semente fixa para reproduzibilidade (default 42).
    n_iter: int
        Número de iterações para o RandomizedSearchCV (default 6, limitado pelas combinações).
    incluir_validacao: bool
        Se True, avalia na partição externa de validação 202501-202509. NUNCA 2026.
    n_splits: int
        Número de folds para o SplitOrigemMovel (default 3).
    limite_densidade: float
        Média mínima de admissões no treino do fold para elegibilidade (D04a, default 10.0).
    """
    inicio_tempo_global = time.perf_counter()

    if not isinstance(painel, pd.DataFrame):
        raise TypeError("O painel de entrada deve ser um pandas DataFrame.")

    if painel.empty:
        raise ValueError("Operação rejeitada: painel vazio.")

    # 1. Proteção estrita do holdout: rejeitar qualquer competência >= 202601 (D10)
    comps = painel["competencia"].dropna().astype(str).unique()
    for c in comps:
        c_val = validar_competencia(c)
        if c_val >= "202601":
            raise ValueError(
                f"Competência de teste '{c}' detectada no painel. O holdout 2026 "
                f"é estritamente congelado (D10) e não pode ser aberto."
            )

    # 2. Referências determinísticas dos baselines (R29 / interface pública)
    if (
        "admissoes_soma_3m" not in painel.columns
        or "admissoes_sazonal_ano_anterior" not in painel.columns
    ):
        raise ValueError(
            "Entrada sem referências fonte suficientes: colunas 'admissoes_soma_3m' "
            "e 'admissoes_sazonal_ano_anterior' são obrigatórias para geração determinística "
            "dos baselines e máscara comum."
        )

    # Recorte MVP R29 com metadados determinísticos
    escopo_mvp = carregar_escopo_mvp()
    painel_mvp = recortar_painel_mvp(painel.copy(), escopo=escopo_mvp)

    # Gerar as duas referências determinísticas a partir de admissoes_soma_3m
    # e admissoes_sazonal_ano_anterior via interface pública prever_baselines
    painel_mvp = prever_baselines(painel_mvp)

    # Avaliação determinística dos dois baselines sob o mesmo split e densidade
    rel_baselines = avaliar_baselines(
        painel=painel_mvp,
        inicio_treino="202101",
        incluir_validacao=incluir_validacao,
        n_splits=n_splits,
        limite_densidade=limite_densidade,
    )

    # 3. Particionamento estrito D10: treino entre 202101 e 202409 (2020 não entra no fit)
    comp_serie = painel_mvp["competencia"].astype(str)
    mascara_treino = (comp_serie >= "202101") & (comp_serie <= "202409")
    df_treino = painel_mvp[mascara_treino].copy()

    if df_treino.empty:
        raise ValueError("Nenhum dado encontrado para treino no intervalo 202101-202409.")

    # Validar alvo no treino
    if "alvo" not in df_treino.columns:
        raise ValueError("Coluna obrigatória 'alvo' ausente no painel.")

    valores_alvo = df_treino["alvo"].dropna().to_numpy(dtype=float)
    if len(valores_alvo) > 0 and (not np.isfinite(valores_alvo).all() or (valores_alvo < 0).any()):
        raise ValueError("Coluna 'alvo' contém valores não finitos ou negativos no treino.")

    # Partição de validação externa (somente se incluir_validacao=True)
    df_val_externa: pd.DataFrame | None = None
    if incluir_validacao:
        mascara_val = (comp_serie >= "202501") & (comp_serie <= "202509")
        df_val_externa = painel_mvp[mascara_val].copy()
        if not df_val_externa.empty and "alvo" in df_val_externa.columns:
            valores_alvo_val = df_val_externa["alvo"].dropna().to_numpy(dtype=float)
            if len(valores_alvo_val) > 0 and (
                not np.isfinite(valores_alvo_val).all() or (valores_alvo_val < 0).any()
            ):
                raise ValueError(
                    "Coluna 'alvo' contém valores não finitos ou negativos "
                    "na partição de validação (2025)."
                )

    # 4. Configuração dos grids de hiperparâmetros congelados
    grids: dict[str, dict[str, list[Any]]] = {
        "ridge": {
            "alpha": [0.1, 1.0, 10.0, 100.0],
        },
        "random_forest": {
            "n_estimators": [100, 200],
            "max_depth": [6, 12, None],
            "min_samples_leaf": [1, 3, 5],
        },
        "hist_gradient_boosting": {
            "learning_rate": [0.03, 0.1],
            "max_leaf_nodes": [15, 31],
            "l2_regularization": [0.0, 1.0],
        },
    }

    # 5. Splitter temporal com embargo
    splitter = SplitOrigemMovel(
        n_splits=n_splits,
        tamanho_validacao_meses=3,
        meses_embargo=3,
        tamanho_minimo_treino_meses=12,
        coluna_tempo="competencia",
        limite_treino_maximo="202409",
    )
    scorer = _criar_scorer_elegivel()

    modelos_finais: dict[str, EstimadorClassicoElegivel] = {}
    cv_detalhes: dict[str, Any] = {}
    tempos_modelos: dict[str, float] = {}

    # Executar RandomizedSearchCV para cada um dos 3 modelos
    for nome_algoritmo, grid in grids.items():
        t0 = time.perf_counter()
        estimador_base = EstimadorClassicoElegivel(
            algoritmo=nome_algoritmo,
            limite_densidade=limite_densidade,
            seed=seed,
            n_jobs=6 if nome_algoritmo == "random_forest" else 1,
        )

        total_combinacoes = 1
        for valores in grid.values():
            total_combinacoes *= len(valores)

        n_iter_efetivo = min(n_iter, total_combinacoes)

        search = RandomizedSearchCV(
            estimator=estimador_base,
            param_distributions=grid,
            n_iter=n_iter_efetivo,
            cv=splitter,
            scoring=scorer,
            random_state=seed,
            n_jobs=1,
            refit=True,
            error_score="raise",
        )

        with threadpoolctl.threadpool_limits(limits=6):
            search.fit(df_treino, df_treino["alvo"])

        t1 = time.perf_counter()
        tempos_modelos[nome_algoritmo] = round(t1 - t0, 4)
        modelos_finais[nome_algoritmo] = search.best_estimator_
        cv_detalhes[nome_algoritmo] = {
            "melhores_parametros": search.best_params_,
            "melhor_score_mae_negativo": float(search.best_score_),
            "cv_resultados": {
                "params": search.cv_results_["params"],
                "mean_test_score": [float(s) for s in search.cv_results_["mean_test_score"]],
                "std_test_score": [float(s) for s in search.cv_results_["std_test_score"]],
            },
        }

    # 6. Avaliação detalhada dos folds de CV com cálculo de escala MASE e OOF predictions
    folds_info: list[dict[str, Any]] = []
    linhas_previsoes_cv: list[dict[str, Any]] = []

    for fold_idx, (idx_tr, idx_vl) in enumerate(splitter.split(df_treino)):
        f_tr = df_treino.iloc[idx_tr].copy()
        f_vl = df_treino.iloc[idx_vl].copy()

        rel_dens_fold = calcular_densidade_treino(
            f_tr,
            limite_minimo=limite_densidade,
            coluna_alvo="alvo",
            coluna_tempo="competencia",
            limite_competencia_treino=None,
        )
        series_eleg_fold = obter_series_elegiveis(rel_dens_fold)
        mapa_escalas_fold = _calcular_escalas_treino(f_tr, series_eleg_fold)
        mascara_val_fold = _obter_mascara_comum(f_vl, series_eleg_fold)

        info_fold: dict[str, Any] = {
            "fold": fold_idx,
            "meses_treino": sorted(f_tr["competencia"].unique()),
            "meses_validacao": sorted(f_vl["competencia"].unique()),
            "meses_embargo": 3,
            "series_elegiveis": len(series_eleg_fold),
            "series_excluidas_densidade": len(rel_dens_fold) - len(series_eleg_fold),
            "baselines": (
                rel_baselines["folds"][fold_idx]["baselines"]
                if fold_idx < len(rel_baselines.get("folds", []))
                else {}
            ),
            "modelos": {},
        }

        # Ajustar e avaliar modelo para este fold
        for nome_algoritmo, est_final in modelos_finais.items():
            est_fold = clone(est_final)
            est_fold.fit(f_tr, f_tr["alvo"])

            # Predizer em toda a janela de validação do fold
            y_pred_fold = est_fold.predict(f_vl)

            # Métricas no conjunto elegível e justo (usando a máscara comum invariante ao modelo)
            metricas_fold = _avaliar_previsoes_conjunto(
                f_vl,
                y_pred_fold,
                mascara_val_fold,
                mapa_escalas_fold,
            )
            info_fold["modelos"][nome_algoritmo] = metricas_fold

            # Coletar previsões chaveadas para a tabela aplicando a exata mesma máscara comum
            if np.any(mascara_val_fold):
                df_eval_fold = f_vl.iloc[mascara_val_fold]
                y_pred_fold_eval = y_pred_fold[mascara_val_fold]
                for (_, row), prev in zip(df_eval_fold.iterrows(), y_pred_fold_eval, strict=True):
                    linhas_previsoes_cv.append(
                        {
                            "competencia": str(row["competencia"]),
                            "destino": str(row["destino"]),
                            "uf": str(row["uf"]),
                            "modelo": nome_algoritmo,
                            "alvo": float(row["alvo"]),
                            "previsao": float(prev),
                            "particao": f"cv_fold_{fold_idx}",
                        }
                    )

        folds_info.append(info_fold)

    # 7. Resumo consolidado de métricas por modelo através dos folds
    resumo_cv_modelos: dict[str, Any] = {}
    for nome_algoritmo in modelos_finais:
        maes = [
            f["modelos"][nome_algoritmo]["mae"]
            for f in folds_info
            if f["modelos"][nome_algoritmo]["mae"] is not None
        ]
        rmses = [
            f["modelos"][nome_algoritmo]["rmse"]
            for f in folds_info
            if f["modelos"][nome_algoritmo]["rmse"] is not None
        ]
        wapes = [
            f["modelos"][nome_algoritmo]["wape"]
            for f in folds_info
            if f["modelos"][nome_algoritmo]["wape"] is not None
        ]
        mases = [
            f["modelos"][nome_algoritmo]["mase"]
            for f in folds_info
            if f["modelos"][nome_algoritmo]["mase"] is not None
        ]

        resumo_cv_modelos[nome_algoritmo] = {
            "mae_media": float(np.mean(maes)) if maes else None,
            "mae_desvio": float(np.std(maes, ddof=1)) if len(maes) > 1 else None,
            "rmse_media": float(np.mean(rmses)) if rmses else None,
            "rmse_desvio": float(np.std(rmses, ddof=1)) if len(rmses) > 1 else None,
            "wape_media": float(np.mean(wapes)) if wapes else None,
            "wape_desvio": float(np.std(wapes, ddof=1)) if len(wapes) > 1 else None,
            "mase_media": float(np.mean(mases)) if mases else None,
            "mase_desvio": float(np.std(mases, ddof=1)) if len(mases) > 1 else None,
        }

    # 8. Diagnóstico de ajuste (Fit no Treino Completo vs Generalização CV)
    series_elegiveis_global = modelos_finais["ridge"].series_elegiveis_
    mapa_escalas_global = _calcular_escalas_treino(df_treino, series_elegiveis_global)
    mascara_tr = _obter_mascara_comum(df_treino, series_elegiveis_global)

    diagnostico_fit: dict[str, Any] = {}
    for nome_algoritmo, est_final in modelos_finais.items():
        y_pred_tr = est_final.predict(df_treino)
        eval_tr = _avaliar_previsoes_conjunto(
            df_treino,
            y_pred_tr,
            mascara_tr,
            mapa_escalas_global,
        )
        mae_cv = resumo_cv_modelos[nome_algoritmo]["mae_media"]
        mae_tr = eval_tr["mae"]
        gap = (mae_cv - mae_tr) if (mae_cv is not None and mae_tr is not None) else None
        razao = (
            float(mae_cv / mae_tr)
            if (mae_cv is not None and mae_tr is not None and mae_tr > 0.0)
            else None
        )

        diagnostico_fit[nome_algoritmo] = {
            "mae_treino": mae_tr,
            "rmse_treino": eval_tr["rmse"],
            "wape_treino": eval_tr["wape"],
            "mase_treino": eval_tr["mase"],
            "mae_cv_media": mae_cv,
            "gap_overfit_mae": gap,
            "razao_cv_treino_mae": razao,
            "diagnostico": "descritivo",
            "aviso": (
                "Diagnóstico puramente descritivo de generalização temporal (fit no treino vs CV). "
                "Não há limiar universal pré-registrado para rotular adequação; "
                "sem veredito automático de over/underfitting nem alteração de promoção "
                "(D10a congelado)."
            ),
        }

    # 9. Avaliação Externa de Validação (202501-202509) - somente com incluir_validacao=True
    validacao_externa_dict: dict[str, Any] | None = None
    linhas_previsoes_val: list[dict[str, Any]] = []

    if incluir_validacao and df_val_externa is not None and not df_val_externa.empty:
        validacao_externa_dict = {
            "periodo": ["202501", "202509"],
            "series_elegiveis": len(series_elegiveis_global),
            "baselines": (
                rel_baselines["validacao"]["baselines"] if rel_baselines.get("validacao") else {}
            ),
            "modelos": {},
        }
        mascara_val_externa = _obter_mascara_comum(df_val_externa, series_elegiveis_global)

        for nome_algoritmo, est_final in modelos_finais.items():
            y_pred_val = est_final.predict(df_val_externa)
            eval_val = _avaliar_previsoes_conjunto(
                df_val_externa,
                y_pred_val,
                mascara_val_externa,
                mapa_escalas_global,
            )
            validacao_externa_dict["modelos"][nome_algoritmo] = eval_val

            if np.any(mascara_val_externa):
                df_eval_val = df_val_externa.iloc[mascara_val_externa]
                y_pred_val_eval = y_pred_val[mascara_val_externa]
                for (_, row), prev in zip(df_eval_val.iterrows(), y_pred_val_eval, strict=True):
                    linhas_previsoes_val.append(
                        {
                            "competencia": str(row["competencia"]),
                            "destino": str(row["destino"]),
                            "uf": str(row["uf"]),
                            "modelo": nome_algoritmo,
                            "alvo": float(row["alvo"]),
                            "previsao": float(prev),
                            "particao": "validacao",
                        }
                    )

    # 10. Tabela final de previsões
    todas_linhas = linhas_previsoes_cv + linhas_previsoes_val
    df_previsoes = pd.DataFrame(
        todas_linhas,
        columns=["competencia", "destino", "uf", "modelo", "alvo", "previsao", "particao"],
    )

    # 11. Relatório auditável estruturado
    colunas_num_usadas = modelos_finais["ridge"].colunas_numericas_
    ausentes_treino = modelos_finais["ridge"].ausentes_treino_
    tempo_total = round(time.perf_counter() - inicio_tempo_global, 4)

    contagem_negativas = {
        m: int((df_previsoes[df_previsoes["modelo"] == m]["previsao"] < 0).sum())
        for m in modelos_finais
    }

    relatorio: dict[str, Any] = {
        "recorte": {
            "decisao": "R29",
            "versao": escopo_mvp.get("versao", "1.0"),
            "destinos": sorted(painel_mvp["destino"].unique()),
            "ufs": sorted(painel_mvp["uf"].unique()),
            "hash_recorte": escopo_mvp["hash_recorte"],
            "sha256_escopo": escopo_mvp["sha256_escopo"],
            "status_rubricas": escopo_mvp.get("status_rubricas", "revisao_humana_pendente"),
        },
        "baselines": {
            "persistencia": {
                "cv_resumo": rel_baselines["resumo_folds"]["persistencia"],
                "folds": [f["baselines"]["persistencia"] for f in rel_baselines["folds"]],
                "validacao_externa": (
                    rel_baselines["validacao"]["baselines"]["persistencia"]
                    if rel_baselines.get("validacao")
                    else None
                ),
            },
            "sazonal": {
                "cv_resumo": rel_baselines["resumo_folds"]["sazonal"],
                "folds": [f["baselines"]["sazonal"] for f in rel_baselines["folds"]],
                "validacao_externa": (
                    rel_baselines["validacao"]["baselines"]["sazonal"]
                    if rel_baselines.get("validacao")
                    else None
                ),
            },
            "folds": rel_baselines["folds"],
            "resumo_folds": rel_baselines["resumo_folds"],
            "validacao": rel_baselines.get("validacao"),
        },
        "populacao": "superior+ (Caged movimentações nível superior ou pós)",
        "features": {
            "preditores_numericos": colunas_num_usadas,
            "preditores_categoricos": COLUNAS_CATEGORICAS,
            "identificadores": ["competencia", "destino", "uf"],
            "alvo": "alvo",
        },
        "ambiente": {
            "seed": seed,
            "n_jobs_max": 6,
            "python_versao": sys.version,
            "plataforma": platform.platform(),
        },
        "periodo_treino": {
            "inicio": str(df_treino["competencia"].min()),
            "fim": str(df_treino["competencia"].max()),
        },
        "densidade": {
            "limite_minimo_admissoes": limite_densidade,
            "series_elegiveis_treino_global": len(series_elegiveis_global),
            "series_excluidas_treino_global": (
                len(modelos_finais["ridge"].relatorio_densidade_) - len(series_elegiveis_global)
            ),
        },
        "hiperparametros_e_cv": cv_detalhes,
        "folds": folds_info,
        "resumo_cv": resumo_cv_modelos,
        "cv_aninhada": False,
        "diagnostico_fit": diagnostico_fit,
        "validacao_externa": validacao_externa_dict,
        "ausentes_treino": ausentes_treino,
        "exclusoes_e_avisos": {
            "previsoes_negativas": contagem_negativas,
            "alvos_fora_treino": int(df_treino["alvo"].isna().sum()),
        },
        "tempo_execucao_segundos": {
            "modelos": tempos_modelos,
            "total": tempo_total,
        },
        "coeficientes_ridge": modelos_finais["ridge"].coeficientes_,
        "importancias_rf": modelos_finais["random_forest"].importancias_,
        "limites": [
            "Modelos treinados exclusivamente com origens 202101-202409 (D10).",
            (
                "CV nao-aninhada: hiperparametros selecionados nos mesmos folds reportados; "
                "metricas sujeitas a vies otimista de selecao, nao uma estimativa independente "
                "de generalizacao. Validacao externa separada somente quando explicitada."
            ),
            (
                "Previsões negativas preservadas brutas para métricas; "
                "política de clipagem pertence ao serving."
            ),
            (
                "Proteção em memória valida ausência de competências >= 202601 "
                "(não constitui barreira de I/O em disco); o isolamento do holdout de teste "
                "2026 depende do fornecimento segregado do painel DEV pelo orquestrador. "
                "Nenhum dado >= 202601 é processado."
            ),
            "Não promove modelos automaticamente (D10a congelado).",
            (
                "Loader de artefatos verifica integridade via SHA-256 apenas para artefatos "
                "próprios em diretório confiável; não confere autenticidade criptográfica nem "
                "imunidade a execução de código arbitrário via pickle/joblib."
            ),
        ],
    }

    return ResultadoTreinamentoClassicos(
        estimadores=modelos_finais,
        relatorio=relatorio,
        previsoes=df_previsoes,
    )
