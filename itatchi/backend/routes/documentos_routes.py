# itatchi/backend/routes/documentos_routes.py

from flask import Blueprint, jsonify, request
from datetime import datetime, date

from itatchi.backend.database.connection import db
from itatchi.backend.models.models import Documento, Filial, TipoDocumento
from ..logic.status_calculator import calcular_status

documento_bp = Blueprint('documento_bp', __name__)


# -----------------------------
# GET /documentos  (lista simples)
# -----------------------------
@documento_bp.route('/documentos', methods=['GET'])
def listar_documentos():
    # 1. Inicializa a consulta base (sem filtro de status por enquanto)
    query = Documento.query

    # Parâmetros da URL
    status_filtro = request.args.get('status')
    titulo_filtro = request.args.get('titulo')

    # Filtro por título na query SQL
    if titulo_filtro:
        query = query.filter(Documento.titulo.ilike(f'%{titulo_filtro}%'))

    documentos = query.all()

    # 2. Recalcula status de todos os documentos retornados
    houve_mudanca = False
    hoje = date.today()

    for d in documentos:
        nova_situacao = calcular_status(d.validade)
        if nova_situacao != d.status_calc:
            d.status_calc = nova_situacao
            houve_mudanca = True

    if houve_mudanca:
        db.session.commit()

    # 3. Se veio filtro de status, aplica agora em memória
    if status_filtro:
        documentos = [d for d in documentos if d.status_calc == status_filtro]

    # 4. Monta a resposta
    lista = []
    for d in documentos:
        filial = Filial.query.get(d.filial_id)
        tipo = TipoDocumento.query.get(d.tipo_id)

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
# POST /documentos  (cadastro)
# -----------------------------
@documento_bp.route('/documentos', methods=['POST'])
def cadastrar_documento():
    dados = request.get_json() or {}

    # 1. Validação mínima de campos obrigatórios
    # Requerimentos: titulo, responsavel, filial_id, tipo_id
    if not all(k in dados for k in ['titulo', 'responsavel', 'filial_id', 'tipo_id']):
         return jsonify({"erro": "Campos obrigatórios (titulo, responsavel, filial_id, tipo_id) ausentes."}), 400

    # Conversão de datas
    data_validade = None
    data_emissao = None

    try:
        if dados.get('validade'):
            data_validade = datetime.strptime(dados['validade'], '%Y-%m-%d').date()
        
        if dados.get('emissao'):
            data_emissao = datetime.strptime(dados['emissao'], '%Y-%m-%d').date()

    except ValueError:
        return jsonify({"erro": "Formato de data inválido. Use YYYY-MM-DD."}), 400

    # 2. Executa a lógica de cálculo de status
    status_calculado = calcular_status(data_validade)
    
    # 3. Cria o novo objeto Documento
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
        # Define o status calculado 
        status_calc=status_calculado 
    )

    try:
        # 4. Salva no banco de dados
        db.session.add(novo_documento)
        db.session.commit()
        
        return jsonify({
            "mensagem": "Documento cadastrado com sucesso.",
            "status": novo_documento.status_calc,
            "id": novo_documento.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro interno ao salvar documento. {str(e)}"}), 500


# -----------------------------
# GET /home  (para Home)
# -----------------------------
@documento_bp.route("/home", methods=["GET"])
def listar_alertas():
    """
    Retorna:
      - documentos_relacionados: todos os documentos dentro do período/categoria
      - proximos_vencimento: subset com status A_VENCER ou VENCIDO
    """

    categoria = request.args.get("categoria")  # Regulatórios, Qualidade, ...
    inicio_str = request.args.get("inicio")
    fim_str = request.args.get("fim")

    query = Documento.query.join(TipoDocumento, Documento.tipo_id == TipoDocumento.id)

    # Filtro por categoria (opcional)
    if categoria and categoria.lower() != "todas":
        query = query.filter(TipoDocumento.categoria == categoria)

    # Filtro por período de validade (opcional)
    try:
        if inicio_str:
            data_inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
            query = query.filter(Documento.validade >= data_inicio)
        if fim_str:
            data_fim = datetime.strptime(fim_str, "%Y-%m-%d").date()
            query = query.filter(Documento.validade <= data_fim)
    except ValueError:
        return jsonify({"erro": "Parâmetros de data inválidos. Use YYYY-MM-DD."}), 400

    documentos = query.all()

    # 1. Recalcula status de todos do período
    houve_mudanca = False
    for d in documentos:
        nova_situacao = calcular_status(d.validade)
        if nova_situacao != d.status_calc:
            d.status_calc = nova_situacao
            houve_mudanca = True

    if houve_mudanca:
        db.session.commit()

    # 2. Monta resposta já com status atualizados
    documentos_relacionados = []
    proximos_vencimento = []

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

        if d.status_calc in ("A_VENCER", "VENCIDO"):
            proximos_vencimento.append(item)

    return jsonify(
        {
            "documentos_relacionados": documentos_relacionados,
            "proximos_vencimento": proximos_vencimento,
        }
    )