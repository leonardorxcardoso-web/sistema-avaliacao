"""Tela de login."""

import streamlit as st

from src.auth import autenticar
from src.data import BaseDados
from src.ui import exibir_logo


def renderizar(base: BaseDados) -> None:
    st.write("")
    st.write("")
    exibir_logo()

    st.markdown("<div class='title-box'>Portal do Avaliador</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle-box'>Acesso aos Projetos e Gestão de Colaboradores</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        email_input = st.text_input(
            "E-mail corporativo:", placeholder="Digite seu e-mail da FGV..."
        )

        _, col_centro, _ = st.columns([1, 1, 1])
        with col_centro:
            st.write("")
            entrar = st.button("Acessar Plataforma", use_container_width=True, type="primary")

        if entrar:
            sessao = autenticar(base, email_input)
            if sessao is None:
                st.error("Credenciais inválidas. Verifique seu e-mail e tente novamente.")
            else:
                st.session_state.logado = True
                st.session_state.email = sessao.email
                st.session_state.nome = sessao.nome
                st.session_state.regiao = sessao.regiao
                st.session_state.eh_admin = sessao.eh_admin
                st.session_state.eh_aeroporto = sessao.eh_aeroporto
                st.session_state.eh_supervisor = sessao.eh_supervisor
                st.session_state.pode_avaliar = sessao.pode_avaliar
                st.session_state.pode_ver_dashboard = sessao.pode_ver_dashboard
                st.rerun()
