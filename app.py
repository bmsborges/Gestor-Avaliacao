import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Grelha de Avaliação Prática", layout="wide")

st.title("📋 Grelha de Avaliação Prática por Formando")
st.write(
    "Preencha a avaliação prática de cada formando utilizando a escala estrita"
    " de **1, 3 ou 5** por parâmetro."
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
        "2. Ficheiro dos Parâmetros (.xlsx, .xls, .xlsm, .csv)",
        type=["xlsx", "xls", "xlsm", "csv"],
        key="parametros",
    )


def carregar_ficheiro(uploaded_file):
    """Lê ficheiros Excel (.xlsx/.xls/.xlsm) ou CSV."""
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
        # Extrair Formandos (Coluna K -> índice 10)
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

        # Extrair Parâmetros da Macro/Excel
        excel_param = pd.ExcelFile(file_parametros, engine="openpyxl")
        folhas = excel_param.sheet_names

        st.markdown("---")
        if len(folhas) > 1:
            aba = st.selectbox(
                "Selecione a folha que contém os Parâmetros de Avaliação:",
                options=folhas,
            )
            df_param = pd.read_excel(
                file_parametros, sheet_name=aba, engine="openpyxl"
            )
        else:
            df_param = pd.read_excel(file_parametros, engine="openpyxl")

        colunas_selecionadas = st.multiselect(
            "Selecione as colunas de parâmetros a incluir:",
            options=df_param.columns.tolist(),
            default=df_param.columns.tolist(),
        )

        parametros = []
        for col in colunas_selecionadas:
            for item in df_param[col].dropna().tolist():
                parametros.append(f"{col} - {item}")

        if formandos and parametros:
            # Estado da sessão para guardar as notas preenchidas
            if "avaliacoes" not in st.session_state:
                st.session_state.avaliacoes = {
                    f: {p: 1 for p in parametros} for f in formandos
                }

            st.subheader("👤 Seleção do Formando")
            formando_selecionado = st.selectbox(
                "Escolha o formando para preencher a grelha prática:",
                options=formandos,
            )

            st.markdown(f"### 📝 Grelha Prática: **{formando_selecionado}**")

            # Construir formulário individual de avaliação (opções 1, 3, 5)
            with st.form(key=f"form_{formando_selecionado}"):
                novas_notas = {}
                cols = st.columns(2)

                for idx, param in enumerate(parametros):
                    col_idx = idx % 2
                    val_atual = st.session_state.avaliacoes[
                        formando_selecionado
                    ].get(param, 1)

                    with cols[col_idx]:
                        nota = st.selectbox(
                            label=param,
                            options=[1, 3, 5],
                            index=[1, 3, 5].index(val_atual),
                            key=f"{formando_selecionado}_{param}",
                        )
                        novas_notas[param] = nota

                submetido = st.form_submit_button("💾 Guardar Avaliação do Formando")
                if submetido:
                    st.session_state.avaliacoes[formando_selecionado] = (
                        novas_notas
                    )
                    st.success(
                        f"Avaliação guardada com sucesso para"
                        f" **{formando_selecionado}**!"
                    )

            # Resumo Geral e Exportação
            st.markdown("---")
            st.subheader("📊 Resumo de Todos os Formandos")

            # Montar a tabela resumo com médias
            dados_resumo = []
            for f in formandos:
                linha = {"Nome do Formando": f}
                notas_f = st.session_state.avaliacoes[f]
                soma = 0
                for p in parametros:
                    val = notas_f.get(p, 1)
                    linha[p] = val
                    soma += val
                linha["Média Prática"] = round(soma / len(parametros), 2)
                dados_resumo.append(linha)

            df_resumo = pd.DataFrame(dados_resumo)
            st.dataframe(df_resumo, use_container_width=True)

            # Exportação Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_resumo.to_excel(
                    writer, index=False, sheet_name="Avaliação Prática"
                )

            st.download_button(
                label="📥 Descarregar Grelha Prática Completa (Excel)",
                data=buffer.getvalue(),
                file_name="grelha_avaliacao_pratica_1_3_5.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
