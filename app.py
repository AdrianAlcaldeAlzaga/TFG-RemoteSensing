from flask import Flask, json, jsonify, request
import psycopg2 
import ee

app = Flask(__name__)

# --- 1. INICIALIZAR EARTH ENGINE ---
try:
    ee.Initialize()
    print("Earth Engine inicializado correctamente.")
except Exception as e:
    print(f"Error al inicializar Earth Engine: {e}")

# --- 2. DATOS DE CONEXIÓN A POSTGRESQL ---
DB_CONFIG = {
    "host": "localhost",
    "database": "tfg_remotesensing_aaa",
    "user": "postgres",
    "password": "tfgs2"
}

# --- 3. FUNCIÓN DE CONEXIÓN REUTILIZABLE ---
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
    
def extract_embedding(lat, lon):
    """Función de ejemplo para extraer un embedding basado en latitud y longitud."""
    try:
        year = 2024 # Año fijo para este ejemplo
        # Crear punto
        punto = ee.Geometry.Point([lon, lat])
        
        # Cargar colección de embeddings
        embeddings = ee.ImageCollection('GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL')
        
        # Filtrar por año y crear mosaico
        mosaic = embeddings.filterDate(f'{year}-01-01', f'{year + 1}-01-01').mosaic()
        
        # Extraer muestra del punto
        sample = mosaic.sample(region=punto, scale=10, numPixels=1).first()
        
        # Obtener valores como diccionario
        valores = sample.toDictionary().getInfo()
        
        return {
            "status": "success",
            "embeddings": valores,
            "punto": {"lat": lat, "lon": lon}
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "punto": {"lat": lat, "lon": lon}
        }
    
def search_point_bbdd(cursor, lat, lon, tolerancia=0.0001):
    try:
        """Busca si existe un punto similar en la base de datos."""
        query = """
            SELECT id_coordenadaAEF, latitud, longitud, es_residuo, tipo_residuo
            FROM AlphaEarth
            WHERE latitud BETWEEN %s AND %s
            AND longitud BETWEEN %s AND %s
            LIMIT 1;
        """
        cursor.execute(query, (lat - tolerancia, lat + tolerancia, lon - tolerancia, lon + tolerancia))
        return cursor.fetchone()
    except psycopg2.Error as db_error:
        print(f"Error de PostgreSQL en search_point_bbdd: {db_error}")
        print(f"Código de error: {db_error.pgcode}")
        print(f"Detalles del error: {db_error.pgerror}")
        return None
    except Exception as e:
        print(f"Error general en search_point_bbdd: {type(e).__name__}: {e}")
        return None



def save_point_bbdd(cursor, lat, lon, embeddings_data):
    """Guarda un nuevo punto con embeddings en la base de datos."""
    try:
        # Obtener los embeddings
        embeddings = embeddings_data['embeddings']
        
        # Crear las columnas A01 a A63
        columnas_embeddings = [f"A{i:02d}" for i in range(1, 64)]  # A01, A02, ..., A63
        
        # Crear la lista de valores para los embeddings
        valores_embeddings = []
        for col in columnas_embeddings:
            # Si existe el embedding para esa columna, lo usa; sino pone None
            valor = embeddings.get(col, None)
            valores_embeddings.append(valor)
        
        # Crear la query dinámicamente
        columnas_str = ", ".join(["latitud", "longitud", "es_residuo", "tipo_residuo"] + columnas_embeddings)
        placeholders = ", ".join(["%s"] * (4 + len(columnas_embeddings)))
        
        query = f"""
            INSERT INTO AlphaEarth ({columnas_str})
            VALUES ({placeholders})
            RETURNING id_coordenadaAEF;
        """
        
        # Combinar todos los valores
        valores = [lat, lon, False, 'unknown'] + valores_embeddings
        
        print(f"Insertando punto con {len(valores_embeddings)} valores de embeddings")
        print(f"Primeros 5 embeddings: {valores_embeddings[:5]}")
        
        cursor.execute(query, valores)
        nuevo_id = cursor.fetchone()[0]
        
        print(f"Punto guardado en BBDD con ID: {nuevo_id}")
        return nuevo_id
        
    except psycopg2.Error as db_error:
        print(f"Error de PostgreSQL en save_point_bbdd: {db_error}")
        print(f"Código de error: {db_error.pgcode}")
        print(f"Detalles del error: {db_error.pgerror}")
        return None
    except Exception as e:
        print(f"Error al guardar punto en BBDD: {e}")
        return None

# --- 3. RUTA DE PRUEBA: OBTENER TODOS LOS DATOS ---
@app.route('/api/alphaearth/points', methods=['GET'])
def get_points_embedding():
    # Establecemos las credenciales con gee
    service_account = 'tfg-remoterensing-aaa@proyecto-de-prueba-471508.iam.gserviceaccount.com'
    credentials = ee.ServiceAccountCredentials(service_account,  srvconf['PYSRV_GEE_CONFIG_FILE'])
    ee.Initialize(credentials)

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "No se pudo conectar a la base de datos."}), 500

    try:
        cursor = conn.cursor()
        
        # Obtener parámetros de la URL (no JSON)
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        print(f"Buscando punto lat={lat}, lon={lon} en BBDD...")
        punto_existente = search_point_bbdd(cursor, lat, lon)

        if punto_existente:
            print("Punto encontrado en BBDD, devolviendo datos existentes.")
        else:
            print("Punto no encontrado en BBDD, extrayendo embeddings y guardando nuevo punto.")
            embeddings_data = extract_embedding(lat, lon)
            if embeddings_data['status'] == 'success':
                nuevo_id = save_point_bbdd(cursor, lat, lon, embeddings_data)
                if nuevo_id:
                    conn.commit()  # Confirmar cambios en la base de datos
                else:
                    return jsonify({"error_guardar": "No se pudo guardar el nuevo punto."}), 500
            else:
                return jsonify({"error_embeddings": embeddings_data['error']}), 500
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
    app.run(host='0.0.0.0', port=5000)