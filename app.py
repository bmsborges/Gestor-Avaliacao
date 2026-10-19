import streamlit as st
import pandas as pd

st.title("Gestor de Avaliações")

file_alunos = st.file_uploader("Carregar Ficheiro de Alunos (Excel)", type=["xlsx"])

if file_alunos:
    df_alunos = pd.read_excel(file_alunos)
    
    # 1. Limpar espaços nos cabeçalhos
    df_alunos.columns = df_alunos.columns.astype(str).str.strip()
    
    # 2. Identificar a coluna de nomes
    coluna_nome = next((col for col in df_alunos.columns if col.lower() in ['nome', 'aluno']), None)
    
    if coluna_nome is None:
        st.error(f"Erro: Não encontramos nenhuma coluna com o cabeçalho 'Nome' ou 'Aluno'. Colunas lidas: {list(df_alunos.columns)}")
    else:
        notas_teoricas = []
        with st.form("form_notas"):
            for index, row in df_alunos.iterrows():
                col1, col2 = st.columns([3, 1])
                # 3. Acesso seguro ao nome
                col1.write(f"**Aluno:** {row[coluna_nome]}")
                nota = col2.number_input(f"Nota Teórica", key=f"nota_{index}", min_value=0.0, max_value=20.0)
                notas_teoricas.append(nota)
            
            submetido = st.form_submit_button("Submeter")
