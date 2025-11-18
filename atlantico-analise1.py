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

if st.sidebar.button("🔁 Análise Reabertas"):
    st.session_state.active_analysis = "reabertas"

# ----------------------------------------------
# SE NÃO HÁ ARQUIVO, ENCERRA
# ----------------------------------------------
if not uploaded_file:
    st.info("⬅️ Envie um arquivo Excel para começar")
    st.stop()

# ----------------------------------------------
# LEITURA DO ARQUIVO (somente colunas necessárias)
# ----------------------------------------------
df = pd.read_excel(uploaded_file, usecols=[9, 11, 15, 27])
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

# ===================================================================
# =====================  A N Á L I S E   R E A B E R T A S  ==========
# ===================================================================

if st.session_state.active_analysis == "reabertas":

    st.subheader("🔁 Análise de Tarefas Reabertas")

    # Pie-chart Sim X Não
    cont = df["Reaberta?"].value_counts().reset_index()
    cont.columns = ["Reaberta", "Total"]

    fig = px.pie(cont, names="Reaberta", values="Total", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # Função explode para separar múltiplos responsáveis
    # -------------------------------
    def explode_responsaveis(df):
        df = df.copy()
        df["Para"] = df["Para"].fillna("").astype(str)
        df["lista"] = df["Para"].apply(lambda x: [p.strip() for p in x.split(",") if p.strip()])
        df = df.explode("lista")
        df["Responsavel"] = df["lista"]
        return df.drop(columns=["lista"])

    # Apenas reabertas
    df_r = explode_responsaveis(df[df["Reaberta?"] == "Sim"])

    # Gráfico por pessoa
    agrup = df_r.groupby("Responsavel").size().reset_index(name="Total").sort_values("Total")

    fig2 = px.bar(
        agrup, x="Total", y="Responsavel",
        orientation="h", text="Total", height=500
    )
    fig2.update_layout(
        xaxis=dict(showgrid=True, gridcolor="#cccccc", gridwidth=0.5),
        yaxis=dict(showgrid=False),   # normalmente não usamos grid no eixo categórico
    )
    st.plotly_chart(fig2, use_container_width=True)

    # DataFrame filtrável
    st.markdown("### 📄 Tarefas por Responsável")

    pessoa = st.selectbox("Filtrar por responsável:", ["(todas)"] + sorted(df_r["Responsavel"].unique()))

    df_view = df_r if pessoa == "(todas)" else df_r[df_r["Responsavel"] == pessoa]

    st.dataframe(
        df_view[
            ["Tarefa", "Responsavel", "Criada em", "Reaberta?"]
        ].sort_values("Criada em", ascending=False),
        use_container_width=True
    )
