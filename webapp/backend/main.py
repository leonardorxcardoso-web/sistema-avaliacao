"""API do Sistema de Avaliação FGV — reaproveita as regras de negócio de src/.

Endpoints REST equivalentes às telas do app Streamlit original: login,
avaliação de colaboradores e dashboard administrativo.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.auth import autenticar
from src.avaliacao_service import (
    NovaAvaliacao,
    avaliacoes_do_avaliador,
    calcular_medias_por_colaborador,
    colaboradores_pendentes,
    registrar_avaliacao,
    restaurar_colaborador,
)
from src.config import CERTAME_PADRAO
from src.data import colaboradores_por_regiao
from src.sheets_repository import SheetsRepository, SheetsRepositoryError

from webapp.backend.schemas import (
    AvaliacaoAeroportoSubmitRequest,
    AvaliacaoSubmitRequest,
    LoginRequest,
    LoginResponse,
    RestaurarRequest,
)
from webapp.backend.session import (
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    criar_cookie_valor,
    ler_email_do_cookie,
)
from webapp.backend.state import estado

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def _df_para_records(df) -> list:
    """Converte DataFrame em list[dict] seguro para JSON.

    NaN/NaT/Inf não são JSON-compliant (json.dumps padrão rejeita), e
    aparecem com frequência em colunas de planilha carregadas do Sheets.
    Convertemos para None antes de serializar.
    """
    import numpy as np
    import pandas as pd

    df_limpo = df.replace([np.inf, -np.inf], None)
    df_limpo = df_limpo.where(pd.notna(df_limpo), None)
    return df_limpo.to_dict("records")

app = FastAPI(title="Sistema de Avaliação FGV")

_origens_extra = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", *_origens_extra],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sessao_atual(sessao_cookie: Optional[str]) -> dict:
    email = ler_email_do_cookie(sessao_cookie)
    if email is None:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")

    sessao = autenticar(estado.base, email)
    if sessao is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")

    return {
        "email": sessao.email,
        "nome": sessao.nome,
        "regiao": sessao.regiao,
        "eh_admin": sessao.eh_admin,
        "eh_aeroporto": sessao.eh_aeroporto,
        "eh_supervisor": sessao.eh_supervisor,
        "pode_avaliar": sessao.pode_avaliar,
        "pode_ver_dashboard": sessao.pode_ver_dashboard,
    }


def _regiao_como_texto(regiao) -> str:
    import pandas as pd

    if pd.isna(regiao) or regiao == "":
        return ""
    texto = str(regiao).strip()
    # Regiões cadastradas em Base.xlsx são siglas curtas (SUDESTE, NORTE...);
    # descrições especiais (admin/aeroporto) já vêm formatadas e não devem
    # ser forçadas para maiúsculo.
    return texto.upper() if texto.isupper() or texto.islower() else texto


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response):
    sessao = autenticar(estado.base, payload.email)
    if sessao is None:
        raise HTTPException(status_code=401, detail="Credenciais inválidas. Verifique seu e-mail e tente novamente.")

    response.set_cookie(
        key=COOKIE_NAME,
        value=criar_cookie_valor(sessao.email),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
    )
    return LoginResponse(
        email=sessao.email,
        nome=sessao.nome,
        regiao=_regiao_como_texto(sessao.regiao),
        eh_admin=sessao.eh_admin,
        eh_aeroporto=sessao.eh_aeroporto,
        eh_supervisor=sessao.eh_supervisor,
        pode_avaliar=sessao.pode_avaliar,
        pode_ver_dashboard=sessao.pode_ver_dashboard,
    )


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@app.get("/api/me", response_model=LoginResponse)
def me(sessao_avaliador: Optional[str] = Cookie(default=None)):
    sessao = _sessao_atual(sessao_avaliador)
    return LoginResponse(
        email=sessao["email"],
        nome=sessao["nome"],
        regiao=_regiao_como_texto(sessao["regiao"]),
        eh_admin=sessao["eh_admin"],
        eh_aeroporto=sessao["eh_aeroporto"],
        eh_supervisor=sessao["eh_supervisor"],
        pode_avaliar=sessao["pode_avaliar"],
        pode_ver_dashboard=sessao["pode_ver_dashboard"],
    )


# ---------------------------------------------------------------------------
# Avaliação
# ---------------------------------------------------------------------------

@app.get("/api/avaliacoes/status")
def status_avaliacao(
    certame: str = CERTAME_PADRAO, sessao_avaliador: Optional[str] = Cookie(default=None)
):
    """Estado consolidado da tela de avaliação: colaboradores da região,
    quais já foram avaliados pelo usuário e quais ainda estão pendentes —
    evita o frontend precisar inferir "região vazia" vs. "tudo avaliado"
    combinando múltiplas chamadas.

    A lista de colaboradores/regiões varia por certame (cada certame tem sua
    própria aba em Base.xlsx), então `certame` é obrigatório para saber qual
    planilha consultar.

    Administradores puros não avaliam (só têm acesso ao Dashboard)."""
    sessao = _sessao_atual(sessao_avaliador)
    if not sessao["pode_avaliar"]:
        raise HTTPException(status_code=403, detail="Este perfil não realiza avaliações.")

    import pandas as pd

    colaboradores_regiao = colaboradores_por_regiao(
        estado.base, certame, sessao["regiao"], ver_todos=sessao["eh_aeroporto"]
    )
    avaliacoes_usuario = avaliacoes_do_avaliador(estado.df_avaliacoes, sessao["email"])

    # IDs de colaborador não são globalmente únicos entre certames (cada
    # certame tem sua própria planilha), então "pendente" só pode ser
    # calculado comparando com avaliações do MESMO certame — senão um ID já
    # avaliado no ENARE apareceria erroneamente como concluído no CFC.
    avaliacoes_do_certame = (
        avaliacoes_usuario[avaliacoes_usuario["Certame"] == certame]
        if "Certame" in avaliacoes_usuario.columns
        else avaliacoes_usuario
    )
    pendentes = colaboradores_pendentes(colaboradores_regiao, avaliacoes_do_certame)

    return {
        "regiao_vazia": colaboradores_regiao.empty,
        "eh_aeroporto": sessao["eh_aeroporto"],
        "pendentes": [
            {"id": str(row["ID"]), "nome": row["Nome"]}
            for _, row in pendentes.iterrows()
            if pd.notna(row["Nome"])
        ],
        "minhas_avaliacoes": _df_para_records(
            avaliacoes_do_certame[["ID_Colaborador", "Nome_Colaborador"]].drop_duplicates()
        ),
    }


@app.post("/api/avaliacoes")
def criar_avaliacao(
    payload: AvaliacaoSubmitRequest, sessao_avaliador: Optional[str] = Cookie(default=None)
):
    """Grava avaliação do formulário local (avaliador de região)."""
    sessao = _sessao_atual(sessao_avaliador)
    if not sessao["pode_avaliar"]:
        raise HTTPException(status_code=403, detail="Este perfil não realiza avaliações.")
    if sessao["eh_aeroporto"]:
        raise HTTPException(
            status_code=403, detail="Use o formulário de avaliação da equipe aeroporto."
        )

    nova = NovaAvaliacao(
        certame=payload.certame,
        email_avaliador=sessao["email"],
        id_colaborador=payload.id_colaborador,
        nome_colaborador=payload.nome_colaborador,
        eh_aeroporto=False,
        pontualidade_local=payload.pontualidade_local,
        proatividade_ocorrencias=payload.proatividade_ocorrencias,
        proatividade_lancamentos=payload.proatividade_lancamentos,
        proatividade_respostas=payload.proatividade_respostas,
        resolucao_problemas=payload.resolucao_problemas,
        observacoes=payload.observacoes or "",
    )

    erro = nova.validar()
    if erro:
        raise HTTPException(status_code=422, detail=erro)

    try:
        repo = SheetsRepository.conectar()
        estado.df_avaliacoes = registrar_avaliacao(repo, estado.df_avaliacoes, nova)
    except SheetsRepositoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"ok": True}


@app.post("/api/avaliacoes/aeroporto")
def criar_avaliacao_aeroporto(
    payload: AvaliacaoAeroportoSubmitRequest, sessao_avaliador: Optional[str] = Cookie(default=None)
):
    """Grava avaliação do formulário da equipe aeroporto."""
    sessao = _sessao_atual(sessao_avaliador)
    if not sessao["eh_aeroporto"]:
        raise HTTPException(
            status_code=403, detail="Endpoint restrito à equipe aeroporto."
        )

    nova = NovaAvaliacao(
        certame=payload.certame,
        email_avaliador=sessao["email"],
        id_colaborador=payload.id_colaborador,
        nome_colaborador=payload.nome_colaborador,
        eh_aeroporto=True,
        pontualidade_aeroporto=payload.pontualidade_aeroporto,
        facilidade_carga=payload.facilidade_carga,
        resolutividade_despacho=payload.resolutividade_despacho,
        observacoes=payload.observacoes or "",
    )

    erro = nova.validar()
    if erro:
        raise HTTPException(status_code=422, detail=erro)

    try:
        repo = SheetsRepository.conectar()
        estado.df_avaliacoes = registrar_avaliacao(repo, estado.df_avaliacoes, nova)
    except SheetsRepositoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"ok": True}


@app.post("/api/avaliacoes/restaurar")
def restaurar(payload: RestaurarRequest, sessao_avaliador: Optional[str] = Cookie(default=None)):
    sessao = _sessao_atual(sessao_avaliador)

    try:
        repo = SheetsRepository.conectar()
        estado.df_avaliacoes = restaurar_colaborador(
            repo, estado.df_avaliacoes, sessao["email"], payload.certame, payload.id_colaborador
        )
    except SheetsRepositoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"ok": True}


# ---------------------------------------------------------------------------
# Dashboard admin
# ---------------------------------------------------------------------------

@app.get("/api/dashboard/certames")
def listar_certames(sessao_avaliador: Optional[str] = Cookie(default=None)):
    sessao = _sessao_atual(sessao_avaliador)
    if not sessao["pode_ver_dashboard"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")

    df = estado.df_avaliacoes.copy()
    if df.empty:
        return []
    if "Certame" not in df.columns:
        df["Certame"] = CERTAME_PADRAO
    return df["Certame"].fillna(CERTAME_PADRAO).unique().tolist()


@app.get("/api/dashboard/ranking")
def ranking(certame: Optional[str] = None, sessao_avaliador: Optional[str] = Cookie(default=None)):
    sessao = _sessao_atual(sessao_avaliador)
    if not sessao["pode_ver_dashboard"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")

    df = estado.df_avaliacoes.copy()
    if df.empty:
        return []
    if "Certame" not in df.columns:
        df["Certame"] = CERTAME_PADRAO
    df["Certame"] = df["Certame"].fillna(CERTAME_PADRAO)

    if certame:
        df = df[df["Certame"] == certame]
    if df.empty:
        return []

    df_medias = calcular_medias_por_colaborador(df)
    df_ranking = df_medias.sort_values(by="Nota_Geral_Projeto", ascending=False)
    return _df_para_records(df_ranking.round(2))


@app.get("/api/dashboard/colaborador/{nome_colaborador}/observacoes")
def observacoes_colaborador(
    nome_colaborador: str, certame: Optional[str] = None, sessao_avaliador: Optional[str] = Cookie(default=None)
):
    sessao = _sessao_atual(sessao_avaliador)
    if not sessao["pode_ver_dashboard"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")

    import pandas as pd

    df = estado.df_avaliacoes.copy()
    if "Certame" not in df.columns:
        df["Certame"] = CERTAME_PADRAO
    df["Certame"] = df["Certame"].fillna(CERTAME_PADRAO)
    if certame:
        df = df[df["Certame"] == certame]

    obs = df[df["Nome_Colaborador"] == nome_colaborador][
        ["Data", "Certame", "Email_Avaliador", "Observacoes"]
    ]
    obs = obs[obs["Observacoes"].apply(lambda v: pd.notna(v) and str(v).strip() != "")]
    return _df_para_records(obs)


@app.get("/api/dashboard/export")
def exportar_excel(certame: Optional[str] = None, sessao_avaliador: Optional[str] = Cookie(default=None)):
    sessao = _sessao_atual(sessao_avaliador)
    if not sessao["pode_ver_dashboard"]:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores.")

    import io

    import pandas as pd

    df = estado.df_avaliacoes.copy()
    if df.empty:
        raise HTTPException(status_code=404, detail="Nenhuma avaliação registrada para exportar.")
    if "Certame" not in df.columns:
        df["Certame"] = CERTAME_PADRAO
    df["Certame"] = df["Certame"].fillna(CERTAME_PADRAO)
    if certame:
        df = df[df["Certame"] == certame]

    df_medias = calcular_medias_por_colaborador(df)
    df_ranking = df_medias.sort_values(by="Nota_Geral_Projeto", ascending=False)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_ranking.to_excel(writer, sheet_name="Ranking_Desempenho", index=False)
    buffer.seek(0)

    nome_arquivo = f"Ranking_Avaliadores_{(certame or 'Todos').replace(' ', '_')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


# ---------------------------------------------------------------------------
# Frontend estático
# ---------------------------------------------------------------------------

app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")
