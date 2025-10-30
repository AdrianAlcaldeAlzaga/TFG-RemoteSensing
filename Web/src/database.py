import psycopg2
from psycopg2 import pool
from flask import current_app, g

class Database:
    """Clase para manejar el pool de conexiones a PostgreSQL."""
    
    _connection_pool = None
    
    @classmethod
    def initialize(cls, app):
        """Inicializa el pool de conexiones."""
        try:
            cls._connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=app.config['DB_HOST'],
                database=app.config['DB_DATABASE'],
                user=app.config['DB_USER'],
                password=app.config['DB_PASSWORD'],
                port=app.config.get('DB_PORT', 5432)
            )
            print("Pool de conexiones creado correctamente.")
        except psycopg2.Error as e:
            print(f"Error al crear pool de conexiones: {e}")
    
    @classmethod
    def get_connection(cls):
        """Obtiene una conexión del pool."""
        if cls._connection_pool:
            return cls._connection_pool.getconn()
        return None
    
    @classmethod
    def return_connection(cls, conn):
        """Devuelve una conexión al pool."""
        if cls._connection_pool and conn:
            cls._connection_pool.putconn(conn)
    
    @classmethod
    def close_all_connections(cls):
        """Cierra todas las conexiones del pool."""
        if cls._connection_pool:
            cls._connection_pool.closeall()
            print("Pool de conexiones cerrado.")

def get_db():
    """Obtiene una conexión de la base de datos para el contexto de la request."""
    if 'db' not in g:
        g.db = Database.get_connection()
    return g.db

def close_db(e=None):
    """Cierra la conexión de la base de datos al final de la request."""
    db = g.pop('db', None)
    if db is not None:
        Database.return_connection(db)