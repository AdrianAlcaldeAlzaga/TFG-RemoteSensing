from extensions import db
    
class Sentinel2(db.Model):
    __tablename__ = 'sentinel2'
    
    id_sentinel2 = db.Column(db.Integer, primary_key=True)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    es_residuo = db.Column(db.Boolean, nullable=False)
    tipo_residuo = db.Column(db.String(50), nullable=True)
    b1 = db.Column(db.Float, nullable=False)
    b2 = db.Column(db.Float, nullable=False)
    b3 = db.Column(db.Float, nullable=False)
    b4 = db.Column(db.Float, nullable=False)
    b5 = db.Column(db.Float, nullable=False)
    b6 = db.Column(db.Float, nullable=False)
    b7 = db.Column(db.Float, nullable=False)
    b8 = db.Column(db.Float, nullable=False)
    b8a = db.Column(db.Float, nullable=False)
    b9 = db.Column(db.Float, nullable=False)
    b11 = db.Column(db.Float, nullable=False)
    b12 = db.Column(db.Float, nullable=False)
    nubosidad = db.Column(db.Float, nullable=True)

    def __init__(self, latitud, longitud, fecha, es_residuo, tipo_residuo=None, nubosidad=None, **kwargs):
        self.latitud = latitud
        self.longitud = longitud
        self.fecha = fecha
        self.es_residuo = es_residuo
        self.tipo_residuo = tipo_residuo
        
        # Asignar bandas dinámicamente
        for i in range(1, 13):
            banda = f'b{i}' if i != 8 else 'b8'
            if banda in kwargs:
                setattr(self, banda, kwargs[banda])
        if 'b8a' in kwargs:
            self.b8a = kwargs['b8a']

        self.nubosidad = nubosidad

    def __repr__(self):
        return f"<Sentinel2 lat={self.latitud}, lon={self.longitud}, fecha={self.fecha}, nubosidad={self.nubosidad}>"