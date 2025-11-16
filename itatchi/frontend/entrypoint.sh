#!/bin/bash
echo "Iniciando o frontend Streamlit..."
streamlit run app_frontend.py --server.port=8501 --server.address=0.0.0.0
