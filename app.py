import os
from flask import Flask
from models import db
from config import Config
from routes import init_routes

# --- INICIALIZACIÓN DE LA APLICACIÓN ---

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Inicializa la base de datos con la aplicación Flask
    db.init_app(app)
    # Inicializa las rutas
    init_routes(app)
    return app

app = create_app()

# Crear todas las tablas dentro del contexto de la aplicación
with app.app_context():
    # Solo crea las tablas si la DB es SQLite y el archivo no existe
    if Config.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///') and not os.path.exists('database.db'):
        db.create_all()
    # Para otros casos (como MySQL en producción), solo crea las tablas
    elif not Config.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///'):
        db.create_all()

if __name__ == '__main__':
    # Ejecutar la aplicación
    app.run(debug=True)