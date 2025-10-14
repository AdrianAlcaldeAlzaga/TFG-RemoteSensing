from flask import Flask, jsonify
import psycopg2 

app = Flask(__name__)

# --- 1. DATOS DE CONEXIÓN A POSTGRESQL ---
DB_CONFIG = {
    "host": "localhost",
    "database": "tfg_remotesensing_aaa",
    "user": "postgres",
    "password": "tfgs2"
}

# --- 2. FUNCIÓN DE CONEXIÓN REUTILIZABLE ---
def get_db_connection():
    """Establece y devuelve una conexión a la base de datos."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        # En caso correcto, mostramos un mensaje en consola
        print("Conexión a la base de datos establecida.")
        return conn
    except psycopg2.Error as e:
        # En caso de error, es mejor registrarlo y devolver None
        print(f"Error al conectar con la base de datos: {e}")
        return None

# --- 3. RUTA DE PRUEBA: OBTENER TODOS LOS DATOS ---
@app.route('/api/alphaearth/puntos', methods=['GET'])
def obtener_puntos_de_entrenamiento():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "No se pudo conectar a la base de datos."}), 500

    try:
        cursor = conn.cursor()
        
        # Selecciona todos los puntos. NOTA: ¡Esta consulta puede ser lenta en producción!
        cursor.execute("SELECT id_coordenadaAEF, latitud, longitud, es_vertedero, tipo_residuo FROM AlphaEarth LIMIT 10;")
        
        # Obtiene todos los resultados
        resultados = cursor.fetchall()
        
        # Obtiene los nombres de las columnas para crear un diccionario (mejor formato JSON)
        columnas = [desc[0] for desc in cursor.description]
        
        # Convierte la lista de tuplas a una lista de diccionarios
        puntos = [dict(zip(columnas, fila)) for fila in resultados]

        return jsonify({"data": puntos, "total_registros_devueltos": len(puntos)})

    except psycopg2.Error as e:
        return jsonify({"error_query": str(e)}), 500
    
    finally:
        # CIERRA la conexión siempre, incluso si hay un error
        if conn:
            conn.close()

# --- 4. INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    # 'host=0.0.0.0' permite acceder desde tu máquina host si usas una VM
    app.run(host='0.0.0.0', port=5000)