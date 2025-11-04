CREATE TABLE Sentinel2 (
    -- Clave primaria: Identificador único para cada punto de entrenamiento
    id_coordenadaAEF SERIAL PRIMARY KEY, -- Mantener el mismo nombre de ID para consistencia, o cambiar a id_coordenadaS2

    -- 1. Coordenadas Geográficas (WGS84)
    latitud DOUBLE PRECISION NOT NULL,  
    longitud DOUBLE PRECISION NOT NULL,
    anio INTEGER NOT NULL, -- Mantener el campo anio como en AlphaEarth original
    
    -- 2. Etiquetas de Verdad Terreno (Ground Truth) para la Clasificación
    es_residuo BOOLEAN NOT NULL,
    tipo_residuo VARCHAR(50),   

    -- 3. Las 12 Bandas Espectrales de Sentinel-2
    -- (Tipo DOUBLE PRECISION para almacenar la reflectancia)
    
    B01 DOUBLE PRECISION, -- Banda 1 - Aerosoles
    B02 DOUBLE PRECISION, -- Banda 2 - Azul
    B03 DOUBLE PRECISION, -- Banda 3 - Verde
    B04 DOUBLE PRECISION, -- Banda 4 - Rojo
    B05 DOUBLE PRECISION, -- Banda 5 - Red Edge 1
    B06 DOUBLE PRECISION, -- Banda 6 - Red Edge 2
    B07 DOUBLE PRECISION, -- Banda 7 - Red Edge 3
    B08 DOUBLE PRECISION, -- Banda 8 - NIR
    B8A DOUBLE PRECISION, -- Banda 8A - Narrow NIR
    B09 DOUBLE PRECISION, -- Banda 9 - Vapor de agua
    -- B10 (Cirrus) se omite, ya que se usa para detección de nubes.
    B11 DOUBLE PRECISION, -- Banda 11 - SWIR 1
    B12 DOUBLE PRECISION  -- Banda 12 - SWIR 2
);

alter table sentinel2
RENAME COLUMN anio TO fecha;

ALTER TABLE sentinel2
ALTER COLUMN fecha TYPE DATE
USING MAKE_DATE(fecha, 1, 1);