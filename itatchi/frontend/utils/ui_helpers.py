import streamlit as st
from pathlib import Path

def load_global_style():
    """
    Aplica o CSS global (style.css) e garante a fonte Inter
    para todas as páginas do Streamlit.
    """
    # Diretório base = pasta "frontend"
    base_dir = Path(__file__).resolve().parent.parent
    css_path = base_dir / "style.css"

    try:
        with open(css_path, encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ Arquivo CSS não encontrado: {css_path}")
