import streamlit as st
import pandas as pd
import requests
import json
import io
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Finanças J&L",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* Oculta barra do Streamlit e rodapé */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }

    /* Ajuste de espaçamento no mobile */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 650px;
    }
    
    /* Estilo das abas */
    button[data-baseweb="tab"] {
        padding-left: 8px !important;
        padding-right: 8px !important;
        font-size: 0.85rem !important;
    }
    
    /* Cards de Resumo */
    .card-metric {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        margin-bottom: 8px;
    }
    .card-title { color: #94a3b8; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
    .card-value { font-size: 1.1rem; font-weight: 700; margin-top: 2px; }
    .text-green { color: #10b981; }
    .text-red { color: #f43f5e; }
    .text-blue { color: #38bdf8; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DO GIST DO GITHUB ---
GIST_ID = st.secrets.get("GIST_ID", "")
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")

def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Financas-App-Streamlit"
    }

def carregar_dados():
    if not GIST_ID or not GITHUB_TOKEN:
        st.error("⚠️ Configurações de GIST_ID ou GITHUB_TOKEN faltando nos Secrets.")
        return pd.DataFrame()
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    try:
        res = requests.get(url, headers=get_headers(), timeout=10)
        if res.status_code == 200:
            files = res.json().get("files", {})
            if "dados.json" in files:
                content = files["dados.json"].get("content", "[]")
                if content.strip():
                    data = json.loads(content)
                    return pd.DataFrame(data)
                return pd.DataFrame()
        else:
            st.error(f"Erro ao acessar Gist ({res.status_code}): {res.text}")
    except Exception as e:
        st.error(f"Erro de conexão com o GitHub: {e}")
    
    return pd.DataFrame()

def salvar_dados(df):
    if not GIST_ID or not GITHUB_TOKEN:
        st.error("⚠️ Não foi possível salvar: GIST_ID ou GITHUB_TOKEN faltando.")
        return False
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    payload = {
        "files": {
            "dados.json": {
                "content": json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2)
            }
        }
    }
    try:
        res = requests.patch(url, headers=get_headers(), json=payload, timeout=10)
        if res.status_code == 200:
            return True
        else:
            st.error(f"Erro ao salvar no Gist ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        st.error(f"Erro ao conectar com o GitHub: {e}")
        return False

# --- AUTENTICAÇÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = ""

if not st.session_state.autenticado:
    st.markdown("<h3 style='text-align: center;'>🔐 Finanças J&L</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Faça login para continuar</p>", unsafe_allow_html=True)
    
    usuarios = st.secrets.get("USERS", {"Jack": "1234", "Loli": "5678"})
    
    with st.form("form_login"):
        user_input = st.selectbox("Usuário", list(usuarios.keys()))
        pass_input = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar", use_container_width=True, type="primary")
        
        if btn_login:
            if str(usuarios.get(user_input)) == str(pass_input):
                st.session_state.autenticado = True
                st.session_state.usuario_logado = user_input
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
    st.stop()

# --- ESTRUTURA DA PLANILHA (GRUPOS E SUBGRUPOS) ---
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

# --- CABEÇALHO COM LOGOUT ---
c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.markdown(f"<h3 style='margin:0;'>💳 Finanças J&L</h3>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#94a3b8; font-size:0.85rem;'>Usuário: <b>{st.session_state.usuario_logado}</b></span>", unsafe_allow_html=True)
with c_head2:
    if st.button("Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_logado = ""
        st.rerun()

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# --- NAVEGAÇÃO POR ABAS HORIZONTAIS ---
tab_lancar, tab_resumo, tab_historico, tab_gerenciar = st.tabs([
    "➕ Novo", "📊 Resumo", "📜 Histórico", "⚙️ Editar"
])

# ==========================================
# 1. ABA: LANÇAR
# ==========================================
with tab_lancar:
    st.markdown("##### ➕ Novo Lançamento")
    
    tipo = st.radio("Tipo de Operação", ["Despesa", "Receita", "Boleto Pessoal (Investimento)", "Benefício"], horizontal=True)
    
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

    grupo_selecionado = st.selectbox("Grupo (Categoria)", grupos_validos)
    subgrupos_validos = ESTRUTURA.get(grupo_selecionado, [])
    subgrupo_selecionado = st.selectbox("Subgrupo (Item)", subgrupos_validos)
    
    with st.form("form_lancamento", clear_on_submit=True):
        valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        meio_pagamento = st.selectbox("Meio de Rec. / Pagamento", [
            "Transferência Bancária", "Pix", "Cartão de Crédito", "Cartão de Débito",
            "Ticket Restaurante", "Sodexo", "Dinheiro"
        ])
        data_lancamento = st.date_input("Data", datetime.today())
        observacao = st.text_input("Observação (Opcional)")
        
        btn_salvar = st.form_submit_button("Salvar Registro", use_container_width=True, type="primary")
        
        if btn_salvar:
            novo_registro = {
                "id": int(datetime.now().timestamp()),
                "data": data_lancamento.strftime("%Y-%m-%d"),
                "tipo": tipo,
                "grupo": grupo_selecionado,
                "subgrupo": subgrupo_selecionado,
                "valor": float(valor),
                "meio_pagamento": meio_pagamento,
                "usuario": st.session_state.usuario_logado,
                "observacao": observacao
            }
            
            df_atual = carregar_dados()
            df_novo = pd.concat([df_atual, pd.DataFrame([novo_registro])], ignore_index=True)
            
            if salvar_dados(df_novo):
                st.success(f"✅ Lançamento de R$ {valor:,.2f} salvo com sucesso!")
            else:
                st.error("❌ Falha ao salvar no Gist. Verifique a mensagem acima.")

# ==========================================
# 2. ABA: RESUMO
# ==========================================
with tab_resumo:
    st.markdown("##### 📊 Resumo Mensal")
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
            st.markdown("###### Total por Grupo")
            resumo_grupo = df_mes.groupby(["grupo", "tipo"])["valor"].sum().reset_index()
            st.dataframe(resumo_grupo, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum lançamento neste mês.")
    else:
        st.info("Nenhum dado encontrado no Gist.")

# ==========================================
# 3. ABA: HISTÓRICO & EXPORTAÇÃO
# ==========================================
with tab_historico:
    st.markdown("##### 📜 Histórico e Exportação")
    df = carregar_dados()
    
    if not df.empty:
        df = df.sort_values(by="data", ascending=False)
        st.dataframe(
            df[["data", "usuario", "tipo", "grupo", "subgrupo", "valor", "meio_pagamento", "observacao"]],
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        st.markdown("###### 📥 Exportar Relatório")
        col_exp1, col_exp2 = st.columns(2)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Lancamentos')
        
        with col_exp1:
            st.download_button(
                label="🟢 Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"financas_jl_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        csv_data = df.to_csv(index=False).encode('utf-8')
        with col_exp2:
            st.download_button(
                label="📄 CSV",
                data=csv_data,
                file_name=f"financas_jl_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("Nenhum dado salvo até o momento.")

# ==========================================
# 4. ABA: GERENCIAR (EDITAR / DELETAR)
# ==========================================
with tab_gerenciar:
    st.markdown("##### ⚙️ Editar ou Excluir Lançamentos")
    df = carregar_dados()
    
    if not df.empty:
        df["id"] = df["id"].astype(int)
        
        opcoes_registro = {
            row["id"]: f"{row['data']} | {row['subgrupo']} | R$ {row['valor']:,.2f} ({row['usuario']})"
            for _, row in df.sort_values(by="data", ascending=False).iterrows()
        }
        
        selected_id = st.selectbox("Selecione o Lançamento para Alterar", list(opcoes_registro.keys()), format_func=lambda x: opcoes_registro[x])
        idx_match = df.index[df['id'] == selected_id].tolist()
        
        if idx_match:
            idx = idx_match[0]
            item = df.loc[idx]
            
            st.markdown("---")
            with st.form("form_edicao"):
                st.markdown(f"**Editando ID:** `{item['id']}`")
                
                edit_data = st.date_input("Data", datetime.strptime(str(item["data"]), "%Y-%m-%d"))
                edit_valor = st.number_input("Valor (R$)", min_value=0.01, value=float(item["valor"]), step=10.0, format="%.2f")
                edit_subgrupo = st.text_input("Subgrupo", value=str(item["subgrupo"]))
                edit_meio = st.selectbox("Meio de Pagamento", [
                    "Transferência Bancária", "Pix", "Cartão de Crédito", "Cartão de Débito",
                    "Ticket Restaurante", "Sodexo", "Dinheiro"
                ], index=0)
                edit_obs = st.text_input("Observação", value=str(item.get("observacao", "")))
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    btn_atualizar = st.form_submit_button("✏️ Atualizar", type="primary", use_container_width=True)
                with c_btn2:
                    btn_deletar = st.form_submit_button("🗑️ Excluir", use_container_width=True)
                
                if btn_atualizar:
                    df.at[idx, "data"] = edit_data.strftime("%Y-%m-%d")
                    df.at[idx, "valor"] = float(edit_valor)
                    df.at[idx, "subgrupo"] = edit_subgrupo
                    df.at[idx, "meio_pagamento"] = edit_meio
                    df.at[idx, "observacao"] = edit_obs
                    
                    if salvar_dados(df):
                        st.success("✅ Registro atualizado com sucesso!")
                        st.rerun()
                        
                if btn_deletar:
                    df = df.drop(index=idx)
                    if salvar_dados(df):
                        st.warning("🗑️ Registro excluído com sucesso!")
                        st.rerun()
    else:
        st.info("Nenhum lançamento cadastrado para editar.")
