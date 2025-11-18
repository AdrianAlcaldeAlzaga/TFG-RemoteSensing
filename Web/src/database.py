from flask_sqlalchemy import SQLAlchemy

def init_db(app, db):
    """Inicializa la base de datos con la aplicación Flask."""
    try:
        db.init_app(app)
        with app.app_context():
            db.create_all()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

def get_db(db):
    """Obtiene la instancia de la base de datos."""
    return db.session

def close_db(db, e=None):
    """Cierra la sesión de la base de datos al final de la solicitud."""
    if e:
        db.session.rollback()
    # Cerrar la sesión
    db.session.remove()

def commit_db(db):
    """Confirma los cambios en la base de datos."""
    try:
        db.session.commit()
        print("Cambios en la base de datos confirmados.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al confirmar los cambios en la base de datos: {e}")
        raise

def rollback_db(db):
    """Revierte los cambios en la base de datos."""
    db.session.rollback()
    print("Cambios en la base de datos revertidos.")