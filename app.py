import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Grelha de Avaliação Prática", layout="wide")

st.title("📋 Grelha de Avaliação Prática por Formando")
st.write(
    "Agrupamento de parâmetros: **Coluna A** (Categorias/Grupos) e **Coluna G** (Critérios/Parâmetros)."
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
        # 1. Extrair Formandos (Coluna K -> índice 10)
        df_formandos = carregar_ficheiro(file_formandos)
        if df_formandos.shape[1] > 10:
            formandos = df_formandos.iloc[:, 10].dropna().tolist()
            seccao_header = df_formandos.columns[10]
            if formandos and formandos[0] == seccao_header:
                formandos = formandos[1:]
        else:
            st.error(
                f"O ficheiro '{file_formandos.name}' não tem colunas suficientes (Coluna K não encontrada)."
            )
            formandos = []

        # 2. Extrair Parâmetros: Coluna A (Grupo) e Coluna G (Parâmetro)
        df_param = carregar_ficheiro(file_parametros)

        if df_param.shape[1] > 6:
            # Coluna A é índice 0, Coluna G é índice 6
            df_selecionado = df_param.iloc[:, [0, 6]].copy()
            df_selecionado.columns = ["Grupo", "Parametro"]

            # Preencher células mescladas na Coluna A (se existirem)
            df_selecionado["Grupo"] = df_selecionado["Grupo"].ffill()

            # Remover linhas onde o parâmetro (Coluna G) esteja vazio
            df_selecionado = df_selecionado.dropna(subset=["Parametro"])

            # Criar lista de parâmetros formatados: "Grupo - Parâmetro"
            parametros_agrupados = []
            for _, row in df_selecionado.iterrows():
                grupo = str(row["Grupo"]).strip()
                param = str(row["Parametro"]).strip()
                parametros_agrupados.append(f"[{grupo}] {param}")
        else:
            st.error(
                f"O ficheiro '{file_parametros.name}' não tem colunas suficientes (é necessária a Coluna G)."
            )
            parametros_agrupados = []

        if formandos and parametros_agrupados:
            st.success(
                f"✓ Foram carregados **{len(formandos)} formandos** e **{len(parametros_agrupados)} parâmetros** agrupados pela Coluna A e G."
            )

            # Estado da sessão para guardar avaliações
            if "avaliacoes" not in st.session_state:
                st.session_state.avaliacoes = {
                    f: {p: 1 for p in parametros_agrupados} for f in formandos
                }

            st.markdown("---")
            st.subheader("👤 Avaliação Prática Individual")

            formando_selecionado = st.selectbox(
                "Selecione o formando a avaliar:", options=formandos
            )

            st.markdown(f"### 📝 Ficha de Avaliação: **{formando_selecionado}**")

            # Formulário com escala 1, 3 ou 5 por parâmetro
            with st.form(key=f"form_{formando_selecionado}"):
                novas_notas = {}
                cols = st.columns(2)

                for idx, param in enumerate(parametros_agrupados):
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
                    st.session_state.avaliacoes[formando_selecionado] = novas_notas
                    st.success(
                        f"Avaliação guardada com sucesso para **{formando_selecionado}**!"
                    )

            # Resumo Geral e Exportação
            st.markdown("---")
            st.subheader("📊 Resumo Global da Turma")

            dados_resumo = []
            for f in formandos:
                linha = {"Nome do Formando": f}
                notas_f = st.session_state.avaliacoes[f]
                soma = 0
                for p in parametros_agrupados:
                    val = notas_f.get(p, 1)
                    linha[p] = val
                    soma += val
                linha["Média Prática"] = (
                    round(soma / len(parametros_agrupados), 2)
                    if parametros_agrupados
                    else 0
                )
                dados_resumo.append(linha)

            df_resumo = pd.DataFrame(dados_resumo)
            st.dataframe(df_resumo, use_container_width=True)

            # Exportar para Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_resumo.to_excel(
                    writer, index=False, sheet_name="Avaliação Prática"
                )

            st.download_button(
                label="📥 Descarregar Grelha Prática Completa (Excel)",
                data=buffer.getvalue(),
                file_name="grelha_avaliacao_pratica_colunaA_G.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
