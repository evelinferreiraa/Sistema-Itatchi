from flask import Blueprint, jsonify, request
from models.models import db, Documento, Filial, TipoDocumento 
from datetime import datetime
from logic.status_calculator import calcular_status

documento_bp = Blueprint('documento_bp', __name__)

@documento_bp.route('/documentos', methods=['GET'])
def listar_documentos():
    # 1. Inicializa a consulta base
    query = Documento.query
    
    # 2. Obtém parâmetros de filtro da URL
    status_filtro = request.args.get('status')
    titulo_filtro = request.args.get('titulo')
    
    # 3. Aplica o filtro de STATUS
    # Apenas se o parâmetro 'status' for fornecido na URL 
    if status_filtro:
        query = query.filter(Documento.status_calc == status_filtro)
    
    # 4. Aplica o filtro de TÍTULO
    # Apenas se o parametro 'titulo' for fornecido na URL
    if titulo_filtro:
        query = query.filter(Documento.titulo.ilike(f'%{titulo_filtro}%')) 

    # 5. Executa a consulta com todos os filtros aplicados
    documentos = query.all()
    
    lista = []
    for d in documentos:
        # 6. Busca os nomes completos da Filial e Tipo para o Frontend
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