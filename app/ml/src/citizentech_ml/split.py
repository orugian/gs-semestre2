"""Divisão temporal de dados (D10 / T04): split calendário fixo e origem móvel com embargo."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import pandas as pd

from citizentech_ml.features.datas import (
    deslocar_mes,
    validar_competencia,
)

# Partições de calendário fixadas pela decisão D10
COMPETENCIA_FIM_TREINO = "202409"
COMPETENCIA_INICIO_EMBARGO_1 = "202410"
COMPETENCIA_FIM_EMBARGO_1 = "202412"
COMPETENCIA_INICIO_VALIDACAO = "202501"
COMPETENCIA_FIM_VALIDACAO = "202509"
COMPETENCIA_INICIO_EMBARGO_2 = "202510"
COMPETENCIA_FIM_EMBARGO_2 = "202512"
COMPETENCIA_INICIO_TESTE = "202601"
COMPETENCIA_FIM_TESTE = "202606"


def obter_split_calendario(
    df: pd.DataFrame,
    incluir_teste: bool = False,
    coluna_tempo: str = "competencia",
) -> tuple[pd.DataFrame, pd.DataFrame] | tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Realiza a divisão temporal canônica D10 com embargos trimestrais reais.

    Partições:
    - Treino: t <= 202409
    - Embargo 1: 202410..202412 (não incluído em treino nem em validação)
    - Validação: 202501..202509
    - Embargo 2: 202510..202512 (não incluído em validação nem em teste)
    - Teste: 202601..202606 (retornado APENAS se incluir_teste=True)

    Por padrão (incluir_teste=False), retorna apenas (df_treino, df_validacao).
    """
    if coluna_tempo not in df.columns:
        raise ValueError(f"Coluna temporal '{coluna_tempo}' não encontrada no DataFrame.")

    comp_serie = df[coluna_tempo].astype(str).map(validar_competencia)

    mascara_treino = comp_serie <= COMPETENCIA_FIM_TREINO
    mascara_val = (comp_serie >= COMPETENCIA_INICIO_VALIDACAO) & (
        comp_serie <= COMPETENCIA_FIM_VALIDACAO
    )

    df_treino = df[mascara_treino].copy()
    df_val = df[mascara_val].copy()

    if not incluir_teste:
        return df_treino, df_val

    mascara_teste = (comp_serie >= COMPETENCIA_INICIO_TESTE) & (
        comp_serie <= COMPETENCIA_FIM_TESTE
    )
    df_teste = df[mascara_teste].copy()

    return df_treino, df_val, df_teste


class SplitOrigemMovel:
    """Splitter de janela expansiva (origem móvel) compatível com a convenção do scikit-learn.

    Regras congeladas (D10 / T04):
    - Opera com base em meses de calendário reais (não índice de linhas em painel).
    - Expulsa exatamente 'meses_embargo' meses de calendário imediatamente anteriores
      ao início de cada janela de validação em TODAS as séries do painel.
    - Embargo mínimo obrigatório de 3 meses reais (meses_embargo >= 3).
    - Origens ficam estritamente contidas no limite do treino (limite_treino_maximo <= 202409).
    - Parâmetros devem ser inteiros estritos (rejeita float e bool).
    - Nunca retorna folds com treino ou validação vazios (rejeita com ValueError explícito).
    """

    def __init__(
        self,
        n_splits: int = 3,
        tamanho_validacao_meses: int = 3,
        meses_embargo: int = 3,
        tamanho_minimo_treino_meses: int = 12,
        coluna_tempo: str = "competencia",
        limite_treino_maximo: str = COMPETENCIA_FIM_TREINO,
    ) -> None:
        for nome, val in [
            ("n_splits", n_splits),
            ("tamanho_validacao_meses", tamanho_validacao_meses),
            ("meses_embargo", meses_embargo),
            ("tamanho_minimo_treino_meses", tamanho_minimo_treino_meses),
        ]:
            if type(val) is not int:
                raise TypeError(
                    f"'{nome}' deve ser int estrito, recebido {type(val).__name__}: {val!r}"
                )

        if n_splits < 1:
            raise ValueError(f"n_splits deve ser >= 1, recebido {n_splits}")
        if tamanho_validacao_meses < 1:
            raise ValueError(
                f"tamanho_validacao_meses deve ser >= 1, recebido {tamanho_validacao_meses}"
            )
        if meses_embargo < 3:
            raise ValueError(
                f"meses_embargo deve ser >= 3 conforme decisão congelada D10, "
                f"recebido {meses_embargo}"
            )
        if tamanho_minimo_treino_meses < 1:
            raise ValueError(
                f"tamanho_minimo_treino_meses deve ser >= 1, recebido {tamanho_minimo_treino_meses}"
            )

        limite_val = validar_competencia(limite_treino_maximo)
        if limite_val > COMPETENCIA_FIM_TREINO:
            raise ValueError(
                f"limite_treino_maximo '{limite_val}' não pode ser posterior a "
                f"{COMPETENCIA_FIM_TREINO} conforme decisão congelada D10."
            )

        self.n_splits = n_splits
        self.tamanho_validacao_meses = tamanho_validacao_meses
        self.meses_embargo = meses_embargo
        self.tamanho_minimo_treino_meses = tamanho_minimo_treino_meses
        self.coluna_tempo = coluna_tempo
        self.limite_treino_maximo = limite_val

    def _obter_serie_tempo(self, X: Any, groups: Any = None) -> pd.Series:
        if isinstance(X, pd.DataFrame):
            if self.coluna_tempo in X.columns:
                return X[self.coluna_tempo].astype(str)
        if groups is not None:
            return pd.Series(groups).astype(str)
        if isinstance(X, pd.Series):
            return X.astype(str)
        raise ValueError(
            f"Não foi possível extrair a coluna temporal '{self.coluna_tempo}' de X nem de groups."
        )

    def _calcular_janelas_folds(self, serie_tempo: pd.Series) -> list[tuple[str, str, str]]:
        """Calcula as tuplas (limite_treino, val_inicio, val_fim) para cada fold."""
        meses_unicos = sorted(serie_tempo.map(validar_competencia).unique())
        meses_treino = [m for m in meses_unicos if m <= self.limite_treino_maximo]

        if not meses_treino:
            raise ValueError(
                f"Nenhum mês disponível <= limite_treino_maximo ({self.limite_treino_maximo})"
            )

        # Determinar os n_splits finais retroagindo a partir do último mês de treino disponível
        janelas: list[tuple[str, str, str]] = []
        idx_candidato = len(meses_treino) - 1

        while idx_candidato >= 0 and len(janelas) < self.n_splits:
            val_fim_corrente = meses_treino[idx_candidato]
            val_inicio_corrente = deslocar_mes(
                val_fim_corrente, -(self.tamanho_validacao_meses - 1)
            )
            limite_treino_corrente = deslocar_mes(
                val_inicio_corrente, -(self.meses_embargo + 1)
            )

            # Verificar se a janela de validação possui dados reais
            meses_na_val = [
                m for m in meses_treino if val_inicio_corrente <= m <= val_fim_corrente
            ]
            if not meses_na_val:
                idx_candidato -= 1
                continue

            # Verificar se ainda há dados suficientes de treino antes do embargo
            meses_antes = [m for m in meses_treino if m <= limite_treino_corrente]
            if len(meses_antes) < self.tamanho_minimo_treino_meses:
                # Não é possível recuar mais mantendo treino suficiente
                break

            janelas.append((limite_treino_corrente, val_inicio_corrente, val_fim_corrente))

            # Próximo candidato a val_fim deve ser estritamente anterior a val_inicio desta janela
            proximo_fim = deslocar_mes(val_inicio_corrente, -1)
            while idx_candidato >= 0 and meses_treino[idx_candidato] > proximo_fim:
                idx_candidato -= 1

        if len(janelas) < self.n_splits:
            raise ValueError(
                f"Dados insuficientes para gerar {self.n_splits} splits válidos e não vazios "
                f"com val={self.tamanho_validacao_meses}, embargo={self.meses_embargo} "
                f"e treino_min={self.tamanho_minimo_treino_meses}. Foram possíveis {len(janelas)}."
            )

        # Inverte para que o fold 0 seja o mais antigo e o fold n_splits-1 seja o mais recente
        janelas.reverse()
        return janelas

    def split(
        self,
        X: Any,
        y: Any = None,
        groups: Any = None,
    ) -> Iterator[tuple[np.ndarray, np.ndarray]]:
        """Gera índices (train_idx, val_idx) para cada fold."""
        serie_tempo = self._obter_serie_tempo(X, groups=groups)
        comp_array = serie_tempo.map(validar_competencia).to_numpy()

        janelas = self._calcular_janelas_folds(serie_tempo)

        for limite_treino, val_inicio, val_fim in janelas:
            idx_treino = np.where(comp_array <= limite_treino)[0]
            idx_val = np.where((comp_array >= val_inicio) & (comp_array <= val_fim))[0]
            if len(idx_treino) == 0 or len(idx_val) == 0:
                raise ValueError(
                    f"Fold inválido gerado: len(treino)={len(idx_treino)}, "
                    f"len(validacao)={len(idx_val)}. Índices vazios não são permitidos."
                )
            yield idx_treino, idx_val

    def get_n_splits(
        self,
        X: Any = None,
        y: Any = None,
        groups: Any = None,
    ) -> int:
        """Retorna o número de splits configurado."""
        if X is not None or groups is not None:
            serie_tempo = self._obter_serie_tempo(X, groups=groups)
            janelas = self._calcular_janelas_folds(serie_tempo)
            return len(janelas)
        return self.n_splits
