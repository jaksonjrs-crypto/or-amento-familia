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

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
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
        
        # Inserção de dados padrão de Metas
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

        # Inserção de dados padrão de Benefícios
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

# --- CONTROLO DE SESSÃO & DATAS ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = True  # Ajuste para True ou adicione ecrã de login
    st.session_state.user = "Jack"

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today()

# --- CSS TOTAL DE INJEÇÃO PARA CORREÇÃO MOBILE ---
st.markdown("""
<style>
    /* 1. Fundo do App e reset de margens */
    .stApp {
        background-color: #0b1120 !important;
        color: #f8fafc !important;
    }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    /* 2. Remoção completa de fundos brancos de inputs e calendários */
    input, select, textarea, 
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] {
        background-color: #131d31 !important;
        color: #ffffff !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
    }
    
    div[data-baseweb="calendar"], 
    div[role="listbox"] {
        background-color: #131d31 !important;
        color: #ffffff !important;
    }

    /* 3. Cards Estilo Referência */
    .card-ref {
        background-color: #131d31;
        border: 1px solid #1e2d4a;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 10px;
    }

    .card-title {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 500;
    }

    .card-value {
        font-size: 20px;
        font-weight: bold;
        margin-top: 4px;
    }

    /* 4. Cores do Protótipo */
    .val-rec { color: #ffffff; }
    .val-desp { color: #ffffff; }
    .val-saldo { color: #ffffff; }
    .val-red { color: #f43f5e; }
    .val-green { color: #10b981; }

    /* 5. Customização da Barra de Progresso */
    .stProgress > div > div > div > div {
        background-color: #2563eb !important;
        border-radius: 8px;
    }
    .stProgress > div > div {
        background-color: #1a263e !important;
        border-radius: 8px;
    }

    /* 6. Botão de Lançar azul */
    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- MENU INFERIOR COMPACTO ---
selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Lançar", "Metas", "Benefícios", "Histórico", "Orçamento"],
    icons=["grid-fill", "plus-circle-fill", "target", "gift-fill", "clock-history", "pie-chart-fill"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "2px!important", "background-color": "#131d31", "border-radius": "10px", "border": "1px solid #1e2d4a"},
        "icon": {"color": "#38bdf8", "font-size": "12px"},
        "nav-link": {"font-size": "10px", "text-align": "center", "margin": "1px", "color": "#94a3b8", "padding": "6px"},
        "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "bold"},
    }
)

# --- SELETOR DE MÊS ESTILO APP (< Out 2026 >) ---
st.markdown(f"<h3 style='margin-bottom:2px;'>Dashboard</h3><p style='color:#94a3b8; font-size:12px; margin-top:0;'>Visão geral do mês — Olá, {st.session_state.user}!</p>", unsafe_allow_html=True)

m1, m2, m3 = st.columns([1, 2, 1])
with m1:
    if st.button("❮", key="prev_m"):
        st.session_state.current_date = (st.session_state.current_date.replace(day=1) - timedelta(days=1))
        st.rerun()
with m2:
    st.markdown(f"<div style='text-align:center; background:#131d31; padding:6px; border-radius:10px; border:1px solid #1e2d4a; font-weight:bold; font-size:14px;'>📅 {st.session_state.current_date.strftime('%b %Y').title()}</div>", unsafe_allow_html=True)
with m3:
    if st.button("❯", key="next_m"):
        next_m = st.session_state.current_date.replace(day=28) + timedelta(days=4)
        st.session_state.current_date = next_m.replace(day=1)
        st.rerun()

str_mes_ano = st.session_state.current_date.strftime("%Y-%m")

# ==========================================
# 1. DASHBOARD
# ==========================================
if selected == "Dashboard":
    df_trans = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
    
    receitas = df_trans[df_trans['tipo'] == 'Receita']['valor'].sum() if not df_trans.empty else 0.0
    despesas = df_trans[df_trans['tipo'] == 'Despesa']['valor'].sum() if not df_trans.empty else 0.0
    saldo = receitas - despesas

    # Cards Principais de Topo (2x2)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="card-ref">
            <div class="card-title">Receitas</div>
            <div class="card-value val-rec">R$ {receitas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card-ref">
            <div class="card-title">Saldo</div>
            <div class="card-value val-saldo">- R$ {abs(saldo):,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="card-ref">
            <div class="card-title">Despesas</div>
            <div class="card-value val-desp">R$ {despesas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card-ref">
            <div class="card-title">Renda Base</div>
            <div class="card-value val-rec">R$ 0,00</div>
        </div>
        """, unsafe_allow_html=True)

    # Regra Orçamentária 55/5/10/30
    st.markdown("""
    <div class="card-ref">
        <b style="font-size:14px;">🎯 Regra Orçamentária (55/5/10/30)</b><br><br>
    """, unsafe_allow_html=True)
    
    renda = receitas if receitas > 0 else 1.0
    
    st.caption(f"Essenciais (55%) — R$ {despesas:,.2f} / R$ {(renda*0.55):,.2f}")
    st.progress(min(despesas/(renda*0.55), 1.0) if renda > 1 else 0.0)

    st.caption(f"Educação (5%) — R$ 0,00 / R$ {(renda*0.05):,.2f}")
    st.progress(0.0)

    st.caption(f"Livres (10%) — R$ 0,00 / R$ {(renda*0.10):,.2f}")
    st.progress(0.0)

    st.caption(f"Metas (30%) — R$ 0,00 / R$ {(renda*0.30):,.2f}")
    st.progress(0.0)
    st.markdown("</div>", unsafe_allow_html=True)

    # Gráfico Despesas por Categoria
    if not df_trans[df_trans['tipo'] == 'Despesa'].empty:
        st.markdown("<div class='card-ref'><b>🍰 Despesas por Categoria</b>", unsafe_allow_html=True)
        df_cat = df_trans[df_trans['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
        fig = px.pie(df_cat, values='valor', names='categoria', hole=0.6, color_discrete_sequence=['#2563eb', '#38bdf8', '#6366f1', '#818cf8'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'), margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 2. LANÇAR
# ==========================================
elif selected == "Lançar":
    st.markdown("### ➕ Lançar Transação")
    with st.form("form_lancar"):
        tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        categoria = st.selectbox("Categoria", ["Habitação", "Alimentação", "Saúde", "Transporte", "Educação", "Dívidas", "Outros"])
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        meio = st.selectbox("Meio de Pagamento", ["PIX", "Cartão de Crédito", "Débito Automático", "Dinheiro"])
        data_t = st.date_input("Data", datetime.today())
        obs = st.text_input("Observação (Opcional)")
        
        if st.form_submit_button("✈️ Lançar"):
            execute_db("INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (tipo, categoria, valor, meio, data_t.strftime('%Y-%m-%d'), obs, st.session_state.user))
            st.success("Transação registrada!")

# ==========================================
# 3. METAS
# ==========================================
elif selected == "Metas":
    st.markdown("### 🎯 Metas (Boleto Pessoal)")
    st.caption("30% da renda — 5 níveis de metas")
    
    df_m = run_query("SELECT * FROM metas")
    for _, r in df_m.iterrows():
        pct = min(r['valor_atual'] / r['valor_objetivo'], 1.0) if r['valor_objetivo'] > 0 else 0.0
        st.markdown(f"""
        <div class="card-ref">
            <div style="display:flex; justify-content:space-between;">
                <b>{r['nome']}</b>
                <small style="color:#94a3b8;">Prazo: {r['prazo']}</small>
            </div>
            <p style="color:#94a3b8; font-size:12px; margin:4px 0;">{r['descricao']}</p>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>R$ {r['valor_atual']:,.2f} / R$ {r['valor_objetivo']:,.2f}</span>
                <b style="color:#38bdf8;">{pct*100:.1f}%</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(pct)

# ==========================================
# 4. BENEFÍCIOS
# ==========================================
elif selected == "Benefícios":
    st.markdown("### 🎁 Benefícios")
    st.caption("Controle de vales e benefícios")
    
    df_b = run_query("SELECT * FROM beneficios")
    for _, r in df_b.iterrows():
        saldo = r['valor_mensal'] - r['valor_gasto']
        pct = min(r['valor_gasto'] / r['valor_mensal'], 1.0) if r['valor_mensal'] > 0 else 0.0
        st.markdown(f"""
        <div class="card-ref">
            <b>{r['nome']}</b>
            <div style="margin-top:8px; font-size:13px;">
                <div style="display:flex; justify-content:space-between;"><span>Mensal</span> <b>R$ {r['valor_mensal']:,.2f}</b></div>
                <div style="display:flex; justify-content:space-between; color:#f43f5e;"><span>Gasto</span> <b>R$ {r['valor_gasto']:,.2f}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>Saldo</span> <b>R$ {saldo:,.2f}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(pct)

# ==========================================
# 5. HISTÓRICO
# ==========================================
elif selected == "Histórico":
    st.markdown("### 📜 Histórico")
    st.caption("Todas as transações do período")
    
    df_h = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
    if not df_h.empty:
        for _, r in df_h.iterrows():
            cor = "val-green" if r['tipo'] == 'Receita' else "val-red"
            st.markdown(f"""
            <div class="card-ref">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <b>{r['categoria']}</b> <span style="font-size:10px; background:#1e2d4a; padding:2px 6px; border-radius:4px; color:#38bdf8;">{r['usuario']}</span><br>
                        <small style="color:#94a3b8;">{r['data']} • {r['meio_pagamento']}</small>
                    </div>
                    <div class="{cor}" style="font-size:16px; font-weight:bold;">
                        {"-" if r['tipo'] == 'Despesa' else "+"}R$ {r['valor']:,.2f}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma transação registada neste mês.")

# ==========================================
# 6. ORÇAMENTO
# ==========================================
elif selected == "Orçamento":
    st.markdown("### 📑 Orçamento")
    st.caption("Defina limites por categoria e acompanhe o uso")
    
    cats = ["HABITAÇÃO", "DÍVIDAS", "SAÚDE", "TRANSPORTE", "DESPESAS PESSOAIS"]
    for c in cats:
        st.markdown(f"""
        <div class="card-ref">
            <div style="display:flex; justify-content:space-between;">
                <b>{c}</b>
                <span style="font-size:11px; color:#38bdf8; background:#1e2d4a; padding:2px 6px; border-radius:4px;">Despesas Essenciais (55%)</span>
            </div>
            <div style="margin-top:10px; display:flex; justify-content:space-between; font-size:13px;">
                <span>R$ 0,00 gasto</span>
                <span style="color:#94a3b8;">Limite: Não definido</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
