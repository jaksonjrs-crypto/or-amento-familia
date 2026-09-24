import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Jack & Loli - Financeiro",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BANCO DE DADOS ---
DB_NAME = "orcamento.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=15, check_same_thread=False)

def init_db():
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
        
        # Inicializa Metas se vazia
        c.execute("SELECT COUNT(*) FROM metas")
        if c.fetchone()[0] == 0:
            metas = [
                ("METINHAZINHA", "Um jantar, um sapato, uma blusinha", 0.0, 500.0, "3 meses"),
                ("METINHA", "Reserva de Emergência", 0.0, 5000.0, "6 meses a 1 ano"),
                ("META", "Viagem Internacional", 0.0, 20000.0, "1 a 3 anos"),
                ("METONA", "Casa Própria", 0.0, 200000.0, "3 a 10 anos"),
                ("METAZONA", "Aposentadoria", 0.0, 1000000.0, "10 a 30 anos")
            ]
            c.executemany("INSERT OR IGNORE INTO metas (nome, descricao, valor_atual, valor_objetivo, prazo) VALUES (?, ?, ?, ?, ?)", metas)

        # Inicializa Benefícios se vazia
        c.execute("SELECT COUNT(*) FROM beneficios")
        if c.fetchone()[0] == 0:
            ben = [
                ("Vale Refeição", 700.0, 0.0),
                ("Vale Alimentação", 3000.0, 0.0),
                ("Vale Combustível", 1012.0, 0.0)
            ]
            c.executemany("INSERT OR IGNORE INTO beneficios (nome, valor_mensal, valor_gasto) VALUES (?, ?, ?)", ben)
        conn.commit()

init_db()

def run_query(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_db(query, params=()):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# --- GERENCIAMENTO DE SESSÃO & MÊS ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = "Jack"

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today()

# --- STYLES CSS DEFINITIVOS (FIX PARA FUNDOS BRANCOS & MOBILE) ---
st.markdown("""
<style>
    /* Estilo Global Dark Deep Blue */
    .stApp {
        background-color: #060b17 !important;
        color: #f8fafc !important;
    }
    
    /* Remoção de elementos nativos desnecessários */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }

    /* FIX: Tira o fundo branco horroroso dos Inputs e Calendários */
    input, select, textarea, div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="calendar"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }

    /* Card Padrão Referência */
    .ref-card {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }

    /* Valorações */
    .val-rec { color: #10b981; font-weight: bold; }
    .val-desp { color: #f43f5e; font-weight: bold; }
    .val-blue { color: #38bdf8; font-weight: bold; }

    /* Barra de Progresso Dark */
    .stProgress > div > div > div > div {
        background-color: #2563eb !important;
        border-radius: 10px;
    }
    .stProgress > div > div {
        background-color: #1e293b !important;
        border-radius: 10px;
    }

    /* Seletor de Mês Customizado */
    .month-picker-box {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        background-color: #0f172a;
        border: 1px solid #1e293b;
        padding: 8px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<br><br><h2 style='text-align: center;'>🔒 Acesso ao Sistema</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        with st.form("login_form"):
            user = st.selectbox("Selecione o Usuário", ["Jack", "Loli"])
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
    st.stop()

# --- MENU INFERIOR DE NAVEGAÇÃO ---
selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Lançar", "Metas", "Benefícios", "Histórico", "Orçamento"],
    icons=["grid-fill", "plus-circle-fill", "target", "gift-fill", "clock-history", "pie-chart-fill"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "2px!important", "background-color": "#0f172a", "border-radius": "12px", "border": "1px solid #1e293b"},
        "icon": {"color": "#38bdf8", "font-size": "13px"},
        "nav-link": {"font-size": "11px", "text-align": "center", "margin": "1px", "color": "#94a3b8"},
        "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600"},
    }
)

# --- CABEÇALHO DA TELA ---
c_head, c_out = st.columns([3, 1])
with c_head:
    st.markdown(f"#### Olá, **{st.session_state.user}**!")
with c_out:
    if st.button("🚪 Sair"):
        st.session_state.logged_in = False
        st.rerun()

# --- SELETOR DE MÊS ESTILO APP (< Mês/Ano >) ---
m1, m2, m3 = st.columns([1, 2, 1])
with m1:
    if st.button("❮", key="prev_month", use_container_width=True):
        st.session_state.current_date = (st.session_state.current_date.replace(day=1) - timedelta(days=1))
        st.rerun()
with m2:
    st.markdown(f"<h4 style='text-align: center; margin:0;'>📅 {st.session_state.current_date.strftime('%b %Y').title()}</h4>", unsafe_allow_html=True)
with m3:
    if st.button("❯", key="next_month", use_container_width=True):
        # Próximo mês
        next_m = st.session_state.current_date.replace(day=28) + timedelta(days=4)
        st.session_state.current_date = next_m.replace(day=1)
        st.rerun()

str_mes_ano = st.session_state.current_date.strftime("%Y-%m")

# ==========================================
# 1. TELA: DASHBOARD
# ==========================================
if selected == "Dashboard":
    df_trans = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
    
    receitas = df_trans[df_trans['tipo'] == 'Receita']['valor'].sum() if not df_trans.empty else 0.0
    despesas = df_trans[df_trans['tipo'] == 'Despesa']['valor'].sum() if not df_trans.empty else 0.0
    saldo = receitas - despesas

    # Cards Principais
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="ref-card"><small>Receitas</small><h3 class="val-rec">R$ {receitas:,.2f}</h3></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ref-card"><small>Saldo</small><h3 class="val-blue">R$ {saldo:,.2f}</h3></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="ref-card"><small>Despesas</small><h3 class="val-desp">R$ {despesas:,.2f}</h3></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ref-card"><small>Renda Base</small><h3 style="color:#ffffff;">R$ {receitas:,.2f}</h3></div>', unsafe_allow_html=True)

    # Regra Orçamentária 55/5/10/30
    st.markdown("<div class='ref-card'><b>🎯 Regra Orçamentária (55/5/10/30)</b><br><br>", unsafe_allow_html=True)
    renda = receitas if receitas > 0 else 1.0
    
    st.caption(f"Essenciais (55%) — R$ {despesas:,.2f} / R$ {(renda*0.55):,.2f}")
    st.progress(min(despesas/(renda*0.55), 1.0))

    st.caption(f"Educação (5%) — R$ 0,00 / R$ {(renda*0.05):,.2f}")
    st.progress(0.0)

    st.caption(f"Livres (10%) — R$ 0,00 / R$ {(renda*0.10):,.2f}")
    st.progress(0.0)

    st.caption(f"Metas (30%) — R$ 0,00 / R$ {(renda*0.30):,.2f}")
    st.progress(0.0)
    st.markdown("</div>", unsafe_allow_html=True)

    # Gráfico de Pizza de Despesas por Categoria
    if not df_trans[df_trans['tipo'] == 'Despesa'].empty:
        st.markdown("<div class='ref-card'><b>🍕 Despesas por Categoria</b>", unsafe_allow_html=True)
        df_cat = df_trans[df_trans['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
        fig = px.pie(df_cat, values='valor', names='categoria', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 2. TELA: LANÇAR
# ==========================================
elif selected == "Lançar":
    st.markdown("### ➕ Lançar Transação")
    with st.form("form_lancamento", clear_on_submit=True):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        categoria = st.selectbox("Categoria", ["Habitação", "Alimentação", "Saúde", "Transporte", "Educação", "Lazer", "Dívidas", "Outros"])
        valor = st.number_input("Valor (R$)", min_value=0.01, step=1.0)
        meio = st.selectbox("Meio de Pagamento", ["PIX", "Cartão de Crédito", "Débito Automático", "Dinheiro"])
        data_trans = st.date_input("Data", datetime.today())
        obs = st.text_input("Observação (Opcional)")
        
        if st.form_submit_button("✈️ Lançar", use_container_width=True):
            execute_db("INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (tipo, categoria, valor, meio, data_trans.strftime('%Y-%m-%d'), obs, st.session_state.user))
            st.success("Transação gravada!")

# ==========================================
# 3. TELA: METAS
# ==========================================
elif selected == "Metas":
    st.markdown("### 🎯 Metas (Boleto Pessoal)")
    df_m = run_query("SELECT * FROM metas")
    for _, r in df_m.iterrows():
        pct = min(r['valor_atual'] / r['valor_objetivo'], 1.0) if r['valor_objetivo'] > 0 else 0.0
        st.markdown(f"""
        <div class="ref-card">
            <div style="display:flex; justify-content:space-between;">
                <b>{r['nome']}</b>
                <small style="color:#94a3b8;">Prazo: {r['prazo']}</small>
            </div>
            <p style="color:#94a3b8; font-size:12px;">{r['descricao']}</p>
            <small>Acumulado: <b style="color:#10b981;">R$ {r['valor_atual']:,.2f}</b> / R$ {r['valor_objetivo']:,.2f} ({pct*100:.1f}%)</small>
        </div>
        """, unsafe_allow_html=True)
        st.progress(pct)

# ==========================================
# 4. TELA: BENEFÍCIOS
# ==========================================
elif selected == "Benefícios":
    st.markdown("### 🎁 Gestão de Benefícios")
    df_b = run_query("SELECT * FROM beneficios")
    for _, r in df_b.iterrows():
        saldo = r['valor_mensal'] - r['valor_gasto']
        pct = min(r['valor_gasto'] / r['valor_mensal'], 1.0) if r['valor_mensal'] > 0 else 0.0
        st.markdown(f"""
        <div class="ref-card">
            <b>{r['nome']}</b>
            <div style="display:flex; justify-content:space-between; margin-top:10px;">
                <small>Mensal: <b>R$ {r['valor_mensal']:,.2f}</b></small>
                <small>Gasto: <b style="color:#f43f5e;">R$ {r['valor_gasto']:,.2f}</b></small>
                <small>Saldo: <b style="color:#10b981;">R$ {saldo:,.2f}</b></small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(pct)

# ==========================================
# 5. TELA: HISTÓRICO
# ==========================================
elif selected == "Histórico":
    st.markdown("### 📜 Histórico de Transações")
    df_h = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
    
    if not df_h.empty:
        for _, r in df_h.iterrows():
            cor = "#10b981" if r['tipo'] == 'Receita' else "#f43f5e"
            st.markdown(f"""
            <div class="ref-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <b>{r['categoria']}</b> <span style="font-size:10px; background:#1e293b; padding:2px 6px; border-radius:4px;">{r['usuario']}</span><br>
                        <small style="color:#94a3b8;">{r['data']} • {r['meio_pagamento']}</small>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:{cor}; font-weight:bold;">R$ {r['valor']:,.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma transação encontrada para este mês.")

# ==========================================
# 6. TELA: ORÇAMENTO
# ==========================================
elif selected == "Orçamento":
    st.markdown("### 📑 Limites por Categoria")
    cats = ["HABITAÇÃO", "DÍVIDAS", "SAÚDE", "TRANSPORTE", "DESPESAS PESSOAIS"]
    for c in cats:
        st.markdown(f"""
        <div class="ref-card">
            <div style="display:flex; justify-content:space-between;">
                <b>{c}</b>
                <small style="color:#38bdf8;">Despesas Essenciais (55%)</small>
            </div>
            <small>Gasto: <b>R$ 0,00</b> | Limite: <span style="color:#94a3b8;">Não definido</span></small>
        </div>
        """, unsafe_allow_html=True)
