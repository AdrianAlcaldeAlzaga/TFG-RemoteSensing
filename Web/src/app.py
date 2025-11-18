from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from config import config
from database import init_db, get_db, close_db, commit_db, rollback_db
from extensions import db, login_manager, csrf
import os
from dotenv import load_dotenv
import ee

# Models
from models.ModelUser import ModelUser
from models.AlphaEarth import AlphaEarth
from models.Sentinel2 import Sentinel2

# Entities
from models.entities.User import User

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ==========================================
# Cargar configuración desde config.py
app.config.from_object(config['development'])
init_db(app, db)

# Inicializar extensiones con la app
login_manager.init_app(app)
csrf.init_app(app)

# Configurar Flask-Login

login_manager.login_view = 'login'

dotenv_path = 'conf/key.env'
load_dotenv(dotenv_path=dotenv_path)
credentials_path = os.getenv('PC_PATH_GEE_CREDENTIALS')

# Cierre de sesión de base de datos al finalizar la solicitud
@app.teardown_appcontext
def teardown_db(exception):
    """Cierra la sesión de la base de datos al finalizar la solicitud."""
    close_db(db, exception)

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
    if db:
        return ModelUser.get_by_id(get_db(db), id)
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
        user = User(0, username=request.form['username'], password_hash=request.form['password'])
        logged_user = ModelUser().login(get_db(db), user)
        if logged_user != None:
            if logged_user.password_hash:
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

        valores = {key.lower(): value for key, value in valores.items()}
        
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
    
def extract_bands_sentinel2(lat, lon, year):
    """Función para extraer bandas Sentinel-2 usando reduceRegion del año especificado."""
    try:
        # Crear punto
        punto = ee.Geometry.Point([lon, lat])
        
        # Cargar colección Sentinel-2
        sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        
        # Filtrar por año completo y baja nubosidad
        fecha_inicio = f'{year}-01-01'
        fecha_fin = f'{year}-12-31'
        
        filtered = sentinel2.filterDate(fecha_inicio, fecha_fin) \
                            .filterBounds(punto) \
                            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5)) \
                            .sort('CLOUDY_PIXEL_PERCENTAGE')  # Ordenar por menos nubes primero
        
        # Verificar si hay imágenes disponibles
        count = filtered.size().getInfo()
        if count == 0:
            return {
                "status": "error",
                "error": f"No hay imágenes Sentinel-2 con menos de 5% de nubes para el año {year}",
                "punto": {"lat": lat, "lon": lon, "year": year}
            }
        
        # Tomar la primera imagen (la que tiene menos nubes)
        imagen = filtered.first()
        
        valores_bandas = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B11', 'B12']
        imagen = imagen.select(valores_bandas)

        # Usar reduceRegion para extraer los valores del punto
        valores = imagen.reduceRegion(
            reducer=ee.Reducer.first(),  # Toma el primer valor (ya que es un punto)
            geometry=punto,
            scale=10,  # Resolución de 10 metros
            maxPixels=1e9
        ).getInfo()
        
        valores = {key.lower(): value for key, value in valores.items()}
        
        # Obtener la fecha real de la imagen (la que se guardará en BD)
        timestamp = imagen.get('system:time_start').getInfo()
        fecha_imagen = ee.Date(timestamp).format('YYYY-MM-dd').getInfo()
        
        # Obtener metadatos adicionales
        nubosidad = imagen.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        
        print(f"Imagen S2 encontrada: fecha={fecha_imagen}, nubes={nubosidad}%")
        
        return {
            "status": "success",
            "bandas": valores,
            "fecha_imagen": fecha_imagen,  # ← Esta es la fecha que se guardará en BD
            "nubosidad": nubosidad
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "punto": {"lat": lat, "lon": lon, "year": year}
        }
    
def search_alphaearth_and_save(db, lat, lon, year, es_residuo, tipo_residuo):
    embeddings_data = extract_embedding(lat, lon, year)
    
    if embeddings_data['status'] == 'success':
        nuevo_id = save_point_bbdd_aef(db, year, es_residuo, tipo_residuo, embeddings_data)
        
        if nuevo_id:
            
            # Crear estructura de datos
            punto_existente_aef = {
                "id_coordenadaAEF": nuevo_id,
                "latitud": lat,
                "longitud": lon,
                "anio": year,
                "es_residuo": es_residuo,
                "tipo_residuo": tipo_residuo,
                "embeddings": embeddings_data['embeddings']
            }
        else:
            # ❌ ERROR: No se pudo guardar AlphaEarth en BD
            rollback_db(db)
            return jsonify({
                "status": "failed",
                "error": "No se pudo guardar el punto AlphaEarth en la base de datos"
            }), 500
    else:
        # ❌ ERROR: No se pudieron extraer embeddings
        return jsonify({
            "status": "failed",
            "error": "No se pudieron extraer embeddings de Earth Engine",
            "detalles": embeddings_data
        }), 500
    
    return punto_existente_aef

def search_sentinel2_and_save(db, lat, lon, year, es_residuo, tipo_residuo):
    bands_data = extract_bands_sentinel2(lat, lon, year)
    
    if bands_data['status'] == 'success':
        nuevo_id_s2 = save_point_sentinel2(db, lat, lon, es_residuo, tipo_residuo, bands_data)
        
        if nuevo_id_s2:
            print(f"Punto S2 guardado exitosamente con ID: {nuevo_id_s2}")
            
            # Crear estructura de datos
            punto_existente_s2 = {
                "id_coordenadaAEF": nuevo_id_s2,
                "latitud": lat,
                "longitud": lon,
                "fecha": bands_data['fecha_imagen'],
                "es_residuo": es_residuo,
                "tipo_residuo": tipo_residuo,
                "bandas": bands_data['bandas']
            }
        else:
            # ERROR: No se pudo guardar Sentinel-2 en BD
            rollback_db(db)
            return jsonify({
                "status": "failed",
                "error": "No se pudo guardar el punto Sentinel-2 en la base de datos"
            }), 500
    else:
        # ERROR: No se pudieron extraer bandas
        return jsonify({
            "status": "failed",
            "error": "No se pudieron extraer bandas de Sentinel-2 de Earth Engine",
            "detalles": bands_data
        }), 500
    
    return punto_existente_s2

def search_point_bbdd_aef(lat, lon, year, es_residuo, tipo_residuo, tolerancia=0.000001):
    try:
        # Crear las columnas A00 a A63
        columnas_embeddings = [f"a{i:02d}" for i in range(0, 64)]

        # ✅ Crear lista de condiciones para verificar que NO sean NULL
        condiciones_embeddings = [getattr(AlphaEarth, col) != None for col in columnas_embeddings]
        
        # Realizar la consulta usando SQLAlchemy
        print(f"Buscando punto en AlphaEarth con tolerancia: lat={lat}±{tolerancia}, lon={lon}±{tolerancia}, año={year}")
        resultado = AlphaEarth.query.filter(
            AlphaEarth.latitud.between(lat - tolerancia, lat + tolerancia),
            AlphaEarth.longitud.between(lon - tolerancia, lon + tolerancia),
            AlphaEarth.anio == year,
            AlphaEarth.es_residuo == es_residuo,
            AlphaEarth.tipo_residuo == tipo_residuo,
            and_(*condiciones_embeddings)
        ).first()
        
        if resultado:
            print(f"Punto encontrado en BBDD para año {year}")
            
            embeddings_dict = {}
            for col in columnas_embeddings:
                valor = getattr(resultado, col, None)
                if valor is not None:
                    embeddings_dict[col] = valor
            
            # Devolver valores directamente del objeto resultado
            punto_completo = {
                "id_coordenadaAEF": resultado.id_coordenadaaef,
                "latitud": resultado.latitud,
                "longitud": resultado.longitud,
                "anio": resultado.anio,
                "es_residuo": resultado.es_residuo,
                "tipo_residuo": resultado.tipo_residuo,
                "embeddings": embeddings_dict
            }
            
            return punto_completo
        else:
            print(f"No se encontró punto en BBDD para año {year}")
            return None
    except Exception as e:
        print(f"Error en search_point_bbdd: {type(e).__name__}: {e}")
        return None

def search_point_sentinel2(lat, lon, year, es_residuo, tipo_residuo, tolerancia=0.000001):
    """Busca si existe un punto similar en Sentinel-2 y devuelve todos los campos."""
    try:
        # Crear las columnas para las bandas Sentinel-2
        columnas_bandas = ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b8a", "b9", "b11", "b12"]
        
        condiciones_bandas = [getattr(Sentinel2, col) != None for col in columnas_bandas]

        resultado = Sentinel2.query.filter(
            Sentinel2.latitud.between(lat - tolerancia, lat + tolerancia),
            Sentinel2.longitud.between(lon - tolerancia, lon + tolerancia),
            Sentinel2.fecha.between(f'{year}-01-01', f'{year}-12-31'),
            Sentinel2.es_residuo == es_residuo,
            Sentinel2.tipo_residuo == tipo_residuo,
            and_(*condiciones_bandas)
        ).first()

        
        if resultado:
            print(f"Punto Sentinel-2 encontrado en BBDD para año {year}")

            bandas_dict = {}
            for col in columnas_bandas:
                valor = getattr(resultado, col, None)
                if valor is not None:
                    bandas_dict[col] = valor
            
            # Devolver valores directamente del objeto resultado
            punto_completo = {
                "id_sentinel2": resultado.id_sentinel2,
                "latitud": resultado.latitud,
                "longitud": resultado.longitud,
                "fecha": resultado.fecha,
                "es_residuo": resultado.es_residuo,
                "tipo_residuo": resultado.tipo_residuo,
                "bandas": bandas_dict,
                "nubosidad": resultado.nubosidad
            }
            
            return punto_completo
        else:
            print(f"No se encontró punto Sentinel-2 en BBDD para año {year}")
            return None
            
    except Exception as e:
        print(f"Error en search_point_sentinel2: {type(e).__name__}: {e}")
        return None

def save_point_bbdd_aef(db, year, es_residuo, tipo_residuo, embeddings_data):
    """Guarda un nuevo punto con embeddings en la base de datos."""
    try:
        # Obtener los embeddings
        embeddings = embeddings_data['embeddings']
        lat = embeddings_data['punto']['lat']
        lon = embeddings_data['punto']['lon']

        new_point = AlphaEarth(
            latitud=lat,
            longitud=lon,
            anio=year,
            es_residuo=es_residuo,
            tipo_residuo=tipo_residuo,
            **embeddings
        )

        get_db(db).add(new_point)
        commit_db(db)
        
        print(f"Punto guardado en BBDD con ID: {new_point.id_coordenadaaef}")
        return new_point.id_coordenadaaef
    except Exception as e:
        print(f"Error al guardar punto en BBDD: {e}")
        return None
    
def save_point_sentinel2(db, lat, lon, es_residuo, tipo_residuo, bands_data):
    """Guarda un nuevo punto with bandas Sentinel-2 en la base de datos."""
    try:
        # Obtener los datos
        bandas = bands_data['bandas']
        fecha_imagen = bands_data['fecha_imagen']
        nubosidad = bands_data['nubosidad']

        
        # Guardar en la base de datos        
        new_point = Sentinel2(
            latitud=lat,
            longitud=lon,
            fecha=fecha_imagen,
            es_residuo=es_residuo,
            tipo_residuo=tipo_residuo,
            **bandas,
            nubosidad=nubosidad
        )
        get_db(db).add(new_point)
        commit_db(db)
        
        print(f"Punto Sentinel-2 guardado en BBDD con ID: {new_point.id_sentinel2}")
        return new_point.id_sentinel2
    except Exception as e:
        print(f"Error al guardar punto Sentinel-2 en BBDD: {e}")
        return None
    
def obtener_parametros(request):
    """ Obtiene y valida los parámetros de la URL."""
    # 1. OBTENER Y VALIDAR PARÁMETROS DE LA URL
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    user = request.args.get('user', default='anonymous', type=str)
    year = request.args.get('year', default=2024, type=int)
    tipo_residuo = request.args.get('residuo', default='Ninguno', type=str)
    es_residuo = False if tipo_residuo.lower() == 'ninguno' else True

    # Validar parámetros requeridos
    if lat is None or lon is None:
        # ❌ ERROR: Faltan parámetros obligatorios
        return jsonify({
            "status": "failed",
            "error": "Se requieren parámetros 'lat' y 'lon'"
        }), 400
    
    return lat, lon, user, year, es_residuo, tipo_residuo

# --- 4. RUTA PARA OBTENER EMBEDDINGS ---
@app.route('/api/alphaearth/points', methods=['GET'])
def get_points_embedding():
    """
    Obtiene embeddings de AlphaEarth y bandas de Sentinel-2 para un punto geográfico.
    Si existe en BBDD lo devuelve, sino lo extrae de Earth Engine y lo guarda.
    
    Returns:
        JSON con status "success" o "failed" y los datos correspondientes
    """
    try:
        # db = get_db()
        # 1. OBTENER PARÁMETROS DE LA URL
        lat, lon, user, year, es_residuo, tipo_residuo = obtener_parametros(request)

        
        # 2. BUSCAR DATOS EXISTENTES EN BASE DE DATOS
        print(f"Buscando punto lat={lat}, lon={lon}, año={year} en BBDD...")
        punto_existente_aef = search_point_bbdd_aef(lat, lon, year, es_residuo, tipo_residuo)
        punto_existente_s2 = search_point_sentinel2(lat, lon, year, es_residuo, tipo_residuo)

        # 3. SI AMBOS EXISTEN EN BD, DEVOLVER INMEDIATAMENTE
        if punto_existente_aef and punto_existente_s2:
            print("Ambos puntos encontrados en BBDD, devolviendo datos existentes.")
            # ✅ SUCCESS: Datos encontrados en BD
            return jsonify({
                "status": "success",
                "user": user,
                "data_aef": punto_existente_aef, 
                "data_s2": punto_existente_s2
            }), 200

        # 4. SI NO EXISTE AlphaEarth, EXTRAER Y GUARDAR
        if punto_existente_aef is None:
            punto_existente_aef = search_alphaearth_and_save(db, lat, lon, year, es_residuo, tipo_residuo)

        # 5. SI NO EXISTE Sentinel-2, EXTRAER Y GUARDAR
        if punto_existente_s2 is None:
            punto_existente_s2 = search_sentinel2_and_save(db, lat, lon, year, es_residuo, tipo_residuo)
        # 6. DEVOLVER RESPUESTA EXITOSA FINAL
        # ✅ SUCCESS: Datos obtenidos (ya sea de BD o Earth Engine)
        return jsonify({
            "status": "success",
            "user": user,
            "data_aef": punto_existente_aef, 
            "data_s2": punto_existente_s2
        }), 200

    except Exception as e:
        # ❌ ERROR: Excepción general no manejada
        print(f"Error al consultar puntos: {type(e).__name__}: {e}")
        rollback_db(db)
        return jsonify({
            "status": "failed",
            "error": f"Error interno del servidor: {str(e)}"
        }), 500

# --- 5. INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    try:
        app.register_error_handler(401, status_401)
        app.register_error_handler(404, status_404)
        print("Iniciando servidor Flask...")
        print(f"Base de datos: {app.config['DB_DATABASE']}")
        print(f"Host: {app.config['DB_HOST']}:{app.config['DB_PORT']}")
        app.run(debug=True)
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
    except Exception as e:
        print(f"Error al iniciar servidor: {e}")