import streamlit as st
import pandas as pd

st.set_page_config(page_title="Grelha de Avaliação de Formandos", layout="wide")

st.title("📋 Gerador de Grelhas de Avaliação")
st.write("Carregue os ficheiros Excel correspondentes para compilar a lista de formandos e os parâmetros de avaliação.")

# Estrutura em duas colunas para o carregamento dos ficheiros
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Ficheiro dos Formandos")
    file_formandos = st.file_uploader("Selecione o ficheiro dos Formandos (.xlsx, .xls)", type=["xlsx", "xls"], key="formandos")

with col2:
    st.subheader("2. Ficheiro de Avaliação")
    file_parametros = st.file_uploader("Selecione o ficheiro dos Parâmetros (.xlsx, .xls)", type=["xlsx", "xls"], key="parametros")

if file_formandos and file_parametros:
    try:
        # 1. Leitura e extração dos formandos (Coluna K -> índice 10)
        df_formandos = pd.read_excel(file_formandos)
        
        # Verificar se a coluna K existe (A=0, B=1, ..., K=10)
        if df_formandos.shape[1] > 10:
            # Extrai a coluna K e remove valores vazios
            formandos = df_formandos.iloc[:, 10].dropna().tolist()
            # Remove o cabeçalho se corresponder ao nome da coluna
            seccao_header = df_formandos.columns[10]
            if formandos and formandos[0] == seccao_header:
                formandos = formandos[1:]
        else:
            st.error("O ficheiro de formandos não tem colunas suficientes (Coluna K não encontrada).")
            formandos = []

        # 2. Leitura dos parâmetros de avaliação
        df_param = pd.read_excel(file_parametros)
        # Seleção de colunas para os parâmetros
        coluna_parametro = st.selectbox("Selecione a coluna que contém os Parâmetros de Avaliação:", df_param.columns)
        parametros = df_param[coluna_parametro].dropna().tolist()

        if formandos and parametros:
            st.success(f"✓ Carregados **{len(formandos)} formandos** e **{len(parametros)} parâmetros**.")

            # 3. Construção da tabela/grelha consolidada
            # As linhas serão os formandos e as colunas os parâmetros de avaliação
            dados_grelha = {"Nome do Formando": formandos}
            for param in parametros:
                dados_grelha[str(param)] = [None] * len(formandos)

            df_grelha = pd.DataFrame(dados_grelha)

            st.subheader("📊 Grelha de Avaliação Gerada")
            st.write("Pode preencher as notas/avaliações diretamente na tabela abaixo:")

            # Tabela editável diretamente na aplicação
            df_editado = st.data_editor(df_grelha, num_rows="dynamic")

            # 4. Exportação para Excel
            output_name = "grelha_avaliacao_preenchida.xlsx"
            
            # Converter DataFrame editado para buffer Excel
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_editado.to_excel(writer, index=False, sheet_name='Avaliação')
            
            st.download_button(
                label="📥 Descarregar Grelha em Excel",
                data=buffer.getvalue(),
                file_name=output_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os ficheiros: {e}")
