import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Grelha de Avaliação Prática", layout="wide")

st.title("📋 Grelha de Avaliação Prática por Formando")
st.write(
    "Nomes dos formandos extraídos da **Coluna K**. "
    "Selecione as colunas do ficheiro de avaliação que contêm os parâmetros a preencher."
)

# 1. Carregamento dos ficheiros
col1, col2 = st.columns(2)

with col1:
    file_formandos = st.file_uploader(
        "1. Ficheiro dos Formandos (.xlsx, .xls, .csv)",
        type=["xlsx", "xls", "csv"],
        key="formandos",
    )

with col2:
    file_parametros = st.file_uploader(
        "2. Ficheiro da Avaliação Prática (.xlsx, .xls, .csv)",
        type=["xlsx", "xls", "csv"],
        key="parametros",
    )


def carregar_ficheiro(uploaded_file):
    """Lê ficheiros Excel (.xlsx/.xls) ou CSV."""
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

        # 1. Extração FIXA da Coluna K (Índice 10) para os Formandos
        if df_formandos.shape[1] > 10:
            formandos_raw = df_formandos.iloc[:, 10].dropna().astype(str).tolist()
            
            # Remover o cabeçalho se for capturado como o primeiro item
            seccao_header = str(df_formandos.columns[10])
            if formandos_raw and formandos_raw[0] == seccao_header:
                formandos = formandos_raw[1:]
            else:
                formandos = formandos_raw
        else:
            st.error(
                f"O ficheiro '{file_formandos.name}' não tem colunas suficientes para chegar à Coluna K."
            )
            formandos = []

        st.markdown("---")
        st.subheader("⚙️ Seleção das Colunas de Parâmetros")

        # Seleção múltipla de colunas onde estão os parâmetros
        colunas_selecionadas = st.multiselect(
            "Selecione as colunas que contêm os parâmetros (cada coluna será um Grupo):",
            options=df_param.columns.tolist(),
            default=df_param.columns.tolist()[:3] if len(df_param.columns) >= 3 else df_param.columns.tolist()
        )

        estrutura_grupos = {}
        lista_parametros_chave = []

        # Processar as colunas escolhidas
        for col in colunas_selecionadas:
            # O nome da coluna é o Grupo
            grupo = str(col).strip()
            estrutura_grupos[grupo] = []
            
            # As linhas não
