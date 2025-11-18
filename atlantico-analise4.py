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

if st.sidebar.button("Tempo por Tipo de Tarefa"):
    st.session_state.active_analysis = "tempo_tarefa"

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
# ANÁLISE 3  — TEMPO TOTAL E MÉDIO POR Tipo de Tarefa
# ======================================================
if st.session_state.active_analysis == "tempo_tarefa":

    st.markdown("## 🧮 Análise de Tempo Total e Médio por Tipo de Tarefa")

    # Verificar se a coluna existe
    if "Já registradas h" not in df.columns:
        st.error("A coluna 'Já registradas h' não existe no arquivo enviado.")
        st.stop()

    # Converter para número
    df["Já registradas h"] = pd.to_numeric(df["Já registradas h"], errors="coerce")

    # Remover linhas sem valor
    df_temp = df.dropna(subset=["Já registradas h", "Tipo de tarefa"]).copy()

    # ===============================
    # 1) AGRUPAMENTO — TEMPO TOTAL
    # ===============================
    total_por_tarefa = (
        df_temp.groupby("Tipo de tarefa")["Já registradas h"]
        .sum()
        .reset_index()
        .sort_values("Já registradas h", ascending=False)
    )

    total_por_tarefa["Já registradas h"] = total_por_tarefa["Já registradas h"].round(2)

    st.markdown("### 📊 Tempo Total Registrado por Tarefa")

    fig_total = px.bar(
        total_por_tarefa,
        x="Tipo de tarefa",
        y="Já registradas h",
        text="Já registradas h",
        labels={"Já registradas h": "Tempo Total (h)", "Tipo de tarefa": "Tarefa"},
        height=500
    )

    fig_total.update_traces(textposition="outside")
    fig_total.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_total, use_container_width=True)

    # ===============================
    # 2) AGRUPAMENTO — TEMPO MÉDIO
    # ===============================
    media_por_tarefa = (
        df_temp.groupby("Tipo de tarefa")["Já registradas h"]
        .mean()
        .reset_index()
        .sort_values("Já registradas h", ascending=False)
    )

    media_por_tarefa["Já registradas h"] = media_por_tarefa["Já registradas h"].round(2)

    st.markdown("### 📊 Tempo Médio Registrado por Tarefa")

    fig_media = px.bar(
        media_por_tarefa,
        x="Tipo de tarefa",
        y="Já registradas h",
        text="Já registradas h",
        labels={"Já registradas h": "Tempo Médio (h)", "Tipo de tarefa": "Tarefa"},
        height=500
    )

    fig_media.update_traces(textposition="outside")
    fig_media.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_media, use_container_width=True)


    # ===============================
    # 3) DATAFRAME FINAL (com filtro selecionado pelo usuário)
    # ===============================
    st.markdown("### 📄 Dados utilizados nos cálculos")

    # Lista de tipos disponíveis no dataframe filtrado
    tipos_df = sorted(df_temp["Tipo de tarefa"].dropna().unique().tolist())

    tipo_df_sel = st.selectbox(
        "Selecione o tipo de tarefa para exibição no dataframe:",
        options=["(Todas)"] + tipos_df
    )

    # Aplicar filtro APENAS no dataframe
    if tipo_df_sel == "(Todas)":
        df_show = df_temp.copy()
    else:
        df_show = df_temp[df_temp["Tipo de tarefa"] == tipo_df_sel].copy()

    # Colunas para exibir
    colunas_exibir = [
        "ID da Tarefa",
        "Tarefa",
        "Tipo de tarefa",
        "Já registradas h"
    ]

    colunas_exibir = [c for c in colunas_exibir if c in df_show.columns]

    df_show = df_show[colunas_exibir].sort_values(
        "Já registradas h", ascending=False
    ).reset_index(drop=True)

    st.dataframe(df_show, use_container_width=True)
