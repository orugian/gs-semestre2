"""Módulo de redes neurais (MLP PyTorch CPU) para previsão trimestral de admissões."""

from __future__ import annotations

import copy
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from citizentech_ml.baselines import avaliar_baselines, prever_baselines
from citizentech_ml.features.datas import validar_competencia
from citizentech_ml.features.densidade import (
    calcular_densidade_treino,
    filtrar_series_elegiveis,
    obter_series_elegiveis,
)
from citizentech_ml.features.extracao import COLUNAS_FEATURES
from citizentech_ml.metricas import mae, mase, resumir_erros
from citizentech_ml.recorte import carregar_escopo_mvp, recortar_painel_mvp
from citizentech_ml.split import SplitOrigemMovel

# Colunas numéricas principais: COLUNAS_FEATURES sem nenhuma coluna *_total
COLUNAS_NUMERICAS_PADRAO: list[str] = [col for col in COLUNAS_FEATURES if "_total" not in col]

CONFIG_A: dict[str, Any] = {
    "nome": "A",
    "hidden_layers": [64, 32],
    "dropout": 0.1,
    "lr": 0.001,
    "batch_size": 128,
}

CONFIG_B: dict[str, Any] = {
    "nome": "B",
    "hidden_layers": [128, 64],
    "dropout": 0.2,
    "lr": 0.0005,
    "batch_size": 128,
}

CONFIGS_PADRAO: dict[str, dict[str, Any]] = {
    "A": CONFIG_A,
    "B": CONFIG_B,
}


def fixar_seed(seed: int = 42) -> None:
    """Fixa as sementes aleatórias para determinismo em CPU e limita threads."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # Limitar threads em CPU para no máximo 6
    num_threads = min(6, torch.get_num_threads())
    if num_threads > 0:
        torch.set_num_threads(num_threads)


class MLPRegressor(nn.Module):
    """Rede Neural MLP em PyTorch CPU com ReLU, Dropout e saída linear."""

    def __init__(
        self,
        input_dim: int,
        hidden_layers: list[int] | None = None,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_layers = hidden_layers or [64, 32]
        self.dropout = dropout

        layers: list[nn.Module] = []
        in_dim = input_dim
        for h_dim in self.hidden_layers:
            layers.append(nn.Linear(in_dim, h_dim))
            layers.append(nn.ReLU())
            if dropout > 0.0:
                layers.append(nn.Dropout(dropout))
            in_dim = h_dim
        layers.append(nn.Linear(in_dim, 1))
        self.rede = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.rede(x)


class PreprocessadorRNA:
    """Preprocessador tabular estrito com OneHotEncoder, imputação por mediana e StandardScaler.

    Ajustado estritamente no conjunto de fit interno (sem vazamento para validação/teste).
    Serializável em JSON puro sem dependência de pickle arbitrário.
    """

    def __init__(self, colunas_numericas: list[str] | None = None) -> None:
        self.colunas_categoricas: list[str] = ["destino", "uf"]
        self.categorias_map: dict[str, list[str]] = {}
        self.colunas_numericas_candidatas: list[str] = colunas_numericas or COLUNAS_NUMERICAS_PADRAO
        self.colunas_numericas_efetivas: list[str] = []
        self.medianas: dict[str, float] = {}
        self.scaler_x_mean: list[float] = []
        self.scaler_x_scale: list[float] = []
        self.alvo_mean: float = 0.0
        self.alvo_std: float = 1.0
        self.dimensao_entrada: int = 0
        self.ajustado: bool = False

    def fit(self, df: pd.DataFrame, coluna_alvo: str = "alvo") -> PreprocessadorRNA:
        """Ajusta codificação, medianas e scalers exclusivamente nos dados fornecidos."""
        if df.empty:
            raise ValueError("Não é possível ajustar o pré-processador em um DataFrame vazio.")

        # 1. Categorias One-Hot
        self.categorias_map = {}
        for col in self.colunas_categoricas:
            if col in df.columns:
                cats = sorted(df[col].dropna().astype(str).unique().tolist())
                self.categorias_map[col] = cats
            else:
                self.categorias_map[col] = []

        # 2. Features numéricas presentes no DataFrame
        self.colunas_numericas_efetivas = [
            c for c in self.colunas_numericas_candidatas if c in df.columns
        ]

        # 3. Medianas para imputação
        self.medianas = {}
        imputados_list = []
        indicadores_list = []

        for col in self.colunas_numericas_efetivas:
            serie = pd.to_numeric(df[col], errors="coerce")
            med = float(serie.median()) if serie.notna().any() else 0.0
            if np.isnan(med):
                med = 0.0
            self.medianas[col] = med

            # Vetor imputado e indicador de ausente
            imputado = serie.fillna(med).to_numpy(dtype=np.float32)
            indicador = serie.isna().to_numpy(dtype=np.float32)
            imputados_list.append(imputado)
            indicadores_list.append(indicador)

        # 4. StandardScaler de X (numéricas imputadas + indicadores)
        if imputados_list:
            X_num = np.column_stack(imputados_list + indicadores_list)
            means = np.mean(X_num, axis=0)
            stds = np.std(X_num, axis=0)
            stds[stds < 1e-8] = 1.0
            self.scaler_x_mean = [float(m) for m in means]
            self.scaler_x_scale = [float(s) for s in stds]
        else:
            self.scaler_x_mean = []
            self.scaler_x_scale = []

        # 5. Dimensão final de entrada
        dim_cat = sum(len(cats) for cats in self.categorias_map.values())
        dim_num = len(self.scaler_x_mean)
        self.dimensao_entrada = dim_cat + dim_num

        # 6. StandardScaler de y
        if coluna_alvo in df.columns:
            y_serie = pd.to_numeric(df[coluna_alvo], errors="coerce").dropna()
            y_vals = y_serie.to_numpy(dtype=np.float32)
            if len(y_vals) > 0:
                y_mean = float(np.mean(y_vals))
                y_std = float(np.std(y_vals))
                if y_std < 1e-8:
                    y_std = 1.0
                self.alvo_mean = y_mean
                self.alvo_std = y_std
            else:
                self.alvo_mean = 0.0
                self.alvo_std = 1.0
        else:
            self.alvo_mean = 0.0
            self.alvo_std = 1.0

        self.ajustado = True
        return self

    def transform_x(self, df: pd.DataFrame) -> torch.Tensor:
        """Transforma features tabulares em tensor PyTorch CPU float32."""
        if not self.ajustado:
            raise RuntimeError("Pré-processador não ajustado. Chame fit() antes de transform_x().")

        blocos = []

        # One-hot das colunas categóricas
        for col in self.colunas_categoricas:
            cats = self.categorias_map.get(col, [])
            if not cats:
                continue
            if col in df.columns:
                serie_str = df[col].astype(str)
                # Cria matriz binária
                mat = np.zeros((len(df), len(cats)), dtype=np.float32)
                for cat_idx, cat_val in enumerate(cats):
                    mat[:, cat_idx] = (serie_str == cat_val).to_numpy(dtype=np.float32)
                blocos.append(mat)
            else:
                blocos.append(np.zeros((len(df), len(cats)), dtype=np.float32))

        # Features numéricas com imputação e indicadores
        if self.colunas_numericas_efetivas:
            imputados_list = []
            indicadores_list = []
            for col in self.colunas_numericas_efetivas:
                med = self.medianas.get(col, 0.0)
                if col in df.columns:
                    serie = pd.to_numeric(df[col], errors="coerce")
                    imputado = serie.fillna(med).to_numpy(dtype=np.float32)
                    indicador = serie.isna().to_numpy(dtype=np.float32)
                else:
                    imputado = np.full(len(df), med, dtype=np.float32)
                    indicador = np.ones(len(df), dtype=np.float32)
                imputados_list.append(imputado)
                indicadores_list.append(indicador)

            X_num = np.column_stack(imputados_list + indicadores_list)
            means = np.array(self.scaler_x_mean, dtype=np.float32)
            stds = np.array(self.scaler_x_scale, dtype=np.float32)
            X_num_scaled = (X_num - means) / stds
            blocos.append(X_num_scaled)

        if not blocos:
            matriz_final = np.empty((len(df), 0), dtype=np.float32)
        else:
            matriz_final = np.column_stack(blocos)

        return torch.from_numpy(matriz_final).to(torch.float32)

    def transform_y(self, y: pd.Series | list[float] | np.ndarray) -> torch.Tensor:
        """Padroniza valores do alvo usando a média e desvio do fit."""
        arr = np.asarray(y, dtype=np.float32).ravel()
        scaled = (arr - self.alvo_mean) / self.alvo_std
        return torch.from_numpy(scaled).unsqueeze(1).to(torch.float32)

    def inverse_transform_y(self, y_tensor: torch.Tensor | np.ndarray) -> np.ndarray:
        """Restaura valores do alvo na escala original."""
        if isinstance(y_tensor, torch.Tensor):
            arr = y_tensor.detach().cpu().numpy().ravel()
        else:
            arr = np.asarray(y_tensor, dtype=np.float32).ravel()
        return arr * self.alvo_std + self.alvo_mean

    def to_dict(self) -> dict[str, Any]:
        """Exporta estado completo do pré-processador para dicionário/JSON."""
        return {
            "colunas_categoricas": self.colunas_categoricas,
            "categorias_map": self.categorias_map,
            "colunas_numericas_efetivas": self.colunas_numericas_efetivas,
            "medianas": self.medianas,
            "scaler_x_mean": self.scaler_x_mean,
            "scaler_x_scale": self.scaler_x_scale,
            "alvo_mean": self.alvo_mean,
            "alvo_std": self.alvo_std,
            "dimensao_entrada": self.dimensao_entrada,
            "ajustado": self.ajustado,
        }

    @classmethod
    def from_dict(cls, dados: dict[str, Any]) -> PreprocessadorRNA:
        """Reconstrói pré-processador a partir de dicionário validado."""
        prep = cls()
        prep.colunas_categoricas = list(dados["colunas_categoricas"])
        prep.categorias_map = {k: list(v) for k, v in dados["categorias_map"].items()}
        prep.colunas_numericas_efetivas = list(dados["colunas_numericas_efetivas"])
        prep.medianas = {k: float(v) for k, v in dados["medianas"].items()}
        prep.scaler_x_mean = [float(v) for v in dados["scaler_x_mean"]]
        prep.scaler_x_scale = [float(v) for v in dados["scaler_x_scale"]]
        prep.alvo_mean = float(dados["alvo_mean"])
        prep.alvo_std = float(dados["alvo_std"])
        prep.dimensao_entrada = int(dados["dimensao_entrada"])
        prep.ajustado = bool(dados["ajustado"])
        return prep


def _particionar_treino_interno_fold(
    df_tr: pd.DataFrame,
    coluna_tempo: str = "competencia",
    meses_earlystop: int = 3,
    meses_embargo: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    """Particiona o conjunto de treino do fold em fit interno, embargo e earlystop.

    Garante:
    - 3 últimas origens: janela de early stopping interno
    - 3 origens imediatamente anteriores: embargo interno
    - Origens precedentes: subset de fit
    """
    meses_unicos = sorted(df_tr[coluna_tempo].astype(str).unique())
    total_meses = len(meses_unicos)

    if total_meses < (meses_earlystop + meses_embargo + 1):
        # Em fixtures muito reduzidas, ajusta partições mínimas mantendo fit > 0
        n_es = max(1, min(meses_earlystop, total_meses // 3))
        n_emb = max(1, min(meses_embargo, (total_meses - n_es) // 2))
    else:
        n_es = meses_earlystop
        n_emb = meses_embargo

    meses_es = meses_unicos[-n_es:]
    meses_emb = meses_unicos[-(n_es + n_emb) : -n_es]
    meses_fit = meses_unicos[: -(n_es + n_emb)]

    if not meses_fit:
        raise ValueError(
            f"Meses insuficientes no treino do fold ({total_meses} meses) para comportar "
            f"fit, embargo ({n_emb}) e earlystop ({n_es})."
        )

    df_fit = df_tr[df_tr[coluna_tempo].isin(meses_fit)].copy()
    df_es = df_tr[df_tr[coluna_tempo].isin(meses_es)].copy()

    intervalos = {
        "meses_fit": meses_fit,
        "meses_embargo": meses_emb,
        "meses_earlystop": meses_es,
    }

    return df_fit, df_es, intervalos


def _treinar_modelo_com_earlystopping(
    model: MLPRegressor,
    prep: PreprocessadorRNA,
    df_fit: pd.DataFrame,
    df_es: pd.DataFrame,
    lr: float,
    batch_size: int,
    max_epochs: int,
    patience: int,
    min_delta: float,
    seed: int,
    coluna_alvo: str = "alvo",
) -> tuple[MLPRegressor, list[dict[str, Any]], int, int]:
    """Loop de treino com Adam, MSELoss e salvamento do melhor checkpoint."""
    fixar_seed(seed)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # Prepara tensores de fit (onde alvo não é nulo)
    mascara_fit_valida = df_fit[coluna_alvo].notna()
    df_fit_valido = df_fit[mascara_fit_valida]

    X_fit = prep.transform_x(df_fit_valido)
    y_fit = prep.transform_y(df_fit_valido[coluna_alvo])

    # Prepara tensores de earlystop
    mascara_es_valida = df_es[coluna_alvo].notna()
    df_es_valido = df_es[mascara_es_valida]
    tem_es = len(df_es_valido) > 0
    if tem_es:
        X_es = prep.transform_x(df_es_valido)
        y_es = prep.transform_y(df_es_valido[coluna_alvo])

    n_samples = len(X_fit)
    if n_samples == 0:
        raise ValueError("Conjunto de fit não possui amostras válidas com alvo preenchido.")

    best_loss = float("inf")
    best_epoch = 1
    best_state: dict[str, Any] = copy.deepcopy(model.state_dict())
    patience_counter = 0
    historico: list[dict[str, Any]] = []

    for epoca in range(1, max_epochs + 1):
        model.train()
        # Permutação determinística para minibatches
        perm = torch.randperm(n_samples)
        for i in range(0, n_samples, batch_size):
            batch_indices = perm[i : i + batch_size]
            b_x = X_fit[batch_indices]
            b_y = y_fit[batch_indices]

            optimizer.zero_grad()
            out = model(b_x)
            loss = criterion(out, b_y)
            loss.backward()
            optimizer.step()

        # Avaliação no fim da época
        model.eval()
        with torch.no_grad():
            out_fit = model(X_fit)
            loss_fit = float(criterion(out_fit, y_fit).item())

            if tem_es:
                out_es = model(X_es)
                loss_val_interna = float(criterion(out_es, y_es).item())
            else:
                loss_val_interna = loss_fit

        historico.append(
            {
                "epoca": epoca,
                "loss_fit": loss_fit,
                "loss_val_interna": loss_val_interna,
            }
        )

        # Checagem de early stopping
        if (best_loss - loss_val_interna) > min_delta:
            best_loss = loss_val_interna
            best_epoch = epoca
            best_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= patience:
            break

    # Restaura o melhor checkpoint da janela interna
    model.load_state_dict(best_state)
    model.eval()
    return model, historico, best_epoch, len(historico)


def treinar_rna(
    painel: pd.DataFrame,
    seed: int = 42,
    max_epochs: int = 200,
    patience: int = 15,
    min_delta: float = 1e-5,
    incluir_validacao: bool = False,
    n_splits: int = 3,
    limite_densidade: float = 10.0,
    configs: dict[str, dict[str, Any]] | None = None,
    coluna_alvo: str = "alvo",
    coluna_tempo: str = "competencia",
) -> dict[str, Any]:
    """Treina e avalia modelos MLP com PyTorch CPU via validação cruzada por origem móvel.

    Implementa:
    - Verificações de integridade temporal (proibição de dados >= 2026).
    - Aplicação defensiva de recorte do escopo MVP R29.
    - Exclusão de 2020 do fit (apenas contexto histórico para lags).
    - Validação de ausência de valores negativos ou não finitos no alvo de treino.
    - Seleção de séries por densidade de treino (>= 10.0) em cada fold e no global.
    - Separação estrita de fit interno, embargo (3 meses) e early stopping (3 meses).
    - Pré-processador (imputação por mediana, indicadores, OneHotEncoder, StandardScaler X e y)
      ajustado SOMENTE no subset de fit antes do embargo.
    - Avaliação de >= 2 configurações (A e B) via SplitOrigemMovel com embargo.
    - Seleção da melhor configuração estritamente baseada em CV no treino.
    - Refit do modelo global no treino 202101-202409 com número de épocas derivado de CV.
    - Avaliação opcional na partição de validação externa (202501-202509) com mesma máscara justa.
    - Registro auditável de curvas, tempos, contagem de negativos, baselines e manifesto.
    """
    inicio_tempo_global = time.perf_counter()
    fixar_seed(seed)

    if max_epochs <= 0:
        raise ValueError(f"max_epochs deve ser estritamente positivo (> 0), recebido: {max_epochs}")
    if patience <= 0:
        raise ValueError(f"patience deve ser estritamente positivo (> 0), recebido: {patience}")
    if min_delta < 0:
        raise ValueError(f"min_delta não pode ser negativo (>= 0), recebido: {min_delta}")
    if n_splits <= 0:
        raise ValueError(f"n_splits deve ser estritamente positivo (> 0), recebido: {n_splits}")
    if limite_densidade < 0:
        raise ValueError(
            f"limite_densidade não pode ser negativo (>= 0), recebido: {limite_densidade}"
        )

    if painel is None or not isinstance(painel, pd.DataFrame) or painel.empty:
        raise ValueError("Operação rejeitada: painel vazio ou inválido fornecido para treinar_rna.")

    for col in [coluna_tempo, "destino", "uf"]:
        if col not in painel.columns:
            raise ValueError(f"Coluna obrigatória '{col}' ausente no painel.")

    # 1. Validação estrita de competências (proibição de teste >= 2026)
    comps = painel[coluna_tempo].dropna().astype(str).unique()
    for c in comps:
        c_val = validar_competencia(c)
        if c_val >= "202601":
            raise ValueError(
                f"Competência de teste '{c}' presente: esta fatia não permite "
                f"competências de teste (>= 202601)."
            )

    # 3. Colunas fontes obrigatórias de baselines determinísticas
    cols_fontes_baselines = {"admissoes_soma_3m", "admissoes_sazonal_ano_anterior"}
    cols_faltantes = cols_fontes_baselines - set(painel.columns)
    if cols_faltantes:
        raise ValueError(
            f"Colunas de fonte para baselines obrigatórias ausentes no painel: "
            f"{sorted(cols_faltantes)}."
        )

    # 4. Aplicação defensiva de recortar_painel_mvp na interface pública
    escopo = carregar_escopo_mvp()
    painel_recortado = recortar_painel_mvp(painel, escopo=escopo)

    # Valores de particoes/destinos nao usados nao podem controlar o ajuste.
    meses_numericos = painel_recortado[coluna_tempo].between("202101", "202409")
    if incluir_validacao:
        meses_numericos |= painel_recortado[coluna_tempo].between("202501", "202509")
    base_numerica = painel_recortado.loc[meses_numericos]
    for col in [*COLUNAS_NUMERICAS_PADRAO, coluna_alvo]:
        if col in base_numerica and pd.api.types.is_numeric_dtype(base_numerica[col]):
            if np.isinf(base_numerica[col].to_numpy()).any():
                if col == coluna_alvo:
                    raise ValueError("Coluna de alvo contém valores negativos ou não finitos.")
                raise ValueError(f"Valores não finitos na feature '{col}'.")

    # 5. Gerar referências de baselines SEMPRE das features fontes determinísticas
    painel_recortado = prever_baselines(painel_recortado)

    # 6. Validação do alvo no treino (202101 a 202409)
    if coluna_alvo in painel_recortado.columns:
        filtro_treino = (painel_recortado[coluna_tempo] >= "202101") & (
            painel_recortado[coluna_tempo] <= "202409"
        )
        alvos_treino = painel_recortado[filtro_treino][coluna_alvo].dropna().to_numpy()
        if len(alvos_treino) > 0:
            if not np.isfinite(alvos_treino).all() or (alvos_treino < 0).any():
                raise ValueError("Coluna de alvo contém valores negativos ou não finitos.")

    # 7. Se incluir_validacao=True, validar também o alvo em 2025
    if incluir_validacao and coluna_alvo in painel_recortado.columns:
        filtro_val = (painel_recortado[coluna_tempo] >= "202501") & (
            painel_recortado[coluna_tempo] <= "202509"
        )
        alvos_val = painel_recortado[filtro_val][coluna_alvo].dropna().to_numpy()
        if len(alvos_val) > 0:
            if not np.isfinite(alvos_val).all() or (alvos_val < 0).any():
                raise ValueError(
                    "Coluna de alvo na validação externa contém valores negativos ou não finitos."
                )

    # 8. Delimitação do treino: 202101 a 202409 (2020 fica de fora do fit, sendo apenas histórico)
    df_treino_global = painel_recortado[
        (painel_recortado[coluna_tempo] >= "202101") & (painel_recortado[coluna_tempo] <= "202409")
    ].copy()

    if df_treino_global.empty:
        raise ValueError("Conjunto de treino (202101-202409) está vazio.")

    # 9. Avaliação justa dos baselines chamando avaliar_baselines
    rel_baselines = avaliar_baselines(
        painel=painel_recortado,
        inicio_treino="202101",
        incluir_validacao=incluir_validacao,
        n_splits=n_splits,
        limite_densidade=limite_densidade,
    )

    configs_a_avaliar = configs or CONFIGS_PADRAO
    if len(configs_a_avaliar) < 2:
        raise ValueError("É obrigatório avaliar pelo menos duas configurações de RNA.")

    # 10. Splitter de origem móvel no treino global
    splitter = SplitOrigemMovel(n_splits=n_splits, limite_treino_maximo="202409")
    folds_indices = list(splitter.split(df_treino_global))

    relatorio_configs: dict[str, Any] = {}
    todas_curvas: list[dict[str, Any]] = []
    todas_previsoes: list[dict[str, Any]] = []

    # 11. Avaliação de cada configuração nos folds da validação cruzada
    for cfg_nome, cfg_params in configs_a_avaliar.items():
        t0_cfg = time.perf_counter()
        folds_resultado: list[dict[str, Any]] = []

        for fold_idx, (idx_tr, idx_vl) in enumerate(folds_indices):
            f_tr = df_treino_global.iloc[idx_tr].copy()
            f_vl = df_treino_global.iloc[idx_vl].copy()

            # Densidade calculada no treino deste fold (definição científica estrita)
            rel_dens = calcular_densidade_treino(
                f_tr,
                limite_minimo=limite_densidade,
                coluna_alvo=coluna_alvo,
                coluna_tempo=coluna_tempo,
                limite_competencia_treino=None,
            )
            series_elegiveis = obter_series_elegiveis(rel_dens)
            total_series = len(rel_dens)
            series_excluidas = total_series - len(series_elegiveis)

            # Partição interna: fit, embargo e earlystop
            df_fit_raw, df_es_raw, intervalos_fold = _particionar_treino_interno_fold(
                f_tr, coluna_tempo=coluna_tempo
            )

            # Filtrar séries elegíveis
            df_fit = filtrar_series_elegiveis(df_fit_raw, series_elegiveis)
            df_es = filtrar_series_elegiveis(df_es_raw, series_elegiveis)

            # Ajustar pré-processador SOMENTE no fit interno
            prep_fold = PreprocessadorRNA()
            prep_fold.fit(df_fit, coluna_alvo=coluna_alvo)

            # Instanciar e treinar modelo do fold
            model_fold = MLPRegressor(
                input_dim=prep_fold.dimensao_entrada,
                hidden_layers=cfg_params.get("hidden_layers", [64, 32]),
                dropout=float(cfg_params.get("dropout", 0.0)),
            )

            model_fold, hist_fold, best_ep, total_ep = _treinar_modelo_com_earlystopping(
                model=model_fold,
                prep=prep_fold,
                df_fit=df_fit,
                df_es=df_es,
                lr=float(cfg_params.get("lr", 0.001)),
                batch_size=int(cfg_params.get("batch_size", 128)),
                max_epochs=max_epochs,
                patience=patience,
                min_delta=min_delta,
                seed=seed + fold_idx,
                coluna_alvo=coluna_alvo,
            )

            for h in hist_fold:
                todas_curvas.append(
                    {
                        "config": cfg_nome,
                        "fold": fold_idx,
                        "epoca": h["epoca"],
                        "loss_fit": h["loss_fit"],
                        "loss_val_interna": h["loss_val_interna"],
                    }
                )

            # Avaliação no fold com mesma máscara justa dos baselines
            f_vl_elegivel = filtrar_series_elegiveis(f_vl, series_elegiveis)
            fora_alvo = (
                int(f_vl_elegivel[coluna_alvo].isna().sum()) if not f_vl_elegivel.empty else 0
            )
            fora_pers = (
                int(f_vl_elegivel["previsao_persistencia"].isna().sum())
                if not f_vl_elegivel.empty
                else 0
            )
            fora_saz = (
                int(f_vl_elegivel["previsao_sazonal"].isna().sum())
                if not f_vl_elegivel.empty
                else 0
            )

            if f_vl_elegivel.empty:
                df_eval_fold = f_vl_elegivel.iloc[0:0].copy()
            else:
                mascara_justa = (
                    f_vl_elegivel[coluna_alvo].notna()
                    & f_vl_elegivel["previsao_persistencia"].notna()
                    & f_vl_elegivel["previsao_sazonal"].notna()
                )
                df_eval_fold = f_vl_elegivel[mascara_justa].copy()

            # Escala MASE no treino por série (MAE do sazonal)
            mapa_escalas: dict[tuple[str, str], float | None] = {}
            for s in series_elegiveis:
                df_tr_s = f_tr[(f_tr["destino"] == s[0]) & (f_tr["uf"] == s[1])]
                val_tr_s = df_tr_s[
                    df_tr_s[coluna_alvo].notna() & df_tr_s["previsao_sazonal"].notna()
                ]
                if len(val_tr_s) > 0:
                    e_s = mae(val_tr_s[coluna_alvo], val_tr_s["previsao_sazonal"])
                    mapa_escalas[s] = e_s if e_s > 0.0 else None
                else:
                    mapa_escalas[s] = None

            motivos_indefinidos: dict[str, str] = {}

            if not df_eval_fold.empty:
                X_vl_tensor = prep_fold.transform_x(df_eval_fold)
                with torch.no_grad():
                    y_vl_pred_scaled = model_fold(X_vl_tensor)
                y_vl_pred = prep_fold.inverse_transform_y(y_vl_pred_scaled)
                df_eval_fold["previsao_rna"] = y_vl_pred

                res_erro = resumir_erros(
                    df_eval_fold,
                    col_real=coluna_alvo,
                    col_prev="previsao_rna",
                    chaves_serie=["destino", "uf"],
                )
                val_n = res_erro["n"]
                val_mae = res_erro["mae"]
                val_rmse = res_erro["rmse"]
                val_wape = res_erro["wape"]
                val_macro_mae = res_erro["macro_mae"]
                val_tabela_series = res_erro["tabela_series"]

                mases_validos: list[float] = []
                for reg in val_tabela_series:
                    chave_s = (str(reg["destino"]), str(reg["uf"]))
                    esc = mapa_escalas.get(chave_s)
                    val_mase_s = mase([reg["mae"]], [0.0], esc) if esc is not None else None
                    reg["mase"] = val_mase_s
                    if val_mase_s is not None:
                        mases_validos.append(val_mase_s)

                val_mase = float(np.mean(mases_validos)) if mases_validos else None

                if val_wape is None:
                    motivos_indefinidos["wape"] = "soma_real_zero"
                if val_mase is None:
                    motivos_indefinidos["mase"] = "escala_sazonal_indisponivel_ou_zero_no_treino"

                for _, r in df_eval_fold.iterrows():
                    todas_previsoes.append(
                        {
                            "competencia": str(r[coluna_tempo]),
                            "destino": str(r["destino"]),
                            "uf": str(r["uf"]),
                            "modelo": f"MLP_{cfg_nome}_fold{fold_idx}",
                            "alvo": float(r[coluna_alvo]),
                            "previsao": float(r["previsao_rna"]),
                        }
                    )
            else:
                val_n = 0
                val_mae = None
                val_rmse = None
                val_wape = None
                val_mase = None
                val_macro_mae = None
                val_tabela_series = []
                motivos_indefinidos["wape"] = "sem_amostras_na_janela"
                motivos_indefinidos["mase"] = "sem_amostras_na_janela"

            intervalos_dict = {
                "meses_fit": intervalos_fold["meses_fit"],
                "meses_earlystop": intervalos_fold["meses_earlystop"],
                "meses_embargo": intervalos_fold["meses_embargo"],
                "meses_avaliacao": sorted(f_vl[coluna_tempo].astype(str).unique().tolist()),
            }

            folds_resultado.append(
                {
                    "fold": fold_idx,
                    "n": val_n,
                    "mae": val_mae,
                    "rmse": val_rmse,
                    "wape": val_wape,
                    "mase": val_mase,
                    "macro_mae": val_macro_mae,
                    "motivos_indefinidos": motivos_indefinidos,
                    "tabela_series": val_tabela_series,
                    "exclusoes": {
                        "series_elegiveis": len(series_elegiveis),
                        "series_excluidas_densidade": series_excluidas,
                        "linhas_descartadas": {
                            "alvo_ausente": fora_alvo,
                            "persistencia_ausente": fora_pers,
                            "sazonal_ausente": fora_saz,
                        },
                    },
                    "intervalos": intervalos_dict,
                    "series_elegiveis": len(series_elegiveis),
                    "melhor_epoca": best_ep,
                    "epocas_treinadas": total_ep,
                }
            )

        maes_validos = [f["mae"] for f in folds_resultado if f["mae"] is not None]
        wapes_validos = [f["wape"] for f in folds_resultado if f["wape"] is not None]
        mases_validos_cv = [f["mase"] for f in folds_resultado if f["mase"] is not None]

        mae_medio = float(np.mean(maes_validos)) if maes_validos else None
        mae_desvio = float(np.std(maes_validos, ddof=1)) if len(maes_validos) > 1 else None
        wape_medio = float(np.mean(wapes_validos)) if wapes_validos else None
        wape_desvio = float(np.std(wapes_validos, ddof=1)) if len(wapes_validos) > 1 else None
        mase_medio = float(np.mean(mases_validos_cv)) if mases_validos_cv else None
        mase_desvio = float(np.std(mases_validos_cv, ddof=1)) if len(mases_validos_cv) > 1 else None

        tempo_cfg = time.perf_counter() - t0_cfg
        relatorio_configs[cfg_nome] = {
            "params": cfg_params,
            "tempo_segundos": tempo_cfg,
            "folds": folds_resultado,
            "mae_medio": mae_medio,
            "mae_desvio": mae_desvio,
            "wape_medio": wape_medio,
            "wape_desvio": wape_desvio,
            "mase_medio": mase_medio,
            "mase_desvio": mase_desvio,
        }

    # 12. Escolha da melhor configuração estritamente por CV no treino (menor MAE médio)
    configs_com_avaliacao = [k for k, v in relatorio_configs.items() if v["mae_medio"] is not None]
    if not configs_com_avaliacao:
        raise ValueError(
            "Nenhuma configuração de RNA obteve avaliação válida nos folds de validação cruzada."
        )

    ranking_configs = sorted(
        relatorio_configs.keys(),
        key=lambda k: (
            float("inf")
            if relatorio_configs[k]["mae_medio"] is None
            else relatorio_configs[k]["mae_medio"]
        ),
    )
    melhor_nome = ranking_configs[0]
    melhor_cfg_info = relatorio_configs[melhor_nome]

    # Número de épocas para refit derivado de CV (mediana dos melhores epochs nos folds)
    melhores_epochs_folds = [
        f["melhor_epoca"] for f in melhor_cfg_info["folds"] if "melhor_epoca" in f
    ]
    num_epochs_refit = (
        max(1, int(round(float(np.median(melhores_epochs_folds)))))
        if melhores_epochs_folds
        else max_epochs
    )

    # 13. Refit global no treino 202101-202409
    t0_refit = time.perf_counter()
    rel_dens_global = calcular_densidade_treino(
        df_treino_global,
        limite_minimo=limite_densidade,
        coluna_alvo=coluna_alvo,
        coluna_tempo=coluna_tempo,
        limite_competencia_treino="202409",
    )
    series_elegiveis_global = obter_series_elegiveis(rel_dens_global)
    df_treino_elegivel = filtrar_series_elegiveis(df_treino_global, series_elegiveis_global)

    prep_global = PreprocessadorRNA()
    prep_global.fit(df_treino_elegivel, coluna_alvo=coluna_alvo)

    model_global = MLPRegressor(
        input_dim=prep_global.dimensao_entrada,
        hidden_layers=melhor_cfg_info["params"].get("hidden_layers", [64, 32]),
        dropout=float(melhor_cfg_info["params"].get("dropout", 0.0)),
    )

    fixar_seed(seed)
    optimizer_global = torch.optim.Adam(
        model_global.parameters(), lr=float(melhor_cfg_info["params"].get("lr", 0.001))
    )
    criterion = nn.MSELoss()

    df_fit_global_valido = df_treino_elegivel[df_treino_elegivel[coluna_alvo].notna()]
    X_tr_tensor = prep_global.transform_x(df_fit_global_valido)
    y_tr_tensor = prep_global.transform_y(df_fit_global_valido[coluna_alvo])
    n_samples_global = len(X_tr_tensor)
    batch_sz = int(melhor_cfg_info["params"].get("batch_size", 128))

    for epoca in range(1, num_epochs_refit + 1):
        model_global.train()
        perm = torch.randperm(n_samples_global)
        for i in range(0, n_samples_global, batch_sz):
            batch_idx = perm[i : i + batch_sz]
            b_x = X_tr_tensor[batch_idx]
            b_y = y_tr_tensor[batch_idx]

            optimizer_global.zero_grad()
            out = model_global(b_x)
            loss = criterion(out, b_y)
            loss.backward()
            optimizer_global.step()

        model_global.eval()
        with torch.no_grad():
            out_fit = model_global(X_tr_tensor)
            loss_global = float(criterion(out_fit, y_tr_tensor).item())

        todas_curvas.append(
            {
                "config": f"{melhor_nome}_refit_global",
                "fold": -1,
                "epoca": epoca,
                "loss_fit": loss_global,
                "loss_val_interna": loss_global,
            }
        )

    tempo_refit = time.perf_counter() - t0_refit
    model_global.eval()

    # Previsões do modelo global sobre o conjunto de treino
    with torch.no_grad():
        y_tr_pred_scaled = model_global(X_tr_tensor)
    y_tr_pred = prep_global.inverse_transform_y(y_tr_pred_scaled)
    df_fit_global_valido = df_fit_global_valido.copy()
    df_fit_global_valido["previsao_rna"] = y_tr_pred

    res_treino_global = resumir_erros(
        df_fit_global_valido,
        col_real=coluna_alvo,
        col_prev="previsao_rna",
        chaves_serie=["destino", "uf"],
    )

    for _, r in df_fit_global_valido.iterrows():
        todas_previsoes.append(
            {
                "competencia": str(r[coluna_tempo]),
                "destino": str(r["destino"]),
                "uf": str(r["uf"]),
                "modelo": f"MLP_{melhor_nome}_global_treino",
                "alvo": float(r[coluna_alvo]),
                "previsao": float(r["previsao_rna"]),
            }
        )

    # 14. Avaliação externa (202501-202509) SOMENTE com incluir_validacao=True
    relatorio_validacao_externa: dict[str, Any] | None = None
    if incluir_validacao:
        filtro_val_ext = (painel_recortado[coluna_tempo] >= "202501") & (
            painel_recortado[coluna_tempo] <= "202509"
        )
        df_val_externa = painel_recortado[filtro_val_ext].copy()

        df_val_elegivel = filtrar_series_elegiveis(df_val_externa, series_elegiveis_global)
        fora_alvo_val = (
            int(df_val_elegivel[coluna_alvo].isna().sum()) if not df_val_elegivel.empty else 0
        )
        fora_pers_val = (
            int(df_val_elegivel["previsao_persistencia"].isna().sum())
            if not df_val_elegivel.empty
            else 0
        )
        fora_saz_val = (
            int(df_val_elegivel["previsao_sazonal"].isna().sum())
            if not df_val_elegivel.empty
            else 0
        )

        if not df_val_elegivel.empty and "previsao_persistencia" in df_val_elegivel.columns:
            mascara_justa_val = (
                df_val_elegivel[coluna_alvo].notna()
                & df_val_elegivel["previsao_persistencia"].notna()
                & df_val_elegivel["previsao_sazonal"].notna()
            )
            df_eval_val = df_val_elegivel[mascara_justa_val].copy()
        else:
            df_eval_val = df_val_elegivel[df_val_elegivel[coluna_alvo].notna()].copy()

        # Escala MASE no treino global por série (MAE do sazonal)
        mapa_escalas_global: dict[tuple[str, str], float | None] = {}
        for s in series_elegiveis_global:
            df_tr_s = df_treino_global[
                (df_treino_global["destino"] == s[0]) & (df_treino_global["uf"] == s[1])
            ]
            val_tr_s = df_tr_s[df_tr_s[coluna_alvo].notna() & df_tr_s["previsao_sazonal"].notna()]
            if len(val_tr_s) > 0:
                e_s = mae(val_tr_s[coluna_alvo], val_tr_s["previsao_sazonal"])
                mapa_escalas_global[s] = e_s if e_s > 0.0 else None
            else:
                mapa_escalas_global[s] = None

        motivos_indef_val: dict[str, str] = {}

        if not df_eval_val.empty:
            X_val_tensor = prep_global.transform_x(df_eval_val)
            with torch.no_grad():
                y_val_pred_scaled = model_global(X_val_tensor)
            y_val_pred = prep_global.inverse_transform_y(y_val_pred_scaled)
            df_eval_val["previsao_rna"] = y_val_pred

            res_val_ext = resumir_erros(
                df_eval_val,
                col_real=coluna_alvo,
                col_prev="previsao_rna",
                chaves_serie=["destino", "uf"],
            )

            mases_val: list[float] = []
            for reg in res_val_ext["tabela_series"]:
                chave_s = (str(reg["destino"]), str(reg["uf"]))
                esc = mapa_escalas_global.get(chave_s)
                val_mase = mase([reg["mae"]], [0.0], esc) if esc is not None else None
                reg["mase"] = val_mase
                if val_mase is not None:
                    mases_val.append(val_mase)

            mase_global_val = float(np.mean(mases_val)) if mases_val else None

            if res_val_ext["wape"] is None:
                motivos_indef_val["wape"] = "soma_real_zero"
            if mase_global_val is None:
                motivos_indef_val["mase"] = "escala_sazonal_indisponivel_ou_zero_no_treino"

            relatorio_validacao_externa = {
                "n": res_val_ext["n"],
                "mae": res_val_ext["mae"],
                "rmse": res_val_ext["rmse"],
                "wape": res_val_ext["wape"],
                "mase": mase_global_val,
                "macro_mae": res_val_ext["macro_mae"],
                "motivos_indefinidos": motivos_indef_val,
                "tabela_series": res_val_ext["tabela_series"],
                "exclusoes": {
                    "series_elegiveis": len(series_elegiveis_global),
                    "series_excluidas_densidade": (
                        len(rel_dens_global) - len(series_elegiveis_global)
                    ),
                    "linhas_descartadas": {
                        "alvo_ausente": fora_alvo_val,
                        "persistencia_ausente": fora_pers_val,
                        "sazonal_ausente": fora_saz_val,
                    },
                },
                "intervalos": {
                    "meses_treino": sorted(
                        df_treino_global[coluna_tempo].astype(str).unique().tolist()
                    ),
                    "meses_avaliacao": sorted(
                        df_val_externa[coluna_tempo].astype(str).unique().tolist()
                    ),
                },
            }

            for _, r in df_eval_val.iterrows():
                todas_previsoes.append(
                    {
                        "competencia": str(r[coluna_tempo]),
                        "destino": str(r["destino"]),
                        "uf": str(r["uf"]),
                        "modelo": f"MLP_{melhor_nome}_global_validacao",
                        "alvo": float(r[coluna_alvo]),
                        "previsao": float(r["previsao_rna"]),
                    }
                )

    # 15. Auditoria de previsões negativas
    df_previsoes = pd.DataFrame(todas_previsoes)
    contagem_negativos = int((df_previsoes["previsao"] < 0).sum()) if not df_previsoes.empty else 0
    min_previsao_negativa = (
        float(df_previsoes["previsao"].min()) if contagem_negativos > 0 else None
    )

    df_curvas = pd.DataFrame(todas_curvas)
    tempo_total = time.perf_counter() - inicio_tempo_global

    recorte_info = {
        "modo": "mvp_r29",
        "destinos": sorted(escopo["destinos"]),
        "ufs": sorted(painel_recortado["uf"].astype(str).unique().tolist()),
        "hash_recorte": escopo["hash_recorte"],
        "sha256_escopo": escopo["sha256_escopo"],
        "versao": escopo.get("versao", "1.0.0"),
        "decisao": escopo.get("decisao", "R29"),
    }

    relatorio_geral = {
        "recorte": recorte_info,
        "baselines": {
            "persistencia": {
                **rel_baselines["resumo_folds"]["persistencia"],
                "folds": [f["baselines"]["persistencia"] for f in rel_baselines["folds"]],
                "validacao": (
                    rel_baselines.get("validacao", {}).get("baselines", {}).get("persistencia")
                    if incluir_validacao and rel_baselines.get("validacao")
                    else None
                ),
            },
            "sazonal": {
                **rel_baselines["resumo_folds"]["sazonal"],
                "folds": [f["baselines"]["sazonal"] for f in rel_baselines["folds"]],
                "validacao": (
                    rel_baselines.get("validacao", {}).get("baselines", {}).get("sazonal")
                    if incluir_validacao and rel_baselines.get("validacao")
                    else None
                ),
            },
        },
        "ranking_configs": ranking_configs,
        "melhor_config": {
            "nome": melhor_nome,
            "params": melhor_cfg_info["params"],
            "num_epochs_refit": num_epochs_refit,
            "tempo_refit_segundos": tempo_refit,
        },
        "treino_global": res_treino_global,
        "validacao_externa": relatorio_validacao_externa,
        "contagem_negativos": contagem_negativos,
        "min_previsao_negativa": min_previsao_negativa,
        "tempo_total_segundos": tempo_total,
    }

    return {
        "configs": relatorio_configs,
        "curvas": df_curvas,
        "previsoes": df_previsoes,
        "modelo": model_global,
        "preprocessador": prep_global,
        "relatorio": relatorio_geral,
        "melhor_config": melhor_nome,
    }


def carregar_modelo_rna(
    diretorio_ou_manifesto: str | Path,
) -> tuple[MLPRegressor, PreprocessadorRNA, dict[str, Any]]:
    """Carrega checkpoint e pré-processador validando manifesto e integridade SHA-256.

    Segurança e integridade:
    - Lê métricas/manifesto JSON.
    - Exige manifesto válido com formato de dicionário.
    - Exige presença obrigatória dos hashes de checkpoint_rna.pt e preprocessador.json.
    - Valida que os hashes possuem formato hexadecimal de 64 caracteres.
    - Valida hashes SHA-256 do checkpoint e do pré-processador antes de carregar qualquer modelo.
    - Rejeita com ValueError se qualquer hash divergir, faltar ou for inválido.
    - Usa torch.load com weights_only=True e map_location='cpu'.
    - Não permite desserialização de pickle arbitrário sem manifesto.
    """
    p = Path(diretorio_ou_manifesto)
    if p.is_dir():
        caminho_manifesto = p / "metricas.json"
    else:
        caminho_manifesto = p

    if not caminho_manifesto.exists():
        raise FileNotFoundError(f"Manifesto não encontrado em: {caminho_manifesto}")

    with caminho_manifesto.open("r", encoding="utf-8") as f:
        manifesto = json.load(f)

    if not isinstance(manifesto, dict):
        raise ValueError(
            "Manifesto inválido: conteúdo do manifesto deve ser um objeto JSON (dict)."
        )

    dir_base = caminho_manifesto.parent
    hashes_artefatos = manifesto.get("sha256_artefatos")
    if not isinstance(hashes_artefatos, dict):
        raise ValueError(
            "Manifesto inválido: campo 'sha256_artefatos' ausente ou inválido no manifesto."
        )

    # Hashes obrigatórios do checkpoint e pré-processador
    for nome_artefato in ["checkpoint_rna.pt", "preprocessador.json"]:
        if nome_artefato not in hashes_artefatos:
            raise ValueError(f"Hash obrigatório '{nome_artefato}' ausente no manifesto.")
        h_esperado = hashes_artefatos[nome_artefato]
        hex_valido = (
            isinstance(h_esperado, str)
            and len(h_esperado) == 64
            and all(c in "0123456789abcdefABCDEF" for c in h_esperado)
        )
        if not hex_valido:
            raise ValueError(
                f"Hash '{nome_artefato}' no manifesto não é um hash SHA-256 "
                f"hexadecimal válido de 64 caracteres."
            )

    # Validação do checkpoint
    caminho_pt = dir_base / "checkpoint_rna.pt"
    if not caminho_pt.exists():
        raise FileNotFoundError(f"Arquivo de checkpoint ausente: {caminho_pt}")

    hash_pt_calculado = hashlib.sha256(caminho_pt.read_bytes()).hexdigest()
    hash_pt_esperado = hashes_artefatos["checkpoint_rna.pt"]
    if hash_pt_calculado.lower() != hash_pt_esperado.lower():
        raise ValueError(
            f"Hash SHA-256 do checkpoint divergiu do manifesto: "
            f"esperado={hash_pt_esperado}, calculado={hash_pt_calculado}"
        )

    # Validação do pré-processador
    caminho_prep = dir_base / "preprocessador.json"
    if not caminho_prep.exists():
        raise FileNotFoundError(f"Arquivo do pré-processador ausente: {caminho_prep}")

    hash_prep_calculado = hashlib.sha256(caminho_prep.read_bytes()).hexdigest()
    hash_prep_esperado = hashes_artefatos["preprocessador.json"]
    if hash_prep_calculado.lower() != hash_prep_esperado.lower():
        raise ValueError(
            f"Hash SHA-256 do pré-processador divergiu do manifesto: "
            f"esperado={hash_prep_esperado}, calculado={hash_prep_calculado}"
        )

    # Carregamento seguro do pré-processador via JSON puro
    with caminho_prep.open("r", encoding="utf-8") as f:
        dados_prep = json.load(f)
    prep = PreprocessadorRNA.from_dict(dados_prep)

    # Reconstrução e carregamento seguro do checkpoint em CPU
    info_melhor = manifesto.get("melhor_config", {})
    params_melhor = info_melhor.get("params", {})
    hidden_layers = params_melhor.get("hidden_layers", [64, 32])
    dropout = float(params_melhor.get("dropout", 0.0))

    modelo = MLPRegressor(
        input_dim=prep.dimensao_entrada,
        hidden_layers=hidden_layers,
        dropout=dropout,
    )
    state_dict = torch.load(caminho_pt, weights_only=True, map_location="cpu")
    modelo.load_state_dict(state_dict)
    modelo.eval()

    return modelo, prep, manifesto
