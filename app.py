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

# --- INICIALIZAÇÃO DE SENHAS NA SESSÃO (Evita erros de gravação no SQLite) ---
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {
        "Jack": "1234",
        "Loli": "1234"
    }

# --- BANCO DE DADOS (Conexão e Criação de Tabelas Sem Inserts Iniciais) ---
DB_NAME = "orcamento.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    return conn

def init_db():
    """Cria as tabelas do banco de dados sem realizar escritas pesadas no arranque."""
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

# Executa apenas a criação das estruturas
init_db()

# --- FUNÇÕES AUXILIARES DE BANCO DE DADOS ---
def run_query(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_db(query, params=()):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- CSS CUSTOMIZADO (Força o Fundo Escuro em Todos os Inputs e Popovers) ---
st.markdown("""
<style>
    /* Estilo do fundo e texto global */
    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    
    p, span, label, div, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* Correção visual total para Inputs de Texto, Senha e Selectbox */
    div[data-baseweb="input"], 
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"], 
    div[data-baseweb="select"] > div,
    input {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-color: #475569 !important;
    }

    /* Estilização das listas suspensas (Dropdown) */
    div[data-baseweb="popover"],
    ul[role="listbox"],
    li[role="option"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }

    li[role="option"]:hover, 
    li[aria-selected="true"] {
        background-color: #334155 !important;
        color: #38bdf8 !important;
    }

    /* Estilização das Abas */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
    }
    button[data-baseweb="tab"] p {
        color: #94a3b8 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #38bdf8 !important;
        font-weight: bold;
    }

    /* Estilo dos Botões */
    .stButton>button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 8px;
        border: none;
        width: 100%;
        font-weight: 600;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
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
    st.markdown("<h2 style='text-align: center;'>🔐 Acesso Restrito - Jack & Loli</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Entre com suas credenciais para acessar o orçamento doméstico.</p>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
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
            st.caption("Redefina sua senha abaixo:")
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
                        st.success(f"Senha de {user_rec} alterada com sucesso! Você já pode realizar o login com a nova senha.")
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
        "container": {"padding": "0!important", "background-color": "#0f172a", "border-bottom": "1px solid #1e293b"},
        "icon": {"color": "#60a5fa", "font-size": "15px"},
        "nav-link": {
            "font-size": "14px",
            "text-align": "center",
            "margin": "4px",
            "color": "#94a3b8",
            "--hover-color": "#1e293b"
        },
        "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600"},
    }
)

# --- CABEÇALHO ---
col_head1, col_head2, col_head3 = st.columns([2, 1, 1])
with col_head1:
    st.markdown(f"### 🔄 **Jack & Loli** ({st.session_state.user})")
with col_head2:
    mes_ano = st.date_input("Filtro de Período", datetime.today(), label_visibility="collapsed")
    str_mes_ano = mes_ano.strftime("%Y-%m")
with col_head3:
    if st.button("🚪 Sair", key="btn_logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- MÓDULOS ---
if selected == "Dashboard":
    st.markdown("## 📊 Dashboard")
    st.caption(f"Visão geral do mês ({mes_ano.strftime('%b/%Y')})")
    
    try:
        df_transacoes = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
        receitas = df_transacoes[df_transacoes['tipo'] == 'Receita']['valor'].sum() if not df_transacoes.empty else 0.0
        despesas = df_transacoes[df_transacoes['tipo'] == 'Despesa']['valor'].sum() if not df_transacoes.empty else 0.0
    except Exception:
        receitas, despesas = 0.0, 0.0
        
    saldo = receitas - despesas
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Receitas", f"R$ {receitas:,.2f}")
    with c2:
        st.metric("Despesas", f"R$ {despesas:,.2f}")
    with c3:
        st.metric("Saldo", f"R$ {saldo:,.2f}")

elif selected == "Lançar":
    st.markdown("## ➕ Lançar Transação")
    with st.form("form_transacao", clear_on_submit=True):
        tipo = st.radio("Tipo de Transação", ["Despesa", "Receita"], horizontal=True)
        categoria = st.selectbox("Categoria", ["Habitação", "Alimentação", "Saúde", "Transporte", "Educação", "Lazer", "Despesas Pessoais", "Dívidas", "Investimentos", "Outros"])
        valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        meio_pagamento = st.selectbox("Meio de Pagamento", ["PIX", "Cartão de Crédito", "Débito Automático", "Dinheiro", "Benefício"])
        data_trans = st.date_input("Data", datetime.today())
        obs = st.text_input("Observação (Opcional)")
        usuario = st.selectbox("Quem está registrando?", ["Jack", "Loli"], index=0 if st.session_state.user == "Jack" else 1)
        
        if st.form_submit_button("Salvar"):
            execute_db("INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (tipo, categoria, valor, meio_pagamento, data_trans.strftime('%Y-%m-%d'), obs, usuario))
            st.success("Transação registrada com sucesso!")

elif selected == "Metas":
    st.markdown("## 🎯 Metas")
    try:
        df_metas = run_query("SELECT * FROM metas")
        if df_metas.empty:
            st.info("Nenhuma meta cadastrada.")
        else:
            for _, row in df_metas.iterrows():
                st.subheader(row['nome'])
                st.caption(row['descricao'])
                st.write(f"Acumulado: R$ {row['valor_atual']:,.2f} de R$ {row['valor_objetivo']:,.2f}")
    except Exception:
        st.info("Módulo de metas pronto para uso.")

elif selected == "Benefícios":
    st.markdown("## 🎁 Benefícios")
    try:
        df_ben = run_query("SELECT * FROM beneficios")
        st.dataframe(df_ben, use_container_width=True)
    except Exception:
        st.info("Sem benefícios cadastrados.")

elif selected == "Histórico":
    st.markdown("## 📜 Histórico de Transações")
    try:
        df_all = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
        st.dataframe(df_all, use_container_width=True)
    except Exception:
        st.info("Sem lançamentos para este período.")

elif selected == "Orçamento":
    st.markdown("## 📑 Orçamento por Categoria")
    st.info("Planejamento e comparativo por categorias.")
