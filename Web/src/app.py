from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect
from config import config
from database import Database, get_db, close_db
import os
from dotenv import load_dotenv
import ee

# Models
from models.ModelUser import ModelUser

# Entities
from models.entities.User import User

app = Flask(__name__)

# Configurar CSRF para proteger formularios
csrf = CSRFProtect(app)

# Cargar configuración PRIMERO
app.config.from_object(config['development'])

# Inicializar pool de conexiones
Database.initialize(app)

# Registrar función para cerrar conexión al final de cada request
app.teardown_appcontext(close_db)

# Configurar Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

dotenv_path = 'conf/key.env'
load_dotenv(dotenv_path=dotenv_path)
credentials_path = os.getenv('PC_PATH_GEE_CREDENTIALS')

# --- INICIALIZAR EARTH ENGINE ---
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

@login_manager.user_loader
def load_user(id):
    """Carga el usuario dado su ID."""
    db = get_db()
    if db:
        return ModelUser.get_by_id(db, id)
    return None

# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/')
def index():
    """Página de inicio que redirige al login."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el login de usuarios."""
    if request.method == 'POST':
        user = User(0, username=request.form['username'], password=request.form['password'])
        logged_user = ModelUser().login(get_db(), user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                flash("Login successful", "success")
                return redirect(url_for('home'))
            else:
                flash("Incorrect password", "danger")
        else:
            flash("Invalid username", "danger")
        # Aquí iría la lógica de autenticación
        return render_template('auth/login.html', message="Login successful")
    else:
        return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario."""
    logout_user()
    return redirect(url_for('login'))

def status_401(error):
    """Maneja el error 401 - No autorizado."""
    return redirect(url_for('login'))
    
def status_404(error):
    """Maneja el error 404 - No encontrado."""
    return "<h1>404 - Not Found</h1>", 404

@app.route('/home')
def home():
    """Página de inicio al logearse."""
    return render_template('home.html')
    
def extract_embedding(lat, lon, year):
    """Función para extraer un embedding basado en latitud y longitud."""
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
    except Exception as e:
        print(f"Error en search_point_bbdd: {type(e).__name__}: {e}")
        return None

def save_point_bbdd(cursor, lat, lon, year, embeddings_data):
    """Guarda un nuevo punto con embeddings en la base de datos."""
    try:
        # Obtener los embeddings
        embeddings = embeddings_data['embeddings']

        # Crear las columnas A00 a A63
        columnas_embeddings = [f"A{i:02d}" for i in range(0, 64)]

        # Crear la lista de valores para los embeddings
        valores_embeddings = []
        for col in columnas_embeddings:
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
        
        print(f"Insertando punto con {len(valores_embeddings)} valores de embeddings para año {year}")
        print(f"Primeros 5 embeddings: {valores_embeddings[:5]}")
        
        cursor.execute(query, valores)
        nuevo_id = cursor.fetchone()[0]
        
        print(f"Punto guardado en BBDD con ID: {nuevo_id}")
        return nuevo_id
    except Exception as e:
        print(f"Error al guardar punto en BBDD: {e}")
        return None

# --- 4. RUTA PARA OBTENER EMBEDDINGS ---
@app.route('/api/alphaearth/points', methods=['GET'])
def get_points_embedding():
    """
    Obtiene embeddings de un punto geográfico.
    Si existe en BBDD lo devuelve, sino lo extrae de Earth Engine y lo guarda.
    """
    db = get_db()
    if db is None:
        return jsonify({"error": "No se pudo conectar a la base de datos."}), 500

    try:
        cursor = db.cursor()
        
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
            db.rollback()
            
            embeddings_data = extract_embedding(lat, lon, year)
            if embeddings_data['status'] == 'success':
                nuevo_id = save_point_bbdd(cursor, lat, lon, year, embeddings_data)
                if nuevo_id:
                    db.commit()
                    
                    # Crear el punto_existente con los datos recién guardados
                    punto_existente = {
                        "id_coordenadaAEF": nuevo_id,
                        "latitud": lat,
                        "longitud": lon,
                        "anio": year,
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
                    db.rollback()
                    return jsonify({"error": "No se pudo guardar el nuevo punto"}), 500
            else:
                return jsonify({"error": "No se pudieron extraer embeddings", "detalles": embeddings_data}), 500

    except Exception as e:
        print(f"Error general: {e}")
        db.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()

# --- 5. INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    try:
        csrf.init_app(app)
        app.register_error_handler(401, status_401)
        app.register_error_handler(404, status_404)
        app.run()
    finally:
        # Cerrar pool de conexiones al terminar
        Database.close_all_connections()