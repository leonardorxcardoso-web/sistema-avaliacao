import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# CONFIGURAÇÃO DE ADMINISTRADORES
# ==========================================
ADMINISTRADORES = [
    'leonardo.cardoso@fgv.br',
    'admin@fgv.br'
]

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Sistema de Avaliação FGV", page_icon="🎓", layout="centered")

# --- ESTILIZAÇÃO VISUAL CUSTOMIZADA (CSS) ---
st.markdown("""
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
""", unsafe_allow_html=True)

def exibir_logo():
    if os.path.exists("logo_fgv.png"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("logo_fgv.png", use_container_width=True)
        st.write("")

# ==========================================
# 1. LENDO A SUA PLANILHA REAL DE COLABORADORES
# ==========================================
def carregar_dados_base():
    df_colaboradores = pd.read_excel('Base.xlsx', sheet_name='Colaboradores')
    df_funcionarios = pd.read_excel('Base.xlsx', sheet_name='Funcionarios')
    
    df_colaboradores.columns = df_colaboradores.columns.str.strip()
    df_funcionarios.columns = df_funcionarios.columns.str.strip()
    
    return df_colaboradores, df_funcionarios

df_colaboradores, df_funcionarios = carregar_dados_base()

# ==========================================
# 2. CONEXÃO COM O GOOGLE SHEETS (AVALIAÇÕES)
# ==========================================
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Se estiver rodando local no PC com o arquivo credenciais.json
    if os.path.exists('credenciais.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', scope)
    else:
        # Se estiver rodando na nuvem do Streamlit, puxa dos segredos institucionais
        import json
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
    client = gspread.authorize(creds)
    sheet = client.open("Avaliacoes_Salvas").sheet1
    return sheet

# Inicializando e carregando os dados do Google Sheets para o Session State
if 'df_avaliacoes' not in st.session_state:
    try:
        sheet = conectar_google_sheets()
        dados = sheet.get_all_records()
        if dados:
            df_temp = pd.DataFrame(dados)
            if 'Certame' not in df_temp.columns:
                df_temp['Certame'] = 'ENARE'
            st.session_state.df_avaliacoes = df_temp
        else:
            st.session_state.df_avaliacoes = pd.DataFrame(columns=[
                'Data', 'Certame', 'Email_Avaliador', 'ID_Colaborador', 'Nome_Colaborador', 
                'Pontualidade_Aeroporto', 'Pontualidade_Local', 
                'Proatividade_Ocorrencias', 'Proatividade_Lancamentos', 'Proatividade_Respostas',
                'Resolucao_Problemas', 'Observacoes'
            ])
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.session_state.df_avaliacoes = pd.DataFrame(columns=[
            'Data', 'Certame', 'Email_Avaliador', 'ID_Colaborador', 'Nome_Colaborador', 
            'Pontualidade_Aeroporto', 'Pontualidade_Local', 
            'Proatividade_Ocorrencias', 'Proatividade_Lancamentos', 'Proatividade_Respostas',
            'Resolucao_Problemas', 'Observacoes'
        ])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# ==========================================
# TELA DE LOGIN
# ==========================================
if not st.session_state.logado:
    st.write("")
    st.write("")
    exibir_logo()
    
    st.markdown("<div class='title-box'>Portal do Avaliador</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle-box'>Acesso aos Projetos e Gestão de Colaboradores</div>", unsafe_allow_html=True)
    
    with st.container():
        email_input = st.text_input("E-mail corporativo:", placeholder="Digite seu e-mail da FGV...")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.write("")
            entrar = st.button("Acessar Plataforma", use_container_width=True, type="primary")
            
        if entrar:
            email_limpo = email_input.strip().lower()
            df_funcionarios['Email'] = df_funcionarios['Email'].astype(str).str.strip().str.lower()
            
            if email_limpo in df_funcionarios['Email'].values:
                st.session_state.logado = True
                st.session_state.email = email_limpo
                
                regiao_usuario = df_funcionarios.loc[df_funcionarios['Email'] == email_limpo, 'Regiao'].values[0]
                st.session_state.regiao = regiao_usuario
                st.rerun()
            else:
                st.error("Credenciais inválidas. Verifique seu e-mail e tente novamente.")

# ==========================================
# SISTEMA PRINCIPAL LOGADO
# ==========================================
else:
    exibir_logo()
    
    eh_admin = st.session_state.email in [email.lower() for email in ADMINISTRADORES]
    
    with st.container():
        col_user, col_btn = st.columns([4, 1])
        with col_user:
            perfil_txt = "🛡️ Administrador" if eh_admin else "👤 Avaliador"
            st.info(f"**{perfil_txt}:** {st.session_state.email} | **Região de Atuação:** {st.session_state.regiao}")
        with col_btn:
            if st.button("Sair / Logout", use_container_width=True):
                st.session_state.logado = False
                st.rerun()

    st.write("")

    if eh_admin:
        aba1, aba2 = st.tabs(["📝 Realizar Avaliação", "📊 Dashboard Admin (Histórico)"])
        container_avaliacao = aba1
        container_dashboard = aba2
    else:
        container_avaliacao = st.container()

    # ---------------------------------------------------------
    # TELA DE AVALIAÇÃO
    # ---------------------------------------------------------
    with container_avaliacao:
        if pd.isna(st.session_state.regiao) or st.session_state.regiao == '':
            colaboradores_filtrados = df_colaboradores.copy()
        else:
            regiao_user_limpa = str(st.session_state.regiao).strip().lower()
            df_colaboradores['Regiao_Limpa'] = df_colaboradores['Regiao'].astype(str).str.strip().str.lower()
            colaboradores_filtrados = df_colaboradores[df_colaboradores['Regiao_Limpa'] == regiao_user_limpa].copy()

        if colaboradores_filtrados.empty:
            st.warning(f"Nenhum colaborador encontrado para a região '{st.session_state.regiao}'.")
        else:
            if not st.session_state.df_avaliacoes.empty and 'Email_Avaliador' in st.session_state.df_avaliacoes.columns:
                 avaliacoes_do_usuario = st.session_state.df_avaliacoes[
                     st.session_state.df_avaliacoes['Email_Avaliador'] == st.session_state.email
                 ]
                 ids_ja_avaliados = avaliacoes_do_usuario['ID_Colaborador'].tolist()
            else:
                 avaliacoes_do_usuario = pd.DataFrame()
                 ids_ja_avaliados = []

            colaboradores_pendentes = colaboradores_filtrados[~colaboradores_filtrados['ID'].isin(ids_ja_avaliados)]
            
            if colaboradores_pendentes.empty:
                st.success("✅ **Excelente trabalho!** Todas as avaliações da sua região foram concluídas com sucesso.")
                st.balloons()
            else:
                st.markdown("### Configuração da Avaliação")
                
                certame_selecionado = st.selectbox(
                    "Qual certame/projeto você está avaliando agora?", 
                    ["ENARE", "CFC", "OAB", "Outro..."]
                )
                if certame_selecionado == "Outro...":
                    certame_selecionado = st.text_input("Digite o nome do certame:")

                opcoes_colaboradores = dict(zip(colaboradores_pendentes['Nome'], colaboradores_pendentes['ID']))
                colaborador_selecionado = st.selectbox(
                    "Selecione o colaborador que atuou na sua região:",
                    options=list(opcoes_colaboradores.keys())
                )
                id_selecionado = opcoes_colaboradores.get(colaborador_selecionado)

                # FORMULÁRIO DE AVALIAÇÃO
                with st.form("form_avaliacao", clear_on_submit=True):
                    
                    st.caption("💡 Escala de avaliação: 1 estrela (Insatisfatório) a 5 estrelas (Excelente)")
                    
                    st.markdown("<div class='sessao-header'>🕐 Avaliação de Pontualidade</div>", unsafe_allow_html=True)
                    pont_aeroporto = st.radio("Chegada no aeroporto", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                    st.write("")
                    pont_local = st.radio("Chegada no local de aplicação", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                    
                    st.markdown("<div class='sessao-header'>⚡ Avaliação de Proatividade</div>", unsafe_allow_html=True)
                    proat_ocorrencias = st.radio("Ocorrências", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                    st.write("")
                    proat_lancamentos = st.radio("Lançamentos", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                    st.write("")
                    proat_respostas = st.radio("Respostas no grupo", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                    
                    st.markdown("<div class='sessao-header'>🛠️ Resolução de Problemas</div>", unsafe_allow_html=True)
                    resolucao = st.radio("Grau de resolutividade do colaborador", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                    
                    st.markdown("<div class='sessao-header'>📝 Observações Qualitativas</div>", unsafe_allow_html=True)
                    observacoes = st.text_area("Insira recomendações, incidentes ou elogios (Opcional):", height=100)
                    
                    st.write("")
                    submit = st.form_submit_button("Gravar Avaliação no Sistema", type="primary", use_container_width=True)
                    
                    if submit:
                        try:
                            # Salva direto no Google Sheets em tempo real
                            sheet = conectar_google_sheets()
                            nova_linha = [
                                datetime.now().strftime("%d/%m/%Y %H:%M"),
                                certame_selecionado, 
                                st.session_state.email,
                                str(id_selecionado),
                                colaborador_selecionado,
                                int(pont_aeroporto),
                                int(pont_local),
                                int(proat_ocorrencias),
                                int(proat_lancamentos),
                                int(proat_respostas),
                                int(resolucao),
                                observacoes
                            ]
                            sheet.append_row(nova_linha)
                            
                            # Atualiza a session_state local para refletir na hora sem precisar recarregar tudo
                            nova_avaliacao = pd.DataFrame([{
                                'Data': datetime.now().strftime("%d/%m/%Y %H:%M"),
                                'Certame': certame_selecionado, 
                                'Email_Avaliador': st.session_state.email,
                                'ID_Colaborador': id_selecionado,
                                'Nome_Colaborador': colaborador_selecionado,
                                'Pontualidade_Aeroporto': pont_aeroporto,
                                'Pontualidade_Local': pont_local,
                                'Proatividade_Ocorrencias': proat_ocorrencias,
                                'Proatividade_Lancamentos': proat_lancamentos,
                                'Proatividade_Respostas': proat_respostas,
                                'Resolucao_Problemas': resolucao,
                                'Observacoes': observacoes
                            }])
                            st.session_state.df_avaliacoes = pd.concat([st.session_state.df_avaliacoes, nova_avaliacao], ignore_index=True)
                            
                            st.success("Avaliação registrada com sucesso na nuvem!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar no Google Sheets: {e}")

            # SEÇÃO DE RESTAURAÇÃO
            if not avaliacoes_do_usuario.empty:
                st.write("")
                with st.expander("🔄 Precisa corrigir alguma avaliação já enviada?"):
                    st.write("Selecione o colaborador abaixo para anular a nota anterior e avaliá-lo novamente.")
                    opcoes_avaliados = dict(zip(avaliacoes_do_usuario['Nome_Colaborador'], avaliacoes_do_usuario['ID_Colaborador']))
                    colaborador_restaurar = st.selectbox("Colaborador:", options=list(opcoes_avaliados.keys()), key="select_restaurar")
                    id_restaurar = opcoes_avaliados.get(colaborador_restaurar)
                    
                    if st.button("Anular e Restaurar Colaborador"):
                        try:
                            # Reconstrói a base tirando a linha correspondente
                            mask = ~((st.session_state.df_avaliacoes['Email_Avaliador'] == st.session_state.email) & 
                                     (st.session_state.df_avaliacoes['ID_Colaborador'] == id_restaurar))
                            st.session_state.df_avaliacoes = st.session_state.df_avaliacoes[mask]
                            
                            # Atualiza a planilha do Google Sheets reescrevendo os dados limpos
                            sheet = conectar_google_sheets()
                            sheet.clear() # Limpa tudo
                            # Recria o cabeçalho e reinsere os dados atualizados
                            cabecalho = list(st.session_state.df_avaliacoes.columns)
                            linhas = st.session_state.df_avaliacoes.values.tolist()
                            sheet.append_row(cabecalho)
                            if linhas:
                                sheet.append_rows(linhas)
                                
                            st.success("Colaborador restaurado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao restaurar no Google Sheets: {e}")

    # ---------------------------------------------------------
    # TELA DE DASHBOARD ADMIN
    # ---------------------------------------------------------
    if eh_admin:
        with container_dashboard:
            st.markdown("### Histórico Institucional de Desempenho")
            
            if st.session_state.df_avaliacoes.empty:
                st.info("Ainda não há avaliações registradas no sistema.")
            else:
                df_historico = st.session_state.df_avaliacoes.copy()
                
                if 'Certame' not in df_historico.columns:
                    df_historico['Certame'] = 'ENARE'
                df_historico['Certame'] = df_historico['Certame'].fillna('ENARE')
                
                lista_certames = df_historico['Certame'].unique().tolist()
                
                col_filtro1, col_filtro2 = st.columns([1, 2])
                with col_filtro1:
                    filtro_certame = st.selectbox("Filtrar por Projeto:", ["Todos (Histórico Completo)"] + lista_certames)
                
                if filtro_certame != "Todos (Histórico Completo)":
                    df_historico = df_historico[df_historico['Certame'] == filtro_certame]
                
                if df_historico.empty:
                    st.warning("Nenhuma avaliação encontrada para este certame.")
                else:
                    colunas_notas = [
                        'Pontualidade_Aeroporto', 'Pontualidade_Local', 
                        'Proatividade_Ocorrencias', 'Proatividade_Lancamentos', 
                        'Proatividade_Respostas', 'Resolucao_Problemas'
                    ]
                    
                    df_historico[colunas_notas] = df_historico[colunas_notas].apply(pd.to_numeric, errors='coerce')
                    df_historico['Nota_Geral_Projeto'] = df_historico[colunas_notas].mean(axis=1)
                    
                    df_medias = df_historico.groupby(['ID_Colaborador', 'Nome_Colaborador'])[colunas_notas + ['Nota_Geral_Projeto']].mean().reset_index()
                    
                    with col_filtro2:
                        pesquisa = st.selectbox("Buscar painel individual:", options=["📊 Visão Geral (Ranking)"] + df_medias['Nome_Colaborador'].tolist())
                    
                    st.markdown("---")
                    
                    if pesquisa != "📊 Visão Geral (Ranking)":
                        dados_colab = df_medias[df_medias['Nome_Colaborador'] == pesquisa].iloc[0]
                        
                        st.markdown(f"<h3 style='color: #005baa;'>Desempenho: {pesquisa}</h3>", unsafe_allow_html=True)
                        st.caption(f"Dados filtrados por: **{filtro_certame}**")
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Nota Geral Média", f"{dados_colab['Nota_Geral_Projeto']:.1f} / 5.0")
                        c2.metric("Média Pontualidade", f"{dados_colab['Pontualidade_Local']:.1f}")
                        c3.metric("Média Resolutividade", f"{dados_colab['Resolucao_Problemas']:.1f}")
                        
                        st.write("")
                        st.markdown("#### Histórico de Observações")
                        obs_colab = df_historico[df_historico['Nome_Colaborador'] == pesquisa][['Data', 'Certame', 'Email_Avaliador', 'Observacoes']]
                        
                        for _, row in obs_colab.iterrows():
                            if pd.notna(row['Observacoes']) and row['Observacoes'].strip() != "":
                                st.warning(f"**Projeto:** {row['Certame']} | **Em:** {row['Data']} | **Por:** {row['Email_Avaliador']}\n\n{row['Observacoes']}")
                    
                    else:
                        st.markdown(f"#### Ranking Geral de Colaboradores ({filtro_certame})")
                        df_ranking = df_medias.sort_values(by="Nota_Geral_Projeto", ascending=False).reset_index(drop=True)
                        
                        # --- EXPORTAÇÃO PARA EXCEL ---
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df_ranking.to_excel(writer, sheet_name='Ranking_Desempenho', index=False)
                        
                        st.download_button(
                            label="📥 Baixar Relatório em Excel",
                            data=buffer.getvalue(),
                            file_name=f"Ranking_Avaliadores_{filtro_certame.replace(' ', '_')}.xlsx",
                            mime="application/vnd.ms-excel",
                            help="Clique para baixar a tabela completa abaixo em formato Excel"
                        )
                        st.write("") 
                        
                        st.dataframe(
                            df_ranking[['Nome_Colaborador', 'Nota_Geral_Projeto', 'Pontualidade_Local', 'Proatividade_Respostas', 'Resolucao_Problemas']].style.format("{:.1f}", subset=['Nota_Geral_Projeto', 'Pontualidade_Local', 'Proatividade_Respostas', 'Resolucao_Problemas']),
                            use_container_width=True
                        )
