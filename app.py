import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Grelha de Avaliação de Formandos", layout="wide")

st.title("📋 Gerador de Grelhas de Avaliação (Parâmetros em Colunas)")
st.write(
    "Carregue os ficheiros Excel para compilar a lista de formandos e os parâmetros"
    " organizados por colunas de grupos."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Ficheiro dos Formandos")
    file_formandos = st.file_uploader(
        "Selecione o ficheiro dos Formandos (.xlsx, .xls, .csv)",
        type=["xlsx", "xls", "csv"],
        key="formandos",
    )

with col2:
    st.subheader("2. Ficheiro de Avaliação / Parâmetros")
    file_parametros = st.file_uploader(
        "Selecione o ficheiro dos Parâmetros (.xlsx, .xls, .csv)",
        type=["xlsx", "xls", "csv"],
        key="parametros",
    )


def carregar_ficheiro(uploaded_file):
    """Função para carregar ficheiros .xlsx, .xls ou .csv automaticamente sem falhar."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    try:
        # Tenta ler como Excel moderno (.xlsx)
        return pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception:
        # Se falhar (ex: ficheiro .xls antigo), tenta com xlrd/default
        uploaded_file.seek(0)
        try:
            return pd.read_excel(uploaded_file, engine="xlrd")
        except Exception:
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file)


if file_formandos and file_parametros:
    try:
        # 1. Extrair formandos (Coluna K -> índice 10)
        df_formandos = carregar_ficheiro(file_formandos)

        if df_formandos.shape[1] > 10:
            formandos = df_formandos.iloc[:, 10].dropna().tolist()
            seccao_header = df_formandos.columns[10]
            if formandos and formandos[0] == seccao_header:
                formandos = formandos[1:]
        else:
            st.error(
                "O ficheiro de formandos não tem colunas suficientes (Coluna K"
                " não encontrada)."
            )
            formandos = []

        # 2. Processar ficheiro de parâmetros
        df_param = carregar_ficheiro(file_parametros)

        st.markdown("---")
        st.subheader("⚙️ Seleção das Colunas de Parâmetros")

        colunas_selecionadas = st.multiselect(
            "Selecione as colunas que contêm os parâmetros a incluir:",
            options=df_param.columns.tolist(),
            default=df_param.columns.tolist(),
        )

        parametros_agrupados = []

        for col_grupo in colunas_selecionadas:
            itens = df_param[col_grupo].dropna().tolist()
            for item in itens:
                parametros_agrupados.append(f"{col_grupo} - {item}")

        # 3. Gerar a Grelha Consolidada
        if formandos and parametros_agrupados:
            st.success(
                f"✓ Carregados **{len(formandos)} formandos** e"
                f" **{len(parametros_agrupados)} parâmetros** distribuídos por"
                f" **{len(colunas_selecionadas)} grupos**."
            )

            dados = {"Nome do Formando": formandos}
            for p in parametros_agrupados:
                dados[str(p)] = [None] * len(formandos)

            df_grelha = pd.DataFrame(dados)

            st.subheader("📊 Grelha de Avaliação Final")
            df_editado = st.data_editor(df_grelha, num_rows="dynamic")

            # 4. Exportação para Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_editado.to_excel(writer, index=False, sheet_name="Avaliação")

            st.download_button(
                label="📥 Descarregar Grelha em Excel",
                data=buffer.getvalue(),
                file_name="grelha_avaliacao_colunas.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
