# itatchi/frontend/pages/2_consulta_e_filtros.py
# PESQUISA / CENTRAL INICIAL

import streamlit as st
import requests
from datetime import date
import calendar
import pandas as pd

API_URL = "http://localhost:5000"

st.title("Central de consultas")
st.caption("Visualize documentos relacionados e próximos ao vencimento.")
st.markdown("---")

# -----------------------------
# Filtros superiores
# -----------------------------
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

# Período: usamos o mês de referência (apenas uma data -> mês inteiro)
data_ref = col_periodo.date_input("Período (mês de referência)", value=date.today())

extra_opcao = col_extra.selectbox(
    "Algo a mais?",
    options=[
        "Todos",
        "Somente próximos ao vencimento",
        "Somente vencidos",
    ],
)

botao_buscar = col_buscar.button("Buscar")
botao_relatorio = col_rel.button("Gerar Relatório")

# Estado para manter os resultados
if "docs_relacionados" not in st.session_state:
    st.session_state["docs_relacionados"] = []

if "docs_proximos" not in st.session_state:
    st.session_state["docs_proximos"] = []


# -----------------------------
# Chamada ao backend ao clicar em Buscar
# -----------------------------
def buscar_alertas():
    ano = data_ref.year
    mes = data_ref.month

    # Primeiro e último dia do mês
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

            # Filtro extra
            if extra_opcao == "Somente próximos ao vencimento":
                docs_prox = [d for d in docs_prox if d.get("status") == "A_VENCER"]
            elif extra_opcao == "Somente vencidos":
                docs_prox = [d for d in docs_prox if d.get("status") == "VENCIDO"]

            st.session_state["docs_relacionados"] = docs_rel
            st.session_state["docs_proximos"] = docs_prox

            st.success("Busca realizada com sucesso.")
        else:
            # Tratamento de erro mais seguro: tenta JSON, cai para texto bruto
            try:
                payload = resp.json()
                msg = payload.get("erro", "Resposta JSON sem campo 'erro'.")
            except ValueError:
                msg = resp.text or "Resposta não JSON do servidor."

            st.error(
                f"Erro ao buscar alertas (HTTP {resp.status_code}): {msg}"
            )

    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao backend. Verifique se o Flask está rodando.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado na busca: {e}")


if botao_buscar:
    buscar_alertas()

# -----------------------------
# Layout principal: esquerda (listas) / direita (calendário)
# -----------------------------
col_esq, col_dir = st.columns([1, 2])

# --- COLUNA ESQUERDA ---
with col_esq:
    st.markdown("### Documentos relacionados")

    docs_rel = st.session_state["docs_relacionados"]
    if docs_rel:
        df_rel = pd.DataFrame(docs_rel)
        colunas_rel = [
            c for c in ["titulo", "responsavel", "validade", "status"]
            if c in df_rel.columns
        ]
        st.dataframe(df_rel[colunas_rel], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum documento encontrado para os filtros selecionados.")

    st.markdown("---")
    st.markdown("### Próximos ao vencimento")

    docs_prox = st.session_state["docs_proximos"]
    if docs_prox:
        df_prox = pd.DataFrame(docs_prox)
        colunas_prox = [
            c for c in ["titulo", "validade", "status"]
            if c in df_prox.columns
        ]
        st.dataframe(df_prox[colunas_prox], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum documento próximo do vencimento encontrado.")

# --- COLUNA DIREITA (Calendário simplificado) ---
with col_dir:
    ano = data_ref.year
    mes = data_ref.month
    nome_mes = calendar.month_name[mes].capitalize()

    st.markdown(f"### {nome_mes} - {ano}")

    # Matriz de dias do mês (0 = dia vazio)
    matriz_dias = calendar.monthcalendar(ano, mes)

    # Nomes de colunas ÚNICOS para evitar erro do PyArrow
    nomes_colunas = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    df_cal = pd.DataFrame(matriz_dias, columns=nomes_colunas)
    df_cal.replace(0, "", inplace=True)

    st.table(df_cal)

    st.caption(
        "Os marcadores visuais no calendário serão implementados futuramente, "
        "com base nos documentos retornados pelo backend."
    )

# -----------------------------
# Geração de relatório (simples CSV por enquanto)
# -----------------------------
if botao_relatorio:
    docs_prox = st.session_state["docs_proximos"]
    if not docs_prox:
        st.warning("Não há documentos próximos ao vencimento para gerar relatório.")
    else:
        df_rel = pd.DataFrame(docs_prox)
        csv = df_rel.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Baixar relatório em CSV",
            data=csv,
            file_name=f"relatorio_alertas_{data_ref.strftime('%Y_%m')}.csv",
            mime="text/csv",
        )
