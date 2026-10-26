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
            
            # As linhas não vazias desta coluna são os critérios
            itens = df_param[col].dropna().astype(str).tolist()
            
            for item in itens:
                param = item.strip()
                if param not in estrutura_grupos[grupo]:
                    estrutura_grupos[grupo].append(param)
                
                chave_unica = f"{grupo} -> {param}"
                if chave_unica not in lista_parametros_chave:
                    lista_parametros_chave.append(chave_unica)

        # 3. Interface de Avaliação Prática Individual
        if formandos and estrutura_grupos:
            st.success(
                f"✓ Carregados **{len(formandos)} formandos** da Coluna K e **{len(lista_parametros_chave)} parâmetros** distribuídos por **{len(colunas_selecionadas)} grupos**."
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
                    # Se o grupo tiver parâmetros, desenha a secção
                    if criterios:
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
                file_name="grelha_avaliacao_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
