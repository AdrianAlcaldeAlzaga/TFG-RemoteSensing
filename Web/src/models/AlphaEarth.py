from extensions import db

class AlphaEarth(db.Model):
    __tablename__ = 'alphaearth'

    id_coordenadaaef = db.Column(db.Integer, primary_key=True)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    es_residuo = db.Column(db.Boolean, nullable=False)
    tipo_residuo = db.Column(db.String(50), nullable=True)
    a00 = db.Column(db.Float, nullable=False)
    a01 = db.Column(db.Float, nullable=False)
    a02 = db.Column(db.Float, nullable=False)
    a03 = db.Column(db.Float, nullable=False)
    a04 = db.Column(db.Float, nullable=False)
    a05 = db.Column(db.Float, nullable=False)
    a06 = db.Column(db.Float, nullable=False)
    a07 = db.Column(db.Float, nullable=False)
    a08 = db.Column(db.Float, nullable=False)
    a09 = db.Column(db.Float, nullable=False)
    a10 = db.Column(db.Float, nullable=False)
    a11 = db.Column(db.Float, nullable=False)
    a12 = db.Column(db.Float, nullable=False)
    a13 = db.Column(db.Float, nullable=False)
    a14 = db.Column(db.Float, nullable=False)
    a15 = db.Column(db.Float, nullable=False)
    a16 = db.Column(db.Float, nullable=False)
    a17 = db.Column(db.Float, nullable=False)
    a18 = db.Column(db.Float, nullable=False)
    a19 = db.Column(db.Float, nullable=False)
    a20 = db.Column(db.Float, nullable=False)
    a21 = db.Column(db.Float, nullable=False)
    a22 = db.Column(db.Float, nullable=False)
    a23 = db.Column(db.Float, nullable=False)
    a24 = db.Column(db.Float, nullable=False)
    a25 = db.Column(db.Float, nullable=False)
    a26 = db.Column(db.Float, nullable=False)
    a27 = db.Column(db.Float, nullable=False)
    a28 = db.Column(db.Float, nullable=False)
    a29 = db.Column(db.Float, nullable=False)
    a30 = db.Column(db.Float, nullable=False)
    a31 = db.Column(db.Float, nullable=False)
    a32 = db.Column(db.Float, nullable=False)
    a33 = db.Column(db.Float, nullable=False)
    a34 = db.Column(db.Float, nullable=False)
    a35 = db.Column(db.Float, nullable=False)
    a36 = db.Column(db.Float, nullable=False)
    a37 = db.Column(db.Float, nullable=False)
    a38 = db.Column(db.Float, nullable=False)
    a39 = db.Column(db.Float, nullable=False)
    a40 = db.Column(db.Float, nullable=False)
    a41 = db.Column(db.Float, nullable=False)
    a42 = db.Column(db.Float, nullable=False)
    a43 = db.Column(db.Float, nullable=False)
    a44 = db.Column(db.Float, nullable=False)
    a45 = db.Column(db.Float, nullable=False)
    a46 = db.Column(db.Float, nullable=False)
    a47 = db.Column(db.Float, nullable=False)
    a48 = db.Column(db.Float, nullable=False)
    a49 = db.Column(db.Float, nullable=False)
    a50 = db.Column(db.Float, nullable=False)
    a51 = db.Column(db.Float, nullable=False)
    a52 = db.Column(db.Float, nullable=False)
    a53 = db.Column(db.Float, nullable=False)
    a54 = db.Column(db.Float, nullable=False)
    a55 = db.Column(db.Float, nullable=False)
    a56 = db.Column(db.Float, nullable=False)
    a57 = db.Column(db.Float, nullable=False)
    a58 = db.Column(db.Float, nullable=False)
    a59 = db.Column(db.Float, nullable=False)
    a60 = db.Column(db.Float, nullable=False)
    a61 = db.Column(db.Float, nullable=False)
    a62 = db.Column(db.Float, nullable=False)
    a63 = db.Column(db.Float, nullable=False)

    def __init__(self, latitud, longitud, anio, es_residuo, tipo_residuo=None, **kwargs):
        self.latitud = latitud
        self.longitud = longitud
        self.anio = anio
        self.es_residuo = es_residuo
        self.tipo_residuo = tipo_residuo
        
        # Asignar bandas dinámicamente
        for i in range(64):
            banda = f'a{i:02d}'
            if banda in kwargs:
                setattr(self, banda, kwargs[banda])

    def __repr__(self):
        return f"<AlphaEarth lat={self.latitud}, lon={self.longitud}, año={self.anio}>"