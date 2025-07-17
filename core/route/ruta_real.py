# core/route/ruta_real.py
import openrouteservice

client = openrouteservice.Client(key='eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjRkODBkZDYyNWYxNjRjZjQ5NjYwM2FkZTcxYmNjNTI3IiwiaCI6Im11cm11cjY0In0=')  # Reemplaza con tu API key válida

def calcular_ruta_real(origen, destino, modo="driving-car"):
    try:
        # Validar modo de transporte
        modos_validos = ["driving-car", "driving-hgv", "cycling-regular", "foot-walking", "wheelchair"]
        if modo not in modos_validos:
            print(f"⚠️ Modo '{modo}' no válido. Usando 'driving-car' por defecto.")
            modo = "driving-car"

        lon_origen, lat_origen = origen[1], origen[0]
        lon_destino, lat_destino = destino[1], destino[0]

        ruta = client.directions(
            coordinates=[(lon_origen, lat_origen), (lon_destino, lat_destino)],
            profile=modo,
            format="geojson"
        )

        coords_extraidas = ruta["features"][0]["geometry"]["coordinates"]
        coords_latlon = [(lat, lon) for lon, lat in coords_extraidas]

        distancia_m = ruta["features"][0]["properties"]["segments"][0]["distance"]
        duracion_s = ruta["features"][0]["properties"]["segments"][0]["duration"]

        return {
            "coordenadas": coords_latlon,
            "longitud_km": round(distancia_m / 1000, 2),
            "duracion_min": round(duracion_s / 60, 1)
        }
    except Exception as e:
        print("❌ Error calculando ruta real:", e)
        return None
