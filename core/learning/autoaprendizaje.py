import json
import os

APRENDIZAJE_FILE = "data/aprendizaje.json"
MUNICIPIOS_FILE = "data/municipios.json"

def guardar_municipios(lista):
    with open(MUNICIPIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)

def agregar_conexion(origen, destino, ruta):
    datos = {}

    if os.path.exists(APRENDIZAJE_FILE):
        with open(APRENDIZAJE_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)

    if origen not in datos:
        datos[origen] = {}

    datos[origen][destino] = ruta

    with open(APRENDIZAJE_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

def municipios_mas_cercanos(origen_dict, lista_municipios, cantidad=5):
    ox = __import__("osmnx")
    from geopy.distance import geodesic

    origen_coord = origen_dict["coordenadas"]
    calculados = []

    for m in lista_municipios:
        if m["nombre"] == origen_dict["nombre"]:
            continue
        dist = geodesic(origen_coord, m["coordenadas"]).km
        calculados.append((m["nombre"], dist))

    calculados.sort(key=lambda x: x[1])
    return [{"nombre": nombre, "distancia": round(dist, 2)} for nombre, dist in calculados[:cantidad]]

def buscar_ruta_aprendida(origen, destino):
    if not os.path.exists(APRENDIZAJE_FILE):
        return None

    with open(APRENDIZAJE_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)

    return datos.get(origen, {}).get(destino)
