"""Painel administrativo: ranking geral e detalhamento por colaborador."""

import io

import pandas as pd
import streamlit as st

from src.avaliacao_service import calcular_medias_por_colaborador
from src.config import CERTAME_PADRAO

_OPCAO_VISAO_GERAL = "📊 Visão Geral (Ranking)"
_OPCAO_TODOS_CERTAMES = "Todos (Histórico Completo)"


def renderizar() -> None:
    st.markdown("### Histórico Institucional de Desempenho")

    if st.session_state.df_avaliacoes.empty:
        st.info("Ainda não há avaliações registradas no sistema.")
        return

    df_historico = _normalizar_certame(st.session_state.df_avaliacoes.copy())
    filtro_certame = _selecionar_filtro_certame(df_historico)

    if filtro_certame != _OPCAO_TODOS_CERTAMES:
        df_historico = df_historico[df_historico["Certame"] == filtro_certame]

    if df_historico.empty:
        st.warning("Nenhuma avaliação encontrada para este certame.")
        return

    df_medias = calcular_medias_por_colaborador(df_historico)
    pesquisa = st.selectbox(
        "Buscar painel individual:",
        options=[_OPCAO_VISAO_GERAL] + df_medias["Nome_Colaborador"].tolist(),
    )

    st.markdown("---")

    if pesquisa == _OPCAO_VISAO_GERAL:
        _renderizar_ranking(df_medias, filtro_certame)
    else:
        _renderizar_painel_individual(df_historico, df_medias, pesquisa, filtro_certame)


def _normalizar_certame(df: pd.DataFrame) -> pd.DataFrame:
    if "Certame" not in df.columns:
        df["Certame"] = CERTAME_PADRAO
    df["Certame"] = df["Certame"].fillna(CERTAME_PADRAO)
    return df


def _selecionar_filtro_certame(df_historico: pd.DataFrame) -> str:
    lista_certames = df_historico["Certame"].unique().tolist()
    return st.selectbox("Filtrar por Projeto:", [_OPCAO_TODOS_CERTAMES] + lista_certames)


def _renderizar_painel_individual(
    df_historico: pd.DataFrame, df_medias: pd.DataFrame, nome_colaborador: str, filtro_certame: str
) -> None:
    dados_colab = df_medias[df_medias["Nome_Colaborador"] == nome_colaborador].iloc[0]

    st.markdown(f"<h3 style='color: #005baa;'>Desempenho: {nome_colaborador}</h3>", unsafe_allow_html=True)
    st.caption(f"Dados filtrados por: **{filtro_certame}**")

    c1, c2, c3 = st.columns(3)
    c1.metric("Nota Geral Média", f"{dados_colab['Nota_Geral_Projeto']:.1f} / 5.0")
    c2.metric("Média Pontualidade", f"{dados_colab['Pontualidade_Local']:.1f}")
    c3.metric("Média Resolutividade", f"{dados_colab['Resolucao_Problemas']:.1f}")

    st.write("")
    st.markdown("#### Histórico de Observações")
    obs_colab = df_historico[df_historico["Nome_Colaborador"] == nome_colaborador][
        ["Data", "Certame", "Email_Avaliador", "Observacoes"]
    ]

    for _, row in obs_colab.iterrows():
        observacao = row["Observacoes"]
        if pd.notna(observacao) and str(observacao).strip():
            st.warning(
                f"**Projeto:** {row['Certame']} | **Em:** {row['Data']} | **Por:** {row['Email_Avaliador']}\n\n{observacao}"
            )


def _renderizar_ranking(df_medias: pd.DataFrame, filtro_certame: str) -> None:
    st.markdown(f"#### Ranking Geral de Colaboradores ({filtro_certame})")
    df_ranking = df_medias.sort_values(by="Nota_Geral_Projeto", ascending=False).reset_index(drop=True)

    st.download_button(
        label="📥 Baixar Relatório em Excel",
        data=_gerar_excel(df_ranking),
        file_name=f"Ranking_Avaliadores_{filtro_certame.replace(' ', '_')}.xlsx",
        mime="application/vnd.ms-excel",
        help="Clique para baixar a tabela completa abaixo em formato Excel",
    )
    st.write("")

    colunas_exibidas = [
        "Nome_Colaborador", "Nota_Geral_Projeto", "Pontualidade_Local",
        "Proatividade_Respostas", "Resolucao_Problemas",
    ]
    colunas_numericas = colunas_exibidas[1:]
    st.dataframe(
        df_ranking[colunas_exibidas].style.format("{:.1f}", subset=colunas_numericas),
        use_container_width=True,
    )


def _gerar_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Ranking_Desempenho", index=False)
    return buffer.getvalue()
