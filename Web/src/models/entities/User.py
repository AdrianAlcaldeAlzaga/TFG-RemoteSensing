from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    """
    Modelo de Usuario usando SQLAlchemy.
    Hereda de UserMixin para integración con Flask-Login.
    """
    __tablename__ = 'users'
    
    # Definir columnas de la tabla
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    def __init__(self, id, username, password_hash):
        """
        Constructor del modelo User.
        
        Args:
            id: ID del usuario
            username: Nombre de usuario
            password: Contraseña (puede ser hash o plain text)
            fullname: Nombre completo (opcional)
        """
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @classmethod
    def check_password(cls, hashed_password, password):
        """
        Verifica si una contraseña coincide con su hash.
        
        Args:
            hashed_password: Hash almacenado en BD
            password: Contraseña en texto plano a verificar
        
        Returns:
            bool: True si coincide, False si no
        """
        return check_password_hash(hashed_password, password)
    
    @staticmethod
    def generate_password_hash(password):
        """
        Genera un hash de contraseña.
        
        Args:
            password: Contraseña en texto plano
        
        Returns:
            str: Hash de la contraseña
        """
        return generate_password_hash(password)
    
    def __repr__(self):
        """Representación del objeto User."""
        return f"<User id={self.id} username='{self.username}'>"
