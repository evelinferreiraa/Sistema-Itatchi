from flask import Blueprint, jsonify, request
from models.models import db, Documento
from datetime import datetime
from logic.status_calculator import calcular_status

documento_bp = Blueprint('documento_bp', __name__)

@documento_bp.route('/documentos', methods=['GET'])
def listar_documentos():
    documentos = Documento.query.all()
    lista = [{
        "id": d.id,
        "titulo": d.titulo,
        "responsavel": d.responsavel,
        "validade": str(d.validade),
        "status": d.status_calc
    } for d in documentos]
    return jsonify(lista)

# POST /documentos para cadastro
@documento_bp.route('/documentos', methods=['POST'])
def cadastrar_documento():
    dados = request.get_json()

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