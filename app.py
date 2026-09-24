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

# --- CSS CUSTOMIZADO (Visual Dark elegante, Responsivo para Celular e Correção de Fontes Escuras) ---
st.markdown("""
<style>
    /* Tags Meta para WebApp / PWA no Celular */
    @media screen {
        body {
            -webkit-user-select: none;
            -webkit-tap-highlight-color: transparent;
        }
    }
    
    /* Estilo global dark */
    .stApp {
        background-color: #0b1120;
        color: #f1f5f9 !important;
    }
    
    /* Forçar cores claras em todos os textos, inputs e selectboxes */
    p, span, label, div, h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
    }
    
    /* Forçar texto visível em caixas de entrada (Inputs/Selectbox/Formulários) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div {
        color: #f1f5f9 !important;
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }
    
    /* Corrigir texto dentro dos menus dropdown / opções */
    div[data-baseweb="popover"] div, div[data-baseweb="menu"] div, option {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }
    
    /* Ocultar elementos desnecessários */
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
    
    /* Estilo dos Expandores no Histórico */
    .streamlit-expanderHeader {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border-radius: 8px;
    }
    
    /* Ajuste de botões */
    .stButton>button {
        border-radius: 8px;
        background-color: #2563eb;
        color: white !important;
        border: none;
        font-weight: 600;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }
</style>
""", unsafe_allow_html=True)

# --- BANCO DE DADOS (SQLite) ---
DB_NAME = "orcamento.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de Usuários (Login)
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            senha TEXT
        )
    ''')
    
    # Tabela de Lançamentos
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
    
    # Tabela de Metas
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
    
    # Tabela de Benefícios
    c.execute('''
        CREATE TABLE IF NOT EXISTS beneficios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE,
            valor_mensal REAL,
            valor_gasto REAL
        )
    ''')
    
    # Inserir usuários padrão (se não existirem)
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('Jack', '1234')")
        c.execute("INSERT INTO usuarios VALUES ('Loli', '1234')")
        
    # Inserção de dados iniciais para Metas (se vazio)
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
        
    # Inserção de dados iniciais para Benefícios (se vazio)
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

init_db()

# --- FUNÇÕES AUXILIARES DE BANCO ---
def run_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_db(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

# --- SISTEMA DE AUTENTICAÇÃO E LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

def tela_login():
    st.markdown("<h2 style='text-align: center;'>🔐 Acesso Restrito - Jack & Loli</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Entre com suas credenciais para acessar o orçamento doméstico.</p>", unsafe_allow_html=True)
    
    col_cen1, col_cen2, col_cen3 = st.columns([1, 2, 1])
    with col_cen2:
        tab_entrar, tab_esqueci = st.tabs(["🔑 Entrar", "🔄 Alterar / Esqueci a Senha"])
        
        with tab_entrar:
            user = st.selectbox("Usuário", ["Jack", "Loli"])
            senha = st.text_input("Senha", type="password")
            if st.button("Acessar App"):
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
            
            if st.button("Salvar Nova Senha"):
                if nova_senha and nova_senha == conf_senha:
                    execute_db("UPDATE usuarios SET senha = ? WHERE username = ?", (nova_senha, user_rec))
                    st.success("Senha alterada com sucesso! Agora você pode entrar.")
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

# --- CABEÇALHO COM SELEÇÃO DE PERÍODO E SAÍDA ---
col_head1, col_head2, col_head3 = st.columns([2, 1, 1])
with col_head1:
    st.markdown(f"### 🔄 **Jack & Loli** ({st.session_state.user})")
with col_head2:
    mes_ano = st.date_input("Filtro de Período", datetime.today(), label_visibility="collapsed")
    str_mes_ano = mes_ano.strftime("%Y-%m")
with col_head3:
    if st.button("🚪 Sair"):
        st.session_state.logged_in = False
        st.rerun()

# --- MÓDULO 1: DASHBOARD ---
if selected == "Dashboard":
    st.markdown("## 📊 Dashboard")
    st.caption(f"Visão geral do mês ({mes_ano.strftime('%b/%Y')})")
    
    # Busca de dados do mês
    df_transacoes = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ?", (str_mes_ano,))
    
    receitas = df_transacoes[df_transacoes['tipo'] == 'Receita']['valor'].sum() if not df_transacoes.empty else 0.0
    despesas = df_transacoes[df_transacoes['tipo'] == 'Despesa']['valor'].sum() if not df_transacoes.empty else 0.0
    saldo = receitas - despesas
    renda_base = receitas if receitas > 0 else 1.0
    
    # Top Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-title">Receitas</div>
            <div class="card-value val-positive">R$ {receitas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-title">Despesas</div>
            <div class="card-value val-negative">R$ {despesas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        cor_s = "val-positive" if saldo >= 0 else "val-negative"
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-title">Saldo</div>
            <div class="card-value {cor_s}">R$ {saldo:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="card-metric">
            <div class="card-title">Renda Base</div>
            <div class="card-value val-neutral">R$ {receitas:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    # Regra Orçamentária (55/5/10/30)
    st.markdown("---")
    st.markdown("### 🎯 Regra Orçamentária (55/5/10/30)")
    
    metas_regra = {
        "Essenciais (55%)": (0.55 * renda_base, df_transacoes[df_transacoes['categoria'].isin(['Habitação', 'Alimentação', 'Saúde', 'Transporte'])]['valor'].sum() if not df_transacoes.empty else 0),
        "Educação (5%)": (0.05 * renda_base, df_transacoes[df_transacoes['categoria'] == 'Educação']['valor'].sum() if not df_transacoes.empty else 0),
        "Livres (10%)": (0.10 * renda_base, df_transacoes[df_transacoes['categoria'].isin(['Lazer', 'Despesas Pessoais'])]['valor'].sum() if not df_transacoes.empty else 0),
        "Metas/Investimentos (30%)": (0.30 * renda_base, df_transacoes[df_transacoes['categoria'] == 'Investimentos']['valor'].sum() if not df_transacoes.empty else 0)
    }
    
    with st.container():
        for nome, (limite, gasto) in metas_regra.items():
            pct = min(gasto / limite if limite > 0 else 0.0, 1.0)
            col_r1, col_r2 = st.columns([3, 1])
            with col_r1:
                st.write(f"**{nome}**")
                st.progress(pct)
            with col_r2:
                st.write(f"R$ {gasto:,.2f} / R$ {limite:,.2f}")

    # Gráficos de Despesas e Metas
    st.markdown("---")
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        st.markdown("### 🍰 Despesas por Categoria")
        if not df_transacoes.empty and despesas > 0:
            df_desp = df_transacoes[df_transacoes['tipo'] == 'Despesa'].groupby('categoria')['valor'].sum().reset_index()
            red_shades = ['#e11d48', '#f43f5e', '#fb7185', '#fda4af', '#9f1239', '#881337', '#be123c']
            
            fig = px.pie(
                df_desp, 
                values='valor', 
                names='categoria', 
                hole=0.4,
                color_discrete_sequence=red_shades
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f1f5f9'),
                margin=dict(t=20, b=20, l=10, r=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada neste período.")
            
    with g_col2:
        st.markdown("### 📈 Progresso das Metas")
        df_metas = run_query("SELECT * FROM metas")
        if not df_metas.empty:
            df_metas['Progresso (%)'] = (df_metas['valor_atual'] / df_metas['valor_objetivo']) * 100
            fig_metas = px.bar(
                df_metas,
                x='Progresso (%)',
                y='nome',
                orientation='h',
                text=df_metas['Progresso (%)'].apply(lambda x: f"{x:.1f}%"),
                color_discrete_sequence=['#38bdf8']
            )
            fig_metas.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f1f5f9'),
                xaxis=dict(range=[0, 100], showgrid=False),
                yaxis=dict(title=None),
                margin=dict(t=20, b=20, l=10, r=10)
            )
            st.plotly_chart(fig_metas, use_container_width=True)

# --- MÓDULO 2: LANÇAR TRANSAÇÃO ---
elif selected == "Lançar":
    st.markdown("## ➕ Lançar Transação")
    st.caption("Registre novas receitas e despesas com praticidade.")
    
    with st.form("form_transacao", clear_on_submit=True):
        tipo = st.radio("Tipo de Transação", ["Despesa", "Receita"], horizontal=True)
        
        c_cat, c_val = st.columns(2)
        with c_cat:
            categoria = st.selectbox("Categoria", [
                "Habitação", "Alimentação", "Saúde", "Transporte", 
                "Educação", "Lazer", "Despesas Pessoais", "Dívidas", 
                "Investimentos", "Receita Fixa", "Outros"
            ])
        with c_val:
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
            
        c_meio, c_data = st.columns(2)
        with c_meio:
            meio_pagamento = st.selectbox("Meio de Pagamento", [
                "PIX", "Cartão de Crédito", "Débito Automático", 
                "Transferência Bancária", "Dinheiro", "Benefício"
            ])
        with c_data:
            data_trans = st.date_input("Data", datetime.today())
            
        c_obs, c_user = st.columns(2)
        with c_obs:
            obs = st.text_input("Observação (Opcional)")
        with c_user:
            usuario = st.selectbox("Quem está registrando?", ["Jack", "Loli"], index=0 if st.session_state.user == "Jack" else 1)
            
        submitted = st.form_submit_button("Lançar Transação")
        if submitted:
            execute_db(
                "INSERT INTO lancamentos (tipo, categoria, valor, meio_pagamento, data, observacao, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tipo, categoria, valor, meio_pagamento, data_trans.strftime('%Y-%m-%d'), obs, usuario)
            )
            st.success("Transação lançada com sucesso!")

# --- MÓDULO 3: METAS (BOLETO PESSOAL) ---
elif selected == "Metas":
    st.markdown("## 🎯 Metas (Boleto Pessoal)")
    st.caption("Acompanhe suas conquistas por nível e atualize seus saldos.")
    
    df_metas = run_query("SELECT * FROM metas")
    
    for _, row in df_metas.iterrows():
        pct = min(row['valor_atual'] / row['valor_objetivo'] if row['valor_objetivo'] > 0 else 0.0, 1.0)
        with st.expander(f"📌 **{row['nome']}** — R$ {row['valor_atual']:,.2f} / R$ {row['valor_objetivo']:,.2f} ({pct*100:.1f}%)"):
            st.write(f"**Descrição:** {row['descricao']}")
            st.write(f"**Prazo Recomendado:** {row['prazo']}")
            st.progress(pct)
            
            with st.form(f"form_meta_{row['id']}"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    novo_atual = st.number_input("Valor Atual Salvo (R$)", value=float(row['valor_atual']), key=f"act_{row['id']}")
                with col_m2:
                    novo_obj = st.number_input("Meta / Objetivo (R$)", value=float(row['valor_objetivo']), key=f"obj_{row['id']}")
                
                if st.form_submit_button("Atualizar Meta"):
                    execute_db("UPDATE metas SET valor_atual = ?, valor_objetivo = ? WHERE id = ?", (novo_atual, novo_obj, row['id']))
                    st.success(f"Meta '{row['nome']}' atualizada!")
                    st.rerun()

    st.markdown("---")
    st.markdown("### ➕ Adicionar Nova Meta")
    with st.form("nova_meta", clear_on_submit=True):
        nome_meta = st.text_input("Nome da Meta")
        desc_meta = st.text_input("Descrição")
        c_v1, c_v2, c_v3 = st.columns(3)
        with c_v1:
            val_in = st.number_input("Valor Inicial (R$)", min_value=0.0)
        with c_v2:
            val_ob = st.number_input("Objetivo Final (R$)", min_value=1.0)
        with c_v3:
            prz = st.text_input("Prazo estimado")
            
        if st.form_submit_button("Cadastrar Nova Meta"):
            if nome_meta:
                try:
                    execute_db("INSERT INTO metas (nome, descricao, valor_atual, valor_objetivo, prazo) VALUES (?, ?, ?, ?, ?)",
                               (nome_meta, desc_meta, val_in, val_ob, prz))
                    st.success("Nova meta cadastrada!")
                    st.rerun()
                except:
                    st.error("Já existe uma meta com esse nome!")

# --- MÓDULO 4: BENEFÍCIOS ---
elif selected == "Benefícios":
    st.markdown("## 🎁 Benefícios")
    st.caption("Controle de vales (Alimentação, Refeição, Combustível).")
    
    df_ben = run_query("SELECT * FROM beneficios")
    
    cols = st.columns(len(df_ben) if len(df_ben) > 0 else 1)
    for idx, (_, row) in enumerate(df_ben.iterrows()):
        saldo_b = row['valor_mensal'] - row['valor_gasto']
        with cols[idx % len(cols)]:
            st.markdown(f"""
            <div class="card-metric">
                <div class="card-title">{row['nome']}</div>
                <div style="font-size: 0.9rem; margin-top:5px;">Mensal: <b>R$ {row['valor_mensal']:,.2f}</b></div>
                <div style="font-size: 0.9rem;">Gasto: <b style="color:#f87171">R$ {row['valor_gasto']:,.2f}</b></div>
                <div class="card-value val-positive" style="font-size: 1.3rem; margin-top:8px;">Saldo: R$ {saldo_b:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.popover(f"⚙️ Editar {row['nome']}"):
                with st.form(f"form_ben_{row['id']}"):
                    nm = st.number_input("Valor Mensal do Benefício", value=float(row['valor_mensal']))
                    ng = st.number_input("Valor Já Gasto", value=float(row['valor_gasto']))
                    if st.form_submit_button("Salvar Benefício"):
                        execute_db("UPDATE beneficios SET valor_mensal = ?, valor_gasto = ? WHERE id = ?", (nm, ng, row['id']))
                        st.success("Atualizado!")
                        st.rerun()

    st.markdown("---")
    st.markdown("### ➕ Cadastrar Novo Benefício")
    with st.form("novo_beneficio", clear_on_submit=True):
        nb_nome = st.text_input("Nome do Benefício (Ex: Vale Plano de Saúde)")
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            nb_mensal = st.number_input("Carga Mensal (R$)", min_value=0.0)
        with c_b2:
            nb_gasto = st.number_input("Gasto Atual (R$)", min_value=0.0)
            
        if st.form_submit_button("Cadastrar Benefício"):
            if nb_nome:
                try:
                    execute_db("INSERT INTO beneficios (nome, valor_mensal, valor_gasto) VALUES (?, ?, ?)",
                               (nb_nome, nb_mensal, nb_gasto))
                    st.success("Benefício adicionado!")
                    st.rerun()
                except:
                    st.error("Benefício já cadastrado com esse nome.")

# --- MÓDULO 5: HISTÓRICO & GERADOR DE RELATÓRIO PDF ---
elif selected == "Histórico":
    st.markdown("## 📜 Histórico de Transações")
    st.caption("Pesquise, edite, exclua ou imprima seus relatórios financeiros.")
    
    df_all = run_query("SELECT * FROM lancamentos WHERE strftime('%Y-%m', data) = ? ORDER BY data DESC", (str_mes_ano,))
    
    # Gerador de Relatório Impresso / PDF (HTML Impresso)
    if not df_all.empty:
        rec_tot = df_all[df_all['tipo'] == 'Receita']['valor'].sum()
        desp_tot = df_all[df_all['tipo'] == 'Despesa']['valor'].sum()
        saldo_tot = rec_tot - desp_tot
        
        # Criação da página HTML formatada para impressão
        html_report = f"""
        <html>
        <head>
            <title>Relatório Financeiro - {mes_ano.strftime('%m/%Y')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; color: #333; }}
                h1 {{ color: #1e293b; text-align: center; }}
                .summary {{ display: flex; justify-content: space-between; background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #cbd5e1; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; }}
                th {{ background-color: #0f172a; color: white; }}
                .despesa {{ color: #dc2626; font-weight: bold; }}
                .receita {{ color: #16a34a; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Jack & Loli - Relatório Financeiro ({mes_ano.strftime('%m/%Y')})</h1>
            <div class="summary">
                <div><b>Receitas:</b> R$ {rec_tot:,.2f}</div>
                <div><b>Despesas:</b> R$ {desp_tot:,.2f}</div>
                <div><b>Saldo Final:</b> R$ {saldo_tot:,.2f}</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Tipo</th>
                        <th>Categoria</th>
                        <th>Valor (R$)</th>
                        <th>Pagamento</th>
                        <th>Resp.</th>
                        <th>Obs.</th>
                    </tr>
                </thead>
                <tbody>
        """
        for _, r in df_all.iterrows():
            cor_cls = "despesa" if r['tipo'] == "Despesa" else "receita"
            html_report += f"""
                <tr>
                    <td>{r['data']}</td>
                    <td class="{cor_cls}">{r['tipo']}</td>
                    <td>{r['categoria']}</td>
                    <td>R$ {r['valor']:,.2f}</td>
                    <td>{r['meio_pagamento']}</td>
                    <td>{r['usuario']}</td>
                    <td>{r['observacao'] if r['observacao'] else ''}</td>
                </tr>
            """
        html_report += """
                </tbody>
            </table>
            <script>window.print();</script>
        </body>
        </html>
        """
        
        b64 = base64.b64encode(html_report.encode()).decode()
        href = f'<a href="data:text/html;base64,{b64}" download="Relatorio_{str_mes_ano}.html" style="background-color:#2563eb; color:white; padding:10px 18px; border-radius:8px; text-decoration:none; font-weight:bold; display:inline-block; margin-bottom:15px;">🖨️ Baixar / Imprimir Relatório PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

    if not df_all.empty:
        f_tipo = st.multiselect("Filtrar por Tipo", options=["Despesa", "Receita"], default=["Despesa", "Receita"])
        df_filtered = df_all[df_all['tipo'].isin(f_tipo)]
        
        st.markdown("---")
        for _, row in df_filtered.iterrows():
            cor_txt = "🔴" if row['tipo'] == "Despesa" else "🟢"
            with st.expander(f"{cor_txt} {row['data']} - **{row['categoria']}**: R$ {row['valor']:,.2f} ({row['usuario']})"):
                col_e1, col_e2 = st.columns([3, 1])
                with col_e1:
                    st.write(f"**Meio de Pagamento:** {row['meio_pagamento']}")
                    st.write(f"**Observação:** {row['observacao'] if row['observacao'] else 'Sem observação'}")
                with col_e2:
                    if st.button("🗑️ Deletar", key=f"del_{row['id']}"):
                        execute_db("DELETE FROM lancamentos WHERE id = ?", (row['id'],))
                        st.warning("Lançamento removido com sucesso!")
                        st.rerun()
                
                st.markdown("---")
                st.caption("Editar este lançamento:")
                with st.form(f"edit_form_{row['id']}"):
                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        e_cat = st.text_input("Categoria", value=row['categoria'])
                        e_val = st.number_input("Valor", value=float(row['valor']))
                    with e_c2:
                        e_obs = st.text_input("Observação", value=row['observacao'] if row['observacao'] else "")
                        e_data = st.text_input("Data (AAAA-MM-DD)", value=str(row['data']))
                        
                    if st.form_submit_button("Salvar Alterações"):
                        execute_db("UPDATE lancamentos SET categoria = ?, valor = ?, observacao = ?, data = ? WHERE id = ?",
                                   (e_cat, e_val, e_obs, e_data, row['id']))
                        st.success("Lançamento atualizado!")
                        st.rerun()
    else:
        st.info("Nenhum lançamento encontrado neste mês.")

# --- MÓDULO 6: ORÇAMENTO ---
elif selected == "Orçamento":
    st.markdown("## 📑 Orçamento e Limites por Categoria")
    st.caption("Defina limites mensais para acompanhar o teto de gastos.")
    
    categorias = ["Habitação", "Dívidas", "Saúde", "Transporte", "Despesas Pessoais", "Educação", "Lazer"]
    df_trans_m = run_query("SELECT categoria, SUM(valor) as total FROM lancamentos WHERE tipo = 'Despesa' AND strftime('%Y-%m', data) = ? GROUP BY categoria", (str_mes_ano,))
    
    gastos_dict = dict(zip(df_trans_m['categoria'], df_trans_m['total'])) if not df_trans_m.empty else {}
    
    for cat in categorias:
        gasto_cat = gastos_dict.get(cat, 0.0)
        with st.container():
            st.markdown(f"""
            <div class="card-metric">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:1.1rem; font-weight:700;">{cat}</span>
                    <span style="color:#94a3b8;">Gasto Atual: <b>R$ {gasto_cat:,.2f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
