from flask import Blueprint, jsonify, request
from models.models import db, Documento

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
