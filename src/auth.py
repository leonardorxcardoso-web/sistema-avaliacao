"""Autenticação simples por e-mail cadastrado na base de funcionários."""

from dataclasses import dataclass
from typing import Optional, Union

from src.config import ADMINISTRADORES, EMAIL_AEROPORTO, SUPERVISORES
from src.data import BaseDados


@dataclass(frozen=True)
class Sessao:
    email: str
    nome: str
    regiao: Union[str, float]
    eh_admin: bool
    eh_aeroporto: bool = False
    eh_supervisor: bool = False

    @property
    def pode_avaliar(self) -> bool:
        """Administradores puros não avaliam; todos os outros perfis sim."""
        return not self.eh_admin

    @property
    def pode_ver_dashboard(self) -> bool:
        """Administradores e supervisores enxergam o Dashboard Admin."""
        return self.eh_admin or self.eh_supervisor


def autenticar(base: BaseDados, email_digitado: str) -> Optional[Sessao]:
    """Retorna a Sessao do usuário se o e-mail for reconhecido, senão None.

    Ordem de checagem:
    1. Administrador (só Dashboard, visão global, não precisa estar em
       Funcionarios).
    2. Equipe aeroporto (só avalia, visão global, formulário próprio).
    3. Funcionário cadastrado em Funcionarios (região específica) — se o
       e-mail também estiver em SUPERVISORES, ganha acesso ao Dashboard
       além de continuar avaliando normalmente.
    """
    email_limpo = email_digitado.strip().lower()
    if not email_limpo:
        return None

    if email_limpo in ADMINISTRADORES:
        return Sessao(
            email=email_limpo,
            nome="Administrador",
            regiao="Visão Global (Admin)",
            eh_admin=True,
        )

    if email_limpo == EMAIL_AEROPORTO.lower():
        return Sessao(
            email=email_limpo,
            nome="Equipe Aeroporto",
            regiao="Todas (Logística Aeroporto)",
            eh_admin=False,
            eh_aeroporto=True,
        )

    linha = base.funcionarios.loc[base.funcionarios["Email"] == email_limpo]
    if linha.empty:
        return None

    nome = str(linha["Nome"].values[0]).strip()
    regiao = linha["Regiao"].values[0]
    eh_supervisor = email_limpo in SUPERVISORES
    return Sessao(
        email=email_limpo, nome=nome, regiao=regiao, eh_admin=False, eh_supervisor=eh_supervisor
    )
