"""Estado do processo: cache da base local e das avaliações carregadas do Sheets.

Equivalente ao st.session_state do app Streamlit, mas por processo (a API é
single-tenant local, então isso é suficiente e evita reconectar ao Sheets a
cada requisição).
"""

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config import CERTAMES_COM_PLANILHA, COLUNAS_AVALIACAO
from src.data import BaseDados
from src.sheets_repository import SheetsRepository, SheetsRepositoryError

_BASE_XLSX = str(Path(__file__).resolve().parents[2] / "Base.xlsx")


def _carregar_base_sem_cache(caminho: str) -> BaseDados:
    """Mesma lógica de src.data.carregar_dados_base, sem o decorator
    @st.cache_data (que exige runtime do Streamlit e não funciona aqui)."""
    colaboradores_por_certame = {}
    for certame in CERTAMES_COM_PLANILHA:
        df = pd.read_excel(caminho, sheet_name=f"Colaboradores_{certame}")
        df.columns = df.columns.str.strip()
        df["Regiao"] = df["Regiao"].astype(str).str.strip().str.lower()
        colaboradores_por_certame[certame] = df

    df_funcionarios = pd.read_excel(caminho, sheet_name="Funcionarios")
    df_funcionarios.columns = df_funcionarios.columns.str.strip()
    df_funcionarios["Email"] = df_funcionarios["Email"].astype(str).str.strip().str.lower()

    return BaseDados(
        colaboradores_por_certame=colaboradores_por_certame, funcionarios=df_funcionarios
    )


class AppState:
    def __init__(self) -> None:
        self._base: Optional[BaseDados] = None
        self._df_avaliacoes: Optional[pd.DataFrame] = None

    @property
    def base(self) -> BaseDados:
        if self._base is None:
            self._base = _carregar_base_sem_cache(_BASE_XLSX)
        return self._base

    @property
    def df_avaliacoes(self) -> pd.DataFrame:
        if self._df_avaliacoes is None:
            self._df_avaliacoes = self._carregar_avaliacoes_iniciais()
        return self._df_avaliacoes  # type: ignore[return-value]

    @df_avaliacoes.setter
    def df_avaliacoes(self, valor: pd.DataFrame) -> None:
        self._df_avaliacoes = valor

    @staticmethod
    def _carregar_avaliacoes_iniciais() -> pd.DataFrame:
        try:
            repo = SheetsRepository.conectar()
            return repo.carregar_avaliacoes()
        except SheetsRepositoryError:
            return pd.DataFrame(columns=COLUNAS_AVALIACAO)


estado = AppState()
