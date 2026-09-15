"""Ponto de entrada do Sistema de Avaliação FGV.

Orquestra a sessão do Streamlit e delega para as views em src/views/.
Regras de negócio, acesso a dados e acesso ao Google Sheets vivem em
módulos separados (src/) — este arquivo só decide qual tela mostrar.
"""

import pandas as pd
import streamlit as st

from src.config import COLUNAS_AVALIACAO, CUSTOM_CSS
from src.data import carregar_dados_base
from src.sheets_repository import SheetsRepository, SheetsRepositoryError
from src.views import login_view, painel_view

st.set_page_config(page_title="Sistema de Avaliação FGV", page_icon="🎓", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _inicializar_avaliacoes() -> None:
    if "df_avaliacoes" in st.session_state:
        return
    try:
        repo = SheetsRepository.conectar()
        st.session_state.df_avaliacoes = repo.carregar_avaliacoes()
    except SheetsRepositoryError as exc:
        st.error(str(exc))
        st.session_state.df_avaliacoes = pd.DataFrame(columns=COLUNAS_AVALIACAO)


def main() -> None:
    base = carregar_dados_base()
    _inicializar_avaliacoes()

    if "logado" not in st.session_state:
        st.session_state.logado = False

    if st.session_state.logado:
        painel_view.renderizar(base)
    else:
        login_view.renderizar(base)


main()
