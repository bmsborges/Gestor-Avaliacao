import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Grelha de Avaliação Prática", layout="wide")

st.title("📋 Grelha de Avaliação Prática por Formando")
st.write(
    "Carregue os ficheiros e selecione livremente as colunas pretendidas para o agrupamento dos parâmetros."
)

# 1. Carregamento dos ficheiros
col1, col2 = st.columns(2)

with col1:
    file_formandos = st.file_uploader(
        "1. Ficheiro dos Formandos (.xlsx, .xls, .xlsm, .csv)",
        type=["xlsx", "xls", "xlsm", "csv"],
        key="formandos",
    )

with col2:
    file_parametros = st.file_uploader(
        "2. Ficheiro da Avaliação Prática (.xlsx, .xls, .xlsm, .csv)",
        type=["xlsx", "xls", "xlsm", "csv"],
        key="parametros",
    )


def carregar_ficheiro(uploaded_file):
    """Lê ficheiros Excel (.xlsx/.xls/.xlsm) ou CSV sem impor posições fixas."""
    nome = uploaded_file.name.lower()
    if nome.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=";")
    try:
        return pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception:
        uploaded_file.seek(0)
        try:
            return pd.read_excel(uploaded_file, engine="xlrd")
        except Exception:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file)


if file_formandos and file_parametros:
    try:
        df_formandos = carregar_ficheiro(file_formandos)
        df_param = carregar_ficheiro(file_parametros)

        st.markdown("---")
        st.subheader("⚙️ Seleção Dinâmica das Colunas para Agrupamento")

        # Menu para escolher livremente qualquer coluna de ambos os ficheiros
        c1, c2, c3 = st.columns(3)

        with c1:
            col_formando = st.selectbox(
                "Coluna com Nomes dos Formandos (Ficheiro 1):",
                options=df_formandos.columns.tolist(),
            )

        with c2:
            col_grupo = st.selectbox(
                "Coluna do Grupo / Categoria (Ficheiro 2):",
                options=df_param.columns.tolist(),
                index=0 if len(df_param.columns) > 0 else 0,
            )

        with c3:
            col_criterio = st.selectbox(
                "Coluna do Parâmetro / Critério (Ficheiro 2):",
                options=df_param.columns.tolist(),
                index=1 if len(df_param.columns) > 1 else 0,
            )

        # 1. Extração da lista de formandos
        formandos
