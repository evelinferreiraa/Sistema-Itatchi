# itatchi/backend/database/connection.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env (na raiz do projeto)
load_dotenv()

# Objeto global de banco (compartilhado pelos models)
db = SQLAlchemy()


def create_app():
    """Factory que cria e configura a aplicação Flask."""
    app = Flask(__name__)
    CORS(app)

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializa o SQLAlchemy com essa app
    db.init_app(app)

    # Importa os models aqui dentro para evitar import circular
    from itatchi.backend.models.models import Documento  # noqa: F401

    # Se quiser garantir criação de tabelas (somente em dev / teste):
    # with app.app_context():
    #     db.create_all()

    return app
