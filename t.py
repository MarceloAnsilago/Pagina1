import streamlit as st

st.title("Página de Teste Streamlit")
st.write("Este é um exemplo básico de uma aplicação Streamlit para teste de deploy.")

# Adicione uma entrada de texto
nome = st.text_input("Qual é o seu nome?")

# Exibe uma mensagem de boas-vindas
if nome:
    st.write(f"Olá, {nome}! Bem-vindo à sua primeira aplicação Streamlit.")

# Adicione um botão
if st.button("Clique aqui"):
    st.write("Você clicou no botão!")