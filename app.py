import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Grelha de Avaliação Prática", layout="wide")

st.title("📋 Grelha de Avaliação Prática por Formando")
st.write(
    "Aplicação com extração automática dos cabeçalhos dos parâmetros de"
    " avaliação."
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
        "2. Ficheiro da Avaliação Prática (com Parâmetros/Cabeçalhos)",
        type=["xlsx", "xls", "xlsm", "csv"],
        key="parametros",
    )


def carregar_ficheiro(uploaded_file, header_row=0):
    """Lê ficheiros Excel (.xlsx/.xls/.xlsm) ou CSV especificando a linha do cabeçalho."""
    nome = uploaded_file.name.lower()
    if nome.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, header=header_row)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=";", header=header_row)
    try:
        return pd.read_excel(
            uploaded_file, engine="openpyxl", header=header_row
        )
    except Exception:
        uploaded_file.seek(0)
        try:
            return pd.read_excel(
                uploaded_file, engine="xlrd", header=header_row
            )
        except Exception:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file, header=header_row)


if file_formandos and file_parametros:
    try:
        # 1. Extrair Formandos (Coluna K -> índice 10)
        df_formandos = carregar_ficheiro(file_formandos)
        if df_formandos.shape[1] > 10:
            formandos = df_formandos.iloc[:, 10].dropna().tolist()
            seccao_header = df_formandos.columns[10]
            if formandos and formandos[0] == seccao_header:
                formandos = formandos[1:]
        else:
            st.error(
                f"O ficheiro '{file_formandos.name}' não tem colunas"
                " suficientes (Coluna K não encontrada)."
            )
            formandos = []

        st.markdown("---")
        st.subheader("⚙️ Extração Automática de Cabeçalhos e Parâmetros")

        # Configuração para definir em que linha estão os cabeçalhos no Excel de parâmetros
        linha_cabecalho = st.number_input(
            "Indique em que linha do Excel estão os cabeçalhos dos parâmetros (0 = 1ª Linha, 1 = 2ª Linha):",
            min_value=0,
            max_value=10,
            value=0,
            step=1,
        )

        # 2. Ler ficheiro de avaliação prática e extrair cabeçalhos
        df_param = carregar_ficheiro(
            file_parametros, header_row=linha_cabecalho
        )

        # Obter a lista de cabeçalhos das colunas (ignorando colunas não nomeadas/Unnamed)
        cabecalhos_detetados = [
            str(col).strip()
            for col in df_param.columns
            if not str(col).startswith("Unnamed:")
        ]

        if not cabecalhos_detetados:
            st.warning(
                "Não foram encontrados cabeçalhos válidos na linha selecionada."
            )
        else:
            st.success(
                f"✓ Foram detetados **{len(cabecalhos_detetados)} cabeçalhos/parâmetros** no ficheiro de avaliação."
            )

            # Selecionar quais os cabeçalhos que farão parte da grelha de avaliação
            parametros_selecionados = st.multiselect(
                "Confirme os parâmetros de avaliação a incluir:",
                options=cabecalhos_detetados,
                default=cabecalhos_detetados,
            )

            if formandos and parametros_selecionados:
                # Estado da sessão para manter o registo das notas
                if "avaliacoes" not in st.session_state:
                    st.session_state.avaliacoes = {
                        f: {p: 1 for p in parametros_selecionados}
                        for f in formandos
                    }

                st.markdown("---")
                st.subheader("👤 Ficha de Avaliação Prática por Formando")

                formando_selecionado = st.selectbox(
                    "Selecione o formando a avaliar:", options=formandos
                )

                st.markdown(
                    f"
