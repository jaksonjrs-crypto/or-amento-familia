import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Jack & Loli - Finanças",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS MINIMALISTA (COMPATÍVEL COM WEB E MOBILE) ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 650px;
    }
    .card-metric {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .card-title { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; }
    .card-value { font-size: 1.3rem; font-weight: 700; margin-top: 2px; }
    .text-green { color: #10b981; }
    .text-red { color: #f43f5e; }
    .text-blue { color: #38bdf8; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DO GIST DA GITHUB ---
GIST_ID = st.secrets.get("GIST_ID", "")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")

def carregar_dados():
    if not GIST_ID or not GITHUB_TOKEN:
        st.warning("⚠️ Chaves do GitHub Gist não configuradas nos Secrets.")
        return pd.DataFrame()
    
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/gists/{GIST_ID}"
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            files = res.json().get("files", {})
            if "dados.json" in files:
                content = files["dados.json"]["content"]
                data = json.loads(content)
                return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    
    return pd.DataFrame()

def salvar_dados(df):
    if not GIST_ID or not GITHUB_TOKEN:
        st.error("⚠️ Não foi possível salvar: GIST_ID ou GITHUB_TOKEN faltando.")
        return False
    
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/gists/{GIST_ID}"
    
    payload = {
        "files": {
            "dados.json": {
                "content": json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2)
            }
        }
    }
    
    res = requests.patch(url, headers=headers, json=payload)
    return res.status_code == 200

# --- ESTRUTURA DA SUA PLANILHA (GRUPOS E SUBGRUPOS) ---
ESTRUTURA = {
    "Receitas Fixas": ["Fonte de Renda 1 (Lílian)", "Fonte de Renda 2 (Jakson)", "Outros"],
    "Receitas Variáveis": ["13º Salário Líquido", "Férias", "Bônus e extras"],
    "Boleto Pessoal (30%)": [
        "METINHAZINHA (3 meses)", "METINHA (6 meses)", 
        "META (1 ano)", "METONA (10 anos)", "METAZONA (30 anos)"
    ],
    "Habitação (55%)": [
        "Aluguel", "Condomínio", "IPTU", "Conta de água", "Conta de energia",
        "Seguro Residencial", "Conta de gás", "Celular+TV+internet", "Celular",
        "Streaming", "Supermercado", "Feira", "Semear", "Faxineira"
    ],
    "Dívidas (55%)": [
        "Financiamento", "Cheque especial", "Cartão Lílian", "Cartão Jakson",
        "Tributos atrasados", "Outros"
    ],
    "Saúde (55%)": ["Plano de Saúde", "Médicos e terapeutas", "Dentista", "Farmácia", "Outros"],
    "Transporte (55%)": [
        "Licenciamento + multas", "IPVA + Seguro Obrigatório", "Seguro de Carro",
        "Combustível", "Estacionamentos", "Lavagens", "Mecânico / Revisão",
        "Multas", "Pedágios + tag", "Apps de carro"
    ],
    "Despesas Pessoais (55%)": [
        "Pós Graduação", "Material escolar", "Higiene Pessoal", "Cosméticos",
        "Cabeleireiro", "Vestuário", "Academia", "Seguro de Vida", "Outros"
    ],
    "Educação (5%)": ["Cursos Extra Curriculares", "Livros", "Outros"],
    "Lazer (10%)": [
        "Restaurantes", "Cafés, bares e boates", "Livraria, jornais e revistas",
        "Spotify, música e outros", "Passeios", "Outros"
    ],
    "Outros Gastos (10%)": [
        "Tarifas Bancárias", "Ajuda aos pais", "Doações / Dízimos", "Extras diários",
        "Manutenção e reparos", "Médicos e remédios esporádicos", "Suplementos",
        "Presentes", "Utilidades domésticas e decoração", "Outros"
    ],
    "Benefícios": ["Vale Refeição", "Vale Alimentação", "Vale Combustível", "Outros"]
}

# --- GERENCIAMENTO DE NAVEGAÇÃO ---
if "page" not in st.session_state:
    st.session_state.page = "Lançar"

if "usuario" not in st.session_state:
    st.session_state.usuario = "Jack"

# --- CABEÇALHO RESPONSIVO ---
col_u1, col_u2 = st.columns([2, 1])
with col_u1:
    st.title("💳 Finanças Jack & Loli")
with col_u2:
    st.session_state.usuario = st.selectbox("Usuário", ["Jack", "Loli"], index=0 if st.session_state.usuario == "Jack" else 1)

# --- BOTÕES DE NAVEGAÇÃO NATIVOS (Garantidos no Mobile) ---
c_nav1, c_nav2, c_nav3 = st.columns(3)
with c_nav1:
    if st.button("➕ Lançar", use_container_width=True, type="primary" if st.session_state.page == "Lançar" else "secondary"):
        st.session_state.page = "Lançar"
        st.rerun()
with c_nav2:
    if st.button("📊 Resumo", use_container_width=True, type="primary" if st.session_state.page == "Resumo" else "secondary"):
        st.session_state.page = "Resumo"
        st.rerun()
with c_nav3:
    if st.button("📜 Histórico", use_container_width=True, type="primary" if st.session_state.page == "Histórico" else "secondary"):
        st.session_state.page = "Histórico"
        st.rerun()

st.markdown("---")

# ==========================================
# 1. TELA: LANÇAR (FIEL À PLANILHA)
# ==========================================
if st.session_state.page == "Lançar":
    st.subheader("➕ Novo Lançamento")
    
    # Tipo de Lançamento
    tipo = st.radio("Tipo de Operação", ["Despesa", "Receita", "Boleto Pessoal (Investimento)", "Benefício"], horizontal=True)
    
    # Filtro de Grupos
    if tipo == "Receita":
        grupos_validos = ["Receitas Fixas", "Receitas Variáveis"]
    elif tipo == "Boleto Pessoal (Investimento)":
        grupos_validos = ["Boleto Pessoal (30%)"]
    elif tipo == "Benefício":
        grupos_validos = ["Benefícios"]
    else:
        grupos_validos = [
            "Habitação (55%)", "Dívidas (55%)", "Saúde (55%)", "Transporte (55%)",
            "Despesas Pessoais (55%)", "Educação (5%)", "Lazer (10%)", "Outros Gastos (10%)"
        ]

    # Seleção do Grupo
    grupo_selecionado = st.selectbox("Grupo (Categoria)", grupos_validos)
    
    # Seleção do Subgrupo encadeado
    subgrupos_validos = ESTRUTURA.get(grupo_selecionado, [])
    subgrupo_selecionado = st.selectbox("Subgrupo (Item)", subgrupos_validos)
    
    with st.form("form_lancamento", clear_on_submit=True):
        valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        meio_pagamento = st.selectbox("Meio de Rec. / Pagamento", [
            "Transferência Bancária", "Pix", "Cartão de Crédito", "Cartão de Débito",
            "Ticket Restaurante", "Sodexo", "Dinheiro"
        ])
        data_lancamento = st.date_input("Data", datetime.today())
        observacao = st.text_input("Observação / Detalhe (Opcional)")
        
        btn_salvar = st.form_submit_button("Salvar no Gist", use_container_width=True, type="primary")
        
        if btn_salvar:
            novo_registro = {
                "id": int(datetime.now().timestamp()),
                "data": data_lancamento.strftime("%Y-%m-%d"),
                "tipo": tipo,
                "grupo": grupo_selecionado,
                "subgrupo": subgrupo_selecionado,
                "valor": float(valor),
                "meio_pagamento": meio_pagamento,
                "usuario": st.session_state.usuario,
                "observacao": observacao
            }
            
            df_atual = carregar_dados()
            df_novo = pd.concat([df_atual, pd.DataFrame([novo_registro])], ignore_index=True)
            
            if salvar_dados(df_novo):
                st.success(f"✅ Lançamento de R$ {valor:,.2f} salvo com sucesso!")
            else:
                st.error("❌ Erro ao salvar dados no Gist. Verifique suas chaves.")

# ==========================================
# 2. TELA: RESUMO (ESTILO MÊS PLANILHA)
# ==========================================
elif st.session_state.page == "Resumo":
    st.subheader("📊 Resumo Mensal")
    df = carregar_dados()
    
    if not df.empty:
        df["data"] = pd.to_datetime(df["data"])
        mes_ano_sel = st.date_input("Mês de Referência", datetime.today()).strftime("%Y-%m")
        
        df_mes = df[df["data"].dt.strftime("%Y-%m") == mes_ano_sel]
        
        rec = df_mes[df_mes["tipo"] == "Receita"]["valor"].sum()
        desp = df_mes[df_mes["tipo"] == "Despesa"]["valor"].sum()
        inv = df_mes[df_mes["tipo"] == "Boleto Pessoal (Investimento)"]["valor"].sum()
        saldo = rec - desp - inv
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="card-metric"><div class="card-title">Receita</div><div class="card-value text-green">R$ {rec:,.2f}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card-metric"><div class="card-title">Despesas</div><div class="card-value text-red">R$ {desp:,.2f}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card-metric"><div class="card-title">Saldo</div><div class="card-value {"text-blue" if saldo >= 0 else "text-red"}">R$ {saldo:,.2f}</div></div>', unsafe_allow_html=True)

        if not df_mes.empty:
            st.markdown("### Total por Grupo")
            resumo_grupo = df_mes.groupby(["grupo", "tipo"])["valor"].sum().reset_index()
            st.dataframe(resumo_grupo, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum lançamento neste mês.")
    else:
        st.info("Nenhum dado encontrado no Gist.")

# ==========================================
# 3. TELA: HISTÓRICO
# ==========================================
elif st.session_state.page == "Histórico":
    st.subheader("📜 Todos os Lançamentos")
    df = carregar_dados()
    
    if not df.empty:
        df = df.sort_values(by="data", ascending=False)
        st.dataframe(
            df[["data", "usuario", "tipo", "grupo", "subgrupo", "valor", "meio_pagamento", "observacao"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum dado salvo até o momento.")
