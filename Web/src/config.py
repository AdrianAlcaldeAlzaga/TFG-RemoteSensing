import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('conf/key.env')

class Config:
    """Configuración base."""
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuración de PostgreSQL
    DB_HOST = "localhost"
    DB_DATABASE = "tfg_remotesensing_aaa"
    DB_USER = "postgres"
    DB_PASSWORD = "tfgs2"
    DB_PORT = 5432
    
    # Configuración de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # True para ver las queries SQL en consola
    
    # Pool de conexiones
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,           # Número de conexiones permanentes
        'pool_recycle': 3600,      # Reciclar conexiones cada hora
        'pool_pre_ping': True,     # Verificar conexión antes de usar
        'max_overflow': 20         # Conexiones adicionales si se necesitan
    }

class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Mostrar queries SQL en desarrollo

config = {
    'development': DevelopmentConfig
}