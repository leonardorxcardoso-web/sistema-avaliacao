"""Cabeçalho de sessão logada e roteamento entre telas (avaliação / dashboard).

Segue a mesma regra de acesso do app web: quem `pode_avaliar` vê a tela de
avaliação, quem `pode_ver_dashboard` vê o Dashboard Admin — um perfil pode
ter as duas coisas (supervisor) ou só uma delas (admin puro ou avaliador).
"""

import streamlit as st

from src.data import BaseDados
from src.ui import exibir_logo
from src.views import avaliacao_view, dashboard_view


def _perfil_texto() -> str:
    if st.session_state.eh_admin:
        return "🛡️ Administrador"
    if st.session_state.eh_supervisor:
        return "⭐ Supervisor"
    if st.session_state.eh_aeroporto:
        return "✈️ Equipe Aeroporto"
    return "👤 Avaliador"


def renderizar(base: BaseDados) -> None:
    exibir_logo()
    _renderizar_cabecalho()

    st.write("")

    pode_avaliar = st.session_state.pode_avaliar
    pode_ver_dashboard = st.session_state.pode_ver_dashboard

    if pode_avaliar and pode_ver_dashboard:
        aba_avaliacao, aba_dashboard = st.tabs(["📝 Realizar Avaliação", "📊 Dashboard Admin (Histórico)"])
        with aba_avaliacao:
            avaliacao_view.renderizar(base)
        with aba_dashboard:
            dashboard_view.renderizar()
    elif pode_avaliar:
        avaliacao_view.renderizar(base)
    elif pode_ver_dashboard:
        dashboard_view.renderizar()


def _renderizar_cabecalho() -> None:
    with st.container():
        col_user, col_btn = st.columns([4, 1])
        with col_user:
            st.info(
                f"**{_perfil_texto()}:** {st.session_state.nome} ({st.session_state.email}) | "
                f"**Região de Atuação:** {st.session_state.regiao}"
            )
        with col_btn:
            if st.button("Sair / Logout", use_container_width=True):
                st.session_state.logado = False
                st.rerun()
