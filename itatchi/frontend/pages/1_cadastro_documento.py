# itatchi/frontend/pages/1_cadastro_documento.py
# Página Streamlit para o formulário de cadastro de novos documentos.

import streamlit as st
import requests
from datetime import datetime, date
from typing import Optional, Dict, Any

from utils.ui_helpers import load_global_style, setup_logo

# --- CONFIGURAÇÃO GLOBAL / CSS E LOGO ---
setup_logo() 
load_global_style()

# URL do Backend Flask
API_URL: str = "http://localhost:5000"

# --- Dados Iniciais Mockados (devem ser substituídos por chamadas à API) ---
OPCOES_FILIAIS: Dict[int, str] = {1: "Matriz São Paulo"} 
OPCOES_TIPOS: Dict[int, Dict[str, str]] = {
    1: {"nome": "CNPJ", "categoria": "Regulatórios"},
    2: {"nome": "ANTT", "categoria": "Veículos"},
    3: {"nome": "CNH", "categoria": "Pessoas"}
}

def formatar_data(data: Optional[date]) -> Optional[str]:
    """Converte um objeto date ou datetime para o formato string YYYY-MM-DD exigido pela API."""
    if data and isinstance(data, (datetime, date)):
        return data.strftime('%Y-%m-%d')
    return None

# --- ESTRUTURA DA TELA DE CADASTRO ---

st.title("Cadastro de Informações")
st.subheader("Preencha as informações principais para agendar seu lembrete.")
st.markdown("---")

with st.form(key='cadastro_documento_form'):
    # Campos Obrigatórios
    st.header("Dados Essenciais")
    col1, col2 = st.columns(2)
    
    filial_selecionada: int = col1.selectbox("Filial", options=list(OPCOES_FILIAIS.keys()), format_func=lambda x: OPCOES_FILIAIS[x])
    tipo_selecionado_id: int = col2.selectbox("Tipo de Documento", options=list(OPCOES_TIPOS.keys()), format_func=lambda x: OPCOES_TIPOS[x]['nome'])
    
    st.subheader("Informações Básicas")
    col_a, col_b = st.columns(2)
    categoria_derivada: str = OPCOES_TIPOS[tipo_selecionado_id]['categoria']
    
    col_a.text_input("Categoria (Derivada do Tipo)", value=categoria_derivada, disabled=True)
    titulo: Optional[str] = col_b.text_input("Título / Descrição Breve", placeholder="Licença Sanitária Loja A")
    responsavel: Optional[str] = st.text_input("Pessoa/Setor Responsável", placeholder="João da Silva ou RH", help="Campo obrigatório.")

    st.markdown("---")
    
    st.header("Validade")
    col3, col4, col5 = st.columns(3)
    emissao: Optional[date] = col3.date_input("Data de Emissão (opcional)", value=None)
    sem_validade: bool = col5.checkbox("Sem Validade Definida", value=False)
    
    validade: Optional[date] = None
    if not sem_validade:
        validade = col4.date_input("Data de Validade (opcional)", value=None, min_value=date.today())
        if validade is None:
            col4.warning("Recomendado informar a Validade.")

    col6, col7 = st.columns(2)
    numero: Optional[str] = col6.text_input("Número do Documento", placeholder="000123/2025")
    orgao_emissor: Optional[str] = col7.text_input("Órgão Emissor", placeholder="Prefeitura de São Paulo")
    caminho_atual: Optional[str] = st.text_input("Caminho do Arquivo Local", placeholder="C:\\docs\\SP01\\Licenca.pdf")
    observacoes: Optional[str] = st.text_area("Observações / Anotações")
    
    st.markdown("---")
    submit_button: bool = st.form_submit_button(label='Cadastrar Documento')

# --- Lógica de Envio (Ação de POST para o Flask) ---
if submit_button:
    # 1. Validação de campos obrigatórios no frontend
    if not titulo or not responsavel:
        st.error("Por favor, preencha o **Título** e o **Responsável**.")
    else:
        # 2. Construção do payload
        payload: Dict[str, Any] = {
            "filial_id": filial_selecionada,
            "tipo_id": tipo_selecionado_id,
            "titulo": titulo,
            "numero": numero,
            "responsavel": responsavel,
            "emissao": formatar_data(emissao),
            "validade": formatar_data(validade) if not sem_validade else None, 
            "sem_validade": sem_validade,
            "orgao_emissor": orgao_emissor,
            "observacoes": observacoes,
            "caminho_atual": caminho_atual
        }

        # 3. Chamada à API
        try:
            response = requests.post(f"{API_URL}/documentos", json=payload)
            
            if response.status_code == 201:
                data: Dict[str, Any] = response.json()
                st.success(f"Documento cadastrado com sucesso! ID: {data['id']}. Status Calculado: **{data['status']}**")
                st.balloons()
            else:
                # Trata erros retornados pelo backend (ex: erro de validação de data, 400)
                error_msg: str = response.json().get('erro', 'Resposta desconhecida do servidor.')
                st.error(f"Erro ao cadastrar documento (Código {response.status_code}): {error_msg}")

        except requests.exceptions.ConnectionError:
            st.error("Erro de Conexão. Verifique se o Backend Flask está rodando em http://localhost:5000.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")