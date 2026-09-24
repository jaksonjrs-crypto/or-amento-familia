import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

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
    # Cria os usuários padrão se não existirem (Senhas iniciais: jack123 e loli123)
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
    return resultado[0] if resultado else None

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

# --- SISTEMA DE SESSÃO DO STREAMLIT ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
    st.session_state["nome_usuario"] = ""
    st.session_state["username"] = ""

# --- TELA DE LOGIN ---
if not st.session_state["logado"]:
    st.markdown("<h1 style='text-align: center;'>🔐 Orçamento Jack & Loli</h1>", unsafe_allow_html=True)
    
    with st.form("Formulário de Login"):
        usuario_input = st.text_input("Usuário").strip().lower()
        senha_input = st.text_input("Senha", type="password")
        botao_login = st.form_submit_button("Entrar")
        
        if botao_login:
            nome_confirmado = verificar_login(usuario_input, senha_input)
            if nome_confirmado:
                st.session_state["logado"] = True
                st.session_state["nome_usuario"] = nome_confirmado
                st.session_state["username"] = usuario_input
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# --- APP AUTENTICADO ---
else:
    # Sidebar
    st.sidebar.title(f"👋 Olá, {st.session_state['nome_usuario']}!")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "📝 Novo Lançamento", "📋 Histórico de Lançamentos"])
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state["logado"] = False
        st.session_state["nome_usuario"] = ""
        st.session_state["username"] = ""
        st.rerun()

    # --- PÁGINA 1: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.title("📊 Painel de Controle Orçamentário")
        df = obter_dados()
        
        if df.empty:
            st.info("Nenhum dado cadastrado ainda. Vá em 'Novo Lançamento' para começar!")
        else:
            # Tratamento de datas
            df['data'] = pd.to_datetime(df['data'])
            df['Mes_Ano'] = df['data'].dt.strftime('%m/%Y')
            
            # Filtro de Mês no Topo
            meses_disponiveis = df['Mes_Ano'].unique()
            mes_selecionado = st.selectbox("Selecione o Mês de Análise", meses_disponiveis)
            
            # Filtrando dados pelo mês selecionado
            df_mes = df[df['Mes_Ano'] == mes_selecionado]
            
            # Cálculos de KPI
            receitas = df_mes[df_mes['tipo'] == 'Receita']['valor'].sum()
            despesas = df_mes[df_mes['tipo'] == 'Despesa']['valor'].sum()
            saldo = receitas - despesas
            
            # Cards de resumo visual
            col1, col2, col3 = st.columns(3)
            col1.metric("🟢 Renda Total do Mês", f"R$ {receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col2.metric("🔴 Despesas Totais", f"R$ {despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col3.metric("🔵 Saldo Final (Sobra)", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 
                        delta=f"R$ {saldo:,.2f}", delta_color="normal" if saldo >= 0 else "inverse")
            
            st.markdown("---")
            
            # Gráficos
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                st.subheader("🍕 Distribuição de Despesas por Categoria")
                df_despesas = df_mes[df_mes['tipo'] == 'Despesa']
                if not df_despesas.empty:
                    fig_pizza = px.pie(df_despesas, values='valor', names='categoria', hole=0.4,
                                       color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig_pizza, use_container_width=True)
                else:
                    st.write("Sem despesas para este mês.")
                    
            with col_graf2:
                st.subheader("📈 Evolução Financeira Histórica")
                df_historico = df.groupby(['Mes_Ano', 'tipo'])['valor'].sum().unstack().fillna(0).reset_index()
                fig_linha = px.line(df_historico, x='Mes_Ano', y=['Receita', 'Despesa'], markers=True,
                                    labels={'value': 'Valor (R$)', 'Mes_Ano': 'Mês/Ano'},
                                    color_discrete_map={'Receita': '#2ecc71', 'Despesa': '#e74c3c'})
                st.plotly_chart(fig_linha, use_container_width=True)

    # --- PÁGINA 2: NOVO LANÇAMENTO ---
    elif menu == "📝 Novo Lançamento":
        st.title("📝 Adicionar Lançamento")
        
        with st.form("Formulário de Cadastro"):
            col1, col2 = st.columns(2)
            with col1:
                data = st.date_input("Data do Fato", datetime.now())
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                
                # Dinamismo de categorias com base nas suas fornecidas
                if tipo == "Despesa":
                    categoria = st.selectbox("Categoria", ["HABITAÇÃO", "DIVÍDAS", "TRANSPORTE", "DESPESAS PESSOAIS", "SAÚDE", "LAZER", "EDUCAÇÃO", "OUTROS"])
                else:
                    categoria = st.selectbox("Categoria", ["Fonte de Renda Fixa", "Receitas Variáveis/Extras", "Benefícios"])
                    
            with col2:
                descricao = st.text_input("Descrição (Ex: Conta de Luz, Pix da Mãe, etc.)")
                valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
                meio_pagamento = st.selectbox("Meio de Movimentação", ["Pix", "Transferência Bancária", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Vale/Benefício", "Débito Automático"])
                
            botao_salvar = st.form_submit_button("💾 Salvar Registro")
            
            if botao_salvar:
                inserir_lancamento(data.strftime('%Y-%m-%d'), tipo, categoria, descricao, valor, meio_pagamento, st.session_state["nome_usuario"])
                st.success("Registro adicionado com sucesso ao banco de dados!")

    # --- PÁGINA 3: HISTÓRICO DE LANÇAMENTOS ---
    elif menu == "📋 Histórico de Lançamentos":
        st.title("📋 Todos os Registros")
        df = obter_dados()
        
        if df.empty:
            st.info("Nenhum registro encontrado.")
        else:
            # Permite visualizar em formato de tabela organizada e deletar registros se necessário
            st.dataframe(df.sort_values(by="data", ascending=False), use_container_width=True)

