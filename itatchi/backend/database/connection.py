# itatchi/backend/database/connection.py
# Configuração da conexão com o banco de dados e inicialização da aplicação Flask.

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env (na raiz do projeto)
load_dotenv()

# Objeto global de banco de dados (compartilhado pelos models)
db = SQLAlchemy()


def create_app():
    """
    Factory que cria e configura a aplicação Flask.
    
    Configura o CORS e a URI de conexão com o banco de dados
    a partir das variáveis de ambiente (.env).
    """
    app = Flask(__name__)
    CORS(app)

    # 1. Obter variáveis de conexão do ambiente (.env local ou variáveis do Docker)
    db_user = os.getenv("DB_USER", "itatchi_user")
    db_password = os.getenv("DB_PASSWORD", "itatchi_pass")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "itatchi_db")

    # 2. Montar a URL de conexão para MySQL + PyMySQL
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    # Recomendado: desabilitar rastreamento de modificações para melhor performance
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 3. Inicializa o SQLAlchemy com essa app
    db.init_app(app)

    # 4. Importa os models (necessário para o SQLAlchemy registrar as tabelas)
    try:
        # se estiver usando como pacote 'itatchi'
        from itatchi.backend.models.models import Documento  # noqa: F401
    except ModuleNotFoundError:
        # fallback para execução direta dentro do container (sem pacote itatchi)
        from models.models import Documento  # noqa: F401

    return app