# Sistema de Avaliação FGV

Portal para avaliação de colaboradores por certame/projeto, com painel administrativo
de acompanhamento.

- **App oficial (FastAPI)**: `webapp/` — é o que deve ser usado.
- `app.py` (Streamlit) é uma versão legada, **desatualizada** em relação às
  regras de negócio atuais (perfis, formulário por certame). Não rodar em produção.

## Pré-requisitos

- Python 3.9 ou superior
- (Opcional) Credenciais de uma Service Account do Google com acesso à planilha
  `Avaliacoes_Salvas` no Google Sheets — sem isso o app funciona normalmente,
  mas não salva/carrega avaliações.

## Instalação

```bash
cd sistema-avaliacao
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configurando o Google Sheets (opcional)

1. Crie uma Service Account no Google Cloud e baixe o JSON de credenciais.
2. Compartilhe a planilha `Avaliacoes_Salvas` no Google Sheets com o e-mail da
   Service Account.
3. Salve o JSON como `credenciais.json` na raiz do projeto (mesmo nível de `app.py`).

Sem esse arquivo, o app roda normalmente mas mostra um aviso de que não
conseguiu conectar ao Sheets — as telas de login e avaliação continuam
funcionando para navegação/teste.

## Rodando o app

```bash
source venv/bin/activate
uvicorn webapp.backend.main:app --reload --port 8000
```

Acesse **http://localhost:8000**.

## Perfis de login

O login é feito só por e-mail (sem senha). Existem quatro tipos de perfil:

| Perfil | Acesso | Como reconhecer |
|---|---|---|
| Administrador | Só Dashboard (não avalia) | e-mail em `ADMINISTRADORES` (`src/config.py`) |
| Supervisor | Avalia (região própria) + Dashboard | e-mail em `SUPERVISORES`, cadastrado em `Funcionarios` |
| Equipe Aeroporto | Só avalia (visão global, formulário próprio) | `aeroporto@fgv.br` (`EMAIL_AEROPORTO`) |
| Avaliador | Só avalia (região própria) | qualquer e-mail cadastrado em `Funcionarios` |

E-mails de teste já cadastrados em `Base.xlsx` (aba `Funcionarios`):

- `syllas.alves@fgv.br` — Nordeste
- `allana.glauco@fgv.br` — Centro-Oeste
- `leonardo.cardoso@fgv.br` — Sudeste (supervisor: avalia + Dashboard)
- `valtricia.bertinato@fgv.br` — Sul
- `tiago.aveiro@fgv.br` — Norte
- `admin@fgv.br` — administrador (só Dashboard)
- `aeroporto@fgv.br` — equipe aeroporto (visão global, formulário próprio)

## Colaboradores por certame

Cada certame (ENARE, CFC, OAB...) tem sua **própria** aba de colaboradores em
`Base.xlsx`, porque a lista de colaboradores e suas regiões pode variar de um
certame para outro:

```
Colaboradores_ENARE
Colaboradores_CFC
Colaboradores_OAB
Funcionarios
```

Todas as abas `Colaboradores_<CERTAME>` têm as mesmas colunas: `ID`, `Uf`,
`Municipio`, `Regiao`, `Nome`, `Local`. Um certame sem planilha própria (ex.:
"Outro..." digitado livre na tela de avaliação) cai para a planilha do
certame padrão (`ENARE`).

Para adicionar um novo certame com planilha própria:
1. Criar a aba `Colaboradores_<NOME_DO_CERTAME>` em `Base.xlsx` com as mesmas colunas.
2. Adicionar `<NOME_DO_CERTAME>` em `CERTAMES_COM_PLANILHA` (`src/config.py`).
3. Adicionar a opção no seletor de certame do frontend (`webapp/frontend/index.html`, `<select id="select-certame">`).

A aba `Funcionarios` (login/avaliadores) é única e não varia por certame.

## Estrutura do projeto

```
app.py                   # versão Streamlit legada (não usar)
src/                      # lógica de negócio compartilhada (auth, dados, Sheets)
webapp/
  backend/                # API FastAPI (reaproveita src/)
  frontend/                # HTML/CSS/JS servido pelo FastAPI
Base.xlsx                 # base local: Colaboradores_<CERTAME> + Funcionarios
logo_fgv.png               # logo usada nas telas
```
