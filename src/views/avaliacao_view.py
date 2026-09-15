"""Tela de registro de avaliações e restauração de avaliações enviadas.

Fluxo em duas etapas, pois cada certame tem sua própria planilha de
colaboradores/regiões: escolhe o certame primeiro, depois carrega quem pode
ser avaliado naquele certame. Há dois formulários conforme o perfil:
local (avaliador de região) ou aeroporto (equipe de logística).
"""

import pandas as pd
import streamlit as st

from src.avaliacao_service import (
    NovaAvaliacao,
    avaliacoes_do_avaliador,
    colaboradores_pendentes,
    registrar_avaliacao,
    restaurar_colaborador,
)
from src.config import CERTAMES_DISPONIVEIS
from src.data import BaseDados, colaboradores_por_regiao
from src.sheets_repository import SheetsRepository, SheetsRepositoryError


def renderizar(base: BaseDados) -> None:
    email = st.session_state.email
    regiao = st.session_state.regiao
    eh_aeroporto = st.session_state.eh_aeroporto

    certame = _selecionar_certame()
    if not certame:
        return

    colaboradores_regiao = colaboradores_por_regiao(base, certame, regiao, ver_todos=eh_aeroporto)
    if colaboradores_regiao.empty:
        st.warning("Nenhum colaborador encontrado para a sua região neste certame.")
        return

    avaliacoes_usuario = avaliacoes_do_avaliador(st.session_state.df_avaliacoes, email)
    avaliacoes_do_certame = (
        avaliacoes_usuario[avaliacoes_usuario["Certame"] == certame]
        if "Certame" in avaliacoes_usuario.columns
        else avaliacoes_usuario
    )
    pendentes = colaboradores_pendentes(colaboradores_regiao, avaliacoes_do_certame)

    if pendentes.empty:
        st.success("✅ **Excelente trabalho!** Todas as avaliações deste certame foram concluídas com sucesso.")
        st.balloons()
    else:
        _renderizar_formulario(certame, pendentes, email, eh_aeroporto)

    if not avaliacoes_do_certame.empty:
        _renderizar_secao_restauracao(certame, avaliacoes_do_certame)


def _selecionar_certame() -> str:
    st.markdown("### Configuração da Avaliação")
    st.caption(
        "Cada certame tem sua própria lista de colaboradores e regiões. "
        "Selecione o certame para carregar quem você pode avaliar."
    )
    certame = st.selectbox("Qual certame/projeto você está avaliando agora?", CERTAMES_DISPONIVEIS)
    if certame == "Outro...":
        certame = st.text_input("Digite o nome do certame:")
    return certame


def _campo_estrelas(rotulo: str) -> int:
    return st.radio(
        rotulo, options=[1, 2, 3, 4, 5], index=2, horizontal=True,
        format_func=lambda x: "⭐" * x,
    )


def _renderizar_formulario(certame: str, pendentes: pd.DataFrame, email: str, eh_aeroporto: bool) -> None:
    opcoes_colaboradores = dict(zip(pendentes["Nome"], pendentes["ID"]))
    colaborador_selecionado = st.selectbox(
        "Selecione o colaborador que atuou na sua região:",
        options=list(opcoes_colaboradores.keys()),
    )
    id_selecionado = opcoes_colaboradores.get(colaborador_selecionado)

    with st.form("form_avaliacao", clear_on_submit=True):
        st.caption("💡 Escala de avaliação: 1 estrela (Insatisfatório) a 5 estrelas (Excelente)")

        if eh_aeroporto:
            st.markdown("<div class='sessao-header'>✈️ Recebimento dos Materiais</div>", unsafe_allow_html=True)
            pont_aeroporto = _campo_estrelas("Pontualidade ao chegar no aeroporto")
            st.write("")
            facilidade_carga = _campo_estrelas("Facilidade em carregar material")
            st.write("")
            resolutividade_despacho = _campo_estrelas("Resolutividade na hora do despacho")
        else:
            st.markdown("<div class='sessao-header'>🕐 Avaliação de Pontualidade</div>", unsafe_allow_html=True)
            pont_local = _campo_estrelas("Chegada no local de aplicação")

            st.markdown("<div class='sessao-header'>⚡ Avaliação de Proatividade</div>", unsafe_allow_html=True)
            proat_ocorrencias = _campo_estrelas("Ocorrências")
            st.write("")
            proat_lancamentos = _campo_estrelas("Lançamentos")
            st.write("")
            proat_respostas = _campo_estrelas("Respostas no grupo")

            st.markdown("<div class='sessao-header'>🛠️ Resolução de Problemas</div>", unsafe_allow_html=True)
            resolucao = _campo_estrelas("Grau de resolutividade do colaborador")

        st.markdown("<div class='sessao-header'>📝 Observações Qualitativas</div>", unsafe_allow_html=True)
        observacoes = st.text_area("Insira recomendações, incidentes ou elogios (Opcional):", height=100)

        st.write("")
        submit = st.form_submit_button("Gravar Avaliação no Sistema", type="primary", use_container_width=True)

        if submit:
            if eh_aeroporto:
                nova = NovaAvaliacao(
                    certame=certame,
                    email_avaliador=email,
                    id_colaborador=id_selecionado,
                    nome_colaborador=colaborador_selecionado,
                    eh_aeroporto=True,
                    pontualidade_aeroporto=pont_aeroporto,
                    facilidade_carga=facilidade_carga,
                    resolutividade_despacho=resolutividade_despacho,
                    observacoes=observacoes,
                )
            else:
                nova = NovaAvaliacao(
                    certame=certame,
                    email_avaliador=email,
                    id_colaborador=id_selecionado,
                    nome_colaborador=colaborador_selecionado,
                    eh_aeroporto=False,
                    pontualidade_local=pont_local,
                    proatividade_ocorrencias=proat_ocorrencias,
                    proatividade_lancamentos=proat_lancamentos,
                    proatividade_respostas=proat_respostas,
                    resolucao_problemas=resolucao,
                    observacoes=observacoes,
                )
            _processar_submissao(nova)


def _processar_submissao(nova: NovaAvaliacao) -> None:
    erro_validacao = nova.validar()
    if erro_validacao:
        st.error(erro_validacao)
        return

    try:
        repo = SheetsRepository.conectar()
        st.session_state.df_avaliacoes = registrar_avaliacao(
            repo, st.session_state.df_avaliacoes, nova
        )
    except SheetsRepositoryError as exc:
        st.error(str(exc))
        return

    st.success("Avaliação registrada com sucesso na nuvem!")
    st.rerun()


def _renderizar_secao_restauracao(certame: str, avaliacoes_do_certame: pd.DataFrame) -> None:
    st.write("")
    with st.expander("🔄 Precisa corrigir alguma avaliação já enviada?"):
        st.write("Selecione o colaborador abaixo para anular a nota anterior e avaliá-lo novamente.")

        opcoes_avaliados = dict(
            zip(avaliacoes_do_certame["Nome_Colaborador"], avaliacoes_do_certame["ID_Colaborador"])
        )
        colaborador_restaurar = st.selectbox(
            "Colaborador:", options=list(opcoes_avaliados.keys()), key="select_restaurar"
        )
        id_restaurar = opcoes_avaliados.get(colaborador_restaurar)

        if st.button("Anular e Restaurar Colaborador"):
            try:
                repo = SheetsRepository.conectar()
                st.session_state.df_avaliacoes = restaurar_colaborador(
                    repo, st.session_state.df_avaliacoes, st.session_state.email, certame, id_restaurar
                )
            except SheetsRepositoryError as exc:
                st.error(str(exc))
                return

            st.success("Colaborador restaurado com sucesso!")
            st.rerun()
