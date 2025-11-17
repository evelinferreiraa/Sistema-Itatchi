# itatchi/frontend/pages/2_central_de_alertas.py
# Página Streamlit para a Central de Alertas (Visualização de VENCIDO e A_VENCER).

import os
import streamlit as st
import requests
import pandas as pd
from typing import List, Dict, Any

from utils.ui_helpers import load_global_style, setup_logo

# --- CONFIGURAÇÃO GLOBAL / CSS E LOGO ---
setup_logo() 
load_global_style()

API_URL = os.getenv("API_URL", "http://localhost:5000")

st.title("Central de Alertas")

# --- FUNÇÕES DE BUSCA E ESTILO ---

def carregar_documentos(status_lista: List[str]) -> List[Dict[str, Any]]:
    """Busca documentos na API com base nos status fornecidos."""
    data_total: List[Dict[str, Any]] = []
    
    try:
        for status in status_lista:
            # Chama a API /documentos com o filtro de status
            response = requests.get(f"{API_URL}/documentos", params={'status': status})
            
            if response.status_code == 200:
                data = response.json()
                data_total.extend(data)
            else:
                st.error(f"Erro ao buscar documentos {status} (Código {response.status_code}).")
                
        return data_total
            
    except requests.exceptions.ConnectionError:
        st.error("Erro de Conexão. Verifique se o Backend Flask está rodando em http://localhost:5000.")
        return []

def style_status(val: str) -> str:
    """Função de estilo Pandas para aplicar cores à coluna 'Status de Alerta'."""
    if val == 'VENCIDO':
        # Vermelho (Alto Alerta)
        return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' 
    elif val == 'A_VENCER':
        # Amarelo (Alerta Moderado)
        return 'background-color: #ffecb3; color: #ff9800; font-weight: bold;' 
    return ''

# --- LÓGICA PRINCIPAL ---

# 1. Carrega todos os documentos críticos
documentos_criticos = carregar_documentos(['A_VENCER', 'VENCIDO'])

if documentos_criticos:
    df = pd.DataFrame(documentos_criticos)
    
    df = df.rename(columns={'status': 'Status de Alerta'})
    
    # 2. Define a prioridade e ordena: VENCIDO (1) > A_VENCER (2)
    df['prioridade'] = df['Status de Alerta'].apply(lambda x: 1 if x == 'VENCIDO' else 2)
    df = df.sort_values(by=['prioridade', 'validade'], ascending=[True, True])
    
    # 3. Separa DataFrames e define colunas de exibição
    vencidos = df[df['Status de Alerta'] == 'VENCIDO'].drop(columns=['prioridade'])
    a_vencer = df[df['Status de Alerta'] == 'A_VENCER'].drop(columns=['prioridade'])
    
    colunas_exibicao = ['titulo', 'validade', 'responsavel', 'filial', 'tipo', 'Status de Alerta']

    # Seção 1: Documentos Vencidos
    st.header("Documentos Vencidos")
    if not vencidos.empty:
        st.warning(f"**{len(vencidos)} documento(s) está(ão) VENCIDO(S)!** ")
        st.dataframe(
            vencidos[colunas_exibicao]
                .style.applymap(style_status, subset=['Status de Alerta']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("Nenhum documento encontrado com status VENCIDO. ")

    st.markdown("---")

    # Seção 2: Próximos Vencimentos
    st.header("Próximos Vencimentos")
    if not a_vencer.empty:
        st.info(f"**{len(a_vencer)} documento(s)** próximo(s) de vencer. ")
        st.dataframe(
            a_vencer[colunas_exibicao]
                .style.applymap(style_status, subset=['Status de Alerta']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum documento encontrado com status A VENCER. ")

else:
    st.success("Tudo certo! Não há alertas de vencimento.")