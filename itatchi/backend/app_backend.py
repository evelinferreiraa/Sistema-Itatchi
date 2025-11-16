# itatchi/backend/app_backend.py
# Ponto de entrada do servidor Flask. Configura o aplicativo e as rotas base.

# from itatchi.backend.database.connection import create_app, db -- removido para rodar no docker
# from itatchi.backend.routes.documentos_routes import documento_bp
from routes.documentos_routes import documento_bp
from database.connection import create_app, db

from sqlalchemy import text # Necessário para executar comandos SQL brutos no SQLAlchemy 2.x

# Cria a aplicação Flask usando o padrão factory
app = create_app()

# Registra o Blueprint que contém as rotas de documentos (CRUD e alertas)
app.register_blueprint(documento_bp)

@app.route("/")
def index() -> str:
    """Retorna uma mensagem de status simples para verificar se a API está no ar."""
    return "API Itatchi está no ar. Use /documentos para listar documentos."

@app.route("/test_db")
def test_db() -> str:
    """Tenta executar uma query simples no banco para testar a conexão."""
    try:
        # SQLAlchemy 2.x exige o uso de text() para comandos brutos
        db.session.execute(text("SELECT 1"))
        return "✅ Conexão com o banco MySQL OK!"
    except Exception as e:
        return f"❌ Erro ao conectar: {e}"

if __name__ == '__main__':
    # Inicia o servidor em modo de desenvolvimento (debug=True, porta 5000)
    app.run(host="0.0.0.0", port=5000, debug=True)
