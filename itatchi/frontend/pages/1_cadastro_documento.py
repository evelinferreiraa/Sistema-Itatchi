# FORMULÁRIO DE CADASTRO

import streamlit as st
import requests
from datetime import datetime, date

st.set_page_config(page_title="Cadastro de Documento")

# URL do Backend Flask
API_URL = "http://localhost:5000"

# --- Dados Iniciais Mockados ---
# (Baseado nos dados de teste inseridos no SQL para teste)
OPCOES_FILIAIS = {1: "Matriz São Paulo"} 
OPCOES_TIPOS = {
    1: {"nome": "CNPJ", "categoria": "Regulatórios"},
    2: {"nome": "ANTT", "categoria": "Veículos"},
    3: {"nome": "CNH", "categoria": "Pessoas"}
}

def formatar_data(data):
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
    
    filial_selecionada = col1.selectbox("Filial", options=list(OPCOES_FILIAIS.keys()), format_func=lambda x: OPCOES_FILIAIS[x])
    tipo_selecionado_id = col2.selectbox("Tipo de Documento", options=list(OPCOES_TIPOS.keys()), format_func=lambda x: OPCOES_TIPOS[x]['nome'])
    
    st.subheader("Informações Básicas")
    col_a, col_b = st.columns(2)
    categoria_derivada = OPCOES_TIPOS[tipo_selecionado_id]['categoria']
    col_a.text_input("Categoria (Derivada do Tipo)", value=categoria_derivada, disabled=True)
    titulo = col_b.text_input("Título / Descrição Breve", placeholder="Licença Sanitária Loja A")
    responsavel = st.text_input("Pessoa/Setor Responsável", placeholder="João da Silva ou RH", help="Campo obrigatório.")

    st.markdown("---")
    
    st.header("Validade")
    col3, col4, col5 = st.columns(3)
    emissao = col3.date_input("Data de Emissão (opcional)", value=None)
    sem_validade = col5.checkbox("Sem Validade Definida", value=False)
    
    validade = None
    if not sem_validade:
        validade = col4.date_input("Data de Validade (opcional)", value=None, min_value=date.today())
        if validade is None:
            col4.warning("Recomendado informar a Validade.")

    col6, col7 = st.columns(2)
    numero = col6.text_input("Número do Documento", placeholder="000123/2025")
    orgao_emissor = col7.text_input("Órgão Emissor", placeholder="Prefeitura de São Paulo")
    caminho_atual = st.text_input("Caminho do Arquivo Local", placeholder="C:\\docs\\SP01\\Licenca.pdf")
    observacoes = st.text_area("Observações / Anotações")
    
    st.markdown("---")
    submit_button = st.form_submit_button(label='Cadastrar Documento')

# --- Lógica de Envio (Ação de POST para o Flask) ---
if submit_button:
    if not titulo or not responsavel:
        st.error("Por favor, preencha o **Título** e o **Responsável**.")
    else:
        payload = {
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

        try:
            response = requests.post(f"{API_URL}/documentos", json=payload)
            
            if response.status_code == 201:
                data = response.json()
                st.success(f"Documento cadastrado com sucesso! ID: {data['id']}. Status Calculado: **{data['status']}**")
                st.balloons()
            else:
                st.error(f"Erro ao cadastrar documento (Código {response.status_code}): {response.json().get('erro', 'Resposta desconhecida do servidor.')}")

        except requests.exceptions.ConnectionError:
            st.error("Erro de Conexão. Verifique se o Backend Flask está rodando em http://localhost:5000.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")