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

if st.sidebar.button("Tempo de Entrega"):
    st.session_state.active_analysis = "tempo"

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
    # ANÁLISE 2 — TEMPO ENTRE ENTREGA DESEJADA E FECHADA
    # ======================================================
if st.session_state.active_analysis == "tempo":

    st.markdown("### ⏱ Análise de Tempo entre Entrega Desejada e Fechada (por Equipe)")

    # ---------------------------
    # 1) PREPARAR/EXPANDIR EQUIPES
    # ---------------------------
    if "Equipe" in df.columns:
        df = df.rename(columns={"Equipe": "Equipe_orig"})
    else:
        df["Equipe_orig"] = ""

    df["Equipe_orig"] = df["Equipe_orig"].fillna("").astype(str)

    def split_equipe(val):
        if isinstance(val, (list, tuple)):
            return [str(x).strip() for x in val if str(x).strip()]
        s = str(val)
        if s.strip() == "":
            return []
        return [item.strip() for item in s.split(",") if item.strip()]
    
    df["Equipe_list"] = df["Equipe_orig"].apply(split_equipe)
    
    df_exp = df.explode("Equipe_list").reset_index(drop=True)
    df_exp["Equipe"] = df_exp["Equipe_list"].astype(str).str.strip()
    df_exp = df_exp.drop(columns=["Equipe_list", "Equipe_orig"], errors="ignore")

    # ---------------------------
    # 2) CÁLCULO DO TEMPO EM DIAS (FLOAT)
    # ---------------------------
    df_exp["tempo_dias"] = (df_exp["Fechada em"] - df_exp["Entrega desejada"]) / pd.Timedelta(days=1) * 24 * -1

    df_valid = df_exp.dropna(subset=["tempo_dias", "Equipe"]).copy()

    df_valid = df_valid[(df_valid["tempo_dias"].abs() < 10000)]
    

    # ---------------------------
    # 3) MÉDIA GERAL POR EQUIPE
    # ---------------------------
    agrupado = (
        df_valid.groupby("Equipe")["tempo_dias"]
        .mean()
        .reset_index()
        .sort_values("tempo_dias", ascending=False)
    )
    agrupado["tempo_dias"] = agrupado["tempo_dias"].round(2)

    fig_tempo = px.bar(
        agrupado,
        x="Equipe",
        y="tempo_dias",
        text="tempo_dias",
        labels={"tempo_dias": "Horas (média)", "Equipe": "Equipe"},
        height=500
    )
    fig_tempo.update_traces(textposition="outside")
    fig_tempo.update_layout(margin=dict(l=150, r=40, t=50, b=50))

    st.plotly_chart(fig_tempo, use_container_width=True)


    # ======================================================
    # 4) NOVA ANÁLISE — MÉDIA SOMENTE DOS ATRASOS
    # ======================================================
    st.markdown("### ⚠ Tempo de Atraso (somente valores positivos)")

    df_atrasos = df_valid[df_valid["tempo_dias"] < 0].copy()
    df_atrasos["tempo_dias"]  = df_atrasos["tempo_dias"] * -1  

    if df_atrasos.empty:
        st.info("Nenhum atraso encontrado.")
    else:
        agrupado_atraso = (
            df_atrasos.groupby("Equipe")["tempo_dias"]
            .mean()
            .reset_index()
            .sort_values("tempo_dias", ascending=False)
        )
        agrupado_atraso["tempo_dias"] = agrupado_atraso["tempo_dias"].round(2)

        # --- Gráfico de barras vertical (como solicitado)
        fig_atraso = px.bar(
            agrupado_atraso,
            x="Equipe",
            y="tempo_dias",
            text="tempo_dias",
            labels={"tempo_dias": "Média de atraso (HORAS)", "Equipe": "Equipe"},
            height=450
        )
        fig_atraso.update_traces(textposition="outside")

        st.plotly_chart(fig_atraso, use_container_width=True)

        # --- Dataframe abaixo com os valores usados
        # st.markdown("#### 📄 Dados utilizados na média dos atrasos")
        # cols = ["ID da Tarefa", "Tarefa", "Equipe", "Entrega desejada", "Fechada em", "tempo_dias"]
        # cols = [c for c in cols if c in df_atrasos.columns]
        
        # st.dataframe(
        #     df_atrasos[cols]
        #     .sort_values("tempo_dias", ascending=False)
        #     .reset_index(drop=True)
        # )

    


    # ---------------------------
    # 5) DIAGNÓSTICO POR EQUIPE (mantido)
    # ---------------------------
    st.markdown("#### 🔎 Inspecionar valores individuais por equipe")

    equipes = sorted(df_valid["Equipe"].dropna().unique().tolist())
    equipe_sel = st.selectbox("Selecione uma equipe", ["(todas)"] + equipes)

    amostra = df_valid if equipe_sel == "(todas)" else df_valid[df_valid["Equipe"] == equipe_sel]

    cols = ["ID da Tarefa", "Tarefa", "Equipe", "Entrega desejada", "Fechada em", "tempo_dias"]
    cols = [c for c in cols if c in amostra.columns]

    st.dataframe(amostra[cols].sort_values("tempo_dias", ascending=False).reset_index(drop=True))

