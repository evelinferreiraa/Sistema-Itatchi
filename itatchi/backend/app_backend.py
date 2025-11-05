from itatchi.backend.database.connection import create_app, db
from itatchi.backend.routes.documentos_routes import documento_bp
from sqlalchemy import text   # <-- ADICIONE ISSO

app = create_app()
app.register_blueprint(documento_bp)

@app.route("/")
def index():
    return "API Itatchi está no ar. Use /documentos para listar documentos."

@app.route("/test_db")
def test_db():
    try:
        # SQLAlchemy 2.x exige o uso de text()
        db.session.execute(text("SELECT 1"))
        return "✅ Conexão com o banco MySQL OK!"
    except Exception as e:
        return f"❌ Erro ao conectar: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)