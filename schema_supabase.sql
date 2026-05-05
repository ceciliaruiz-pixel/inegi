-- =============================================
-- SCHEMA: Arquitectura Cloud INEGI - DENUE
-- Base de datos: Supabase (PostgreSQL)
-- Alumna: Cecilia Ruiz
-- =============================================

-- 1. Catalogo de actividades economicas
CREATE TABLE cat_actividad (
  id_actividad  SERIAL PRIMARY KEY,
  codigo_act    VARCHAR(10) NOT NULL UNIQUE,
  nombre_act    VARCHAR(100) NOT NULL
);

-- 2. Catalogo de rangos de personal
CREATE TABLE cat_rango_personal (
  id_rango     SERIAL PRIMARY KEY,
  descripcion  VARCHAR(50) NOT NULL UNIQUE
);

-- 3. Entidades federativas (32)
CREATE TABLE entidad (
  id_entidad  SERIAL PRIMARY KEY,
  nombre      VARCHAR(100) NOT NULL UNIQUE
);

-- 4. Municipios
CREATE TABLE municipio (
  id_municipio  SERIAL PRIMARY KEY,
  id_entidad    INT NOT NULL REFERENCES entidad(id_entidad),
  nombre        VARCHAR(100) NOT NULL
);

-- 5. Localidades
CREATE TABLE localidad (
  id_localidad  SERIAL PRIMARY KEY,
  id_municipio  INT NOT NULL REFERENCES municipio(id_municipio),
  nombre        VARCHAR(150) NOT NULL
);

-- 6. Tabla principal de establecimientos (21,093 registros)
CREATE TABLE establecimiento (
  id           INT PRIMARY KEY,
  nom_estab    VARCHAR(200),
  raz_social   VARCHAR(200),
  id_actividad INT REFERENCES cat_actividad(id_actividad),
  id_rango     INT REFERENCES cat_rango_personal(id_rango),
  id_localidad INT REFERENCES localidad(id_localidad),
  telefono     VARCHAR(20),
  correoelec   VARCHAR(100),
  latitud      NUMERIC(12, 8),
  longitud     NUMERIC(12, 8),
  fecha_alta   VARCHAR(10)
);
