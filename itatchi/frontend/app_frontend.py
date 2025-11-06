# itatchi/frontend/app_frontend.py

import streamlit as st
import requests
from datetime import date, datetime
import calendar
import pandas as pd
import math
from io import BytesIO

from utils.ui_helpers import load_global_style   # aplica CSS + fonte Inter

# ----------------------------------
# CONFIGURAÇÃO GLOBAL / CSS
# ----------------------------------
st.set_page_config(layout="wide", page_title="Itatchi - Gerenciamento de Documentos")
load_global_style()

# Logo fixa no topo à esquerda (opcional)
st.markdown(
    """
    <div class="logo-container">
        <img src="assets/logo_itatchi.png" class="logo-image">
    </div>
    """,
    unsafe_allow_html=True
)

API_URL = "http://localhost:5000"

# ----------------------------------
# TÍTULO / DESCRIÇÃO
# ----------------------------------
st.title("Central de consultas")
st.caption("Visualize documentos relacionados e próximos ao vencimento.")
st.markdown("---")

# ==================================
# 1. FILTROS SUPERIORES
# ==================================

col_cat, col_inicio, col_fim, col_extra, col_buscar, col_rel = st.columns(
    [2, 2, 2, 2, 1, 1]
)

CATEGORIAS = [
    "Todas",
    "Regulatórios",
    "Qualidade",
    "Pessoas",
    "Veículos",
    "Locais",
]

categoria = col_cat.selectbox("Categoria", options=CATEGORIAS, index=0)

hoje = date.today()
primeiro_dia_mes = hoje.replace(day=1)
ultimo_dia_mes = date(
    hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1]
)

data_inicio = col_inicio.date_input("Início do período", value=primeiro_dia_mes)
data_fim = col_fim.date_input("Fim do período", value=ultimo_dia_mes)

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

if data_fim < data_inicio:
    st.error("⚠ A data final não pode ser menor que a data inicial.")
    st.stop()

# ==================================
# 2. ESTADO GLOBAL (SESSION_STATE)
# ==================================
if "docs_relacionados" not in st.session_state:
    st.session_state["docs_relacionados"] = []

if "docs_proximos" not in st.session_state:
    st.session_state["docs_proximos"] = []

# Páginas de paginação
st.session_state.setdefault("relacionados_page", 1)
st.session_state.setdefault("proximos_page", 1)
st.session_state.setdefault("cal_page_home", 0)

# ==================================
# 3. FUNÇÕES AUXILIARES
# ==================================

def buscar_alertas():
    """Chama o endpoint /home com filtros de categoria e período."""
    params = {
        "inicio": data_inicio.isoformat(),
        "fim": data_fim.isoformat(),
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

            # Reseta paginações
            st.session_state["relacionados_page"] = 1
            st.session_state["proximos_page"] = 1
            st.session_state["cal_page_home"] = 0

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


def mostrar_tabela_paginada(df, colunas, chave_prefixo, titulo):
    """Renderiza tabela com paginação."""
    st.markdown(f"### {titulo}")

    if df.empty:
        st.info("Nenhum documento encontrado.")
        return

    page_size = 10
    total = len(df)
    total_pages = max(1, math.ceil(total / page_size))

    current_page = st.session_state.get(f"{chave_prefixo}_page", 1)

    col_prev, col_info, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀", key=f"{chave_prefixo}_prev") and current_page > 1:
            current_page -= 1
    with col_next:
        if st.button("▶", key=f"{chave_prefixo}_next") and current_page < total_pages:
            current_page += 1

    st.session_state[f"{chave_prefixo}_page"] = current_page

    start = (current_page - 1) * page_size
    end = start + page_size
    df_page = df.iloc[start:end]

    col_info.markdown(
        f"Página **{current_page}** de **{total_pages}** "
        f"(total de {total} documentos)."
    )

    st.dataframe(
        df_page[colunas],
        use_container_width=True,
        hide_index=True,
    )


def iterar_meses(inicio: date, fim: date):
    """Gera (ano, mês) para todos os meses entre duas datas (inclusive)."""
    ano = inicio.year
    mes = inicio.month
    while (ano, mes) <= (fim.year, fim.month):
        yield ano, mes
        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1


def desenhar_calendario(documentos_prox, inicio: date, fim: date):
    """
    Desenha calendário com paginação de mês.
    Marca dias com documentos próximos/vencidos usando ⚠.
    """
    st.markdown("### Calendário de vencimentos")

    meses = list(iterar_meses(inicio, fim))
    if not meses:
        st.info("Período selecionado não contém meses válidos.")
        return

    col_prev, col_label, col_next = st.columns([1, 4, 1])

    idx = st.session_state.get("cal_page_home", 0)

    with col_prev:
        if st.button("◀ mês", key="cal_home_prev") and idx > 0:
            idx -= 1
    with col_next:
        if st.button("mês ▶", key="cal_home_next") and idx < len(meses) - 1:
            idx += 1

    st.session_state["cal_page_home"] = idx
    ano, mes = meses[idx]
    nome_mes = calendar.month_name[mes].capitalize()
    col_label.markdown(f"#### {nome_mes} / {ano}")

    # Descobre dias com alerta nesse mês
    dias_com_alerta = set()
    for d in documentos_prox:
        validade_str = d.get("validade")
        if not validade_str:
            continue
        try:
            dt_validade = datetime.fromisoformat(validade_str).date()
        except ValueError:
            try:
                dt_validade = datetime.strptime(validade_str, "%Y-%m-%d").date()
            except Exception:
                continue

        if dt_validade.year == ano and dt_validade.month == mes:
            dias_com_alerta.add(dt_validade.day)

    matriz = calendar.monthcalendar(ano, mes)
    linhas = []
    for semana in matriz:
        linha = []
        for dia in semana:
            if dia == 0:
                linha.append("")
            elif dia in dias_com_alerta:
                linha.append(f"⚠ {dia}")
            else:
                linha.append(str(dia))
        linhas.append(linha)

    nomes_colunas = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    df_cal = pd.DataFrame(linhas, columns=nomes_colunas)
    styler = df_cal.style.set_properties(**{"text-align": "left"})
    st.table(styler)

    st.caption(
        "Dias marcados com ⚠ indicam documentos próximos do vencimento ou já vencidos "
        "no período selecionado."
    )

# ==================================
# 4. EXECUTA BUSCA (se clicar)
# ==================================
if botao_buscar:
    buscar_alertas()

# ==================================
# 5. LAYOUT PRINCIPAL
# ==================================
col_esq, col_dir = st.columns([1, 2])

# -------- COLUNA ESQUERDA --------
with col_esq:
    docs_rel = st.session_state["docs_relacionados"]
    docs_prox = st.session_state["docs_proximos"]

    if docs_rel:
        df_rel = pd.DataFrame(docs_rel)
    else:
        df_rel = pd.DataFrame([])

    if docs_prox:
        df_prox = pd.DataFrame(docs_prox)
    else:
        df_prox = pd.DataFrame([])

    colunas_rel = [
        c for c in ["titulo", "responsavel", "validade", "status"]
        if c in df_rel.columns
    ]
    colunas_prox = [
        c for c in ["titulo", "validade", "status"]
        if c in df_prox.columns
    ]

    mostrar_tabela_paginada(
        df_rel, colunas_rel, "relacionados", "Documentos relacionados"
    )

    st.markdown("---")

    mostrar_tabela_paginada(
        df_prox, colunas_prox, "proximos", "Próximos ao vencimento"
    )

# -------- COLUNA DIREITA (CALENDÁRIO) --------
with col_dir:
    desenhar_calendario(
        st.session_state["docs_proximos"],
        data_inicio,
        data_fim
    )

# ==================================
# 6. RELATÓRIO EM EXCEL
# ==================================
if botao_relatorio:
    docs_rel = st.session_state["docs_relacionados"]
    docs_prox = st.session_state["docs_proximos"]

    if not docs_rel and not docs_prox:
        st.warning("Não há documentos para gerar relatório.")
    else:
        # Junta relacionados + próximos e remove duplicados por ID (se existir)
        todos = (docs_rel or []) + (docs_prox or [])
        if todos and isinstance(todos[0], dict) and "id" in todos[0]:
            dedup = {}
            for d in todos:
                did = d.get("id")
                if did not in dedup:
                    dedup[did] = d
            todos_final = list(dedup.values())
        else:
            todos_final = todos

        df_full = pd.DataFrame(todos_final)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_full.to_excel(writer, index=False, sheet_name="Alertas")
        buffer.seek(0)

        st.download_button(
            label="⬇️ Baixar relatório em XLSX",
            data=buffer,
            file_name=f"relatorio_alertas_{data_inicio}_a_{data_fim}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )