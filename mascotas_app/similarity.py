"""
similarity.py — Motor de coincidencias vectoriales para reportes de mascotas
=============================================================================
Convierte cada Reporte en un vector numérico y calcula similitud de coseno
para encontrar qué reportes existentes coinciden con uno recién publicado.

Vector de características:
  [0]  raza_match        — 1.0 si la raza es igual (case-insensitive), 0.0 si no
  [1]  color_match       — similitud de palabras en el color (Jaccard)
  [2]  tamano_sim        — similitud de tamaño (1 - diff_normalizada)
  [3]  geo_sim           — proximidad geográfica (decay exponencial, radio ~5 km)
  [4]  tipo_compatible   — 1.0 si los tipos de reporte son compatibles entre sí

Retorna un score de 0.0 a 1.0 (se muestra como 0–100 %).
"""

import math
from typing import Optional


# ---------------------------------------------------------------------------
# Pesos por dimensión (deben sumar 1.0 para interpretación limpia)
# ---------------------------------------------------------------------------
PESOS = {
    "raza":   0.35,
    "color":  0.25,
    "tamano": 0.15,
    "geo":    0.15,
    "tipo":   0.10,
}

# Tipos de reporte que "se buscan mutuamente":
# Un reporte "Perdido" busca coincidencia con "Encontrado" o "Avistado"
TIPOS_COMPATIBLES = {
    "Perdido":    {"Encontrado", "Avistado"},
    "Encontrado": {"Perdido"},
    "Avistado":   {"Perdido"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _jaccard_palabras(a: str, b: str) -> float:
    """Similitud Jaccard entre conjuntos de palabras (para colores)."""
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a and not set_b:
        return 1.0
    interseccion = set_a & set_b
    union = set_a | set_b
    return len(interseccion) / len(union)


def _similitud_tamano(t1: Optional[float], t2: Optional[float]) -> float:
    """
    Similitud de tamaño normalizada.
    - Si ambos son None → neutral 0.5
    - Si solo uno es None → 0.5 (sin penalizar)
    - Diferencia se normaliza sobre un rango de 0–80 kg
    """
    if t1 is None or t2 is None:
        return 0.5
    diff = abs(float(t1) - float(t2))
    RANGO_MAX = 80.0
    return max(0.0, 1.0 - diff / RANGO_MAX)


def _similitud_geo(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Similitud geográfica con decay exponencial.
    - Distancia 0 km  → 1.0
    - Distancia 2 km  → ~0.74
    - Distancia 5 km  → ~0.37
    - Distancia 10 km → ~0.14
    - Reportes en (0,0) son de adopción → retorna 0.5 (neutral)
    """
    # Coordenadas nulas = adopción, sin ubicación real
    if (lat1 == 0 and lon1 == 0) or (lat2 == 0 and lon2 == 0):
        return 0.5

    # Fórmula de Haversine simplificada (suficiente para distancias cortas)
    R = 6371.0  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    distancia_km = 2 * R * math.asin(math.sqrt(a))

    # Decay exponencial: e^(-d/λ) con λ = 5 km
    LAMBDA = 5.0
    return math.exp(-distancia_km / LAMBDA)


def _tipo_compatible(tipo_nuevo: str, tipo_existente: str) -> float:
    """1.0 si los tipos son complementarios, 0.0 si no."""
    compatibles = TIPOS_COMPATIBLES.get(tipo_nuevo, set())
    return 1.0 if tipo_existente in compatibles else 0.0


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def calcular_coincidencia(reporte_nuevo, reporte_existente) -> float:
    """
    Calcula el score de coincidencia entre dos instancias de Reporte.
    Retorna un float entre 0.0 y 1.0.

    'reporte_nuevo'    — el reporte recién publicado (o el que se consulta)
    'reporte_existente'— un reporte de la BD contra el que comparamos
    """
    # No comparar un reporte consigo mismo
    if reporte_nuevo.pk == reporte_existente.pk:
        return 0.0

    scores = {}

    # 1. Raza
    raza_n = (reporte_nuevo.raza or "").strip().lower()
    raza_e = (reporte_existente.raza or "").strip().lower()
    scores["raza"] = 1.0 if raza_n and raza_e and raza_n == raza_e else 0.0

    # 2. Color
    color_n = reporte_nuevo.color or ""
    color_e = reporte_existente.color or ""
    scores["color"] = _jaccard_palabras(color_n, color_e)

    # 3. Tamaño
    scores["tamano"] = _similitud_tamano(reporte_nuevo.tamano, reporte_existente.tamano)

    # 4. Geolocalización
    scores["geo"] = _similitud_geo(
        float(reporte_nuevo.latitud),  float(reporte_nuevo.longitud),
        float(reporte_existente.latitud), float(reporte_existente.longitud),
    )

    # 5. Compatibilidad de tipo
    scores["tipo"] = _tipo_compatible(
        reporte_nuevo.tipo_reporte,
        reporte_existente.tipo_reporte,
    )

    # Score ponderado final
    score_total = sum(PESOS[k] * v for k, v in scores.items())
    return round(score_total, 4)


def buscar_coincidencias(reporte_nuevo, umbral: float = 0.40, top_n: int = 10):
    """
    Busca todos los reportes en la BD y retorna los más parecidos al nuevo.

    Args:
        reporte_nuevo: instancia de Reporte (puede ser sin guardar aún)
        umbral:        score mínimo para incluir en resultados (default 40 %)
        top_n:         máximo de resultados a retornar

    Returns:
        Lista de dicts:
        [
          {
            "reporte_id": int,
            "score": float (0.0–1.0),
            "porcentaje": float (0–100),
            "detalle": { ... datos del reporte ... }
          },
          ...
        ]  ordenada de mayor a menor score.
    """
    from .models import Reporte  # import aquí para evitar circular

    resultados = []

    candidatos = Reporte.objects.exclude(pk=reporte_nuevo.pk if reporte_nuevo.pk else -1)

    for existente in candidatos:
        score = calcular_coincidencia(reporte_nuevo, existente)
        if score >= umbral:
            resultados.append({
                "reporte_id": existente.pk,
                "score": score,
                "porcentaje": round(score * 100, 1),
                "nombre_mascota": existente.nombre_mascota,
                "raza": existente.raza,
                "color": existente.color,
                "tipo_reporte": existente.tipo_reporte,
                "estado_reporte": existente.estado_reporte,
                "fech_perdida": str(existente.fech_perdida),
                "latitud": float(existente.latitud),
                "longitud": float(existente.longitud),
                "foto_url_one": existente.foto_url_one,
                "descripcion": existente.descripcion,
            })

    # Ordenar descendente por score
    resultados.sort(key=lambda x: x["score"], reverse=True)

    return resultados[:top_n]