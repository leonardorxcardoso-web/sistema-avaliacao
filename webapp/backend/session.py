"""Sessão de login via cookie assinado (stateless, sem tabela de sessões).

O cookie carrega o e-mail autenticado; região/perfil admin são sempre
recalculados a partir da base local a cada requisição, então mesmo que o
cookie seja replayed depois de uma mudança de cadastro, os dados nunca ficam
desatualizados.
"""

import os
from typing import Optional

from itsdangerous import BadSignature, URLSafeTimedSerializer

_SECRET_KEY = os.environ.get("SESSION_SECRET_KEY", "dev-secret-troque-em-producao")
_COOKIE_NAME = "sessao_avaliador"
_MAX_IDADE_SEGUNDOS = 8 * 60 * 60  # 8h

_serializer = URLSafeTimedSerializer(_SECRET_KEY, salt="sistema-avaliacao-fgv")


def criar_cookie_valor(email: str) -> str:
    return _serializer.dumps({"email": email})


def ler_email_do_cookie(valor_cookie: Optional[str]) -> Optional[str]:
    if not valor_cookie:
        return None
    try:
        dados = _serializer.loads(valor_cookie, max_age=_MAX_IDADE_SEGUNDOS)
    except BadSignature:
        return None
    return dados.get("email")


COOKIE_NAME = _COOKIE_NAME
COOKIE_MAX_AGE = _MAX_IDADE_SEGUNDOS
