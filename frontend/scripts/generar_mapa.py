"""Convierte el GeoJSON de los estados de Mexico en trazos SVG listos para usar.

Se ejecuta UNA vez y su salida (`src/paginas/Panorama/geometria.js`) se versiona.
Asi el navegador nunca descarga el GeoJSON ni necesita una libreria de proyeccion:
recibe solo cadenas `d` de `<path>`, que es lo minimo indispensable para dibujar.

Origen de los datos: https://github.com/angelnmara/geojson (mexicoHigh.json),
geometria de dominio publico derivada de fuentes oficiales.

Uso:
    python frontend/scripts/generar_mapa.py ruta/al/mexicoHigh.json
"""
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ANCHO = 1000  # ancho del viewBox; el alto sale de la proporcion real

# Tolerancia de simplificacion, en unidades del viewBox. Subirla adelgaza el
# archivo y redondea las costas; bajarla conserva detalle y pesa mas.
TOLERANCIA = 0.6

# El GeoJSON llama "Mexico" al Estado de Mexico; en el sistema es otra clave.
ALIAS = {"mexico": "estado-de-mexico"}


def slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def mercator(lon: float, lat: float) -> tuple[float, float]:
    """Proyeccion de Mercator. Adecuada para el rango de latitudes de Mexico."""
    x = math.radians(lon)
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def simplificar(puntos: list, tolerancia: float) -> list:
    """Ramer-Douglas-Peucker iterativo.

    Se evita la recursion porque algunas costas traen miles de vertices y
    Python agotaria la pila.
    """
    if len(puntos) < 3:
        return puntos

    conservar = [False] * len(puntos)
    conservar[0] = conservar[-1] = True
    pila = [(0, len(puntos) - 1)]

    while pila:
        inicio, fin = pila.pop()
        if fin <= inicio + 1:
            continue

        ax, ay = puntos[inicio]
        bx, by = puntos[fin]
        dx, dy = bx - ax, by - ay
        norma = math.hypot(dx, dy)

        peor, indice = 0.0, -1
        for i in range(inicio + 1, fin):
            px, py = puntos[i]
            if norma == 0:
                dist = math.hypot(px - ax, py - ay)
            else:
                dist = abs(dy * px - dx * py + bx * ay - by * ax) / norma
            if dist > peor:
                peor, indice = dist, i

        if peor > tolerancia and indice != -1:
            conservar[indice] = True
            pila.append((inicio, indice))
            pila.append((indice, fin))

    return [p for p, mantener in zip(puntos, conservar) if mantener]


def anillos(geometria: dict) -> list:
    """Devuelve todos los anillos exteriores, sin importar si es Polygon o MultiPolygon."""
    tipo = geometria["type"]
    if tipo == "Polygon":
        return [geometria["coordinates"][0]]
    if tipo == "MultiPolygon":
        return [poligono[0] for poligono in geometria["coordinates"]]
    raise ValueError(f"Geometria no contemplada: {tipo}")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    origen = Path(sys.argv[1])
    datos = json.loads(origen.read_text(encoding="utf-8"))

    # Primera pasada: proyectar todo y hallar los limites reales.
    crudos: dict[str, list] = {}
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for elemento in datos["features"]:
        clave = slug(elemento["properties"]["name"])
        clave = ALIAS.get(clave, clave)
        piezas = []
        for anillo in anillos(elemento["geometry"]):
            proyectado = [mercator(lon, lat) for lon, lat in anillo]
            piezas.append(proyectado)
            for x, y in proyectado:
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)
        crudos[clave] = piezas

    escala = ANCHO / (max_x - min_x)
    alto = round((max_y - min_y) * escala, 1)

    # Segunda pasada: llevar a coordenadas del viewBox, simplificar y armar el trazo.
    # La y se invierte porque en SVG crece hacia abajo.
    trazos: dict[str, str] = {}
    for clave, piezas in crudos.items():
        partes = []
        for anillo in piezas:
            puntos = [
                ((x - min_x) * escala, (max_y - y) * escala) for x, y in anillo
            ]
            puntos = simplificar(puntos, TOLERANCIA)
            if len(puntos) < 3:
                continue  # isla demasiado pequena para el nivel de detalle elegido
            d = f"M{puntos[0][0]:.1f} {puntos[0][1]:.1f}"
            d += "".join(f"L{x:.1f} {y:.1f}" for x, y in puntos[1:])
            partes.append(d + "Z")
        if partes:
            trazos[clave] = "".join(partes)

    salida = Path(__file__).resolve().parents[1] / "src/paginas/Panorama/geometria.js"
    cuerpo = ",\n".join(
        f"  '{clave}': '{d}'" for clave, d in sorted(trazos.items())
    )

    salida.write_text(
        "/* GENERADO POR scripts/generar_mapa.py — NO EDITAR A MANO.\n"
        " *\n"
        " * Trazos SVG de los estados de Mexico, ya proyectados (Mercator) y\n"
        " * simplificados. Origen: https://github.com/angelnmara/geojson\n"
        " */\n\n"
        f"export const VIEWBOX = '0 0 {ANCHO} {alto}'\n\n"
        "export const TRAZOS = {\n"
        f"{cuerpo}\n"
        "}\n",
        encoding="utf-8",
    )

    peso = salida.stat().st_size / 1024
    print(f"{len(trazos)} estados -> {salida.name} ({peso:.0f} KB)")
    print(f"viewBox: 0 0 {ANCHO} {alto}")


if __name__ == "__main__":
    main()
