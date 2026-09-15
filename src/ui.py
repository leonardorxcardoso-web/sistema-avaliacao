"""Helpers de UI reutilizados entre views."""

import os

import streamlit as st


def exibir_logo(caminho: str = "logo_fgv.png") -> None:
    if not os.path.exists(caminho):
        return
    _, col_centro, _ = st.columns([1, 2, 1])
    with col_centro:
        st.image(caminho, use_container_width=True)
    st.write("")
