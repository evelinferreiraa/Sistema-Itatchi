# itatchi/backend/routes/documentos_routes.py
# Rotas da API REST para Documentos (Listar, Cadastrar, Listar Alertas/Home).

from flask import Blueprint, jsonify, request, Response
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from itatchi.backend.database.connection import db
from itatchi.backend.models.models import Documento, Filial, TipoDocumento
from ..logic.status_calculator import calcular_status

documento_bp = Blueprint('documento_bp', __name__)

# -----------------------------
# GET /documentos (lista simples)
# -----------------------------
@documento_bp.route('/documentos', methods=['GET'])
def listar_documentos() -> Response:
    """
    Lista todos os documentos, com filtros opcionais por status e título.
    
    Recalcula e atualiza o status de cada documento no banco antes de retornar.

    Query Params:
        - status (str, opcional): Filtra por status_calc ('A_VENCER', 'VENCIDO').
        - titulo (str, opcional): Filtra por parte do título (case-insensitive).
        
    Retorna:
        - JSON: Lista de documentos detalhados.
    """
    query = Documento.query

    status_filtro: Optional[str] = request.args.get('status')
    titulo_filtro: Optional[str] = request.args.get('titulo')

    # 1. Filtro por título (executado no banco de dados)
    if titulo_filtro:
        query = query.filter(Documento.titulo.ilike(f'%{titulo_filtro}%'))

    documentos: List[Documento] = query.all()

    # 2. Recalcula e atualiza o status de todos os documentos
    houve_mudanca = False
    for d in documentos:
        nova_situacao: str = calcular_status(d.validade)
        if nova_situacao != d.status_calc:
            d.status_calc = nova_situacao
            houve_mudanca = True

    if houve_mudanca:
        db.session.commit()

    # 3. Filtro por status (aplicado em memória após o recalculo)
    if status_filtro:
        documentos = [d for d in documentos if d.status_calc == status_filtro]

    # 4. Monta a resposta com dados detalhados (incluindo Filial e Tipo)
    lista: List[Dict[str, Any]] = []
    for d in documentos:
        filial: Optional[Filial] = Filial.query.get(d.filial_id)
        tipo: Optional[TipoDocumento] = TipoDocumento.query.get(d.tipo_id)

        lista.append({
            "id": d.id,
            "titulo": d.titulo,
            "responsavel": d.responsavel,
            "filial": filial.nome if filial else "",
            "tipo": tipo.nome if tipo else "",
            "validade": str(d.validade) if d.validade else "Sem Validade",
            "status": d.status_calc,
        })

    return jsonify(lista)


# -----------------------------
# POST /documentos (cadastro)
# -----------------------------
@documento_bp.route('/documentos', methods=['POST'])
def cadastrar_documento() -> Tuple[Response, int]:
    """
    Cadastra um novo documento no sistema.
    
    Body JSON (obrigatórios): titulo, responsavel, filial_id, tipo_id.
    
    Retorna:
        - JSON: Mensagem de sucesso e ID (201 Created).
        - JSON: Mensagem de erro (400 Bad Request ou 500 Internal Error).
    """
    dados: Dict[str, Any] = request.get_json() or {}

    # 1. Validação mínima de campos obrigatórios
    required_fields = ['titulo', 'responsavel', 'filial_id', 'tipo_id']
    if not all(k in dados for k in required_fields):
         return jsonify({"erro": "Campos obrigatórios (titulo, responsavel, filial_id, tipo_id) ausentes."}), 400

    # 2. Conversão e validação de datas
    data_validade: Optional[date] = None
    data_emissao: Optional[date] = None

    try:
        if dados.get('validade'):
            data_validade = datetime.strptime(dados['validade'], '%Y-%m-%d').date()
        
        if dados.get('emissao'):
            data_emissao = datetime.strptime(dados['emissao'], '%Y-%m-%d').date()

    except ValueError:
        return jsonify({"erro": "Formato de data inválido. Use YYYY-MM-DD."}), 400

    # 3. Executa a lógica de cálculo de status
    status_calculado: str = calcular_status(data_validade)
    
    # 4. Cria o novo objeto Documento
    novo_documento = Documento(
        filial_id=dados.get('filial_id'),
        tipo_id=dados.get('tipo_id'),
        titulo=dados.get('titulo'),
        numero=dados.get('numero'),
        responsavel=dados.get('responsavel'),
        emissao=data_emissao,
        validade=data_validade,
        sem_validade=dados.get('sem_validade', False),
        orgao_emissor=dados.get('orgao_emissor'),
        observacoes=dados.get('observacoes'),
        caminho_atual=dados.get('caminho_atual'),
        status_calc=status_calculado 
    )

    try:
        # 5. Salva no banco de dados
        db.session.add(novo_documento)
        db.session.commit()
        
        return jsonify({
            "mensagem": "Documento cadastrado com sucesso.",
            "status": novo_documento.status_calc,
            "id": novo_documento.id
        }), 201

    except Exception as e:
        # Em caso de erro, reverte a transação
        db.session.rollback()
        return jsonify({"erro": f"Erro interno ao salvar documento. {str(e)}"}), 500


# -----------------------------
# GET /home (para Home/Alertas)
# -----------------------------
@documento_bp.route("/home", methods=["GET"])
def listar_alertas() -> Tuple[Response, int]:
    """
    Lista documentos para a tela inicial (Central de Consultas), com filtros de período e categoria.
    
    Query Params:
        - categoria (str, opcional): Filtra pela categoria do TipoDocumento.
        - inicio (str, opcional): Data de validade mínima (YYYY-MM-DD).
        - fim (str, opcional): Data de validade máxima (YYYY-MM-DD).
        
    Retorna:
        - JSON:
            - documentos_relacionados: Todos os documentos encontrados no período/categoria.
            - proximos_vencimento: Subset que possui status 'A_VENCER' ou 'VENCIDO'.
    """
    categoria: Optional[str] = request.args.get("categoria")
    inicio_str: Optional[str] = request.args.get("inicio")
    fim_str: Optional[str] = request.args.get("fim")

    # 1. Monta a query, juntando com TipoDocumento para poder filtrar pela categoria
    query = Documento.query.join(TipoDocumento, Documento.tipo_id == TipoDocumento.id)

    # 2. Filtro por categoria (se diferente de "Todas")
    if categoria and categoria.lower() != "todas":
        query = query.filter(TipoDocumento.categoria == categoria)

    # 3. Filtro por período de validade
    try:
        if inicio_str:
            data_inicio: date = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            query = query.filter(Documento.validade >= data_inicio)
        if fim_str:
            data_fim: date = datetime.strptime(fim_str, "%Y-%m-%d").date()
            query = query.filter(Documento.validade <= data_fim)
    except ValueError:
        return jsonify({"erro": "Parâmetros de data inválidos. Use YYYY-MM-DD."}), 400

    documentos: List[Documento] = query.all()

    # 4. Recalcula e atualiza o status de todos os documentos do período
    houve_mudanca = False
    for d in documentos:
        nova_situacao: str = calcular_status(d.validade)
        if nova_situacao != d.status_calc:
            d.status_calc = nova_situacao
            houve_mudanca = True

    if houve_mudanca:
        db.session.commit()

    # 5. Monta o payload de retorno
    documentos_relacionados: List[Dict[str, Any]] = []
    proximos_vencimento: List[Dict[str, Any]] = []

    for d in documentos:
        item = {
            "id": d.id,
            "titulo": d.titulo,
            "tipo_id": d.tipo_id,
            "filial_id": d.filial_id,
            "validade": d.validade.isoformat() if d.validade else None,
            "status": d.status_calc,
            "responsavel": d.responsavel,
        }

        documentos_relacionados.append(item)

        # Separa o subset de alertas
        if d.status_calc in ("A_VENCER", "VENCIDO"):
            proximos_vencimento.append(item)

    return jsonify(
        {
            "documentos_relacionados": documentos_relacionados,
            "proximos_vencimento": proximos_vencimento,
        }
    )