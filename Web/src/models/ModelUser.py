from .entities.User import User

class ModelUser:
    
    def login(self, db, user):
        """Inicia sesión de un usuario."""
        try:
            cursor = db.cursor()
            #user.password = User.generate_password_hash(user.password)
            sql = "SELECT * FROM users WHERE username = %s"
            cursor.execute(sql, (user.username,))
            row = cursor.fetchone()
            if row != None:
                if User.check_password(row[2], user.password):
                    return User(row[0], row[1], row[2])
                else:
                    return User(row[0], row[1], None)
            else:
                print("Login failed: Invalid username or password")
                return None
        except Exception as e:
            raise Exception(f"Error fetching user: {e}") 
        
    @classmethod    
    def get_by_id(self, db, id):
        """Obtiene un usuario por su ID."""
        try:
            cursor = db.cursor()
            sql = "SELECT id, username FROM users WHERE id = %s"
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            if row != None:
                return User(row[0], row[1], None)
            else:
                print("User not found")
                return None
        except Exception as e:
            raise Exception(f"Error fetching user by ID: {e}")