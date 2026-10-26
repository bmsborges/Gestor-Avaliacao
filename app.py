import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Grelha de Avaliação de Formandos", layout="wide")

st.title("📋 Gerador de Grelhas de Avaliação")
st.write(
    "Carregue os ficheiros Excel (incluindo ficheiros com Macros `.xlsm`) para"
    " compilar a lista de formandos e os parâmetros."
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Ficheiro dos Formandos")
    file_formandos = st.file_uploader(
        "Selecione o ficheiro dos Formandos (.xlsx, .xls, .xlsm, .csv)",
        type=["xlsx", "xls", "xlsm", "csv"],
        key="formandos",
    )

with col2:
    st.subheader("2. Ficheiro de Avaliação (com Macro)")
    file_parametros = st.file_uploader(
        "Selecione o ficheiro dos Parâmetros (.xlsx, .xls, .xlsm, .csv)",
        type=["xlsx", "xls", "xlsm", "csv"],
        key="parametros",
    )


def carregar_ficheiro_excel_ou_macro(uploaded_file):
    """Lê ficheiros Excel normais (.xlsx), com Macros (.xlsm), antigos (.xls) ou CSV."""
    nome = uploaded_file.name.lower()

    # 1. Se for CSV
    if nome.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=";")

    # 2. Tenta abrir ficheiros Excel / Ficheiros com Macro (.xlsm / .xlsx)
    try:
        # data_only=True garante que lemos os VALORES resultantes das fórmulas/macros, e não as fórmulas
        return pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception:
        pass

    # 3. Tenta como Excel antigo (.xls)
    uploaded_file.seek(0)
    try:
        return pd.read_excel(uploaded_file, engine="xlrd")
    except Exception:
        pass

    # 4. Tenta como tabela HTML (exportações comuns de sistemas de formação)
    uploaded_file.seek(0)
    try:
        tables = pd.read_html(uploaded_file)
        if tables:
            return tables[0]
    except Exception:
        pass

    # 5. Tenta como texto delimitado
    uploaded_file.seek(0)
    try:
        return pd.read_csv(uploaded_file, sep=None, engine="python")
    except Exception:
        pass

    raise ValueError(f"Não foi possível ler o ficheiro '{uploaded_file.name}'.")


if file_formandos and file_parametros:
    try:
        # 1. Extrair formandos (Coluna K -> índice 10)
        df_formandos = carregar_ficheiro_excel_ou_macro(file_formandos)

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

        # 2. Processar ficheiro de parâmetros (com Macro)
        # Caso o ficheiro tenha várias abas/folhas criadas pela Macro, permite escolher a aba
        excel_param = pd.ExcelFile(file_parametros, engine="openpyxl")
        folhas_disponiveis = excel_param.sheet_names

        st.markdown("---")
        st.subheader("⚙️ Configuração dos Parâmetros da Macro")

        if len(folhas_disponiveis) > 1:
            aba_selecionada = st.selectbox(
                "O ficheiro com Macro tem várias folhas. Selecione a folha que contém os parâmetros:",
                options=folhas_disponiveis,
            )
            df_param = pd.read_excel(
                file_parametros, sheet_name=aba_selecionada, engine="openpyxl"
            )
        else:
            df_param = pd.read_excel(file_parametros, engine="openpyxl")

        # Seleção das colunas que contêm os parâmetros
        colunas_selecionadas = st.multiselect(
            "Selecione as colunas da folha que contêm os parâmetros de avaliação:",
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
                f" **{len(parametros_agrupados)} parâmetros** da folha de"
                " avaliação."
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
                file_name="grelha_avaliacao_macro.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
