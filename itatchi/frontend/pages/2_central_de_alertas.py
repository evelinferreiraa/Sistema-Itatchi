# ALERTA DE VENCIMENTO

import streamlit as st
import requests
import pandas as pd
from utils.ui_helpers import load_global_style

load_global_style()

API_URL = "http://localhost:5000"

st.title("Central de Alertas")

# Função de Busca

def carregar_documentos(status_lista):
    # Busca documentos na API com base nos status fornecidos.
    data_total = []
    
    try:
        for status in status_lista:
            # Chama a API com o filtro de status
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

# Função de Estilo (Retorna CSS)

def style_status(val):
    # Esta função será aplicada à coluna 'Status de Alerta'

    if val == 'VENCIDO':
        return 'background-color: #ffcccc; color: #cc0000; font-weight: bold;' 
    elif val == 'A_VENCER':
        return 'background-color: #ffecb3; color: #ff9800; font-weight: bold;' 
    return '' 

# Lógica Principal da Página 

# 1. Carrega todos os documentos críticos (A_VENCER ou VENCIDO)
documentos_criticos = carregar_documentos(['A_VENCER', 'VENCIDO'])

if documentos_criticos:
    df = pd.DataFrame(documentos_criticos)
    
    # Renomeia as colunas para exibição amigável
    df = df.rename(columns={'status': 'Status de Alerta'})
    
    # Ordena: VENCIDO primeiro, depois A_VENCER
    df['prioridade'] = df['Status de Alerta'].apply(lambda x: 1 if x == 'VENCIDO' else 2)
    df = df.sort_values(by=['prioridade', 'validade'], ascending=[True, True])
    
    # Separa em DataFrames
    vencidos = df[df['Status de Alerta'] == 'VENCIDO'].drop(columns=['prioridade'])
    a_vencer = df[df['Status de Alerta'] == 'A_VENCER'].drop(columns=['prioridade'])
    
    # Colunas a serem exibidas nas tabelas
    colunas_exibicao = ['titulo', 'validade', 'responsavel', 'filial', 'tipo', 'Status de Alerta']

    # Seção de Vencidos (Prioridade 1)
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

    # Seção A Vencer (Prioridade 2)
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