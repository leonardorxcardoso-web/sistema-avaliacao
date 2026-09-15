"""Modelos Pydantic de entrada/saída da API."""

from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str


class LoginResponse(BaseModel):
    email: str
    nome: str
    regiao: str
    eh_admin: bool
    eh_aeroporto: bool = False
    eh_supervisor: bool = False
    pode_avaliar: bool = True
    pode_ver_dashboard: bool = False


class AvaliacaoSubmitRequest(BaseModel):
    """Campos do formulário de avaliação local. Usado quando o avaliador não
    é da equipe aeroporto — ver AvaliacaoAeroportoSubmitRequest para o outro
    formulário."""

    certame: str
    id_colaborador: str
    nome_colaborador: str
    pontualidade_local: int = Field(ge=1, le=5)
    proatividade_ocorrencias: int = Field(ge=1, le=5)
    proatividade_lancamentos: int = Field(ge=1, le=5)
    proatividade_respostas: int = Field(ge=1, le=5)
    resolucao_problemas: int = Field(ge=1, le=5)
    observacoes: Optional[str] = ""


class AvaliacaoAeroportoSubmitRequest(BaseModel):
    """Campos do formulário de avaliação da equipe aeroporto."""

    certame: str
    id_colaborador: str
    nome_colaborador: str
    pontualidade_aeroporto: int = Field(ge=1, le=5)
    facilidade_carga: int = Field(ge=1, le=5)
    resolutividade_despacho: int = Field(ge=1, le=5)
    observacoes: Optional[str] = ""


class RestaurarRequest(BaseModel):
    certame: str
    id_colaborador: str
