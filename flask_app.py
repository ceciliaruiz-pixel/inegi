from flask import Flask, jsonify, request
import psycopg2
import psycopg2.extras

DATABASE_URL = "postgresql://postgres:Cruiz790607!@db.fpobfcrvtikivmdpkppj.supabase.co:5432/postgres"

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route("/")
def root():
    return jsonify({
        "mensaje": "API INEGI activa",
        "endpoints": [
            "GET /api/unidades",
            "GET /api/unidades/<id>",
            "GET /api/unidades/buscar?nombre=texto",
            "GET /api/unidades/filtro?estado=X&actividad=Y",
            "GET /api/unidades/<id>/perfil_completo",
            "GET /api/unidades/cercanas?lat=X&lon=Y&radio=Z",
            "GET /api/estadisticas/total_por_estado",
        ]
    })

# ENDPOINT 1: Catalogo general
@app.route("/api/unidades")
def get_unidades():
    limit = min(int(request.args.get("limit", 50)), 100)
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.id, e.nom_estab AS nombre, e.raz_social,
                   a.nombre_act AS actividad,
                   r.descripcion AS rango_personal,
                   en.nombre AS entidad, m.nombre AS municipio
            FROM establecimiento e
            LEFT JOIN cat_actividad a ON a.id_actividad = e.id_actividad
            LEFT JOIN cat_rango_personal r ON r.id_rango = e.id_rango
            LEFT JOIN localidad l ON l.id_localidad = e.id_localidad
            LEFT JOIN municipio m ON m.id_municipio = l.id_municipio
            LEFT JOIN entidad en ON en.id_entidad = m.id_entidad
            ORDER BY e.id LIMIT %s
        """, (limit,))
        resultados = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({"total": len(resultados), "limit": limit, "datos": [dict(r) for r in resultados]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 2: Buscar por nombre
@app.route("/api/unidades/buscar")
def buscar_unidades():
    nombre = request.args.get("nombre", "")
    if not nombre:
        return jsonify({"error": "Parametro nombre requerido"}), 400
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.id, e.nom_estab AS nombre, e.raz_social,
                   a.nombre_act AS actividad, en.nombre AS entidad,
                   m.nombre AS municipio
            FROM establecimiento e
            LEFT JOIN cat_actividad a ON a.id_actividad = e.id_actividad
            LEFT JOIN localidad l ON l.id_localidad = e.id_localidad
            LEFT JOIN municipio m ON m.id_municipio = l.id_municipio
            LEFT JOIN entidad en ON en.id_entidad = m.id_entidad
            WHERE UPPER(e.nom_estab) LIKE UPPER(%s)
            LIMIT 50
        """, (f"%{nombre}%",))
        resultados = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({"total": len(resultados), "busqueda": nombre, "datos": [dict(r) for r in resultados]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 3: Filtros multiples
@app.route("/api/unidades/filtro")
def filtrar_unidades():
    estado = request.args.get("estado")
    actividad = request.args.get("actividad")
    limit = min(int(request.args.get("limit", 50)), 100)
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        filtros = []
        params = []
        if estado:
            filtros.append("UPPER(en.nombre) LIKE UPPER(%s)")
            params.append(f"%{estado}%")
        if actividad:
            filtros.append("UPPER(a.nombre_act) LIKE UPPER(%s)")
            params.append(f"%{actividad}%")
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        params.append(limit)
        cur.execute(f"""
            SELECT e.id, e.nom_estab AS nombre, e.raz_social,
                   a.nombre_act AS actividad,
                   r.descripcion AS rango_personal,
                   en.nombre AS entidad, m.nombre AS municipio,
                   l.nombre AS localidad
            FROM establecimiento e
            LEFT JOIN cat_actividad a ON a.id_actividad = e.id_actividad
            LEFT JOIN cat_rango_personal r ON r.id_rango = e.id_rango
            LEFT JOIN localidad l ON l.id_localidad = e.id_localidad
            LEFT JOIN municipio m ON m.id_municipio = l.id_municipio
            LEFT JOIN entidad en ON en.id_entidad = m.id_entidad
            {where} ORDER BY e.id LIMIT %s
        """, params)
        resultados = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({"total": len(resultados), "filtros": {"estado": estado, "actividad": actividad}, "datos": [dict(r) for r in resultados]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 4: Consulta por ID
@app.route("/api/unidades/<int:id>")
def get_unidad_por_id(id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.id, e.nom_estab AS nombre, e.raz_social,
                   a.codigo_act, a.nombre_act AS actividad,
                   r.descripcion AS rango_personal,
                   en.nombre AS entidad, m.nombre AS municipio,
                   l.nombre AS localidad,
                   e.telefono, e.correoelec,
                   e.latitud, e.longitud, e.fecha_alta
            FROM establecimiento e
            LEFT JOIN cat_actividad a ON a.id_actividad = e.id_actividad
            LEFT JOIN cat_rango_personal r ON r.id_rango = e.id_rango
            LEFT JOIN localidad l ON l.id_localidad = e.id_localidad
            LEFT JOIN municipio m ON m.id_municipio = l.id_municipio
            LEFT JOIN entidad en ON en.id_entidad = m.id_entidad
            WHERE e.id = %s
        """, (id,))
        resultado = cur.fetchone()
        cur.close(); conn.close()
        if not resultado:
            return jsonify({"error": f"No se encontro unidad con ID {id}"}), 404
        return jsonify(dict(resultado))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 5: KPI total por estado
@app.route("/api/estadisticas/total_por_estado")
def total_por_estado():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT en.nombre AS estado, COUNT(e.id) AS total_unidades
            FROM establecimiento e
            LEFT JOIN localidad l ON l.id_localidad = e.id_localidad
            LEFT JOIN municipio m ON m.id_municipio = l.id_municipio
            LEFT JOIN entidad en ON en.id_entidad = m.id_entidad
            GROUP BY en.nombre
            ORDER BY total_unidades DESC
        """)
        resultados = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({"total_estados": len(resultados), "datos": [dict(r) for r in resultados]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 6: Perfil completo anidado
@app.route("/api/unidades/<int:id>/perfil_completo")
def perfil_completo(id):
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.id, e.nom_estab, e.raz_social, e.fecha_alta,
                   e.telefono, e.correoelec, e.latitud, e.longitud,
                   a.codigo_act, a.nombre_act,
                   r.descripcion AS rango_personal,
                   l.nombre AS localidad,
                   m.nombre AS municipio,
                   en.nombre AS entidad
            FROM establecimiento e
            LEFT JOIN cat_actividad a ON a.id_actividad = e.id_actividad
            LEFT JOIN cat_rango_personal r ON r.id_rango = e.id_rango
            LEFT JOIN localidad l ON l.id_localidad = e.id_localidad
            LEFT JOIN municipio m ON m.id_municipio = l.id_municipio
            LEFT JOIN entidad en ON en.id_entidad = m.id_entidad
            WHERE e.id = %s
        """, (id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            return jsonify({"error": f"No se encontro unidad con ID {id}"}), 404
        return jsonify({
            "id": row["id"],
            "nombre": row["nom_estab"],
            "razon_social": row["raz_social"],
            "fecha_alta": row["fecha_alta"],
            "actividad": {
                "codigo": row["codigo_act"],
                "descripcion": row["nombre_act"],
                "rango_personal": row["rango_personal"]
            },
            "ubicacion": {
                "entidad": row["entidad"],
                "municipio": row["municipio"],
                "localidad": row["localidad"],
                "coordenadas": {
                    "latitud": float(row["latitud"]) if row["latitud"] else None,
                    "longitud": float(row["longitud"]) if row["longitud"] else None
                }
            },
            "contacto": {
                "telefono": row["telefono"],
                "correo": row["correoelec"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT 7: Busqueda geoespacial
@app.route("/api/unidades/cercanas")
def unidades_cercanas():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        radio = float(request.args.get("radio", 5.0))
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT e.id, e.nom_estab AS nombre, e.raz_social,
                   a.nombre_act AS actividad,
                   en.nombre AS entidad, m.nombre AS municipio,
                   e.latitud, e.longitud,
                   ROUND(CAST(
                       6371 * 2 * ASIN(SQRT(
                           POWER(SIN(RADIANS(%s - e.latitud) / 2), 2) +
                           COS(RADIANS(e.latitud)) * COS(RADIANS(%s)) *
                           POWER(SIN(RADIANS(%s - e.longitud) / 2), 2)
                       ))
                   AS NUMERIC), 2) AS distancia_km
            FROM establecimiento e
            LEFT JOIN cat_actividad a ON a.id_actividad = e.id_actividad
            LEFT JOIN localidad l ON l.id_localidad = e.id_localidad
            LEFT JOIN municipio m ON m.id_municipio = l.id_municipio
            LEFT JOIN entidad en ON en.id_entidad = m.id_entidad
            WHERE e.latitud IS NOT NULL AND e.longitud IS NOT NULL
            AND (6371 * 2 * ASIN(SQRT(
                POWER(SIN(RADIANS(%s - e.latitud) / 2), 2) +
                COS(RADIANS(e.latitud)) * COS(RADIANS(%s)) *
                POWER(SIN(RADIANS(%s - e.longitud) / 2), 2)
            ))) <= %s
            ORDER BY distancia_km LIMIT 100
        """, (lat, lat, lon, lat, lat, lon, radio))
        resultados = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({
            "punto_busqueda": {"latitud": lat, "longitud": lon},
            "radio_km": radio,
            "total_encontrados": len(resultados),
            "datos": [dict(r) for r in resultados]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
