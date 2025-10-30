import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('conf/key.env')

class Config:
    """Configuración base."""
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'

class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    # Configuración de PostgreSQL
    DB_HOST = "localhost"
    DB_DATABASE = "tfg_remotesensing_aaa"
    DB_USER = "postgres"
    DB_PASSWORD = "tfgs2"
    DB_PORT = 5432  # Puerto por defecto de PostgreSQL

config = {
    'development': DevelopmentConfig
}