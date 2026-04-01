# Funciones necesarias y uso de paquetes

import osmnx as ox
import folium
import matplotlib
import pandas as pd
import json

def descargar_datos_calles(zona, tipo_calle = "coche"):
    """
    Descarga los datos desde OpenStreetMap.
    Ej. zona = "Algiros, Valencia, Spain"
    tipo_calle = "coche", "peatonal", "bici" o "todo"
    """
    TIPOS_CALLE = {
        "coche": "drive",
        "peatonal": "walk",
        "bici": "bike",
        "todo": "all"
    }
    mapa = ox.graph_from_place(
        zona,
        network_type = TIPOS_CALLE[tipo_calle]
    )
    return mapa
     
def convertir_a_grafo(mapa):
    """
    Convierte el mapa a un grafo (vertices y arcos)
    """
    nodes, edges = ox.graph_to_gdfs(mapa)
    V = nodes.reset_index()[["osmid", "x", "y"]]. \
        rename(columns = {"osmid": "id"})
    E = edges.reset_index()[["name", "u", "v", "length", "highway", "geometry"]]. \
        rename(columns = {"name": "nombre", "u": "origen", \
                          "v": "final","length": "peso", \
                          "highway": "uso", "geometry": "geometria"})
    E["nombre"] = E["nombre"].apply(
        lambda x: " - ".join(x) if isinstance(x, list) else x)
    V, E = reiniciar_indices(V, E)
    return V, E
   
def dibujar_mapa(V, E, nombre_archivo = "mapa.html", base = "CartoBD"):
    """
    Dibuja el grafo a partir de V y E.
    Requiere que E tenga una columna 'geometria' (LineString).
    """
    TIPOS_BASE = {
        "OSM": "OpenStreetMap",
        "CartoBD": "CartoDB positron"
    }
    lat, lon = V["y"].mean(), V["x"].mean()
    m = folium.Map(
        location = (lat, lon),
        zoom_start = 15,
        tiles = TIPOS_BASE[base]
    )
    for _, row in V.iterrows():
        folium.CircleMarker(
            location = (row["y"], row["x"]),
            radius = 3,
            color = "blue",
            fill = True,
            fillColor = "blue",
            fillOpacity = 0.7
        ).add_to(m)
    for _, row in E.iterrows():
        geom = row["geometria"]
        coords = [(y, x) for x, y in geom.coords]
        folium.PolyLine(
            locations = coords,
            color = "red",
            weight = 2,
            tooltip = row.get("nombre", "")
        ).add_to(m)
    m.save(nombre_archivo)
    
def reiniciar_indices(V, E):
    """
    Reinicia los índices de V y E para que sean consecutivos.
    """
    V = V.reset_index(drop = True)
    E = E.reset_index(drop = True)
    mapeo_ids = dict(zip(V["id"].values, range(1, len(V)+1)))
    V["id"] = V["id"].map(mapeo_ids)
    E["origen"] = E["origen"].map(mapeo_ids)
    E["final"] = E["final"].map(mapeo_ids)
    return V, E

def filtrar_calles(V, E, uso_calle = None, quitar_uso_calle = None):
    """
    Filtra las calles por tipo de uso.
    uso_calle o quitar_uso_calle: lista de:
        'secondary', 'residential', 'primary', 'tertiary', 'unclassified',
       'motorway_link', 'living_street', 'motorway', 'tertiary_link'
    """
    if uso_calle:
        E = E[E["uso"].isin(uso_calle)]
    if quitar_uso_calle:
        E = E[~E["uso"].isin(quitar_uso_calle)]
    vertices_en_uso = set(E["origen"]).union(set(E["final"]))
    V = V[V["id"].isin(vertices_en_uso)]
    V, E = reiniciar_indices(V, E)
    return V, E

def exportar_MadnessMad(V, E,
        nombre_archivo = "grafo.json",
        dirigido = True, ponderado = True,
        tamano = [[100, 100], [900, 600]]):
    """
    Exporta V y E al formato JSON de MadnessMad.
    """
    V = V.copy()
    x_min, x_max = V["x"].min(), V["x"].max()
    y_min, y_max = V["y"].min(), V["y"].max()
    escala = min((tamano[1][0] - tamano[0][0]) / (x_max - x_min), \
                    (tamano[1][1] - tamano[0][1]) / (y_max - y_min))
    V["x"] = tamano[0][0] + (V["x"] - x_min) * escala
    V["y"] = tamano[1][1] - (V["y"] - y_min) * escala
    vertices = []
    for _, row in V.iterrows():
        vertices.append({
            "id": f"v{int(row["id"])}",
            "name": f"v{int(row["id"])}",
            "x": float(row["x"]),
            "y": float(row["y"]),
            "color": -1179652,
            "size": 0.2,
            "style": "CIRCLE"
        })
    edges = []
    for _, row in E.iterrows():
        edges.append({
            "id": f"e{int(row.name)}",
            "name": str(row["nombre"]) if pd.notna(row["nombre"]) else "",
            "start": f"v{int(row["origen"])}",
            "end": f"v{int(row["final"])}",
            "weight": float(row["peso"]),
            "style": "DEFAULT",
            "curvature": 0.0,
            "loopAngle": -45.0,
            "loopFactor": 3.0,
            "color": -8281663
        })
    grafo = {
        "vertices": vertices,
        "edges": edges,
        "isDirected": dirigido,
        "isWeighted": ponderado
    }
    with open(nombre_archivo, "w", encoding = "utf-8") as f:
        json.dump(grafo, f, indent = 4, ensure_ascii = False)