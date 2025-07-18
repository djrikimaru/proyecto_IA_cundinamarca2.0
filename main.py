import webview
import folium
import json
import os
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

from core.learning.autoaprendizaje import buscar_ruta_aprendida
from core.route.ruta_real import calcular_ruta_real

SELECCION_FILE = "temp_seleccion.json"
MAP_FILE = "temp_mapa.html"

app = Flask(__name__)
CORS(app)

def cargar_municipios():
    with open("data/municipios.json", "r", encoding="utf-8") as f:
        return json.load(f)

def inicializar_seleccion():
    with open(SELECCION_FILE, "w", encoding="utf-8") as f:
        json.dump({"origen": None, "destino": None}, f)

def leer_seleccion():
    with open(SELECCION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_seleccion(origen, destino):
    with open(SELECCION_FILE, "w", encoding="utf-8") as f:
        json.dump({"origen": origen, "destino": destino}, f)

def extraer_origen_destino(texto, municipios):
    nombres = [m["nombre"] for m in municipios]
    encontrados = [m for m in nombres if m.lower() in texto.lower()]
    return encontrados[:2] if len(encontrados) >= 2 else (None, None)

def generar_mapa_interactivo_estable(municipios, ruta=[]):
    seleccion = leer_seleccion()
    origen = seleccion.get("origen")
    destino = seleccion.get("destino")

    mapa = folium.Map(location=[4.7, -74.2], zoom_start=8, tiles="OpenStreetMap")

    for m in municipios:
        nombre = m["nombre"]
        lat, lon = m["coordenadas"]

        popup_html = f"""
        <b>{nombre}</b><br>
        <button onclick="fetch('http://127.0.0.1:5000/origen?m={nombre}').then(() => location.reload())">Establecer como origen</button><br>
        <button onclick="fetch('http://127.0.0.1:5000/destino?m={nombre}').then(() => location.reload())">Establecer como destino</button>
        """

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=nombre,
            icon=folium.Icon(color="blue")
        ).add_to(mapa)

    if ruta and len(ruta) > 1:
        folium.PolyLine(ruta, color="green", weight=4).add_to(mapa)

    overlay_html = f"""
    <div style='position: fixed; top: 120px; left: 10px; z-index:9999; background-color: white; padding: 8px; border-radius: 6px; box-shadow: 0 0 5px gray;'>
        <button onclick="fetch('http://127.0.0.1:5000/reset').then(() => location.reload())" style='padding:8px;'>🔄 Reiniciar</button><br><br>
        <div>
            <b>Origen:</b> {origen or '-'}<br>
            <b>Destino:</b> {destino or '-'}
        </div><br>
        <input type="text" id="pregunta" placeholder="Haz una pregunta..." style="width:200px; padding:6px;" />
        <button onclick="enviarPregunta()" style="padding:6px;">Preguntar</button>
        <div id="respuesta" style="margin-top:10px; font-style:italic;"></div>

        <script>
            function enviarPregunta() {{
                const pregunta = document.getElementById('pregunta').value;
                document.getElementById('respuesta').innerText = '🤔 Pensando...';
                fetch('http://127.0.0.1:5000/preguntar', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ pregunta }})
                }})
                .then(r => r.text())
                .then(txt => {{
                    document.getElementById('respuesta').innerText = txt;
                    setTimeout(() => location.reload(), 2000);
                }})
                .catch(err => {{
                    document.getElementById('respuesta').innerText = '❌ Error al contactar la IA.';
                    console.error(err);
                }});
            }}
        </script>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(overlay_html))
    mapa.save(MAP_FILE)
    print(f"✅ Mapa generado en {MAP_FILE}")

@app.route("/origen")
def establecer_origen():
    municipio = request.args.get("m")
    seleccion = leer_seleccion()
    seleccion["origen"] = municipio
    guardar_seleccion(seleccion["origen"], seleccion.get("destino"))
    generar_mapa_interactivo_estable(cargar_municipios())
    webview.windows[0].load_url("file://" + os.path.abspath(MAP_FILE))
    return "✅ Origen actualizado"

@app.route("/destino")
def establecer_destino():
    municipio = request.args.get("m")
    seleccion = leer_seleccion()
    seleccion["destino"] = municipio
    guardar_seleccion(seleccion.get("origen"), seleccion["destino"])
    generar_mapa_interactivo_estable(cargar_municipios())
    webview.windows[0].load_url("file://" + os.path.abspath(MAP_FILE))
    return "✅ Destino actualizado"

@app.route("/reset")
def reset_seleccion():
    inicializar_seleccion()
    generar_mapa_interactivo_estable(cargar_municipios())
    webview.windows[0].load_url("file://" + os.path.abspath(MAP_FILE))
    return "✅ Selección reiniciada"

@app.route("/preguntar", methods=["POST"])
def manejar_pregunta():
    municipios = cargar_municipios()
    data = request.get_json()
    pregunta = data.get("pregunta", "")
    origen, destino = extraer_origen_destino(pregunta, municipios)

    if origen and destino:
        ruta_guardada = buscar_ruta_aprendida(origen, destino)
        if ruta_guardada:
            generar_mapa_interactivo_estable(municipios, ruta_guardada)
            webview.windows[0].load_url("file://" + os.path.abspath(MAP_FILE))
            inicializar_seleccion()
            return f"📚 Ruta aprendida entre {origen} y {destino}"
        else:
            guardar_seleccion(origen, destino)
            return f"🔍 Calculando ruta entre {origen} y {destino}..."
    return "❌ No se encontraron dos municipios en la pregunta."

def iniciar_servidor_flask():
    app.run(port=5000, threaded=True)

def actualizar_mapa_periodicamente(municipios):
    while True:
        seleccion = leer_seleccion()
        origen = seleccion.get("origen")
        destino = seleccion.get("destino")
        if origen and destino:
            try:
                coord_origen = next(m["coordenadas"] for m in municipios if m["nombre"] == origen)
                coord_destino = next(m["coordenadas"] for m in municipios if m["nombre"] == destino)

                ruta_real = calcular_ruta_real(coord_origen, coord_destino, modo="driving-car")

                if ruta_real:
                    coords = ruta_real["coordenadas"]
                    generar_mapa_interactivo_estable(municipios, coords)
                    webview.windows[0].load_url("file://" + os.path.abspath(MAP_FILE))
                    inicializar_seleccion()
                else:
                    print("⚠️ No se pudo calcular la ruta real.")
            except Exception as e:
                print("❌ Error calculando ruta:", e)
        time.sleep(1)

def mostrar_mapa(municipios):
    ruta_html = os.path.abspath(MAP_FILE)
    if not os.path.exists(ruta_html):
        print("❌ No se encontró el archivo del mapa.")
        return

    threading.Thread(target=iniciar_servidor_flask, daemon=True).start()
    threading.Thread(target=actualizar_mapa_periodicamente, args=(municipios,), daemon=True).start()
    webview.create_window("Ruta Inteligente Cundinamarca", ruta_html, width=1200, height=800)
    webview.start()

if __name__ == "__main__":
    municipios = cargar_municipios()
    generar_mapa_interactivo_estable(municipios)
    mostrar_mapa(municipios)