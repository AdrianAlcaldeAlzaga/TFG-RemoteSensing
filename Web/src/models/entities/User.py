from werkzeug.security import check_password_hash
from flask_login import UserMixin

class User(UserMixin):
    """Modelo de usuario para autenticación."""
    def __init__(self, id, username, password) -> None:
        """Inicializa un usuario."""
        self.id = id
        self.username = username
        self.password = password

    @classmethod
    def check_password(self, password_hash, password):
        """Verifica la contraseña del usuario."""
        return check_password_hash(password_hash, password)
    
    @classmethod
    def generate_password_hash(self, password):
        """Genera un hash para la contraseña dada."""
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password)
        