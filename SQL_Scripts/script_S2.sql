CREATE TABLE Sentinel2 (
    -- Clave primaria: Identificador único para cada punto de entrenamiento
    id_sentinel2 SERIAL PRIMARY KEY, -- Identificador único

    -- 1. Coordenadas Geográficas (WGS84)
    latitud DOUBLE PRECISION NOT NULL,  
    longitud DOUBLE PRECISION NOT NULL,
    fecha DATE NOT NULL, -- Cambiar de anio a fecha para mayor precisión
    
    -- 2. Etiquetas de Verdad Terreno (Ground Truth) para la Clasificación
    es_residuo BOOLEAN NOT NULL,
    tipo_residuo VARCHAR(15),   

    -- 3. Las 12 Bandas Espectrales de Sentinel-2
    -- (Tipo DOUBLE PRECISION para almacenar la reflectancia)
    
    b1 DOUBLE PRECISION, -- Banda 1 - Aerosoles
    b2 DOUBLE PRECISION, -- Banda 2 - Azul
    b3 DOUBLE PRECISION, -- Banda 3 - Verde
    b4 DOUBLE PRECISION, -- Banda 4 - Rojo
    b5 DOUBLE PRECISION, -- Banda 5 - Red Edge 1
    b6 DOUBLE PRECISION, -- Banda 6 - Red Edge 2
    b7 DOUBLE PRECISION, -- Banda 7 - Red Edge 3
    b8 DOUBLE PRECISION, -- Banda 8 - NIR
    b8a DOUBLE PRECISION, -- Banda 8A - Narrow NIR
    b9 DOUBLE PRECISION, -- Banda 9 - Vapor de agua
    b11 DOUBLE PRECISION, -- Banda 11 - SWIR 1
    b12 DOUBLE PRECISION,  -- Banda 12 - SWIR 2
    
    -- CAMPO NUEVO PARA NUBOSIDAD
    porcentaje_nubes DOUBLE PRECISION
);