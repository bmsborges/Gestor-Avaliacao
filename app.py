import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Consolidador de Excel", layout="centered")

st.title("📂 Recolha de Dados Excel")
st.markdown("Carrega os teus ficheiros e eu trato de os juntar numa única tabela.")

# 1. Upload de múltiplos ficheiros
uploaded_files = st.file_uploader("Seleciona os ficheiros Excel", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    all_data = []
    
    for file in uploaded_files:
        # Lemos cada ficheiro
        df = pd.read_excel(file)
        # Adicionamos uma coluna para saber de que ficheiro veio o dado (opcional)
        df['Fonte'] = file.name
        all_data.append(df)
    
    # 2. Juntar tudo (Empilhar)
    df_final = pd.concat(all_data, ignore_index=True)
    
    st.success(f"Sucesso! {len(uploaded_files)} ficheiros lidos.")
    st.write("### Pré-visualização dos Dados:")
    st.dataframe(df_final.head(10)) # Mostra as primeiras 10 linhas

    # 3. Preparar o download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Dados_Consolidados')
    
    processed_data = output.getvalue()

    st.download_button(
        label="📥 Descarregar Ficheiro Consolidado",
        data=processed_data,
        file_name="dados_recolhidos_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
