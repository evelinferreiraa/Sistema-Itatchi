from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuração da conexão (pra testar tem que mudar a senha)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%40SQL6352@localhost/itatchi'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
