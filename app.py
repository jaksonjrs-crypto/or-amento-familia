import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Jack & Loli - Orçamento Doméstico",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SISTEMA DE AUTENTICAÇÃO SEGURO EM SESSÃO ---
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "Jack": "1234",
        "Loli": "1234"
    }

# --- BANCO DE DADOS ---
DB_NAME = "orcamento.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)

def init_db():
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT,
                    categoria TEXT,
                    valor REAL,
                    meio_pagamento TEXT,
                    data TEXT,
                    observacao TEXT,
                    usuario TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS metas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE,
                    descricao TEXT,
                    valor_atual REAL,
                    valor_objetivo REAL,
                    prazo TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS beneficios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE,
                    valor_mensal REAL,
                    valor_gasto REAL
                )
            ''')
            conn.commit()
    except Exception:
        pass

init_db()

def run_query(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_db(query, params=()):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- CSS CUSTOMIZADO COMPLETO (VISUAL ULTRA MODERNO & DARK) ---
st.markdown("""
<style>
    /* 1. Fundo da Aplicação */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    p, span, label, div, h1, h2, h3, h4, h5, h6 {
        color: #f8fafc !important;
    }

    /* 2. Formulários, Inputs e Selectboxes */
    div[data-baseweb="input"], 
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"], 
    div[data-baseweb="select"] > div,
    input, select {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    /* 3. Correção de Popover, Dropdowns e Calendários */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"],
    li[role="option"],
    div[role="dialog"],
    div[data-baseweb="calendar"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
    }

    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }

    /* 4. Estilização de Tabelas (Fix da Tela Branca) */
    .stDataFrame, div[data-testid="stTable"] {
        background-color: #1e293b !important;
        border-radius: 12px !important;
        padding: 10px !important;
        border: 1px solid #334155 !important;
    }

    iframe {
        background-color: transparent !important;
    }

    /* 5. Cards Personalizados do Dashboard */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
    }
    .metric-title {
        color: #94a3b8 !important;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .val-receita { color: #10b981 !important; }
    .val-despesa { color: #ef4444 !important; }
    .val-saldo { color: #3b82f6 !important; }

    /* 6. Estilo dos Botões */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%) !important;
    }

    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- ESTADO DE SESSÃO DO LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

# --- TELA DE LOGIN ---
def tela_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2.2rem;'>🔐 Acesso Restrito - Jack & Loli</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.05rem;'>Entre com suas credenciais para acessar o orçamento doméstico.</p>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 1.5, 1])
    with col_c2:
        tab_entrar, tab_esqueci = st.tabs(["🔑 Entrar", "🔄 Alterar / Esqueci a Senha"])
        
        with tab_entrar:
            with st.form("form_login"):
                user = st.selectbox("Usuário", ["Jack", "Loli"], key="login_user")
                senha = st.text_input("Senha", type="password", key="login_pass")
                btn_login = st.form_submit_button("Acessar App")
                
                if btn_login:
                    if user in st.session_state.usuarios_db and st.session_state.usuarios_db[user] == senha:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success(f"Bem-vindo(a), {user}!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta!")
                    
        with tab_esqueci:
            with st.form("form_alterar_senha"):
                user_rec = st.selectbox("Selecione o Usuário", ["Jack", "Loli"], key="rec_user")
                nova_senha = st.text_input("Nova Senha", type="password", key="rec_pass")
                conf_senha = st.text_input("Confirme a Nova Senha", type="password", key="rec_pass_conf")
                btn_alterar = st.form_submit_button("Salvar Nova Senha")
                
                if btn_alterar:
                    n_senha = nova_senha.strip()
                    c_senha = conf_senha.strip()
                    
                    if len(n_senha) > 0 and n_senha == c_senha:
                        st.session_state.usuarios_db[user_rec] = n_senha
                        st.success(f"Senha de {user_rec} alterada com sucesso! Você já pode realizar o login.")
                    else:
                        st.error("As senhas não coincidem ou estão em branco!")

if not st.session_state.logged_in:
    tela_login()
    st.stop()

# --- BARRA DE NAVEGAÇÃO SUPERIOR ---
selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Lançar", "Metas", "Benefícios", "Histórico", "Orçamento"],
    icons=["pie-chart-fill", "plus-circle-fill", "target", "gift-fill", "clock-history", "calculator-fill"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "5px!important", "background-color": "#1e293b", "border-radius": "12px", "margin-bottom": "20px"},
        "icon": {"color": "#60a5fa", "font-size": "16px"},
        "nav-link": {
            "font-size": "14px",
            "text-align": "center",
            "margin": "2px",
            "color": "#94a3b8",
            "--hover-color": "#334155"
        },
        "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600", "border-radius": "8px"},
    }
)

# --- CABEÇALHO DA SESSÃO ---
col_head1, col_head2, col_head3 = st.columns([2, 1.2, 0.8])
with col_head1:
    st.markdown(f"### 👤 Usuário: **{st.session_state.user}**")
with col_head2:
    mes_ano = st.date_input("Filtro de Período", datetime.today(), label_visibility="collapsed")
    str_mes_ano = mes_ano.strftime("%Y-%m")
with col_head3:
    if st.button("🚪 Sair", key="btn_logout"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("<hr style='border: 0.5px solid #334155; margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# --- MÓDULOS DA APLICAÇÃO ---
if selected == "Dashboard":
    st.markdown("## 📊 Dashboard Financeiro")
    st.caption(f"Visão geral das finanças no período: **{mes_ano.strftime('%b/%Y')}**")
    st.markdown("<br>", unsafe_allow_html=True)
    
    try:
        df_transacoes = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
        receitas = df_transacoes[df_transacoes['tipo'] == 'Receita']['valor'].sum() if not df_transacoes.empty else 0.0
        despesas = df_transacoes[df_transacoes['tipo'] == 'Despesa']['valor'].sum() if not df_transacoes.empty else 0.0
    except Exception:
        receitas, despesas = 0.0, 0.0
        
    saldo = receitas - despesas
    
    # CARDS ESTILIZADOS
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Receitas</div>
                <div class="metric-value val-receita">R$ {receitas:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Despesas</div>
                <div class="metric-value val-despesa">R$ {despesas:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Saldo</div>
                <div class="metric-value val-saldo">R$ {saldo:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)

elif selected == "Lançar":
    st.markdown("## ➕ Registar Nova Transação")
    with st.form("form_transacao", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tipo = st.radio("Tipo de Transação", ["Despesa", "Receita"], horizontal=True)
            categoria = st.selectbox("Categoria", ["Habitação", "Alimentação", "Saúde", "Transporte", "Educação", "Lazer", "Despesas Pessoais", "Dívidas", "Investimentos", "Outros"])
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        with col_f2:
            meio_pagamento = st.selectbox("Meio de Pagamento", ["PIX", "Cartão de Crédito", "Débito Automático", "Dinheiro", "Benefício"])
            data_trans = st.date_input("Data", datetime.today())
            usuario = st.selectbox("Quem está registrando?", ["Jack", "Loli"], index=0 if st.session_state.user == "Jack" else 1)
            
        obs = st.text_input("Observação (Opcional)")
        
        if st.form_submit_button("Salvar Transação"):
            execute_db("INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (tipo, categoria, valor, meio_pagamento, data_trans.strftime('%Y-%m-%d'), obs, usuario))
            st.success("Transação registrada com sucesso!")

elif selected == "Metas":
    st.markdown("## 🎯 Acompanhamento de Metas")
    try:
        df_metas = run_query("SELECT * FROM metas")
        if df_metas.empty:
            st.info("Nenhuma meta cadastrada até o momento.")
        else:
            for _, row in df_metas.iterrows():
                st.markdown(f"""
                    <div class="metric-card" style="text-align: left; margin-bottom: 15px;">
                        <h4 style="margin: 0; color: #38bdf8 !important;">{row['nome']}</h4>
                        <p style="color: #94a3b8 !important; margin: 5px 0;">{row['descricao']}</p>
                        <p style="font-weight: bold; margin: 0;">Acumulado: <span style="color: #10b981 !important;">R$ {row['valor_atual']:,.2f}</span> de R$ {row['valor_objetivo']:,.2f}</p>
                    </div>
                """, unsafe_allow_html=True)
    except Exception:
        st.info("Módulo de metas pronto para uso.")

elif selected == "Benefícios":
    st.markdown("## 🎁 Benefícios e Vouchers")
    try:
        df_ben = run_query("SELECT * FROM beneficios")
        if not df_ben.empty:
            st.dataframe(df_ben, use_container_width=True)
        else:
            st.info("Nenhum benefício cadastrado.")
    except Exception:
        st.info("Nenhum benefício cadastrado.")

elif selected == "Histórico":
    st.markdown("## 📜 Histórico de Transações")
    try:
        df_all = run_query("SELECT id, data, tipo, categoria, valor, meio_pagamento, usuario, observacao FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
        if not df_all.empty:
            st.dataframe(df_all, use_container_width=True)
        else:
            st.info("Sem lançamentos para este período selecionado.")
    except Exception:
        st.info("Sem lançamentos para este período selecionado.")

elif selected == "Orçamento":
    st.markdown("## 📑 Planejamento Orçamentário")
    st.info("Em breve: comparativo de orçamento planejado vs realizado.")
