import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ----------------------------------------------
st.set_page_config(page_title="Dashboard de Tarefas", layout="wide")
st.title("📊 Dashboard de Tarefas")

# Controle da análise ativa
if "active_analysis" not in st.session_state:
    st.session_state.active_analysis = None

# ----------------------------------------------
# SIDEBAR – UPLOAD E BOTÕES
# ----------------------------------------------
st.sidebar.header("📁 Carregar Arquivo")
uploaded_file = st.sidebar.file_uploader("Envie um arquivo Excel", type=["xlsx", "xls"])

if st.sidebar.button("Esforço Percentual (%)"):
    st.session_state.active_analysis = "percentual"

# ----------------------------------------------
# SE NÃO HÁ ARQUIVO, ENCERRA
# ----------------------------------------------
if not uploaded_file:
    st.info("⬅️ Envie um arquivo Excel para começar")
    st.stop()

# ----------------------------------------------
# LEITURA DO ARQUIVO (somente colunas necessárias)
# ----------------------------------------------
df = pd.read_excel(uploaded_file)
df["Criada em"] = pd.to_datetime(df["Criada em"], errors="coerce")

# ----------------------------------------------
# FUNÇÃO PARA MOSTRAR UM CARD
# ----------------------------------------------
def card(title, value, icon="📄"):
    st.markdown(
        f"""
        <div style="
            background-color:#f5f7fa;padding:18px;border-radius:12px;
            box-shadow:0 2px 6px rgba(0,0,0,0.08);text-align:center;
            border-left:5px solid #4a90e2;min-height:90px;">
            <div style="font-size:26px;">{icon}</div>
            <div style="color:#555;font-size:15px;">{title}</div>
            <div style="font-size:22px;font-weight:700;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------------------
# CARDS RESUMO
# ----------------------------------------------
col1, col2, col3 = st.columns(3)
total = len(df)
menor = df["Criada em"].min()
maior = df["Criada em"].max()

with col1: card("Total de Registros", total, "📄")
with col2: card("Menor Data", menor.strftime("%d/%m/%Y") if pd.notnull(menor) else "-", "📅")
with col3: card("Maior Data", maior.strftime("%d/%m/%Y") if pd.notnull(maior) else "-", "📆")



# ======================================================
# ANÁLISE 5 — Percentuais (%)
# ======================================================
if st.session_state.active_analysis == "percentual":

    st.markdown("## 📉 Análise Esforço Estimado x Tempo lançado (%)")

    # Garantir que a coluna existe
    if "%" not in df.columns:
        st.error("A coluna '%' não existe no arquivo.")
        st.stop()

    # Converter campos para número
    df["Já registradas h"] = pd.to_numeric(df["Já registradas h"], errors="coerce")
    df["%"] = pd.to_numeric(df["%"], errors="coerce")

    # Filtrar registros válidos
    df_val = df[df["Já registradas h"] > 0].copy()
    df_val = df_val.dropna(subset=["%"])

    # ======================================================
    # 1️⃣ PRIMEIRO DATAFRAME — Filtrar pelo slider
    # ======================================================
    st.markdown("### 🔽 1) Percentuais menores ou iguais que o valor escolhido")

    limite = st.slider(
        "Escolha o limite máximo (%)",
        min_value=10,
        max_value=60,
        step=10,
        value=20
    )

    df_menor = df_val[df_val["%"] <= limite/100 ].copy()

    st.markdown(f"#### Valores com **% < {limite}**")
    if df_menor.empty:
        st.info("Nenhum registro encontrado com esse filtro.")
    else:
        colunas_mostrar = [
            "ID da Tarefa",
            "Tarefa",
            "Tipo de tarefa",
            "Esforço estimado h",
            "Já registradas h",
            "%",
            "Entrega desejada",
            "Fechada em"
            ]
        colunas_mostrar = [c for c in colunas_mostrar if c in df_menor.columns]

        st.dataframe(
            df_menor[colunas_mostrar].sort_values("%").reset_index(drop=True),
            use_container_width=True
        )

    # ======================================================
    # 2️⃣ SEGUNDO DATAFRAME — Valores maiores que 100
    # ======================================================
    st.markdown("### 🔼 2) Percentuais maiores que 100% (fixo)")

    df_maior = df_val[df_val["%"] > 1].copy()   # 1 = 100%

    if df_maior.empty:
        st.info("Nenhum registro encontrado com % acima de 100%.")
    else:

        # 👉 Criar coluna formatada
        df_maior["%(percentual)"] = (df_maior["%"] * 100).round(2).astype(str) + "%"

        # 👇 MANTER a coluna '%' para permitir ordenação
        colunas_mostrar = [
            "ID da Tarefa",
            "Tarefa",
            "Tipo de tarefa",
            "Esforço estimado h",
            "Já registradas h",
            "%",                # MANTÉM para ordenação
            "%(percentual)",    # exibe formatado ao usuário
            "Entrega desejada",
            "Fechada em"
        ]

        # remover colunas que não existem
        colunas_mostrar = [c for c in colunas_mostrar if c in df_maior.columns]

        # 👇 ordenar pela coluna original: '%'
        df_view = df_maior[colunas_mostrar].sort_values("%", ascending=False)

        st.dataframe(
            df_view.reset_index(drop=True),
            use_container_width=True
        )
