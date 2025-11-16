# itatchi/frontend/app_frontend.py
# Página principal do frontend (Central de Consultas), com filtros, tabelas paginadas e calendário.
import os
import streamlit as st
import requests
from datetime import date, datetime
import calendar
import pandas as pd
import math
from io import BytesIO
# Importa 'os' apenas se for estritamente necessário para outras partes do código
from typing import List, Dict, Any, Optional, Generator, Tuple

# Importa helpers
from utils.ui_helpers import load_global_style, load_image_b64, setup_logo

# 1. Configura a página (incluindo st.set_page_config e st.logo)
setup_logo() 

# 2. Carrega ícone de alerta (usa caminhos definidos internamente em ui_helpers)
ALERT_ICON_B64: Optional[str] = load_image_b64("alert_marker.png")

# 3. Carrega o CSS global
load_global_style()

API_URL = os.getenv("API_URL", "http://localhost:5000")

# ----------------------------------
# TÍTULO / DESCRIÇÃO
# ----------------------------------
st.title("Central de Consultas")
st.caption("Visualize documentos relacionados e próximos ao vencimento.")
st.markdown("---")

# ==================================
# 1. FILTROS SUPERIORES
# ==================================

col_cat, col_inicio, col_fim, col_extra, col_buscar, col_rel = st.columns(
    [2, 2, 2, 2, 1, 1]
)

CATEGORIAS: List[str] = [
    "Todas",
    "Regulatórios",
    "Qualidade",
    "Pessoas",
    "Veículos",
    "Locais",
]

categoria: str = col_cat.selectbox("Categoria", options=CATEGORIAS, index=0)

hoje: date = date.today()
primeiro_dia_mes: date = hoje.replace(day=1)
ultimo_dia_mes: date = date(
    hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1]
)

data_inicio: date = col_inicio.date_input("Início do período", value=primeiro_dia_mes)
data_fim: date = col_fim.date_input("Fim do período", value=ultimo_dia_mes)

extra_opcao: str = col_extra.selectbox(
    "Algo a mais?",
    options=["Todos", "Somente próximos ao vencimento", "Somente vencidos"],
)

with col_buscar:
    st.markdown("<br>", unsafe_allow_html=True)
    botao_buscar: bool = st.button("Buscar")

with col_rel:
    st.markdown("<br>", unsafe_allow_html=True)
    botao_relatorio: bool = st.button("Gerar Relatório")

if data_fim < data_inicio:
    st.error("⚠ A data final não pode ser menor que a data inicial.")
    st.stop()

relatorio_placeholder = st.empty()

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
    """Chama o endpoint /home com filtros de categoria e período para popular as tabelas e o calendário."""
    params: Dict[str, str] = {
        "inicio": data_inicio.isoformat(),
        "fim": data_fim.isoformat(),
    }
    if categoria != "Todas":
        params["categoria"] = categoria

    try:
        resp = requests.get(f"{API_URL}/home", params=params, timeout=10)

        if resp.status_code == 200:
            data: Dict[str, List[Dict[str, Any]]] = resp.json()
            
            docs_rel_all: List[Dict[str, Any]] = data.get("documentos_relacionados", [])
            docs_prox_all: List[Dict[str, Any]] = data.get("proximos_vencimento", [])

            # --- PRIORIDADE DE STATUS PARA ORDENAÇÃO ---
            prioridade_status: Dict[str, int] = {"VENCIDO": 1, "A_VENCER": 2}

            def sort_key(doc: Dict[str, Any]) -> Tuple[int, str]:
                """Chave de ordenação: por status prioritário, depois por data de validade."""
                status: Optional[str] = doc.get("status")
                validade: str = doc.get("validade") or "9999-12-31"
                return (prioridade_status.get(status, 99), validade)

            # 1. Próximos ao vencimento: SEMPRE mostra todos (A_VENCER + VENCIDO), ordenados
            docs_prox_ordenados: List[Dict[str, Any]] = sorted(docs_prox_all, key=sort_key)

            # 2. Documentos relacionados: FILTRADOS conforme a opção "Algo a mais?"
            if extra_opcao == "Todos":
                docs_rel_filtrados: List[Dict[str, Any]] = sorted(docs_rel_all, key=sort_key)
            elif extra_opcao == "Somente próximos ao vencimento":
                docs_rel_filtrados = [
                    d for d in docs_rel_all if d.get("status") == "A_VENCER"
                ]
                docs_rel_filtrados = sorted(docs_rel_filtrados, key=sort_key)
            elif extra_opcao == "Somente vencidos":
                docs_rel_filtrados = [
                    d for d in docs_rel_all if d.get("status") == "VENCIDO"
                ]
                docs_rel_filtrados = sorted(docs_rel_filtrados, key=sort_key)
            else:
                docs_rel_filtrados = sorted(docs_rel_all, key=sort_key)

            # Guarda nas variáveis de sessão e reseta paginações
            st.session_state["docs_relacionados"] = docs_rel_filtrados
            st.session_state["docs_proximos"] = docs_prox_ordenados
            st.session_state["relacionados_page"] = 1
            st.session_state["proximos_page"] = 1
            st.session_state["cal_page_home"] = 0

            st.success("Busca realizada com sucesso.")
        else:
            try:
                payload: Dict[str, str] = resp.json()
                msg: str = payload.get("erro", "Resposta JSON sem campo 'erro'.")
            except ValueError:
                msg = resp.text or "Resposta não JSON do servidor."

            st.error(f"Erro ao buscar alertas (HTTP {resp.status_code}): {msg}")

    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao backend. Verifique se o Flask está rodando.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado na busca: {e}")


def mostrar_tabela_paginada(df: pd.DataFrame, colunas: List[str], chave_prefixo: str, titulo: str):
    """Renderiza tabela do Pandas com controles de paginação para 10 itens por página."""
    st.markdown(f"### {titulo}")

    if df.empty:
        st.info("Nenhum documento encontrado.")
        return

    page_size: int = 10
    total: int = len(df)
    total_pages: int = max(1, math.ceil(total / page_size))

    current_page: int = st.session_state.get(f"{chave_prefixo}_page", 1)

    # Controles de navegação
    col_prev, col_info, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("◀", key=f"{chave_prefixo}_prev") and current_page > 1:
            current_page -= 1
    with col_next:
        if st.button("▶", key=f"{chave_prefixo}_next") and current_page < total_pages:
            current_page += 1

    st.session_state[f"{chave_prefixo}_page"] = current_page

    # Aplica a paginação ao DataFrame
    start: int = (current_page - 1) * page_size
    end: int = start + page_size
    df_page: pd.DataFrame = df.iloc[start:end]

    col_info.markdown(
        f"Página **{current_page}** de **{total_pages}** "
        f"(total de {total} documentos)."
    )

    st.dataframe(
        df_page[colunas],
        use_container_width=True,
        hide_index=True,
    )


def iterar_meses(inicio: date, fim: date) -> Generator[Tuple[int, int], None, None]:
    """Gera (ano, mês) para todos os meses entre duas datas (inclusive)."""
    ano: int = inicio.year
    mes: int = inicio.month
    while (ano, mes) <= (fim.year, fim.month):
        yield ano, mes
        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1


def desenhar_calendario(documentos_prox: List[Dict[str, Any]], inicio: date, fim: date):
    """
    Desenha calendário interativo com paginação de mês.
    Marca dias com documentos próximos/vencidos usando o ícone de alerta.
    """
    st.markdown("### Calendário de vencimentos")

    meses: List[Tuple[int, int]] = list(iterar_meses(inicio, fim))
    if not meses:
        st.info("Período selecionado não contém meses válidos.")
        return

    # Controles de paginação de mês
    col_prev, col_label, col_spacer, col_next = st.columns([1, 4, 3, 1])

    idx: int = st.session_state.get("cal_page_home", 0)

    with col_prev:
        if st.button("◀ mês", key="cal_home_prev") and idx > 0:
            idx -= 1
    with col_next:
        if st.button("mês ▶", key="cal_home_next") and idx < len(meses) - 1:
            idx += 1

    st.session_state["cal_page_home"] = idx
    ano, mes = meses[idx]
    nome_mes: str = calendar.month_name[mes].capitalize()

    # Título do mês
    col_label.markdown(
        f"<h5 style='text-align:center; margin-top:0.3rem;'>{nome_mes} / {ano}</h5>",
        unsafe_allow_html=True,
    )

    # 1. Descobre dias com alerta nesse mês
    dias_com_alerta: set[int] = set()
    for d in documentos_prox:
        validade_str: Optional[str] = d.get("validade")
        if not validade_str:
            continue
        try:
            dt_validade: date = datetime.fromisoformat(validade_str).date()
        except (ValueError, TypeError):
            continue

        if dt_validade.year == ano and dt_validade.month == mes:
            dias_com_alerta.add(dt_validade.day)

    # 2. Monta matriz de células em HTML
    matriz: List[List[int]] = calendar.monthcalendar(ano, mes)
    linhas_html: str = ""
    for semana in matriz:
        tds: str = ""
        for dia in semana:
            if dia == 0:
                tds += '<td class="empty-cell"></td>'
            else:
                if dia in dias_com_alerta:
                    # Usa o ícone Base64 se carregado, senão usa o fallback ⚠
                    if ALERT_ICON_B64:
                        cell_content = f"""
                        <div class="calendar-marker-cell">
                            <img src="data:image/png;base64,{ALERT_ICON_B64}" class="alert-icon" />
                            <span>{dia}</span>
                        </div>
                        """
                    else:
                        cell_content = f"""
                        <div class="calendar-marker-cell">
                            <span class="alert-fallback">⚠</span>
                            <span>{dia}</span>
                        </div>
                        """
                else:
                    cell_content = f"<span class='day-number'>{dia}</span>"

                tds += f"<td>{cell_content}</td>"
        linhas_html += f"<tr>{tds}</tr>"

    nomes_colunas: List[str] = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    thead: str = "".join(f"<th>{c}</th>" for c in nomes_colunas)

    tabela_html: str = f"""
    <table class="calendar-table">
        <thead>
            <tr>{thead}</tr>
        </thead>
        <tbody>
            {linhas_html}
        </tbody>
    </table>
    """

    st.markdown(tabela_html, unsafe_allow_html=True)
    st.caption(
        "Dias marcados com o ícone indicam documentos próximos do vencimento ou já vencidos no período selecionado."
    )

# ==================================
# 4. EXECUTA BUSCA (se clicar)
# ==================================
if botao_buscar:
    buscar_alertas()

# ==================================
# 5. LAYOUT PRINCIPAL (TABELAS E CALENDÁRIO)
# ==================================
col_esq, col_dir = st.columns([1, 2])

# -------- COLUNA ESQUERDA (Tabelas) --------
with col_esq:
    docs_rel: List[Dict[str, Any]] = st.session_state["docs_relacionados"]
    docs_prox: List[Dict[str, Any]] = st.session_state["docs_proximos"]

    df_rel: pd.DataFrame = pd.DataFrame(docs_rel)
    df_prox: pd.DataFrame = pd.DataFrame(docs_prox)

    colunas_rel: List[str] = [
        c for c in ["titulo", "responsavel", "validade", "status"]
        if c in df_rel.columns
    ]
    colunas_prox: List[str] = [
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
    docs_rel: List[Dict[str, Any]] = st.session_state["docs_relacionados"]
    docs_prox: List[Dict[str, Any]] = st.session_state["docs_proximos"]

    # Sufixo do nome do arquivo conforme filtro
    filtro_slug: str = {
        "Todos": "todos",
        "Somente próximos ao vencimento": "a_vencer",
        "Somente vencidos": "vencidos",
    }.get(extra_opcao, "todos")

    with relatorio_placeholder.container():
        if not docs_rel and not docs_prox:
            st.warning("Não há documentos para gerar relatório.")
        else:
            # Junta relacionados (já filtrados) + próximos (sempre todos do período)
            todos: List[Dict[str, Any]] = (docs_rel or []) + (docs_prox or [])

            # Remove duplicados por 'id', se existir (para evitar documentos em ambas as listas)
            if todos and isinstance(todos[0], dict) and "id" in todos[0]:
                dedup: Dict[Optional[int], Dict[str, Any]] = {}
                for d in todos:
                    did: Optional[int] = d.get("id")
                    if did is not None and did not in dedup:
                        dedup[did] = d
                todos_final: List[Dict[str, Any]] = list(dedup.values())
            else:
                todos_final = todos

            # Ordena pelo mesmo critério de prioridade da tela
            prioridade_status: Dict[str, int] = {"VENCIDO": 1, "A_VENCER": 2}

            def sort_key(doc: Dict[str, Any]) -> Tuple[int, str]:
                status: Optional[str] = doc.get("status")
                validade: str = doc.get("validade") or "9999-12-31"
                return (prioridade_status.get(status, 99), validade)

            todos_ordenados: List[Dict[str, Any]] = sorted(todos_final, key=sort_key)

            df_full: pd.DataFrame = pd.DataFrame(todos_ordenados)

            # Cria o buffer de memória para o Excel
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_full.to_excel(writer, index=False, sheet_name="Alertas")
            buffer.seek(0)

            st.success("Relatório gerado com sucesso! Clique no botão abaixo para baixar o arquivo.")
            st.download_button(
                label="⬇️ Baixar relatório em Excel (.xlsx)",
                data=buffer,
                file_name=(
                    f"relatorio_alertas_{filtro_slug}_"
                    f"{data_inicio.strftime('%Y%m%d')}_a_{data_fim.strftime('%Y%m%d')}.xlsx"
                ),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )