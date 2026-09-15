"""Regras de negócio de avaliações: pendências, gravação e restauração.

Mantém o Google Sheets e o `st.session_state.df_avaliacoes` sempre em sincronia
por acesso desta camada — nenhuma view deve mexer nesses dois estados
diretamente.

Existem dois formulários de avaliação, conforme o perfil do avaliador:
- Local (avaliador de região): pontualidade local, proatividade, resolução.
- Aeroporto (equipe de logística): pontualidade no aeroporto, facilidade de
  carga, resolutividade no despacho.
Os campos do formulário não usado pelo perfil ficam em branco ("") na
planilha, nunca None/NaN — replica o comportamento do app.py original.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

import pandas as pd

from src.config import COLUNAS_NOTAS
from src.sheets_repository import SheetsRepository

Nota = Union[int, str]  # int quando preenchida, "" quando não se aplica ao perfil


@dataclass(frozen=True)
class NovaAvaliacao:
    certame: str
    email_avaliador: str
    id_colaborador: str
    nome_colaborador: str
    observacoes: str
    eh_aeroporto: bool
    pontualidade_aeroporto: Nota = ""
    pontualidade_local: Nota = ""
    proatividade_ocorrencias: Nota = ""
    proatividade_lancamentos: Nota = ""
    proatividade_respostas: Nota = ""
    resolucao_problemas: Nota = ""
    facilidade_carga: Nota = ""
    resolutividade_despacho: Nota = ""

    def validar(self) -> Optional[str]:
        """Retorna mensagem de erro se inválida, senão None."""
        if not self.certame.strip():
            return "Informe o nome do certame antes de gravar a avaliação."
        if not self.id_colaborador or not self.nome_colaborador:
            return "Selecione um colaborador válido antes de gravar a avaliação."
        return None

    def como_linha_planilha(self, data_hora: str) -> list:
        return [
            data_hora,
            self.certame,
            self.email_avaliador,
            str(self.id_colaborador),
            self.nome_colaborador,
            self.pontualidade_aeroporto,
            self.pontualidade_local,
            self.proatividade_ocorrencias,
            self.proatividade_lancamentos,
            self.proatividade_respostas,
            self.resolucao_problemas,
            self.observacoes,
            self.facilidade_carga,
            self.resolutividade_despacho,
        ]

    def como_registro(self, data_hora: str) -> dict:
        return {
            "Data": data_hora,
            "Certame": self.certame,
            "Email_Avaliador": self.email_avaliador,
            "ID_Colaborador": self.id_colaborador,
            "Nome_Colaborador": self.nome_colaborador,
            "Pontualidade_Aeroporto": self.pontualidade_aeroporto,
            "Pontualidade_Local": self.pontualidade_local,
            "Proatividade_Ocorrencias": self.proatividade_ocorrencias,
            "Proatividade_Lancamentos": self.proatividade_lancamentos,
            "Proatividade_Respostas": self.proatividade_respostas,
            "Resolucao_Problemas": self.resolucao_problemas,
            "Observacoes": self.observacoes,
            "Facilidade_Carga": self.facilidade_carga,
            "Resolutividade_Despacho": self.resolutividade_despacho,
        }


def avaliacoes_do_avaliador(df_avaliacoes: pd.DataFrame, email: str) -> pd.DataFrame:
    if df_avaliacoes.empty or "Email_Avaliador" not in df_avaliacoes.columns:
        return pd.DataFrame(columns=df_avaliacoes.columns)
    return df_avaliacoes[df_avaliacoes["Email_Avaliador"] == email]


def colaboradores_pendentes(
    colaboradores_regiao: pd.DataFrame, avaliacoes_usuario: pd.DataFrame
) -> pd.DataFrame:
    ids_avaliados = avaliacoes_usuario["ID_Colaborador"].tolist()
    return colaboradores_regiao[~colaboradores_regiao["ID"].isin(ids_avaliados)]


def registrar_avaliacao(
    repo: SheetsRepository, df_avaliacoes: pd.DataFrame, nova: NovaAvaliacao
) -> pd.DataFrame:
    """Grava no Sheets e devolve o DataFrame local já atualizado.

    Levanta SheetsRepositoryError se a gravação remota falhar; nesse caso o
    DataFrame local não é alterado, evitando que a UI mostre uma avaliação
    "salva" que na verdade não chegou à planilha.
    """
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    repo.adicionar_avaliacao(nova.como_linha_planilha(data_hora))

    linha_local = pd.DataFrame([nova.como_registro(data_hora)])
    return pd.concat([df_avaliacoes, linha_local], ignore_index=True)


def restaurar_colaborador(
    repo: SheetsRepository,
    df_avaliacoes: pd.DataFrame,
    email_avaliador: str,
    certame: str,
    id_colaborador: str,
) -> pd.DataFrame:
    """Remove a avaliação de um colaborador e sincroniza a planilha inteira.

    `certame` é obrigatório: como cada certame tem sua própria planilha de
    colaboradores, o mesmo ID pode representar pessoas diferentes em
    certames diferentes — sem esse filtro, restaurar um colaborador do
    ENARE poderia apagar por engano uma avaliação de outro certame com o
    mesmo ID.
    """
    mask = ~(
        (df_avaliacoes["Email_Avaliador"] == email_avaliador)
        & (df_avaliacoes["Certame"] == certame)
        & (df_avaliacoes["ID_Colaborador"] == id_colaborador)
    )
    df_atualizado = df_avaliacoes[mask]
    repo.substituir_tudo(df_atualizado)
    return df_atualizado


def calcular_medias_por_colaborador(df_historico: pd.DataFrame) -> pd.DataFrame:
    df = df_historico.copy()
    df[list(COLUNAS_NOTAS)] = df[list(COLUNAS_NOTAS)].apply(pd.to_numeric, errors="coerce")
    df["Nota_Geral_Projeto"] = df[list(COLUNAS_NOTAS)].mean(axis=1)

    return (
        df.groupby(["ID_Colaborador", "Nome_Colaborador"])[
            list(COLUNAS_NOTAS) + ["Nota_Geral_Projeto"]
        ]
        .mean()
        .reset_index()
    )
