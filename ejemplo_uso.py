# Descargar datos de calles
# y convertirlos a un grafo para uso en MadnessMad 

#%% Librerías

# ejecutar una vez:
# pip install osmnx folium matplotlib pandas

# funciones necesarias en otro archivo
from utils import *

#%% Descargar datos de las calles

#mapa = descargar_datos_calles("La Carrasca, Algiros, Valencia, Spain", tipo_calle = "coche")
mapa = descargar_datos_calles("Benimaclet, Benimaclet, Valencia, Spain", tipo_calle = "coche")
V, E = convertir_a_grafo(mapa)
#dibujar_mapa(V, E, nombre_archivo = "mapa_desde_VE.html")
V, E = filtrar_calles(V, E, quitar_uso_calle = ["motorway_link", "motorway"])
dibujar_mapa(V, E, nombre_archivo = "mapa_filtrado.html")
exportar_MadnessMad(V, E, nombre_archivo = "grafo.json")

# %%
