# Arquitectura Cloud para BI — DENUE INEGI 🌾

**Alumna:** Cecilia Ruiz  
**Materia:** Cómputo en la Nube  
**Dataset:** DENUE INEGI — Sector Agropecuario (21,093 registros)

---

## Índice
1. [Arquitectura de la Solución](#arquitectura)
2. [Paso 1: Migración a Supabase](#paso-1-migración-a-supabase)
3. [Paso 2: Desarrollo de la API](#paso-2-desarrollo-de-la-api-restful)
4. [Paso 3: Despliegue en PythonAnywhere](#paso-3-despliegue-en-pythonanywhere)
5. [Paso 4: Dashboard BI](#paso-4-dashboard-bi)
6. [URLs de la API](#urls-de-la-api)
7. [Hallazgos](#hallazgos-principales)

---

## Arquitectura

```
Excel INEGI → Supabase (PostgreSQL) → Flask API → PythonAnywhere → Looker Studio
```

| Capa | Tecnología | Descripción |
|------|-----------|-------------|
| Datos | Excel INEGI (DENUE) | 21,093 registros normalizados |
| Base de datos | Supabase (PostgreSQL) | 6 tablas relacionales con PKs y FKs |
| Backend | Flask (Python) | 7 endpoints REST en JSON |
| Hosting | PythonAnywhere | URL pública gratuita |
| BI | Looker Studio | Dashboard con KPIs y gráficas |
| Código | GitHub | Repositorio público |

---

## Paso 1: Migración a Supabase

### 1.1 Crear cuenta y proyecto
1. Ir a [supabase.com](https://supabase.com) y crear una cuenta gratuita
2. Crear un nuevo proyecto con nombre `CECYINEGI`
3. Guardar la contraseña de la base de datos

### 1.2 Modelado físico — Crear tablas
1. En Supabase ir a **SQL Editor**
2. Ejecutar el archivo `schema_supabase.sql` incluido en este repositorio
3. Verificar que se crearon las 6 tablas en **Table Editor**

```
cat_actividad      → Catálogo de 12 actividades económicas
cat_rango_personal → Catálogo de 7 rangos de personal
entidad            → 32 entidades federativas
municipio          → 954 municipios
localidad          → 3,857 localidades
establecimiento    → 21,093 unidades económicas (tabla principal)
```

### 1.3 Carga de datos
Se generaron 6 archivos CSV desde el Excel original de INEGI y se cargaron en Supabase en el siguiente orden (respetando las claves foráneas):

1. `cat_actividad.csv`
2. `cat_rango_personal.csv`
3. `entidad.csv`
4. `municipio.csv`
5. `localidad.csv`
6. `establecimiento.csv`

Para cargar cada CSV: **Table Editor → [tabla] → Insert → Import data from CSV**

---

## Paso 2: Desarrollo de la API RESTful

### 2.1 Requisitos
```bash
pip install flask psycopg2-binary
```

### 2.2 Configuración
Editar la variable `DATABASE_URL` en `flask_app.py` con las credenciales de Supabase:
```
Project Settings → Database → Connection string (URI)
```

### 2.3 Ejecutar localmente
```bash
python flask_app.py
```
La API estará disponible en `http://127.0.0.1:5000`

### 2.4 Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/unidades` | Catálogo general (máx. 100) |
| GET | `/api/unidades/{id}` | Unidad por ID |
| GET | `/api/unidades/buscar?nombre=X` | Búsqueda por nombre |
| GET | `/api/unidades/filtro?estado=X&actividad=Y` | Filtros dinámicos |
| GET | `/api/estadisticas/total_por_estado` | KPI por entidad |
| GET | `/api/unidades/{id}/perfil_completo` | JSON jerárquico anidado |
| GET | `/api/unidades/cercanas?lat=X&lon=Y&radio=Z` | Búsqueda geoespacial |

---

## Paso 3: Despliegue en PythonAnywhere

### 3.1 Crear cuenta
1. Ir a [pythonanywhere.com](https://www.pythonanywhere.com) y crear cuenta gratuita (Beginner)

### 3.2 Subir código desde GitHub
En la consola **Bash** de PythonAnywhere:
```bash
git clone https://github.com/ceciliaruiz-pixel/inegi.git
pip install --user flask psycopg2-binary
```

### 3.3 Configurar Web App
1. Ir a la pestaña **Web → Add a new web app**
2. Seleccionar **Flask** y **Python 3.10**
3. Editar el archivo WSGI (`/var/www/ceciliaruiz_pythonanywhere_com_wsgi.py`):

```python
import sys
sys.path.insert(0, '/home/ceciliaruiz/inegi')
from flask_app import app as application
```

4. Hacer clic en **Reload**

### 3.4 URL pública
```
https://ceciliaruiz.pythonanywhere.com
```

---

## Paso 4: Dashboard BI

### Herramienta: Looker Studio

1. Ir a [lookerstudio.google.com](https://lookerstudio.google.com)
2. Importar datos desde Google Sheets usando Apps Script:

```javascript
function importarDatos() {
  var url = "https://ceciliaruiz.pythonanywhere.com/api/estadisticas/total_por_estado";
  var response = UrlFetchApp.fetch(url);
  var json = JSON.parse(response.getContentText());
  var datos = json.datos;
  var hoja = SpreadsheetApp.getActiveSheet();
  hoja.clearContents();
  hoja.getRange(1,1).setValue("Estado");
  hoja.getRange(1,2).setValue("Total Unidades");
  for (var i = 0; i < datos.length; i++) {
    hoja.getRange(i+2,1).setValue(datos[i].estado);
    hoja.getRange(i+2,2).setValue(datos[i].total_unidades);
  }
}
```

3. Conectar la hoja a Looker Studio → **Añadir datos → Hojas de cálculo de Google**
4. Crear visualizaciones: gráfica de barras, pastel, tabla con KPIs

### KPIs del Dashboard
- Total de unidades económicas por estado
- Distribución por rango de personal
- Actividades económicas más frecuentes

---

## URLs de la API

Base URL: `https://ceciliaruiz.pythonanywhere.com`

```
GET /api/unidades
GET /api/unidades/963
GET /api/unidades/buscar?nombre=rancho
GET /api/unidades/filtro?estado=jalisco
GET /api/unidades/filtro?estado=jalisco&actividad=agricola
GET /api/estadisticas/total_por_estado
GET /api/unidades/963/perfil_completo
GET /api/unidades/cercanas?lat=20.66&lon=-103.35&radio=10
```

---

## Archivos del Repositorio

| Archivo | Descripción |
|---------|-------------|
| `README.md` | Documentación completa del proyecto |
| `flask_app.py` | API REST con Flask y 7 endpoints |
| `schema_supabase.sql` | Script SQL de creación de tablas |
| `diagrama_arquitectura.html` | Diagrama visual de la arquitectura |
| `Insights_INEGI.docx` | Documento de hallazgos de negocio |

---

## Hallazgos Principales

1. **Concentración geográfica desigual** — Los estados del norte y centro concentran más del 50% de las unidades económicas agropecuarias registradas a nivel nacional.

2. **Predominio de microempresas** — La mayoría de establecimientos tienen entre 0 y 5 empleados, lo que refleja la naturaleza micro del sector agropecuario formal en México.
