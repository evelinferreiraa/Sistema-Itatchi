from database.connection import app, db
from routes.documentos_routes import documento_bp

# Registrar rotas
app.register_blueprint(documento_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
