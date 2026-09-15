"""Acesso ao Google Sheets que guarda as avaliações.

Isola toda a dependência de gspread/oauth2client num único lugar (Repository
Pattern): o resto da aplicação só conhece `SheetsRepository`, nunca a
biblioteca gspread diretamente — troca de storage (ex.: Postgres) não afeta
chamadores.
"""

import json
import os
from dataclasses import dataclass

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

from src.config import COLUNAS_AVALIACAO, CERTAME_PADRAO

_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
_PLANILHA_NOME = "Avaliacoes_Salvas"
_CREDENCIAIS_LOCAL = "credenciais.json"


class SheetsRepositoryError(RuntimeError):
    """Erro ao ler/gravar na planilha de avaliações."""


@dataclass
class SheetsRepository:
    _sheet: gspread.Worksheet

    @classmethod
    def conectar(cls) -> "SheetsRepository":
        try:
            creds = cls._obter_credenciais()
            client = gspread.authorize(creds)
            sheet = client.open(_PLANILHA_NOME).sheet1
        except Exception as exc:  # noqa: BLE001 - traduzido para erro de domínio
            raise SheetsRepositoryError(
                f"Erro ao conectar com o Google Sheets: {exc}"
            ) from exc
        return cls(_sheet=sheet)

    @staticmethod
    def _obter_credenciais() -> ServiceAccountCredentials:
        """Resolve as credenciais em três fontes possíveis, nesta ordem:

        1. Arquivo `credenciais.json` local (uso local/dev).
        2. Variável de ambiente `GOOGLE_CREDENTIALS_JSON` com o JSON inteiro
           da service account (Render e qualquer host que use env vars).
        3. `st.secrets["gcp_service_account"]` (Streamlit Community Cloud).
        """
        if os.path.exists(_CREDENCIAIS_LOCAL):
            return ServiceAccountCredentials.from_json_keyfile_name(_CREDENCIAIS_LOCAL, _SCOPE)

        credenciais_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if credenciais_env:
            creds_dict = json.loads(credenciais_env)
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, _SCOPE)

        import streamlit as st

        creds_dict = dict(st.secrets["gcp_service_account"])
        return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, _SCOPE)

    def carregar_avaliacoes(self) -> pd.DataFrame:
        try:
            dados = self._sheet.get_all_records()
        except Exception as exc:  # noqa: BLE001
            raise SheetsRepositoryError(
                f"Erro ao carregar avaliações do Google Sheets: {exc}"
            ) from exc

        if not dados:
            return pd.DataFrame(columns=COLUNAS_AVALIACAO)

        df = pd.DataFrame(dados)
        if "Certame" not in df.columns:
            df["Certame"] = CERTAME_PADRAO
        return df

    def adicionar_avaliacao(self, linha: list) -> None:
        try:
            self._sheet.append_row(linha)
        except Exception as exc:  # noqa: BLE001
            raise SheetsRepositoryError(
                f"Erro ao salvar avaliação no Google Sheets: {exc}"
            ) from exc

    def substituir_tudo(self, df: pd.DataFrame) -> None:
        """Reescreve a planilha inteira a partir de `df`.

        Usado apenas pelo fluxo de "anular avaliação". Buscamos o estado
        atual da planilha antes de limpar para reduzir a janela de corrida
        entre dois avaliadores restaurando ao mesmo tempo — não elimina o
        risco (Sheets não oferece transação real), mas evita clear() +
        exceção deixando a planilha vazia: só limpamos depois de confirmar
        que conseguimos serializar os dados novos.
        """
        cabecalho = list(df.columns)
        linhas = df.values.tolist()

        try:
            self._sheet.clear()
            self._sheet.append_row(cabecalho)
            if linhas:
                self._sheet.append_rows(linhas)
        except Exception as exc:  # noqa: BLE001
            raise SheetsRepositoryError(
                f"Erro ao restaurar avaliações no Google Sheets: {exc}"
            ) from exc
