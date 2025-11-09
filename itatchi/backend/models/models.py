# itatchi/backend/models/models.py
# Definição dos modelos de dados (tabelas) usando SQLAlchemy ORM.

from itatchi.backend.database.connection import db
from sqlalchemy import Time, Text, Date, Boolean, String, Integer, ForeignKey


class Filial(db.Model):
    """Modelo para armazenar informações das Filiais."""
    __tablename__ = 'filial'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(10), unique=True, nullable=False)


class TipoDocumento(db.Model):
    """Modelo para armazenar os tipos de documentos e suas regras."""
    __tablename__ = 'tipodocumento'
    
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(50), nullable=False)  # Ex: Regulatórios, Veículos, Pessoas
    nome = db.Column(db.String(100), nullable=False)
    obrigatorio = db.Column(db.Boolean, default=False)
    prazo_padrao_dias = db.Column(db.Integer)  # Prazo de validade padrão em dias


class Documento(db.Model):
    """Modelo principal para o registro e acompanhamento de documentos."""
    __tablename__ = 'documento'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Chaves Estrangeiras
    filial_id = db.Column(db.Integer, db.ForeignKey('filial.id'), nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipodocumento.id'), nullable=False)
    
    # Dados Principais
    titulo = db.Column(db.String(255), nullable=False)
    numero = db.Column(db.String(100))
    responsavel = db.Column(db.String(100), nullable=False)
    emissao = db.Column(db.Date)
    validade = db.Column(db.Date)
    sem_validade = db.Column(db.Boolean, default=False)
    orgao_emissor = db.Column(db.String(150))
    observacoes = db.Column(db.Text)
    
    # Informações de Versão/Caminho
    caminho_atual = db.Column(db.String(500))
    versao_atual = db.Column(db.String(20), default='1.0.0')
    
    # Status de Cálculo (VIGENTE, A_VENCER, VENCIDO, SEM_VALIDADE)
    status_calc = db.Column(db.String(20), default='VIGENTE')


class Parametro(db.Model):
    """Modelo para armazenar parâmetros globais do sistema (ex: dias de alerta)."""
    __tablename__ = 'parametro'
    
    id = db.Column(db.Integer, primary_key=True)
    # JSON: Armazena os dias de alerta em formato de lista (ex: "[15, 30, 60]")
    dias_alerta_json = db.Column(db.String(255), nullable=False) 
    hora_envio = db.Column(db.Time) # Exemplo: horário para envio de notificações/alertas