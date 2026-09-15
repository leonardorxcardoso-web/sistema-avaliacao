"""Configuração estática da aplicação: administradores, colunas e CSS."""

ADMINISTRADORES = frozenset({
    "admin@fgv.br",
})

# Supervisores têm acesso total: avaliam colaboradores da própria região
# (cadastrada em Base.xlsx) E enxergam o Dashboard Admin — diferente de
# ADMINISTRADORES, que só vê o Dashboard.
SUPERVISORES = frozenset({
    "leonardo.cardoso@fgv.br",
})

EMAIL_AEROPORTO = "aeroporto@fgv.br"

COLUNAS_NOTAS = (
    "Pontualidade_Aeroporto",
    "Pontualidade_Local",
    "Proatividade_Ocorrencias",
    "Proatividade_Lancamentos",
    "Proatividade_Respostas",
    "Resolucao_Problemas",
    "Facilidade_Carga",
    "Resolutividade_Despacho",
)

COLUNAS_AVALIACAO = (
    "Data",
    "Certame",
    "Email_Avaliador",
    "ID_Colaborador",
    "Nome_Colaborador",
    "Pontualidade_Aeroporto",
    "Pontualidade_Local",
    "Proatividade_Ocorrencias",
    "Proatividade_Lancamentos",
    "Proatividade_Respostas",
    "Resolucao_Problemas",
    "Observacoes",
    "Facilidade_Carga",
    "Resolutividade_Despacho",
)

CERTAME_PADRAO = "ENARE"
CERTAMES_DISPONIVEIS = ("ENARE", "CFC", "OAB", "Outro...")

# Certames com aba própria de colaboradores em Base.xlsx (Colaboradores_<CERTAME>).
# "Outro..." não tem planilha própria — cai para CERTAME_PADRAO (ver BaseDados.colaboradores).
CERTAMES_COM_PLANILHA = ("ENARE", "CFC", "OAB")

CUSTOM_CSS = """
    <style>
        .title-box {
            text-align: center;
            color: #002b5c;
            font-size: 2.5em;
            font-weight: 800;
            margin-bottom: 0px;
        }
        .subtitle-box {
            text-align: center;
            color: #005baa;
            font-size: 1.1em;
            margin-bottom: 30px;
        }
        .sessao-header {
            background: linear-gradient(90deg, #002b5c 0%, #005baa 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.2em;
            margin-top: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        div[data-testid="metric-container"] {
            background-color: #ffffff;
            border-left: 5px solid #005baa;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
"""
