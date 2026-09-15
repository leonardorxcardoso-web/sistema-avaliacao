"""Carregamento e normalização da base local de colaboradores/funcionários.

Cada certame (ENARE, CFC, OAB...) tem sua própria aba de colaboradores em
Base.xlsx, pois a lista de colaboradores e suas regiões variam por certame —
uma pessoa pode atuar em regiões diferentes dependendo do projeto. A aba
Funcionarios (avaliadores/login) é única e não varia por certame.
"""

from dataclasses import dataclass
from typing import Dict, Union

import pandas as pd
import streamlit as st

from src.config import CERTAME_PADRAO, CERTAMES_COM_PLANILHA


@dataclass(frozen=True)
class BaseDados:
    colaboradores_por_certame: Dict[str, pd.DataFrame]
    funcionarios: pd.DataFrame

    def colaboradores(self, certame: str) -> pd.DataFrame:
        """Colaboradores do certame informado; cai para o certame padrão
        (ENARE) se o certame não tiver planilha própria (ex.: "Outro...")."""
        chave = certame if certame in self.colaboradores_por_certame else CERTAME_PADRAO
        return self.colaboradores_por_certame[chave]


@st.cache_data
def carregar_dados_base(caminho: str = "Base.xlsx") -> BaseDados:
    """Lê a planilha local de colaboradores/funcionários e normaliza colunas.

    Cacheado pelo Streamlit: a planilha só é lida do disco uma vez por sessão
    de processo, evitando I/O repetido a cada rerender.
    """
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


def colaboradores_por_regiao(
    base: BaseDados, certame: str, regiao: Union[str, float], ver_todos: bool = False
) -> pd.DataFrame:
    """Filtra colaboradores do certame pela região do avaliador logado.

    `ver_todos=True` (contas admin/aeroporto) ou região vazia/NaN enxergam
    todos os colaboradores do certame, sem filtro de região.
    """
    colaboradores = base.colaboradores(certame)

    if ver_todos or pd.isna(regiao) or regiao == "":
        return colaboradores.copy()

    regiao_limpa = str(regiao).strip().lower()
    return colaboradores[colaboradores["Regiao"] == regiao_limpa].copy()
