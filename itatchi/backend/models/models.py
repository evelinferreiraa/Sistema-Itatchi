from itatchi.backend.database.connection import db
from sqlalchemy import Time

class Filial(db.Model):
    __tablename__ = 'filial'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(10), unique=True, nullable=False)

class TipoDocumento(db.Model):
    __tablename__ = 'tipodocumento'
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    obrigatorio = db.Column(db.Boolean, default=False)
    prazo_padrao_dias = db.Column(db.Integer)

class Documento(db.Model):
    __tablename__ = 'documento'
    id = db.Column(db.Integer, primary_key=True)
    filial_id = db.Column(db.Integer, db.ForeignKey('filial.id'), nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipodocumento.id'), nullable=False)
    titulo = db.Column(db.String(255), nullable=False)
    numero = db.Column(db.String(100))
    responsavel = db.Column(db.String(100), nullable=False)
    emissao = db.Column(db.Date)
    validade = db.Column(db.Date)
    sem_validade = db.Column(db.Boolean, default=False)
    orgao_emissor = db.Column(db.String(150))
    observacoes = db.Column(db.Text)
    caminho_atual = db.Column(db.String(500))
    versao_atual = db.Column(db.String(20), default='1.0.0')
    status_calc = db.Column(db.String(20), default='VIGENTE')

class Parametro(db.Model):
    __tablename__ = 'parametro'
    id = db.Column(db.Integer, primary_key=True)
    dias_alerta_json = db.Column(db.String(255), nullable=False) 
    hora_envio = db.Column(db.Time)