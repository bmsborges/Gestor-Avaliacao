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
        formandos = df_formandos[col_formando].dropna().astype(str).tolist()

        # 2. Processamento do agrupamento com base nas colunas escolhidas
        df_selecionado = df_param[[col_grupo, col_criterio]].copy()
        df_selecionado.columns = ["Grupo", "Parametro"]

        # Preencher a hierarquia de categorias caso existam células fundidas ou em bloco no Excel
        df_selecionado["Grupo"] = df_selecionado["Grupo"].ffill()
        df_selecionado = df_selecionado.dropna(subset=["Parametro"])

        estrutura_grupos = {}
        lista_parametros_chave = []

        for _, row in df_selecionado.iterrows():
            grupo = str(row["Grupo"]).strip()
            param = str(row["Parametro"]).strip()

            if grupo not in estrutura_grupos:
                estrutura_grupos[grupo] = []

            if param not in estrutura_grupos[grupo]:
                estrutura_grupos[grupo].append(param)

            chave_unica = f"{grupo} -> {param}"
            if chave_unica not in lista_parametros_chave:
                lista_parametros_chave.append(chave_unica)

        # 3. Interface de Avaliação Prática Individual
        if formandos and estrutura_grupos:
            st.success(
                f"✓ Carregados **{len(formandos)} formandos** e **{len(lista_parametros_chave)} parâmetros** organizados em **{len(estrutura_grupos)} grupos**."
            )

            # Inicializar o estado de sessão para guardas as notas (1, 3 ou 5)
            if "avaliacoes" not in st.session_state:
                st.session_state.avaliacoes = {
                    f: {p: 1 for p in lista_parametros_chave} for f in formandos
                }

            st.markdown("---")
            st.subheader("👤 Avaliação Prática Individual")

            formando_selecionado = st.selectbox(
                "Selecione o formando a avaliar:", options=formandos
            )

            st.markdown(f"### 📝 Ficha de Avaliação: **{formando_selecionado}**")

            with st.form(key=f"form_{formando_selecionado}"):
                novas_notas = {}

                for grupo, criterios in estrutura_grupos.items():
                    st.markdown(f"#### 📂 **{grupo}**")
                    cols = st.columns(2)

                    for idx, criterio in enumerate(criterios):
                        chave_unica = f"{grupo} -> {criterio}"
                        val_atual = st.session_state.avaliacoes[
                            formando_selecionado
                        ].get(chave_unica, 1)

                        col_idx = idx % 2
                        with cols[col_idx]:
                            nota = st.selectbox(
                                label=criterio,
                                options=[1, 3, 5],
                                index=[1, 3, 5].index(val_atual),
                                key=f"{formando_selecionado}_{chave_unica}",
                            )
                            novas_notas[chave_unica] = nota

                    st.divider()

                submetido = st.form_submit_button("💾 Guardar Avaliação do Formando")
                if submetido:
                    st.session_state.avaliacoes[formando_selecionado] = novas_notas
                    st.success(
                        f"Avaliação de **{formando_selecionado}** guardada com sucesso!"
                    )

            # 4. Resumo Global da Turma e Exportação
            st.markdown("---")
            st.subheader("📊 Resumo Global da Turma")

            dados_resumo = []
            for f in formandos:
                linha = {"Nome do Formando": f}
                notas_f = st.session_state.avaliacoes[f]
                soma = 0
                for p in lista_parametros_chave:
                    val = notas_f.get(p, 1)
                    linha[p] = val
                    soma += val
                linha["Média Prática"] = (
                    round(soma / len(lista_parametros_chave), 2)
                    if lista_parametros_chave
                    else 0
                )
                dados_resumo.append(linha)

            df_resumo = pd.DataFrame(dados_resumo)
            st.dataframe(df_resumo, use_container_width=True)

            # Botão de descarregar ficheiro Excel consolidado
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_resumo.to_excel(
                    writer, index=False, sheet_name="Avaliação Prática"
                )

            st.download_button(
                label="📥 Descarregar Grelha Prática Completa (Excel)",
                data=buffer.getvalue(),
                file_name="grelha_avaliacao_dinamica.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
