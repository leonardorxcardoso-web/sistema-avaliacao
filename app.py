import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# CONFIGURAÇÕES DE ACESSO
# ==========================================
ADMINISTRADORES = [
    'leonardo.cardoso@fgv.br',
    'admin@fgv.br'
]

EMAIL_AEROPORTO = 'aeroporto@fgv.br'

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E CSS
# ==========================================
st.set_page_config(page_title="Sistema de Avaliação FGV", page_icon="🎓", layout="centered")

st.markdown("""
    <style>
        .title-box { text-align: center; color: #002b5c; font-size: 2.5em; font-weight: 800; margin-bottom: 0px; }
        .subtitle-box { text-align: center; color: #005baa; font-size: 1.1em; margin-bottom: 30px; }
        .sessao-header {
            background: linear-gradient(90deg, #002b5c 0%, #005baa 100%); color: white; padding: 10px 20px;
            border-radius: 8px; font-weight: bold; font-size: 1.2em; margin-top: 20px; margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .sessao-aeroporto {
            background: linear-gradient(90deg, #d35400 0%, #e67e22 100%); color: white; padding: 10px 20px;
            border-radius: 8px; font-weight: bold; font-size: 1.2em; margin-top: 20px; margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        div[data-testid="metric-container"] {
            background-color: #ffffff; border-left: 5px solid #005baa; padding: 15px;
            border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

def exibir_logo():
    if os.path.exists("logo_fgv.png"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: st.image("logo_fgv.png", use_container_width=True)
        st.write("")

# ==========================================
# 1. LENDO A PLANILHA BASE
# ==========================================
def carregar_dados_base():
    df_colaboradores = pd.read_excel('Base.xlsx', sheet_name='Colaboradores')
    df_funcionarios = pd.read_excel('Base.xlsx', sheet_name='Funcionarios')
    df_colaboradores.columns = df_colaboradores.columns.str.strip()
    df_funcionarios.columns = df_funcionarios.columns.str.strip()
    return df_colaboradores, df_funcionarios

df_colaboradores, df_funcionarios = carregar_dados_base()

# ==========================================
# 2. CONEXÃO COM O GOOGLE SHEETS
# ==========================================
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if os.path.exists('credenciais.json'):
        creds = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', scope)
    else:
        import json
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
    client = gspread.authorize(creds)
    sheet = client.open("Avaliacoes_Salvas").sheet1
    return sheet

COLUNAS_DB = [
    'Data', 'Certame', 'Email_Avaliador', 'ID_Colaborador', 'Nome_Colaborador', 
    'Pontualidade_Aeroporto', 'Pontualidade_Local', 
    'Proatividade_Ocorrencias', 'Proatividade_Lancamentos', 'Proatividade_Respostas',
    'Resolucao_Problemas', 'Observacoes', 'Facilidade_Carga', 'Resolutividade_Despacho'
]

if 'df_avaliacoes' not in st.session_state:
    try:
        sheet = conectar_google_sheets()
        dados = sheet.get_all_records()
        if dados:
            df_temp = pd.DataFrame(dados)
            if 'Certame' not in df_temp.columns: df_temp['Certame'] = 'ENARE'
            if 'Facilidade_Carga' not in df_temp.columns: df_temp['Facilidade_Carga'] = ""
            if 'Resolutividade_Despacho' not in df_temp.columns: df_temp['Resolutividade_Despacho'] = ""
            st.session_state.df_avaliacoes = df_temp
        else:
            st.session_state.df_avaliacoes = pd.DataFrame(columns=COLUNAS_DB)
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.session_state.df_avaliacoes = pd.DataFrame(columns=COLUNAS_DB)

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
            
            if email_limpo in [admin.strip().lower() for admin in ADMINISTRADORES]:
                st.session_state.logado = True
                st.session_state.email = email_limpo
                st.session_state.regiao = "Visão Global (Admin)"
                st.rerun()
                
            elif email_limpo == EMAIL_AEROPORTO.lower():
                st.session_state.logado = True
                st.session_state.email = email_limpo
                st.session_state.regiao = "Todas (Logística Aeroporto)"
                st.rerun()
                
            elif email_limpo in df_funcionarios['Email'].values:
                st.session_state.logado = True
                st.session_state.email = email_limpo
                st.session_state.regiao = df_funcionarios.loc[df_funcionarios['Email'] == email_limpo, 'Regiao'].values[0]
                st.rerun()
                
            else:
                st.error("Credenciais inválidas. Verifique seu e-mail e tente novamente.")

# ==========================================
# SISTEMA PRINCIPAL LOGADO
# ==========================================
else:
    exibir_logo()
    
    eh_admin = st.session_state.email in [email.strip().lower() for email in ADMINISTRADORES]
    eh_aeroporto = st.session_state.email == EMAIL_AEROPORTO.lower()
    
    with st.container():
        col_user, col_btn = st.columns([4, 1])
        with col_user:
            if eh_admin: perfil_txt = "🛡️ Administrador"
            elif eh_aeroporto: perfil_txt = "✈️ Equipe Aeroporto"
            else: perfil_txt = "👤 Avaliador"
            st.info(f"**{perfil_txt}:** {st.session_state.email} | **Região:** {st.session_state.regiao}")
        with col_btn:
            if st.button("Sair / Logout", use_container_width=True):
                st.session_state.logado = False
                st.rerun()

    st.write("")

    # ---------------------------------------------------------
    # TELA EXCLUSIVA DO ADMINISTRADOR (APENAS DASHBOARD)
    # ---------------------------------------------------------
    if eh_admin:
        st.markdown("### Histórico Institucional de Desempenho")
        
        if st.session_state.df_avaliacoes.empty:
            st.info("Ainda não há avaliações registradas no sistema.")
        else:
            df_historico = st.session_state.df_avaliacoes.copy()
            if 'Certame' not in df_historico.columns: df_historico['Certame'] = 'ENARE'
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
                    'Proatividade_Respostas', 'Resolucao_Problemas',
                    'Facilidade_Carga', 'Resolutividade_Despacho'
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
                    c2.metric("Média Aeroporto", f"{df_historico[df_historico['Nome_Colaborador']==pesquisa][['Pontualidade_Aeroporto', 'Facilidade_Carga', 'Resolutividade_Despacho']].mean().mean():.1f}")
                    c3.metric("Média Local/Proatividade", f"{df_historico[df_historico['Nome_Colaborador']==pesquisa][['Pontualidade_Local', 'Proatividade_Ocorrencias', 'Proatividade_Lancamentos', 'Proatividade_Respostas', 'Resolucao_Problemas']].mean().mean():.1f}")
                    
                    st.write("")
                    st.markdown("#### Histórico de Observações")
                    obs_colab = df_historico[df_historico['Nome_Colaborador'] == pesquisa][['Data', 'Certame', 'Email_Avaliador', 'Observacoes']]
                    
                    for _, row in obs_colab.iterrows():
                        if pd.notna(row['Observacoes']) and row['Observacoes'].strip() != "":
                            st.warning(f"**Projeto:** {row['Certame']} | **Em:** {row['Data']} | **Por:** {row['Email_Avaliador']}\n\n{row['Observacoes']}")
                
                else:
                    st.markdown(f"#### Ranking Geral de Colaboradores ({filtro_certame})")
                    df_ranking = df_medias.sort_values(by="Nota_Geral_Projeto", ascending=False).reset_index(drop=True)
                    
                    colunas_para_mostrar = [
                        'Nome_Colaborador', 'Nota_Geral_Projeto',
                        'Pontualidade_Aeroporto', 'Facilidade_Carga', 'Resolutividade_Despacho',
                        'Pontualidade_Local', 'Proatividade_Ocorrencias', 'Proatividade_Respostas', 'Resolucao_Problemas'
                    ]
                    colunas_formatar = [c for c in colunas_para_mostrar if c != 'Nome_Colaborador']
                    
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_ranking.to_excel(writer, sheet_name='Ranking_Desempenho', index=False)
                    
                    st.download_button(
                        label="📥 Baixar Relatório em Excel",
                        data=buffer.getvalue(),
                        file_name=f"Ranking_Avaliadores_{filtro_certame.replace(' ', '_')}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                    st.write("") 
                    
                    st.dataframe(
                        df_ranking[colunas_para_mostrar].style.format("{:.1f}", subset=colunas_formatar, na_rep="-"),
                        use_container_width=True
                    )

    # ---------------------------------------------------------
    # TELA DOS AVALIADORES (AEROPORTO E LOCAL)
    # ---------------------------------------------------------
    else:
        if eh_aeroporto or pd.isna(st.session_state.regiao) or st.session_state.regiao == '':
            colaboradores_filtrados = df_colaboradores.copy()
        else:
            regiao_user_limpa = str(st.session_state.regiao).strip().lower()
            df_colaboradores['Regiao_Limpa'] = df_colaboradores['Regiao'].astype(str).str.strip().str.lower()
            colaboradores_filtrados = df_colaboradores[df_colaboradores['Regiao_Limpa'] == regiao_user_limpa].copy()

        if colaboradores_filtrados.empty:
            st.warning("Nenhum colaborador encontrado para esta região.")
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
                st.success("✅ **Excelente trabalho!** Todas as avaliações foram concluídas.")
            else:
                st.markdown("### Configuração da Avaliação")
                
                certame_selecionado = st.selectbox("Qual certame/projeto você está avaliando agora?", ["ENARE", "CFC", "OAB", "Outro..."])
                if certame_selecionado == "Outro...": certame_selecionado = st.text_input("Digite o nome do certame:")

                opcoes_colaboradores = dict(zip(colaboradores_pendentes['Nome'], colaboradores_pendentes['ID']))
                colaborador_selecionado = st.selectbox(
                    "Selecione o colaborador avaliado:",
                    options=list(opcoes_colaboradores.keys())
                )
                id_selecionado = opcoes_colaboradores.get(colaborador_selecionado)

                with st.form("form_avaliacao", clear_on_submit=True):
                    st.caption("💡 Escala de avaliação: 1 estrela (Insatisfatório) a 5 estrelas (Excelente)")
                    
                    if eh_aeroporto:
                        st.markdown("<div class='sessao-aeroporto'>✈️ Recebimento dos Materiais</div>", unsafe_allow_html=True)
                        pont_aeroporto = st.radio("Pontualidade ao chegar no aeroporto", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                        st.write("")
                        facilidade_carga = st.radio("Facilidade em carregar material", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                        st.write("")
                        resolutividade_despacho = st.radio("Resolutividade na hora do despacho", options=[1, 2, 3, 4, 5], index=2, horizontal=True, format_func=lambda x: "⭐" * x)
                    else:
                        st.markdown("<div class='sessao-header'>🕐 Avaliação de Pontualidade</div>", unsafe_allow_html=True)
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
                            val_pont_aero = int(pont_aeroporto) if eh_aeroporto else ""
                            val_carga = int(facilidade_carga) if eh_aeroporto else ""
                            val_res_desp = int(resolutividade_despacho) if eh_aeroporto else ""
                            
                            val_pont_local = "" if eh_aeroporto else int(pont_local)
                            val_proat_ocor = "" if eh_aeroporto else int(proat_ocorrencias)
                            val_proat_lanc = "" if eh_aeroporto else int(proat_lancamentos)
                            val_proat_resp = "" if eh_aeroporto else int(proat_respostas)
                            val_resolucao = "" if eh_aeroporto else int(resolucao)

                            sheet = conectar_google_sheets()
                            nova_linha = [
                                datetime.now().strftime("%d/%m/%Y %H:%M"),
                                certame_selecionado, 
                                st.session_state.email,
                                str(id_selecionado),
                                colaborador_selecionado,
                                val_pont_aero,
                                val_pont_local,
                                val_proat_ocor,
                                val_proat_lanc,
                                val_proat_resp,
                                val_resolucao,
                                observacoes,
                                val_carga,
                                val_res_desp
                            ]
                            sheet.append_row(nova_linha)
                            
                            nova_avaliacao = pd.DataFrame([{
                                'Data': nova_linha[0], 'Certame': nova_linha[1], 'Email_Avaliador': nova_linha[2],
                                'ID_Colaborador': nova_linha[3], 'Nome_Colaborador': nova_linha[4],
                                'Pontualidade_Aeroporto': nova_linha[5], 'Pontualidade_Local': nova_linha[6],
                                'Proatividade_Ocorrencias': nova_linha[7], 'Proatividade_Lancamentos': nova_linha[8],
                                'Proatividade_Respostas': nova_linha[9], 'Resolucao_Problemas': nova_linha[10],
                                'Observacoes': nova_linha[11], 'Facilidade_Carga': nova_linha[12], 'Resolutividade_Despacho': nova_linha[13]
                            }])
                            st.session_state.df_avaliacoes = pd.concat([st.session_state.df_avaliacoes, nova_avaliacao], ignore_index=True)
                            
                            st.success("Avaliação registrada com sucesso na nuvem!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar no Google Sheets: {e}")

            if not avaliacoes_do_usuario.empty:
                st.write("")
                with st.expander("🔄 Precisa corrigir alguma avaliação já enviada?"):
                    st.write("Selecione o colaborador abaixo para anular a nota anterior e avaliá-lo novamente.")
                    opcoes_avaliados = dict(zip(avaliacoes_do_usuario['Nome_Colaborador'], avaliacoes_do_usuario['ID_Colaborador']))
                    colaborador_restaurar = st.selectbox("Colaborador:", options=list(opcoes_avaliados.keys()), key="select_restaurar")
                    id_restaurar = opcoes_avaliados.get(colaborador_restaurar)
                    
                    if st.button("Anular e Restaurar Colaborador"):
                        try:
                            mask = ~((st.session_state.df_avaliacoes['Email_Avaliador'] == st.session_state.email) & 
                                     (st.session_state.df_avaliacoes['ID_Colaborador'] == id_restaurar))
                            st.session_state.df_avaliacoes = st.session_state.df_avaliacoes[mask]
                            
                            sheet = conectar_google_sheets()
                            sheet.clear()
                            cabecalho = list(st.session_state.df_avaliacoes.columns)
                            linhas = st.session_state.df_avaliacoes.values.tolist()
                            sheet.append_row(cabecalho)
                            if linhas: sheet.append_rows(linhas)
                                
                            st.success("Colaborador restaurado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao restaurar no Google Sheets: {e}")
