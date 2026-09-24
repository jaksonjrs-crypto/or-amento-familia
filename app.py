import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Jack & Loli - Finanças",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILIZAÇÃO CUSTOMIZADA SLIM (Sem quebrar o Streamlit) ---
st.markdown("""
<style>
    /* Ajustes gerais de espaçamento */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 800px;
    }
    
    /* Cards Finos e Modernos */
    .card-metric {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .card-title { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
    .card-value { font-size: 1.5rem; font-weight: 700; margin-top: 4px; }
    .text-green { color: #10b981; }
    .text-red { color: #f43f5e; }
    .text-blue { color: #38bdf8; }
    
    /* Estilização dos Botões de Navegação */
    div[data-testid="stColumn"] > div > div > button {
        width: 100%;
        border-radius: 8px;
        height: 42px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS ---
DB_NAME = "orcamento_v2.db"

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
        
        c.execute("SELECT COUNT(*) FROM metas")
        if c.fetchone()[0] == 0:
            metas = [
                ("METINHAZINHA", "Pequenos desejos", 0.0, 500.0, "3 meses"),
                ("METINHA", "Reserva de Emergência", 0.0, 5000.0, "1 ano"),
                ("META", "Viagem", 0.0, 20000.0, "2 anos"),
                ("METONA", "Carro/Casa", 0.0, 150000.0, "5 anos")
            ]
            c.executemany("INSERT INTO metas (nome, descricao, valor_atual, valor_objetivo, prazo) VALUES (?, ?, ?, ?, ?)", metas)
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

# --- GERENCIAMENTO DE ESTADO ---
if "user" not in st.session_state:
    st.session_state.user = "Jack"

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today()

# --- TOPO DA PÁGINA E SELEÇÃO DE USUÁRIO ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("💳 Dashboard Financeiro")
with col_head2:
    usuario_atual = st.selectbox("Usuário", ["Jack", "Loli"], index=0 if st.session_state.user == "Jack" else 1)
    st.session_state.user = usuario_atual

# --- NAVEGAÇÃO POR BOTÕES NATIVOS ---
st.markdown("---")
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)

pages = [
    ("📊 Geral", "Dashboard", nav_col1),
    ("➕ Lançar", "Lançar", nav_col2),
    ("🎯 Metas", "Metas", nav_col3),
    ("📜 Histórico", "Histórico", nav_col4),
    ("⚙️ Ajustes", "Config", nav_col5)
]

for label, page_name, col in pages:
    with col:
        btn_type = "primary" if st.session_state.page == page_name else "secondary"
        if st.button(label, key=f"nav_{page_name}", type=btn_type):
            st.session_state.page = page_name
            st.rerun()

st.markdown("---")

# --- CONTROLE DE MÊS NAVEGÁVEL ---
m_col1, m_col2, m_col3 = st.columns([1, 3, 1])
with m_col1:
    if st.button("◄ Mês Anterior", use_container_width=True):
        st.session_state.current_date = (st.session_state.current_date.replace(day=1) - timedelta(days=1))
        st.rerun()
with m_col2:
    mes_str = st.session_state.current_date.strftime("%B / %Y").capitalize()
    st.markdown(f"<h3 style='text-align: center; margin: 0;'>📅 {mes_str}</h3>", unsafe_allow_html=True)
with m_col3:
    if st.button("Próximo Mês ►", use_container_width=True):
        next_m = st.session_state.current_date.replace(day=28) + timedelta(days=4)
        st.session_state.current_date = next_m.replace(day=1)
        st.rerun()

str_mes_ano = st.session_state.current_date.strftime("%Y-%m")

# ==========================================
# 1. TELA: DASHBOARD
# ==========================================
if st.session_state.page == "Dashboard":
    df = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
    
    rec = df[df['tipo'] == 'Receita']['valor'].sum() if not df.empty else 0.0
    desp = df[df['tipo'] == 'Despesa']['valor'].sum() if not df.empty else 0.0
    saldo = rec - desp

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-title">Receitas</div>
            <div class="card-value text-green">R$ {rec:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-title">Despesas</div>
            <div class="card-value text-red">R$ {desp:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-title">Saldo Líquido</div>
            <div class="card-value {'text-blue' if saldo >= 0 else 'text-red'}">R$ {saldo:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🎯 Regra Orçamentária (55/5/10/30)")
    renda_base = rec if rec > 0 else 1.0
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.write(f"**Essenciais (55%)**: R$ {desp:,.2f} / R$ {(renda_base * 0.55):,.2f}")
        st.progress(min(desp / (renda_base * 0.55), 1.0) if rec > 0 else 0.0)

        st.write(f"**Educação (5%)**: R$ 0,00 / R$ {(renda_base * 0.05):,.2f}")
        st.progress(0.0)
        
    with col_r2:
        st.write(f"**Livre Escolha (10%)**: R$ 0,00 / R$ {(renda_base * 0.10):,.2f}")
        st.progress(0.0)

        st.write(f"**Metas / Investimentos (30%)**: R$ 0,00 / R$ {(renda_base * 0.30):,.2f}")
        st.progress(0.0)

    if not df[df['tipo'] == 'Despesa'].empty:
        st.markdown("### 📊 Despesas por Categoria")
        df_cat = df[df['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
        fig = px.pie(df_cat, values='valor', names='categoria', hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_layout(margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 2. TELA: LANÇAR
# ==========================================
elif st.session_state.page == "Lançar":
    st.markdown("### ➕ Novo Lançamento")
    with st.form("form_novo_lancamento", clear_on_submit=True):
        f_tipo = st.radio("Tipo de Transação", ["Despesa", "Receita"], horizontal=True)
        f_categoria = st.selectbox("Categoria", ["Habitação", "Alimentação", "Saúde", "Transporte", "Educação", "Lazer", "Dívidas", "Outros"])
        f_valor = st.number_input("Valor (R$)", min_value=0.01, step=1.0)
        f_meio = st.selectbox("Forma de Pagamento", ["PIX", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"])
        f_data = st.date_input("Data", datetime.today())
        f_obs = st.text_input("Observação")
        
        if st.form_submit_button("Salvar Lançamento", use_container_width=True, type="primary"):
            execute_db(
                "INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f_tipo, f_categoria, f_valor, f_meio, f_data.strftime('%Y-%m-%d'), f_obs, st.session_state.user)
            )
            st.success("✅ Lançamento cadastrado com sucesso!")

# ==========================================
# 3. TELA: METAS
# ==========================================
elif st.session_state.page == "Metas":
    st.markdown("### 🎯 Objetivos Financeiros")
    df_metas = run_query("SELECT * FROM metas")
    
    for _, r in df_metas.iterrows():
        pct = min(r['valor_atual'] / r['valor_objetivo'], 1.0) if r['valor_objetivo'] > 0 else 0.0
        with st.container():
            c_meta1, c_meta2 = st.columns([3, 1])
            with c_meta1:
                st.subheader(r['nome'])
                st.caption(f"{r['descricao']} • Prazo: {r['prazo']}")
            with c_meta2:
                st.markdown(f"**R$ {r['valor_atual']:,.2f}** / R$ {r['valor_objetivo']:,.2f}")
            st.progress(pct)
            st.markdown("---")

# ==========================================
# 4. TELA: HISTÓRICO
# ==========================================
elif st.session_state.page == "Histórico":
    st.markdown("### 📜 Registros do Mês")
    df_h = run_query("SELECT id, data, tipo, categoria, valor, meio_pagamento, usuario, observacao FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
    
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro encontrado para este mês.")

# ==========================================
# 5. TELA: CONFIGURAÇÕES
# ==========================================
elif st.session_state.page == "Config":
    st.markdown("### ⚙️ Opções do Sistema")
    st.write(f"Usuário ativo: **{st.session_state.user}**")
    if st.button("Limpar Dados de Teste"):
        execute_db("DELETE FROM lancamentos")
        st.warning("Todos os lançamentos foram apagados.")
        st.rerun()
