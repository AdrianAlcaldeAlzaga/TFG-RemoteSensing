from sqlalchemy import select
from .entities.User import User
from sqlalchemy.orm import Session

class ModelUser:
    
    @classmethod
    def login(cls, db_session, user):
        """
        Inicia sesión de un usuario usando SQLAlchemy.
        
        Args:
            db_session: Sesión de SQLAlchemy (db.session)
            user: Objeto User con username y password
        
        Returns:
            User: Objeto User si el login es exitoso, None si falla
        """
        try:
            # Buscar usuario por username usando SQLAlchemy ORM
            stmt = select(User).filter_by(username=user.username)
            db_user = db_session.execute(stmt).scalar_one_or_none()  
            
            if db_user is not None:
                # Verificar contraseña
                if User.check_password(db_user.password_hash, user.password_hash):
                    # Devolver usuario con contraseña válida
                    return User(db_user.id, db_user.username, db_user.password_hash)
                else:
                    # Devolver usuario sin contraseña (indica contraseña incorrecta)
                    return User(db_user.id, db_user.username, None)
            else:
                print("Login failed: Invalid username")
                return None
                
        except Exception as e:
            print(f"❌ Error en login: {e}")
            raise Exception(f"Error fetching user: {e}") 
        
    @classmethod    
    def get_by_id(cls, db_session, id):
        """
        Obtiene un usuario por su ID usando SQLAlchemy.
        
        Args:
            db_session: Sesión de SQLAlchemy (db.session)
            id: ID del usuario
        
        Returns:
            User: Objeto User si se encuentra, None si no existe
        """
        try:
            # Buscar usuario por ID usando SQLAlchemy ORM
            stmt = select(User).filter_by(id=id)
            db_user = db_session.execute(stmt).scalar_one_or_none()
            
            if db_user is not None:
                # Devolver usuario sin contraseña (por seguridad)
                return User(db_user.id, db_user.username, None)
            else:
                print(f"⚠️ User with ID {id} not found")
                return None
                
        except Exception as e:
            print(f"❌ Error en get_by_id: {e}")
            raise Exception(f"Error fetching user by ID: {e}")