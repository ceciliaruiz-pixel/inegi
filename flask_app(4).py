from flask import Flask, jsonify, request
import requests

SUPABASE_URL = "https://fpobfcrvtikivmdpkppj.supabase.co"
SUPABASE_KEY = "sb_publishable__VQJTYYV640xPWY9PADPdg_VWJrvNqX"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

app = Flask(__name__)

def supabase_get(table, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{params}"
    r = requests.get(url, headers=HEADERS)
    return r.json()

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
            "GET /api/estadisticas/total_por_estado",
        ]
    })

# ENDPOINT 1: Catalogo general
@app.route("/api/unidades")
def get_unidades():
    limit = min(int(request.args.get("limit", 50)), 100)
    params = f"select=id,nom_estab,raz_social&limit={limit}&order=id"
    data = supabase_get("establecimiento", params)
    return jsonify({"total": len(data), "datos": data})

# ENDPOINT 2: Buscar por nombre
@app.route("/api/unidades/buscar")
def buscar_unidades():
    nombre = request.args.get("nombre", "")
    if not nombre:
        return jsonify({"error": "Parametro nombre requerido"}), 400
    params = f"select=id,nom_estab,raz_social&nom_estab=ilike.*{nombre}*&limit=50"
    data = supabase_get("establecimiento", params)
    return jsonify({"total": len(data), "busqueda": nombre, "datos": data})

# ENDPOINT 3: Filtro por estado y/o actividad
@app.route("/api/unidades/filtro")
def filtrar_unidades():
    estado = request.args.get("estado", "")
    actividad = request.args.get("actividad", "")
    limit = min(int(request.args.get("limit", 50)), 100)

    # Obtener IDs de entidad si se filtro por estado
    filtro_loc = ""
    if estado:
        ents = supabase_get("entidad", f"nombre=ilike.*{estado}*&select=id_entidad")
        if ents:
            id_ent = ents[0]["id_entidad"]
            muns = supabase_get("municipio", f"id_entidad=eq.{id_ent}&select=id_municipio")
            if muns:
                ids_mun = ",".join([str(m["id_municipio"]) for m in muns])
                locs = supabase_get("localidad", f"id_municipio=in.({ids_mun})&select=id_localidad")
                if locs:
                    ids_loc = ",".join([str(l["id_localidad"]) for l in locs])
                    filtro_loc = f"&id_localidad=in.({ids_loc})"

    filtro_act = ""
    if actividad:
        acts = supabase_get("cat_actividad", f"nombre_act=ilike.*{actividad}*&select=id_actividad")
        if acts:
            id_act = acts[0]["id_actividad"]
            filtro_act = f"&id_actividad=eq.{id_act}"

    params = f"select=id,nom_estab,raz_social,id_actividad,id_localidad&limit={limit}{filtro_loc}{filtro_act}"
    data = supabase_get("establecimiento", params)
    return jsonify({
        "total": len(data),
        "filtros": {"estado": estado, "actividad": actividad},
        "datos": data
    })

# ENDPOINT 4: Consulta por ID
@app.route("/api/unidades/<int:id>")
def get_unidad_por_id(id):
    params = f"id=eq.{id}&select=id,nom_estab,raz_social,telefono,correoelec,latitud,longitud,fecha_alta"
    data = supabase_get("establecimiento", params)
    if not data:
        return jsonify({"error": f"No se encontro unidad con ID {id}"}), 404
    return jsonify(data[0])

# ENDPOINT 5: KPI total por estado
@app.route("/api/estadisticas/total_por_estado")
def total_por_estado():
    entidades = supabase_get("entidad", "select=id_entidad,nombre&order=nombre")
    resultado = []
    for ent in entidades:
        muns = supabase_get("municipio", f"id_entidad=eq.{ent['id_entidad']}&select=id_municipio")
        total = 0
        if muns:
            ids_mun = ",".join([str(m["id_municipio"]) for m in muns])
            locs = supabase_get("localidad", f"id_municipio=in.({ids_mun})&select=id_localidad")
            if locs:
                ids_loc = ",".join([str(l["id_localidad"]) for l in locs])
                estabs = supabase_get("establecimiento", f"id_localidad=in.({ids_loc})&select=id")
                total = len(estabs)
        resultado.append({"estado": ent["nombre"], "total_unidades": total})
    resultado.sort(key=lambda x: x["total_unidades"], reverse=True)
    return jsonify({"total_estados": len(resultado), "datos": resultado})

# ENDPOINT 6: Perfil completo anidado
@app.route("/api/unidades/<int:id>/perfil_completo")
def perfil_completo(id):
    params = f"id=eq.{id}&select=id,nom_estab,raz_social,telefono,correoelec,latitud,longitud,fecha_alta,id_actividad,id_rango,id_localidad"
    data = supabase_get("establecimiento", params)
    if not data:
        return jsonify({"error": f"No se encontro unidad con ID {id}"}), 404
    row = data[0]

    actividad = {}
    if row.get("id_actividad"):
        act = supabase_get("cat_actividad", f"id_actividad=eq.{row['id_actividad']}&select=codigo_act,nombre_act")
        if act:
            actividad = act[0]

    rango = {}
    if row.get("id_rango"):
        r = supabase_get("cat_rango_personal", f"id_rango=eq.{row['id_rango']}&select=descripcion")
        if r:
            rango = r[0]

    localidad = municipio = entidad = {}
    if row.get("id_localidad"):
        loc = supabase_get("localidad", f"id_localidad=eq.{row['id_localidad']}&select=nombre,id_municipio")
        if loc:
            localidad = loc[0]
            mun = supabase_get("municipio", f"id_municipio=eq.{loc[0]['id_municipio']}&select=nombre,id_entidad")
            if mun:
                municipio = mun[0]
                ent = supabase_get("entidad", f"id_entidad=eq.{mun[0]['id_entidad']}&select=nombre")
                if ent:
                    entidad = ent[0]

    return jsonify({
        "id": row["id"],
        "nombre": row["nom_estab"],
        "razon_social": row["raz_social"],
        "fecha_alta": row["fecha_alta"],
        "actividad": {
            "codigo": actividad.get("codigo_act"),
            "descripcion": actividad.get("nombre_act"),
            "rango_personal": rango.get("descripcion")
        },
        "ubicacion": {
            "entidad": entidad.get("nombre"),
            "municipio": municipio.get("nombre"),
            "localidad": localidad.get("nombre"),
            "coordenadas": {
                "latitud": row.get("latitud"),
                "longitud": row.get("longitud")
            }
        },
        "contacto": {
            "telefono": row.get("telefono"),
            "correo": row.get("correoelec")
        }
    })

if __name__ == "__main__":
    app.run(debug=True)
