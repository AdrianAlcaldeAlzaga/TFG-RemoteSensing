"""
Extensiones de Flask inicializadas aquí para evitar importaciones circulares.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Inicializar extensiones (sin app todavía)
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()