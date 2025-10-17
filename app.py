from flask import Flask, json, jsonify, request
import psycopg2 
import os
from dotenv import load_dotenv
import ee

app = Flask(__name__)

dotenv_path = 'conf/key.env'
load_dotenv(dotenv_path=dotenv_path)
credentials_path = os.getenv('PC_PATH_GEE_CREDENTIALS')

# --- 1. INICIALIZAR EARTH ENGINE ---
try:
    # Verificar que el archivo de credenciales existe y es accesible
    if credentials_path and os.path.exists(credentials_path):
        service_account = 'tfg-remoterensing-aaa@proyecto-de-prueba-471508.iam.gserviceaccount.com'
        credentials = ee.ServiceAccountCredentials(service_account, credentials_path)
        ee.Initialize(credentials)
        print("Earth Engine inicializado correctamente.")
    else:
        print("Error: No se encontró el archivo de credenciales.")
        print("Intentando inicialización por defecto...")
        ee.Initialize()
        print("Earth Engine inicializado con credenciales por defecto.")
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
    
def extract_embedding(lat, lon, year):
    """Función de ejemplo para extraer un embedding basado en latitud y longitud."""
    try:
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
    
def search_point_bbdd(cursor, lat, lon, year, tolerancia=0.0001):
    try:
        """Busca si existe un punto similar en la base de datos y devuelve todos los campos."""
        # Crear las columnas A00 a A63
        columnas_embeddings = [f"A{i:02d}" for i in range(0, 64)]
        
        # Crear la query con todas las columnas
        columnas_str = ", ".join(["id_coordenadaAEF", "latitud", "longitud", "anio", "es_residuo", "tipo_residuo"] + columnas_embeddings)
        
        query = f"""
            SELECT {columnas_str}
            FROM AlphaEarth
            WHERE latitud BETWEEN %s AND %s
            AND longitud BETWEEN %s AND %s
            AND anio = %s
            AND A00 IS NOT NULL
            LIMIT 1;
        """
        
        print(f"Buscando punto con tolerancia: lat={lat}±{tolerancia}, lon={lon}±{tolerancia}, año={year}")
        cursor.execute(query, (lat - tolerancia, lat + tolerancia, lon - tolerancia, lon + tolerancia, year))
        
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"Punto encontrado en BBDD para año {year}")
            # Crear diccionario con todos los campos
            columnas_completas = ["id_coordenadaAEF", "latitud", "longitud", "anio", "es_residuo", "tipo_residuo"] + columnas_embeddings
            punto_dict = dict(zip(columnas_completas, resultado))
            
            # Crear sub-diccionario para embeddings
            embeddings_dict = {}
            for col in columnas_embeddings:
                if punto_dict[col] is not None:
                    embeddings_dict[col] = punto_dict[col]
            
            # Estructura final del registro
            punto_completo = {
                "id_coordenadaAEF": punto_dict["id_coordenadaAEF"],
                "latitud": punto_dict["latitud"],
                "longitud": punto_dict["longitud"],
                "anio": punto_dict["anio"],
                "es_residuo": punto_dict["es_residuo"],
                "tipo_residuo": punto_dict["tipo_residuo"],
                "embeddings": embeddings_dict
            }
            
            return punto_completo
        else:
            print(f"No se encontró punto en BBDD para año {year}")
            return None
            
    except psycopg2.Error as db_error:
        print(f"Error de PostgreSQL en search_point_bbdd: {db_error}")
        print(f"Código de error: {db_error.pgcode}")
        print(f"Detalles del error: {db_error.pgerror}")
        return None
    except Exception as e:
        print(f"Error general en search_point_bbdd: {type(e).__name__}: {e}")
        return None

def save_point_bbdd(cursor, lat, lon, year, embeddings_data):
    """Guarda un nuevo punto con embeddings en la base de datos."""
    try:
        # Obtener los embeddings
        embeddings = embeddings_data['embeddings']

        # Crear las columnas A00 a A63
        columnas_embeddings = [f"A{i:02d}" for i in range(0, 64)]  # A00, A01, ..., A63

        # Crear la lista de valores para los embeddings
        valores_embeddings = []
        for col in columnas_embeddings:
            # Si existe el embedding para esa columna, lo usa; sino pone None
            valor = embeddings.get(col, None)
            valores_embeddings.append(valor)
        
        # Crear la query dinámicamente
        columnas_str = ", ".join(["latitud", "longitud", "anio", "es_residuo", "tipo_residuo"] + columnas_embeddings)
        placeholders = ", ".join(["%s"] * (5 + len(columnas_embeddings)))

        query = f"""
            INSERT INTO AlphaEarth ({columnas_str})
            VALUES ({placeholders})
            RETURNING id_coordenadaAEF;
        """
        
        # Combinar todos los valores
        valores = [lat, lon, year, False, 'unknown'] + valores_embeddings
        
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

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "No se pudo conectar a la base de datos."}), 500

    try:
        cursor = conn.cursor()
        
        # Obtener parámetros de la URL
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        user = request.args.get('user', default='anonymous', type=str)
        year = request.args.get('year', default=2024, type=int)
        
        # Validar parámetros requeridos
        if lat is None or lon is None:
            return jsonify({"error": "Se requieren parámetros 'lat' y 'lon'"}), 400
        
        print(f"Buscando punto lat={lat}, lon={lon}, año={year} en BBDD...")
        punto_existente = search_point_bbdd(cursor, lat, lon, year)

        if punto_existente:
            print("Punto encontrado en BBDD, devolviendo datos existentes.")
            return jsonify({
                "user": user,
                "data": punto_existente, 
                "total_registros_devueltos": 1,
                "origen": "base_de_datos"
            })
        else:
            print("Punto no encontrado en BBDD, extrayendo embeddings y guardando nuevo punto.")
            
            # Limpiar cualquier transacción abortada
            conn.rollback()
            
            embeddings_data = extract_embedding(lat, lon, year)
            if embeddings_data['status'] == 'success':
                nuevo_id = save_point_bbdd(cursor, lat, lon, year, embeddings_data)
                if nuevo_id:
                    conn.commit()  # Confirmar cambios
                    
                    # Crear el punto_existente con los datos recién guardados
                    punto_existente = {
                        "id_coordenadaAEF": nuevo_id,
                        "latitud": lat,
                        "longitud": lon,
                        "anio": year,  # AGREGAR año
                        "es_residuo": False,
                        "tipo_residuo": "unknown",
                        "embeddings": embeddings_data['embeddings']
                    }
                    
                    return jsonify({
                        "user": user,
                        "data": punto_existente, 
                        "total_registros_devueltos": 1,
                        "origen": "earth_engine"
                    })
                else:
                    conn.rollback()
                    return jsonify({"error": "No se pudo guardar el nuevo punto"}), 500
            else:
                return jsonify({"error": "No se pudieron extraer embeddings", "detalles": embeddings_data}), 500

    except psycopg2.Error as e:
        print(f"Error PostgreSQL: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error_query": str(e)}), 500
    
    except Exception as e:
        print(f"Error general: {e}")
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        if conn:
            conn.close()

# --- 4. INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)