# itatchi/frontend/app_frontend.py

import streamlit as st
import os
import requests
from datetime import date, datetime
import calendar
import pandas as pd
from utils.ui_helpers import load_global_style   # ⬅ novo import

# -----------------------------
# CONFIGURAÇÃO GLOBAL / CSS
# -----------------------------
st.set_page_config(layout="wide", page_title="Itatchi - Gerenciamento de Documentos")
load_global_style()  


st.markdown(
    """
    <div class="logo-container">
        <img src="assets/logo_itatchi.png" class="logo-image">
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# CENTRAL DE CONSULTAS (HOME)
# -----------------------------
API_URL = "http://localhost:5000"

st.title("Central de consultas")
st.caption("Visualize documentos relacionados e próximos ao vencimento.")
st.markdown("---")

# Filtros superiores
col_cat, col_periodo, col_extra, col_buscar, col_rel = st.columns([2, 2, 2, 1, 1])

CATEGORIAS = [
    "Todas",
    "Regulatórios",
    "Qualidade",
    "Pessoas",
    "Veículos",
    "Locais",
]

categoria = col_cat.selectbox("Categoria", options=CATEGORIAS, index=0)
data_ref = col_periodo.date_input("Período (mês de referência)", value=date.today())

extra_opcao = col_extra.selectbox(
    "Algo a mais?",
    options=["Todos", "Somente próximos ao vencimento", "Somente vencidos"],
)

with col_buscar:
    st.markdown("<br>", unsafe_allow_html=True)
    botao_buscar = st.button("Buscar")

with col_rel:
    st.markdown("<br>", unsafe_allow_html=True)
    botao_relatorio = st.button("Gerar Relatório")

# Estado
if "docs_relacionados" not in st.session_state:
    st.session_state["docs_relacionados"] = []

if "docs_proximos" not in st.session_state:
    st.session_state["docs_proximos"] = []


def buscar_alertas():
    ano = data_ref.year
    mes = data_ref.month

    primeiro_dia = date(ano, mes, 1)
    _, ultimo_dia_num = calendar.monthrange(ano, mes)
    ultimo_dia = date(ano, mes, ultimo_dia_num)

    params = {
        "inicio": primeiro_dia.isoformat(),
        "fim": ultimo_dia.isoformat(),
    }

    if categoria != "Todas":
        params["categoria"] = categoria

    try:
        resp = requests.get(f"{API_URL}/home", params=params, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            docs_rel = data.get("documentos_relacionados", [])
            docs_prox = data.get("proximos_vencimento", [])

            if extra_opcao == "Somente próximos ao vencimento":
                docs_prox = [d for d in docs_prox if d.get("status") == "A_VENCER"]
            elif extra_opcao == "Somente vencidos":
                docs_prox = [d for d in docs_prox if d.get("status") == "VENCIDO"]

            st.session_state["docs_relacionados"] = docs_rel
            st.session_state["docs_proximos"] = docs_prox

            st.success("Busca realizada com sucesso.")
        else:
            try:
                payload = resp.json()
                msg = payload.get("erro", "Resposta JSON sem campo 'erro'.")
            except ValueError:
                msg = resp.text or "Resposta não JSON do servidor."

            st.error(f"Erro ao buscar alertas (HTTP {resp.status_code}): {msg}")

    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao backend. Verifique se o Flask está rodando.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado na busca: {e}")


if botao_buscar:
    buscar_alertas()

# Layout principal: esquerda (listas) / direita (calendário)
col_esq, col_dir = st.columns([1, 2])

with col_esq:
    st.markdown("### Documentos relacionados")

    docs_rel = st.session_state["docs_relacionados"]
    if docs_rel:
        df_rel = pd.DataFrame(docs_rel)
        colunas_rel = [c for c in ["titulo", "responsavel", "validade", "status"] if c in df_rel.columns]
        st.dataframe(df_rel[colunas_rel], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum documento encontrado para os filtros selecionados.")

    st.markdown("---")
    st.markdown("### Próximos ao vencimento")

    docs_prox = st.session_state["docs_proximos"]
    if docs_prox:
        df_prox = pd.DataFrame(docs_prox)
        colunas_prox = [c for c in ["titulo", "validade", "status"] if c in df_prox.columns]
        st.dataframe(df_prox[colunas_prox], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum documento próximo do vencimento encontrado.")

with col_dir:
    ano = data_ref.year
    mes = data_ref.month
    nome_mes = calendar.month_name[mes].capitalize()

    st.markdown(f"### {nome_mes} - {ano}")

    docs_prox = st.session_state["docs_proximos"]
    dias_com_alerta = set()

    for d in docs_prox:
        validade_str = d.get("validade")
        if not validade_str:
            continue

        try:
            dt_validade = datetime.fromisoformat(validade_str)
        except ValueError:
            try:
                dt_validade = datetime.strptime(validade_str, "%Y-%m-%d")
            except Exception:
                continue

        if dt_validade.year == ano and dt_validade.month == mes:
            dias_com_alerta.add(dt_validade.day)

    matriz_dias = calendar.monthcalendar(ano, mes)
    matriz_marcada = []
    for semana in matriz_dias:
        nova_semana = []
        for dia in semana:
            if dia == 0:
                nova_semana.append("")
            elif dia in dias_com_alerta:
                nova_semana.append(f"⚠ {dia}")
            else:
                nova_semana.append(str(dia))
        matriz_marcada.append(nova_semana)

    nomes_colunas = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    df_cal = pd.DataFrame(matriz_marcada, columns=nomes_colunas)
    styler = df_cal.style.set_properties(**{"text-align": "left"})

    st.table(styler)
    st.caption(
        "Dias marcados com ⚠ indicam documentos próximos do vencimento ou já vencidos "
        "no mês e ano selecionados."
    )

if botao_relatorio:
    docs_prox = st.session_state["docs_proximos"]
    if not docs_prox:
        st.warning("Não há documentos próximos ao vencimento para gerar relatório.")
    else:
        df_relatorio = pd.DataFrame(docs_prox)
        csv = df_relatorio.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Baixar relatório em CSV",
            data=csv,
            file_name=f"relatorio_alertas_{data_ref.strftime('%Y_%m')}.csv",
            mime="text/csv",
        )
