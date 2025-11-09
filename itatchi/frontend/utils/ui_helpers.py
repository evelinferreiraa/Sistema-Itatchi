# itatchi/frontend/utils/ui_helpers.py
# Funções de utilidade para o frontend Streamlit (CSS, Base64 de Imagens).

import streamlit as st
from pathlib import Path
import base64
from typing import Optional

# Define o diretório base como a pasta "frontend"
BASE_DIR = Path(__file__).resolve().parent.parent      # .../itatchi/frontend
ASSETS_DIR = BASE_DIR / "assets"                       # .../itatchi/frontend/assets

# ----------------------------------
# 1. FUNÇÃO PARA APLICAR O CSS GLOBAL
# ----------------------------------
def load_global_style():
    """Carrega o arquivo style.css e aplica o CSS customizado via st.markdown."""
    css_path = BASE_DIR / "style.css"

    try:
        # Abre e lê o arquivo CSS
        with open(css_path, encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ Arquivo CSS não encontrado: {css_path}")

# ----------------------------------
# 2. FUNÇÃO PARA CARREGAR IMAGEM EM BASE64
# ----------------------------------
def load_image_b64(filename: str) -> Optional[str]:
    """
    Carrega uma imagem da pasta 'assets' e retorna seu conteúdo em formato Base64.
    
    Args:
        filename: O nome do arquivo de imagem (ex: 'logo.png').
        
    Returns:
        A string Base64 da imagem, ou None se o arquivo não for encontrado.
    """
    path = ASSETS_DIR / filename
    try:
        # Abre o arquivo em modo binário (rb) e codifica para Base64
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        st.warning(f"⚠️ Imagem não encontrada: {path}")
        return None