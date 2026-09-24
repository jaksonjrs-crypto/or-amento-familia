import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
# Nova biblioteca para o menu atraente
from streamlit_option_menu import option_menu 

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Orçamento Doméstico - Jack & Loli", page_icon="💰", layout="wide")

# --- FUNÇÕES DE SEGURANÇA (LOGIN) ---
def fazer_hash(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def criar_tabela_usuarios():
    conn = sqlite3.connect("orcamento.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            nome TEXT,
            senha TEXT
        )
    """)
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('jack', 'Jakson', ?)", (fazer_hash("jack123"),))
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('loli', 'Lílian', ?)", (fazer_hash("loli123"),))
    conn.commit()
    conn.close()

def verificar_login(usuario, senha):
    conn = sqlite3.connect("orcamento.db")
    c = conn.cursor()
    c.execute("SELECT nome FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, fazer_hash(senha)))
    resultado = c.fetchone()
    conn.close()
    return resultado if resultado else None

# --- BANCO DE DADOS DOS LANÇAMENTOS ---
def criar_tabela_lancamentos():
    conn = sqlite3.connect("orcamento.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL,
            meio_pagamento TEXT,
            usuario TEXT
        )
    """)
    conn.commit()
    conn.close()

def inserir_lancamento(data, tipo, categoria, descricao, valor, meio_pagamento, usuario):
    conn = sqlite3.connect("orcamento.db")
    c = conn.cursor()
    c.execute("INSERT INTO lancamentos (data, tipo, categoria, descricao, valor, meio_pagamento, usuario) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (data, tipo, categoria, descricao, valor, meio_pagamento, usuario))
    conn.commit()
    conn.close()

def obter_dados():
    conn = sqlite3.connect("orcamento.db")
    df = pd.read_sql_query("SELECT * FROM lancamentos", conn)
    conn.close()
    return df

# --- INICIALIZAÇÃO DO APP ---
criar_tabela_usuarios()
criar_tabela_lancamentos()

if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["nome_usuario"] = ""
    st.session_state["username"] = ""

# --- TELA DE LOGIN ---
if not st.session_state["logado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_login_1, col_login_2, col_login_3 = st.columns([1, 1.5, 1])
    
    with col_login_2:
        st.markdown(
            """
            <div style='background-color: #1E1E1E; padding: 30px; border-radius: 15px; border: 1px solid #4A4A4A;'>
                <h2 style='text-align: center; color: #FFFFFF; margin-bottom: 25px;'>🔐 Finanças Jack & Loli</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
        with st.form("Formulário de Login"):
            usuario_input = st.text_input("Usuário").strip().lower()
            senha_input = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar no Painel", use_container_width=True)
            
            if botao_login:
                nome_confirmado = verificar_login(usuario_input, senha_input)
                if nome_confirmado:
                    st.session_state["logado"] = True
                    st.session_state["nome_usuario"] = nome_confirmado[0]
                    st.session_state["username"] = usuario_input
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

# --- APP AUTENTICADO ---
else:
    # --- NOVO MENU DE NAVEGAÇÃO ATRAENTE (SIDEBAR) ---
    with st.sidebar:
        st.markdown(f"<h3 style='text-align: center; color: #2ecc71;'>👋 Olá, {st.session_state['nome_usuario']}!</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Menu customizado com ícones modernos
        menu = option_menu(
            menu_title="Navegação",
            options=["Dashboard", "Novo Lançamento", "Histórico"],
            icons=["chart-pie", "pencil-square", "table"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5px!", "background-color": "#0E1117"},
                "icon": {"color": "#2ecc71", "font-size": "20px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"5px", "--hover-color": "#262730"},
                "nav-link-selected": {"background-color": "#2ecc71", "color": "black", "font-weight": "bold"},
            }
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["nome_usuario"] = ""
            st.session_state["username"] = ""
            st.rerun()

    # --- PÁGINA 1: DASHBOARD ---
    if menu == "Dashboard":
        st.markdown("<h2 style='color: #2ecc71;'>📊 Painel de Controle Orçamentário</h2>", unsafe_allow_html=True)
        df = obter_dados()
        
        if df.empty:
            st.info("Nenhum dado cadastrado ainda. Vá em 'Novo Lançamento' para começar!")
        else:
            df['data'] = pd.to_datetime(df['data'])
            df['Mes_Ano'] = df['data'].dt.strftime('%m/%Y')
            
            # Filtro de Mês estilizado na lateral direita
            col_titulo, col_filtro = st.columns([2, 1])
            with col_filtro:
                meses_disponiveis = sorted(df['Mes_Ano'].unique(), reverse=True)
                mes_selecionado = st.selectbox("📅 Selecione o Mês de Análise", meses_disponiveis)
            
            df_mes = df[df['Mes_Ano'] == mes_selecionado]
            
            receitas = df_mes[df_mes['tipo'] == 'Receita']['valor'].sum()
            despesas = df_mes[df_mes['tipo'] == 'Despesa']['valor'].sum()
            saldo = receitas - despesas
            
            # Cards de resumo visual atualizados
            col1, col2, col3 = st.columns(3)
            col1.metric("🟢 Renda Total do Mês", f"R$ {receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col2.metric("🔴 Despesas Totais", f"R$ {despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            # Cor dinâmica para o saldo (verde se positivo, vermelho se negativo)
            col3.metric("🔵 Saldo Final (Sobra)", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 
                        delta=f"R$ {saldo:,.2f}", delta_color="normal" if saldo >= 0 else "inverse")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                st.markdown("<h4>🍕 Distribuição de Despesas</h4>", unsafe_allow_html=True)
                df_despesas = df_mes[df_mes['tipo'] == 'Despesa']
                if not df_despesas.empty:
                    fig_pizza = px.pie(df_despesas, values='valor', names='categoria', hole=0.5,
                                       color_discrete_sequence=px.colors.qualitative.Safe)
                    fig_pizza.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_pizza, use_container_width=True)
                else:
                    st.write("Sem despesas para este mês.")
                    
            with col_graf2:
                st.markdown("<h4>📈 Evolução Mensal</h4>", unsafe_allow_html=True)
                df_historico = df.groupby(['Mes_Ano', 'tipo'])['valor'].sum().unstack().fillna(0).reset_index()
                fig_linha = px.line(df_historico, x='Mes_Ano', y=['Receita', 'Despesa'], markers=True,
                                    labels={'value': 'Valor (R$)', 'Mes_Ano': 'Mês/Ano'},
                                    color_discrete_map={'Receita': '#2ecc71', 'Despesa': '#e74c3c'})
                fig_linha.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig_linha, use_container_width=True)

    # --- PÁGINA 2: NOVO LANÇAMENTO ---
    elif menu == "Novo Lançamento":
        st.markdown("<h2 style='color: #2ecc71;'>📝 Adicionar Lançamento</h2>", unsafe_allow_html=True)
        
        with st.form("Formulário de Cadastro"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data do Fato", datetime.now())
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                
                if tipo == "Despesa":
                    categoria = st.selectbox("Categoria", ["HABITAÇÃO", "DIVÍDAS", "TRANSPORTE", "DESPESAS PESSOAIS", "SAÚDE", "LAZER", "EDUCAÇÃO", "OUTROS"])
                else:
                    categoria = st.selectbox("Categoria", ["Fonte de Renda Fixa", "Receitas Variáveis/Extras", "Benefícios"])
                    
            with col2:
                descricao = st.text_input("Descrição (Ex: Conta de Luz, Supermercado, etc.)")
                valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
                meio_pagamento = st.selectbox("Meio de Movimentação", ["Pix", "Transferência Bancária", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Vale/Benefício", "Débito Automático"])
                
            st.markdown("<br>", unsafe_allow_html=True)
            botao_salvar = st.form_submit_button("💾 Salvar Registro", use_container_width=True)
            
            if botao_salvar:
