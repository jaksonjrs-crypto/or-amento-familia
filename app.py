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

# --- BANCO DE DADOS (Persistência Segura) ---
DB_NAME = "orcamento.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=15, check_same_thread=False)

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
            
            # Inicialização das metas se tabela estiver vazia
            c.execute("SELECT COUNT(*) FROM metas")
            if c.fetchone()[0] == 0:
                metas_iniciais = [
                    ("METINHAZINHA", "Um jantar, um sapato, uma blusinha", 150.0, 500.0, "3 meses"),
                    ("METINHA", "Reserva de Emergência", 1200.0, 5000.0, "6 meses a 1 ano"),
                    ("META", "Viagem Internacional", 3500.0, 20000.0, "1 a 3 anos"),
                    ("METONA", "Casa Própria", 15000.0, 200000.0, "3 a 10 anos"),
                    ("METAZONA", "Aposentadoria", 45000.0, 1000000.0, "10 a 30 anos")
                ]
                c.executemany("INSERT OR IGNORE INTO metas (nome, descricao, valor_atual, valor_objetivo, prazo) VALUES (?, ?, ?, ?, ?)", metas_iniciais)

            # Inicialização dos benefícios se tabela estiver vazia
            c.execute("SELECT COUNT(*) FROM beneficios")
            if c.fetchone()[0] == 0:
                beneficios_iniciais = [
                    ("Vale Refeição", 700.0, 250.0),
                    ("Vale Alimentação", 3000.0, 1100.0),
                    ("Vale Combustível", 1012.0, 400.0)
                ]
                c.executemany("INSERT OR IGNORE INTO beneficios (nome, valor_mensal, valor_gasto) VALUES (?, ?, ?)", beneficios_iniciais)
                
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

# --- AUTENTICAÇÃO EM SESSÃO ---
if "usuarios_db" not in st.session_state:
    st.session_state.usuarios_db = {"Jack": "1234", "Loli": "1234"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

# --- CSS CUSTOMIZADO MODERN DARK ---
st.markdown("""
<style>
    .stApp {
        background-color: #0b1329 !important;
        color: #f8fafc !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #f8fafc !important;
    }

    /* Cards e Containers Modernos */
    .custom-card {
        background: #131f3a;
        border: 1px solid #1e2d50;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    .metric-title {
        color: #94a3b8 !important;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 5px;
    }
    .val-rec { color: #10b981 !important; }
    .val-desp { color: #f43f5e !important; }
    .val-saldo { color: #38bdf8 !important; }

    /* Estilização de Inputs, Selects e Calendários */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div,
    input {
        background-color: #131f3a !important;
        color: #ffffff !important;
        border: 1px solid #2a3b63 !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {
        background-color: #131f3a !important;
        color: #ffffff !important;
    }

    /* Botões */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
    }
    
    /* Tabelas HTML Customizadas para Fundo Dark Perfeito */
    .dark-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #131f3a;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #1e2d50;
    }
    .dark-table th {
        background-color: #1e2d50;
        color: #38bdf8;
        padding: 12px;
        text-align: left;
        font-size: 0.9rem;
    }
    .dark-table td {
        padding: 12px;
        border-bottom: 1px solid #1e2d50;
        color: #f8fafc;
        font-size: 0.9rem;
    }
    .dark-table tr:hover {
        background-color: #1a2747;
    }

    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
def tela_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🔐 Acesso Restrito - Jack & Loli</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Entre com suas credenciais para acessar o controle orçamentário.</p>", unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 1.2, 1])
    with col_c2:
        tab_entrar, tab_esqueci = st.tabs(["🔑 Entrar", "🔄 Alterar / Esqueci a Senha"])
        
        with tab_entrar:
            with st.form("form_login"):
                user = st.selectbox("Usuário", ["Jack", "Loli"], key="login_user")
                senha = st.text_input("Senha", type="password", key="login_pass")
                if st.form_submit_button("Acessar App"):
                    if user in st.session_state.usuarios_db and st.session_state.usuarios_db[user] == senha:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Senha incorreta!")
                    
        with tab_esqueci:
            with st.form("form_alterar_senha"):
                user_rec = st.selectbox("Selecione o Usuário", ["Jack", "Loli"], key="rec_user")
                nova_senha = st.text_input("Nova Senha", type="password", key="rec_pass")
                conf_senha = st.text_input("Confirme a Nova Senha", type="password", key="rec_pass_conf")
                if st.form_submit_button("Salvar Nova Senha"):
                    n_senha, c_senha = nova_senha.strip(), conf_senha.strip()
                    if len(n_senha) > 0 and n_senha == c_senha:
                        st.session_state.usuarios_db[user_rec] = n_senha
                        st.success(f"Senha de {user_rec} alterada com sucesso!")
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
        "container": {"padding": "5px!important", "background-color": "#131f3a", "border-radius": "12px", "margin-bottom": "15px"},
        "icon": {"color": "#38bdf8", "font-size": "15px"},
        "nav-link": {"font-size": "14px", "text-align": "center", "margin": "2px", "color": "#94a3b8", "--hover-color": "#1e2d50"},
        "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600", "border-radius": "8px"},
    }
)

# --- HEADER DE USUÁRIO E FILTRO ---
c_head1, c_head2, c_head3 = st.columns([2, 1.2, 0.8])
with c_head1:
    st.markdown(f"### 👤 Usuário: **{st.session_state.user}**")
with c_head2:
    mes_ano = st.date_input("Filtro de Período", datetime.today(), label_visibility="collapsed")
    str_mes_ano = mes_ano.strftime("%Y-%m")
with c_head3:
    if st.button("🚪 Sair", key="btn_logout"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("<hr style='border: 0.5px solid #1e2d50; margin-top: 0px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# --- MÓDULO 1: DASHBOARD ---
if selected == "Dashboard":
    st.markdown("## 📊 Dashboard Financeiro")
    st.caption(f"Visão consolidada do mês: **{mes_ano.strftime('%b/%Y')}**")
    
    df_trans = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
    
    receitas = df_trans[df_trans['tipo'] == 'Receita']['valor'].sum() if not df_trans.empty else 0.0
    despesas = df_trans[df_trans['tipo'] == 'Despesa']['valor'].sum() if not df_trans.empty else 0.0
    saldo = receitas - despesas
    
    # 1. Cards Principais
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="custom-card"><div class="metric-title">Receitas</div><div class="metric-value val-rec">R$ {receitas:,.2f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="custom-card"><div class="metric-title">Despesas</div><div class="metric-value val-desp">R$ {despesas:,.2f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="custom-card"><div class="metric-title">Saldo Líquido</div><div class="metric-value val-saldo">R$ {saldo:,.2f}</div></div>', unsafe_allow_html=True)

    # 2. Regra Orçamentária 55 / 5 / 10 / 30
    st.markdown("### 📐 Distribuição Orçamentária Recomendada (Regra 55/5/10/30)")
    renda_base = receitas if receitas > 0 else 1.0
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        st.caption("Essenciais (55%)")
        st.progress(min(despesas / (renda_base * 0.55), 1.0))
        st.write(f"R$ {despesas:,.2f} / R$ {(renda_base * 0.55):,.2f}")
    with col_r2:
        st.caption("Educação (5%)")
        st.progress(0.0)
        st.write(f"R$ 0,00 / R$ {(renda_base * 0.05):,.2f}")
    with col_r3:
        st.caption("Metas/Invest (10%)")
        st.progress(0.0)
        st.write(f"R$ 0,00 / R$ {(renda_base * 0.10):,.2f}")
    with col_r4:
        st.caption("Livre/Lazer (30%)")
        st.progress(0.0)
        st.write(f"R$ 0,00 / R$ {(renda_base * 0.30):,.2f}")

    # 3. Gráfico de Despesas por Categoria (Plotly Dark Adaptativo)
    st.markdown("<br>", unsafe_allow_html=True)
    if not df_trans[df_trans['tipo'] == 'Despesa'].empty:
        df_cat = df_trans[df_trans['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
        fig = px.bar(
            df_cat, x='categoria', y='valor',
            title="Despesas por Categoria",
            text_auto='.2f',
            color='valor',
            color_continuous_scale='Reds'
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f8fafc'),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#1e2d50')
        )
        st.plotly_chart(fig, use_container_width=True)

# --- MÓDULO 2: LANÇAR ---
elif selected == "Lançar":
    st.markdown("## ➕ Lançar Transação")
    with st.form("form_transacao", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            tipo = st.radio("Tipo de Transação", ["Despesa", "Receita"], horizontal=True)
            categoria = st.selectbox("Categoria", ["Habitação", "Alimentação", "Saúde", "Transporte", "Educação", "Lazer", "Despesas Pessoais", "Dívidas", "Investimentos", "Outros"])
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        with f2:
            meio_pagamento = st.selectbox("Meio de Pagamento", ["PIX", "Cartão de Crédito", "Débito Automático", "Dinheiro", "Benefício"])
            data_trans = st.date_input("Data", datetime.today())
            usuario = st.selectbox("Quem está registrando?", ["Jack", "Loli"], index=0 if st.session_state.user == "Jack" else 1)
            
        obs = st.text_input("Observação (Opcional)")
        if st.form_submit_button("Salvar Transação"):
            execute_db("INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (tipo, categoria, valor, meio_pagamento, data_trans.strftime('%Y-%m-%d'), obs, usuario))
            st.success("Transação registrada com sucesso!")

# --- MÓDULO 3: METAS (Boleto Pessoal & Acompanhamento) ---
elif selected == "Metas":
    st.markdown("## 🎯 Gerenciador de Metas (Boleto Pessoal)")
    
    with st.expander("➕ Cadastrar Nova Meta"):
        with st.form("form_nova_meta"):
            n_nome = st.text_input("Nome da Meta")
            n_desc = st.text_input("Descrição")
            n_atual = st.number_input("Valor Já Acumulado (R$)", min_value=0.0)
            n_obj = st.number_input("Objetivo Final (R$)", min_value=1.0)
            n_prazo = st.text_input("Prazo Exemplo: 6 meses")
            if st.form_submit_button("Criar Meta"):
                execute_db("INSERT OR REPLACE INTO metas (nome, descricao, valor_atual, valor_objetivo, prazo) VALUES (?, ?, ?, ?, ?)",
                           (n_nome, n_desc, n_atual, n_obj, n_prazo))
                st.success("Meta criada!")
                st.rerun()

    df_metas = run_query("SELECT * FROM metas")
    for _, row in df_metas.iterrows():
        pct = min(row['valor_atual'] / row['valor_objetivo'], 1.0) if row['valor_objetivo'] > 0 else 0
        st.markdown(f"""
            <div class="custom-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:#38bdf8 !important;">{row['nome']}</h3>
                    <span style="color:#94a3b8; font-size:0.85rem;">Prazo: {row['prazo']}</span>
                </div>
                <p style="color:#94a3b8; margin:5px 0 15px 0;">{row['descricao']}</p>
                <div style="font-weight:bold; margin-bottom:8px;">
                    Acumulado: <span style="color:#10b981;">R$ {row['valor_atual']:,.2f}</span> / <span style="color:#f8fafc;">R$ {row['valor_objetivo']:,.2f}</span> ({pct*100:.1f}%)
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.progress(pct)

# --- MÓDULO 4: BENEFÍCIOS ---
elif selected == "Benefícios":
    st.markdown("## 🎁 Gestão de Benefícios e Vouchers")
    
    df_ben = run_query("SELECT * FROM beneficios")
    for _, row in df_ben.iterrows():
        saldo_ben = row['valor_mensal'] - row['valor_gasto']
        st.markdown(f"""
            <div class="custom-card">
                <h3 style="margin:0; color:#38bdf8 !important;">{row['nome']}</h3>
                <div style="display:flex; gap:30px; margin-top:10px;">
                    <div><span class="metric-title">Valor Mensal:</span><br><b>R$ {row['valor_mensal']:,.2f}</b></div>
                    <div><span class="metric-title">Já Utilizado:</span><br><b style="color:#f43f5e;">R$ {row['valor_gasto']:,.2f}</b></div>
                    <div><span class="metric-title">Saldo Restante:</span><br><b style="color:#10b981;">R$ {saldo_ben:,.2f}</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- MÓDULO 5: HISTÓRICO (Tabela Dark Customizada + Edição/Exclusão) ---
elif selected == "Histórico":
    st.markdown("## 📜 Histórico de Transações")
    df_hist = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
    
    if not df_hist.empty:
        # Tabela Dark HTML
        html_table = "<table class='dark-table'><thead><tr><th>ID</th><th>Data</th><th>Tipo</th><th>Categoria</th><th>Valor</th><th>Pagamento</th><th>Usuário</th><th>Obs</th></tr></thead><tbody>"
        for _, r in df_hist.iterrows():
            cor_v = "#10b981" if r['tipo'] == 'Receita' else "#f43f5e"
            html_table += f"<tr><td>{r['id']}</td><td>{r['data']}</td><td>{r['tipo']}</td><td>{r['categoria']}</td><td style='color:{cor_v}; font-weight:bold;'>R$ {r['valor']:,.2f}</td><td>{r['meio_pagamento']}</td><td>{r['usuario']}</td><td>{r['observacao']}</td></tr>"
        html_table += "</tbody></table>"
        st.markdown(html_table, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("🛠️ Excluir ou Gerenciar Transação"):
            id_del = st.number_input("Digite o ID da Transação para Excluir", min_value=1, step=1)
            if st.button("🗑️ Confirmar Exclusão"):
                execute_db("DELETE FROM lancamentos WHERE id = ?", (id_del,))
                st.success(f"Transação #{id_del} removida!")
                st.rerun()
    else:
        st.info("Nenhum registro encontrado para este mês.")

# --- MÓDULO 6: ORÇAMENTO ---
elif selected == "Orçamento":
    st.markdown("## 📑 Planejamento de Orçamento")
    st.info("Módulo pronto para definir limites teto por categoria de gasto.")
