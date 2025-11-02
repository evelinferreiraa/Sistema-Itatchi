# itatchi/frontend/app_frontend.py

import streamlit as st
import os

# --- FUNÇÃO PARA INJETAR O CSS ---
def local_css(file_name):
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        # Codificação UTF-8 para evitar erros de leitura
        with open(css_path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo CSS não encontrado em {css_path}")

# 1. Carrega o CSS global
local_css("style.css") 
st.set_page_config(layout="wide", page_title="Itatchi - Gerenciamento de Documentos")

# não tá funfando ainda
st.markdown(
    f"""
    <div class="logo-container">
        <img src="assets/logo_itatchi.png" class="logo-image">
    </div>
    """,
    unsafe_allow_html=True
)

# 2. Conteúdo da Home Page (vai ser page 2_consulta_e_filtros ?) 
st.markdown("<h1>Olá, Itatchi!</h1>", unsafe_allow_html=True)
