import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from core.learning.autoaprendizaje import (
    agregar_conexion,
    municipios_mas_cercanos,
    guardar_municipios
)
import folium

geolocator = Nominatim(user_agent="mi_app_rutas")
MAP_FILE = "mapa_generado.html"

def guardar_ruta_aprendida(origen, destino, ruta):
    if origen and destino and ruta:
        agregar_conexion(origen, destino, ruta)

def generar_mapa_ruta(origen, destino):
    print("📍 Calculando coordenadas...")
    origen_location = geolocator.geocode(origen + ", Cundinamarca, Colombia")
    destino_location = geolocator.geocode(destino + ", Cundinamarca, Colombia")

    if not origen_location or not destino_location:
        raise ValueError("No se pudieron geolocalizar el origen o el destino")

    G = ox.graph_from_point((origen_location.latitude, origen_location.longitude), dist=50000, network_type='drive')

    origen_node = ox.distance.nearest_nodes(G, origen_location.longitude, origen_location.latitude)
    destino_node = ox.distance.nearest_nodes(G, destino_location.longitude, destino_location.latitude)

    print("🛣️ Calculando ruta más corta...")
    ruta = nx.shortest_path(G, origen_node, destino_node, weight='length')

    print("🗺️ Generando mapa...")
    mapa = folium.Map(location=[origen_location.latitude, origen_location.longitude], zoom_start=10)
    puntos = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in ruta]
    folium.PolyLine(puntos, color="blue", weight=5, opacity=0.8).add_to(mapa)

    folium.Marker([origen_location.latitude, origen_location.longitude], tooltip="Origen", icon=folium.Icon(color="green")).add_to(mapa)
    folium.Marker([destino_location.latitude, destino_location.longitude], tooltip="Destino", icon=folium.Icon(color="red")).add_to(mapa)

    mapa.save(MAP_FILE)
    guardar_ruta_aprendida(origen, destino, puntos)
    print("✅ Mapa guardado en", MAP_FILE)

def sugerir_destinos_cercanos(origen_nombre, lista_municipios, cantidad=3):
    origen_coords = geolocator.geocode(origen_nombre + ", Cundinamarca, Colombia")
    if not origen_coords:
        return []

    municipio_origen = {
        "nombre": origen_nombre,
        "coordenadas": (origen_coords.latitude, origen_coords.longitude)
    }

    municipios_cercanos = municipios_mas_cercanos(municipio_origen, lista_municipios, cantidad)
    return [m["nombre"] for m in municipios_cercanos]
