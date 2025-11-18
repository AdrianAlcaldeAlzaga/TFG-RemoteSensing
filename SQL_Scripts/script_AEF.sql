
-- Si ya existe una tabla con el mismo nombre y deseas usar este script:
-- DROP TABLE IF EXISTS AlphaEarth; 

-- La tabla para almacenar los datos de entrenamiento basados en AlphaEarth
CREATE TABLE AlphaEarth (
    -- Clave primaria: Identificador único para cada punto de entrenamiento
    id_coordenadaAEF SERIAL PRIMARY KEY,

    -- 1. Coordenadas Geográficas (WGS84) para fácil georreferenciación
    latitud DOUBLE PRECISION NOT NULL, 
    longitud DOUBLE PRECISION NOT NULL,
	anio INTEGER NOT NULL,
	

    -- 2. Etiquetas de Verdad Terreno (Ground Truth) para la Clasificación
    
    -- Columna 1: Etiqueta binaria (¿Es vertedero/escombrera? SI/NO)
    es_residuo BOOLEAN NOT NULL,
    
    -- Columna 2: Etiqueta categórica (Clasificación de 3/4 tipos)
    tipo_residuo VARCHAR(15), 

    -- 3. Las 64 Dimensiones del Embedding de AlphaEarth (A00 a A63)
    -- Tipo DOUBLE PRECISION es el estándar para datos científicos y de ML (float64 en Python).
    
    a00 DOUBLE PRECISION,
    a01 DOUBLE PRECISION,
    a02 DOUBLE PRECISION,
    a03 DOUBLE PRECISION,
    a04 DOUBLE PRECISION,
    a05 DOUBLE PRECISION,
    a06 DOUBLE PRECISION,
    a07 DOUBLE PRECISION,
    a08 DOUBLE PRECISION,
    a09 DOUBLE PRECISION,
    a10 DOUBLE PRECISION,
    a11 DOUBLE PRECISION,
    a12 DOUBLE PRECISION,
    a13 DOUBLE PRECISION,
    a14 DOUBLE PRECISION,
    a15 DOUBLE PRECISION,
    a16 DOUBLE PRECISION,
    a17 DOUBLE PRECISION,
    a18 DOUBLE PRECISION,
    a19 DOUBLE PRECISION,
    a20 DOUBLE PRECISION,
    a21 DOUBLE PRECISION,
    a22 DOUBLE PRECISION,
    a23 DOUBLE PRECISION,
    a24 DOUBLE PRECISION,
    a25 DOUBLE PRECISION,
    a26 DOUBLE PRECISION,
    a27 DOUBLE PRECISION,
    a28 DOUBLE PRECISION,
    a29 DOUBLE PRECISION,
    a30 DOUBLE PRECISION,
    a31 DOUBLE PRECISION,
    a32 DOUBLE PRECISION,
    a33 DOUBLE PRECISION,
    a34 DOUBLE PRECISION,
    a35 DOUBLE PRECISION,
    a36 DOUBLE PRECISION,
    a37 DOUBLE PRECISION,
    a38 DOUBLE PRECISION,
    a39 DOUBLE PRECISION,
    a40 DOUBLE PRECISION,
    a41 DOUBLE PRECISION,
    a42 DOUBLE PRECISION,
    a43 DOUBLE PRECISION,
    a44 DOUBLE PRECISION,
    a45 DOUBLE PRECISION,
    a46 DOUBLE PRECISION,
    a47 DOUBLE PRECISION,
    a48 DOUBLE PRECISION,
    a49 DOUBLE PRECISION,
    a50 DOUBLE PRECISION,
    a51 DOUBLE PRECISION,
    a52 DOUBLE PRECISION,
    a53 DOUBLE PRECISION,
    a54 DOUBLE PRECISION,
    a55 DOUBLE PRECISION,
    a56 DOUBLE PRECISION,
    a57 DOUBLE PRECISION,
    a58 DOUBLE PRECISION,
    a59 DOUBLE PRECISION,
    a60 DOUBLE PRECISION,
    a61 DOUBLE PRECISION,
    a62 DOUBLE PRECISION,
    a63 DOUBLE PRECISION
);