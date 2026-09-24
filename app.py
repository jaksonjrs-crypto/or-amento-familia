import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
from streamlit_option_menu import option_menu
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Jack & Loli - Orçamento Doméstico",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS CUSTOMIZADO (Forçar texto claro em TUDO no Dark Mode) ---
st.markdown("""
<style>
    /* Estilo global dark */
    .stApp {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    
    /* Forçar cores claras em todos os textos de rótulos e títulos */
    p, span, label, div, h1, h2, h3, h4, h5, h6, caption {
        color: #ffffff !important;
    }
    
    /* Inputs, Selectbox, Text Area e Date Input */
    input, textarea, select {
        color: #ffffff !important;
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
    }

    /* Ajuste para caixas do Streamlit (Selectbox e Inputs do BaseWeb) */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div, 
    div[data-baseweb="base-input"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-color: #475569 !important;
    }

    /* Texto dos itens de menus dropdown (listas suspensas) */
    ul[data-baseweb="menu"] li, div[data-baseweb="popover"] * {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }

    /* Correção visual das ABAS (Entrar / Alterar Senha) */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
    }
    button[data-baseweb="tab"] p, button[data-baseweb="tab"] div {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p, 
    button[data-baseweb="tab"][aria-selected="true"] div {
        color: #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }

    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Cards Customizados */
    .card-metric {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .card-title {
        color: #94a3b8 !important;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .card-value {
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .val-positive { color: #38bdf8 !important; }
    .val-negative { color: #f87171 !important; }
    .val-neutral { color: #60a5fa !important; }

    /* Botão Principal */
    .stButton>button {
        border-radius: 8px;
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none;
        font-weight: 600;
        width: 100%;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS (SQLite com verificação robusta) ---
DB_NAME = "orcamento.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Tabela de Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            senha TEXT
        )
    ''')
    
    # 2. Tabela de Lançamentos
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
    
    # 3. Tabela de Metas
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
    
    # 4. Tabela de Benefícios
    c.execute('''
        CREATE TABLE IF NOT EXISTS beneficios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            valor_mensal REAL,
            valor_gasto REAL
        )
    ''')
    
    # Garantir criação dos usuários padrão
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT OR REPLACE INTO usuarios VALUES ('Jack', '1234')")
        c.execute("INSERT OR REPLACE INTO usuarios VALUES ('Loli', '1234')")
        
    # Garantir criação de Metas Iniciais
    c.execute("SELECT COUNT(*) FROM metas")
    if c.fetchone()[0] == 0:
        metas_iniciais = [
            ("METINHAZINHA", "Um jantar, um sapato, uma blusinha", 0.0, 500.0, "3 meses"),
            ("METINHA", "Reserva de Emergência", 0.0, 5000.0, "6 meses a 1 ano"),
            ("META", "Viagem Internacional", 0.0, 20000.0, "1 a 3 anos"),
            ("METONA", "Casa Própria", 0.0, 200000.0, "3 a 10 anos"),
            ("METAZONA", "Aposentadoria", 0.0, 1000000.0, "10 a 30 anos")
        ]
        c.executemany("INSERT INTO metas (nome, descricao, valor_atual, valor_objetivo, prazo) VALUES (?, ?, ?, ?, ?)", metas_iniciais)
        
    # Garantir criação de Benefícios Iniciais
    c.execute("SELECT COUNT(*) FROM beneficios")
    if c.fetchone()[0] == 0:
        beneficios_iniciais = [
            ("Vale Refeição", 700.0, 0.0),
            ("Vale Alimentação", 3000.0, 0.0),
            ("Vale Combustível", 1012.0, 0.0)
        ]
        c.executemany("INSERT INTO beneficios (nome, valor_mensal, valor_gasto) VALUES (?, ?, ?)", beneficios_iniciais)
        
    conn.commit()
    conn.close()

# Executa inicialização do banco
init_db()

# --- FUNÇÕES DE CONSULTA SEGURAS ---
def run_query(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_db(query, params=()):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- GERENCIAMENTO DE SESSÃO ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

# --- TELA DE LOGIN CORRIGIDA ---
def tela_login():
    st.markdown("<h2 style='text-align: center; color: #ffffff;'>🔐 Acesso Restrito - Jack & Loli</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Entre com suas credenciais para acessar o orçamento doméstico.</p>", unsafe_allow_html=True)
    
    col_cen1, col_cen2, col_cen3 = st.columns([1, 2, 1])
    with col_cen2:
        tab_entrar, tab_esqueci = st.tabs(["🔑 Entrar", "🔄 Alterar / Esqueci a Senha"])
        
        with tab_entrar:
            user = st.selectbox("Usuário", ["Jack", "Loli"], key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Acessar App", key="btn_login"):
                # Autenticação direta no banco
                df_u = run_query("SELECT * FROM usuarios WHERE username = ? AND senha = ?", (user, senha))
                if not df_u.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.success(f"Bem-vindo(a), {user}!")
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
                    
        with tab_esqueci:
            st.caption("Redefina sua senha abaixo:")
            user_rec = st.selectbox("Selecione o Usuário", ["Jack", "Loli"], key="rec_user")
            nova_senha = st.text_input("Nova Senha", type="password", key="rec_pass")
            conf_senha = st.text_input("Confirme a Nova Senha", type="password", key="rec_pass_conf")
            
            if st.button("Salvar Nova Senha", key="btn_rec"):
                if nova_senha and nova_senha == conf_senha:
                    execute_db("UPDATE usuarios SET senha = ? WHERE username = ?", (nova_senha, user_rec))
                    st.success("Senha alterada com sucesso! Você já pode realizar o login.")
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

# --- CABEÇALHO DA APLICAÇÃO ---
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

# --- MÓDULO 1: DASHBOARD ---
if selected == "Dashboard":
    st.markdown("## 📊 Dashboard")
    st.caption(f"Visão geral do mês ({mes_ano.strftime('%b/%Y')})")
    
    df_transacoes = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
    
    receitas = df_transacoes[df_transacoes['tipo'] == 'Receita']['valor'].sum() if not df_transacoes.empty else 0.0
    despesas = df_transacoes[df_transacoes['tipo'] == 'Despesa']['valor'].sum() if not df_transacoes.empty else 0.0
    saldo = receitas - despesas
    renda_base = receitas if receitas > 0 else 1.0
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="card-metric"><div class="card-title">Receitas</div><div class="card-value val-positive">R$ {receitas:,.2f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="card-metric"><div class="card-title">Despesas</div><div class="card-value val-negative">R$ {despesas:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        cor_s = "val-positive" if saldo >= 0 else "val-negative"
        st.markdown(f'<div class="card-metric"><div class="card-title">Saldo</div><div class="card-value {cor_s}">R$ {saldo:,.2f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="card-metric"><div class="card-title">Renda Base</div><div class="card-value val-neutral">R$ {receitas:,.2f}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Regra Orçamentária (55/5/10/30)")
    
    metas_regra = {
        "Essenciais (55%)": (0.55 * renda_base, df_transacoes[df_transacoes['categoria'].isin(['Habitação', 'Alimentação', 'Saúde', 'Transporte'])]['valor'].sum() if not df_transacoes.empty else 0),
        "Educação (5%)": (0.05 * renda_base, df_transacoes[df_transacoes['categoria'] == 'Educação']['valor'].sum() if not df_transacoes.empty else 0),
        "Livres (10%)": (0.10 * renda_base, df_transacoes[df_transacoes['categoria'].isin(['Lazer', 'Despesas Pessoais'])]['valor'].sum() if not df_transacoes.empty else 0),
        "Metas/Investimentos (30%)": (0.30 * renda_base, df_transacoes[df_transacoes['categoria'] == 'Investimentos']['valor'].sum() if not df_transacoes.empty else 0)
    }
    
    for nome, (limite, gasto) in metas_regra.items():
        pct = min(gasto / limite if limite > 0 else 0.0, 1.0)
        col_r1, col_r2 = st.columns([3, 1])
        with col_r1:
            st.write(f"**{nome}**")
            st.progress(pct)
        with col_r2:
            st.write(f"R$ {gasto:,.2f} / R$ {limite:,.2f}")

    st.markdown("---")
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        st.markdown("### 🍰 Despesas por Categoria")
        if not df_transacoes.empty and despesas > 0:
            df_desp = df_transacoes[df_transacoes['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
            fig = px.pie(df_desp, values='valor', names='categoria', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada neste período.")
            
    with g_col2:
        st.markdown("### 📈 Progresso das Metas")
        df_metas = run_query("SELECT * FROM metas")
        if not df_metas.empty:
            df_metas['Progresso (%)'] = (df_metas['valor_atual'] / df_metas['valor_objetivo']) * 100
            fig_metas = px.bar(df_metas, x='Progresso (%)', y='nome', orientation='h', text=df_metas['Progresso (%)'].apply(lambda x: f"{x:.1f}%"))
            fig_metas.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'))
            st.plotly_chart(fig_metas, use_container_width=True)

# --- MÓDULO 2: LANÇAR ---
elif selected == "Lançar":
    st.markdown("## ➕ Lançar Transação")
    with st.form("form_transacao", clear_on_submit=True):
        tipo = st.radio("Tipo de Transação", ["Despesa", "Receita"], horizontal=True)
        categoria = st.selectbox("Categoria", ["Habitação", "Alimentação", "Saúde", "Transporte", "Educação", "Lazer", "Despesas Pessoais", "Dívidas", "Investimentos", "Receita Fixa", "Outros"])
        valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        meio_pagamento = st.selectbox("Meio de Pagamento", ["PIX", "Cartão de Crédito", "Débito Automático", "Transferência Bancária", "Dinheiro", "Benefício"])
        data_trans = st.date_input("Data", datetime.today())
        obs = st.text_input("Observação (Opcional)")
        usuario = st.selectbox("Quem está registrando?", ["Jack", "Loli"], index=0 if st.session_state.user == "Jack" else 1)
        
        if st.form_submit_button("Lançar Transação"):
            execute_db("INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (tipo, categoria, valor, meio_pagamento, data_trans.strftime('%Y-%m-%d'), obs, usuario))
            st.success("Transação lançada com sucesso!")

# --- MÓDULO 3: METAS ---
elif selected == "Metas":
    st.markdown("## 🎯 Metas")
    df_metas = run_query("SELECT * FROM metas")
    for _, row in df_metas.iterrows():
        pct = min(row['valor_atual'] / row['valor_objetivo'] if row['valor_objetivo'] > 0 else 0.0, 1.0)
        with st.expander(f"📌 {row['nome']} — R$ {row['valor_atual']:,.2f} / R$ {row['valor_objetivo']:,.2f}"):
            st.progress(pct)
            with st.form(f"form_meta_{row['id']}"):
                novo_atual = st.number_input("Valor Atual Salvo (R$)", value=float(row['valor_atual']), key=f"act_{row['id']}")
                novo_obj = st.number_input("Meta / Objetivo (R$)", value=float(row['valor_objetivo']), key=f"obj_{row['id']}")
                if st.form_submit_button("Atualizar Meta"):
                    execute_db("UPDATE metas SET valor_atual = ?, valor_objetivo = ? WHERE id = ?", (novo_atual, novo_obj, row['id']))
                    st.success("Meta atualizada!")
                    st.rerun()

# --- MÓDULO 4: BENEFÍCIOS ---
elif selected == "Benefícios":
    st.markdown("## 🎁 Benefícios")
    df_ben = run_query("SELECT * FROM beneficios")
    for _, row in df_ben.iterrows():
        st.markdown(f"**{row['nome']}**: Saldo R$ {row['valor_mensal'] - row['valor_gasto']:,.2f}")

# --- MÓDULO 5: HISTÓRICO & PDF ---
elif selected == "Histórico":
    st.markdown("## 📜 Histórico de Transações")
    df_all = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
    if not df_all.empty:
        rec_tot = df_all[df_all['tipo'] == 'Receita']['valor'].sum()
        desp_tot = df_all[df_all['tipo'] == 'Despesa']['valor'].sum()
        html_report = f"<h1>Relatório Financeiro {mes_ano.strftime('%m/%Y')}</h1><p>Receitas: R$ {rec_tot:,.2f} | Despesas: R$ {desp_tot:,.2f}</p><script>window.print();</script>"
        b64 = base64.b64encode(html_report.encode()).decode()
        st.markdown(f'<a href="data:text/html;base64,{b64}" download="Relatorio_{str_mes_ano}.html" style="background-color:#2563eb; color:white; padding:10px 18px; border-radius:8px; text-decoration:none; font-weight:bold; display:inline-block; margin-bottom:15px;">🖨️ Baixar / Imprimir Relatório PDF</a>', unsafe_allow_html=True)
        st.dataframe(df_all)
    else:
        st.info("Nenhum lançamento no mês selecionado.")

# --- MÓDULO 6: ORÇAMENTO ---
elif selected == "Orçamento":
    st.markdown("## 📑 Orçamento por Categoria")
    st.info("Consulte os gastos divididos por categorias no menu Dashboard.")
