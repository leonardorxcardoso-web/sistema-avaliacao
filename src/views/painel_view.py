"""Cabeçalho de sessão logada e roteamento entre abas (avaliação / dashboard)."""

import streamlit as st

from src.data import BaseDados
from src.ui import exibir_logo
from src.views import avaliacao_view, dashboard_view


def renderizar(base: BaseDados) -> None:
    exibir_logo()
    _renderizar_cabecalho()

    st.write("")

    if st.session_state.eh_admin:
        aba_avaliacao, aba_dashboard = st.tabs(["📝 Realizar Avaliação", "📊 Dashboard Admin (Histórico)"])
        with aba_avaliacao:
            avaliacao_view.renderizar(base)
        with aba_dashboard:
            dashboard_view.renderizar()
    else:
        avaliacao_view.renderizar(base)


def _renderizar_cabecalho() -> None:
    with st.container():
        col_user, col_btn = st.columns([4, 1])
        with col_user:
            perfil_txt = "🛡️ Administrador" if st.session_state.eh_admin else "👤 Avaliador"
            st.info(
                f"**{perfil_txt}:** {st.session_state.email} | "
                f"**Região de Atuação:** {st.session_state.regiao}"
            )
        with col_btn:
            if st.button("Sair / Logout", use_container_width=True):
                st.session_state.logado = False
                st.rerun()
