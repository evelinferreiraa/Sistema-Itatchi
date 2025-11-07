# itatchi/frontend/utils/ui_helpers.py

import streamlit as st
from pathlib import Path
import base64

# ----------------------------------
# FUNÇÃO PARA APLICAR O CSS GLOBAL
# ----------------------------------
def load_global_style():
    # Diretório base = pasta "frontend"
    base_dir = Path(__file__).resolve().parent.parent  # .../frontend
    css_path = base_dir / "style.css"

    try:
        with open(css_path, encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ Arquivo CSS não encontrado: {css_path}")

# ----------------------------------
# FUNÇÃO PARA CARREGAR IMAGEM EM BASE64
# ----------------------------------

# Agora o BASE_DIR é a pasta "frontend" (não "utils")
BASE_DIR = Path(__file__).resolve().parent.parent      # .../frontend
ASSETS_DIR = BASE_DIR / "assets"                       # .../frontend/assets

def load_image_b64(filename: str) -> str | None:
    path = ASSETS_DIR / filename
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        # opcional: logar o caminho pra debug
        st.warning(f"⚠️ Imagem não encontrada: {path}")
        return None
