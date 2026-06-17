"""
utils.py — Helpers compartidos entre views.py y tasks.py
"""
from .models import Reporte

PESO_VISUAL  = 0.65
PESO_TEXTUAL = 0.35


def combinar_scores(matches_visuales: dict, matches_textuales: dict) -> list:
    todos_ids = set(matches_visuales) | set(matches_textuales)
    resultado = []
    for rid in todos_ids:
        visual  = matches_visuales.get(rid, 0.0)
        textual = matches_textuales.get(rid, 0.0)
        if rid not in matches_visuales:
            score_final = textual
        elif rid not in matches_textuales:
            score_final = visual
        else:
            score_final = (visual * PESO_VISUAL) + (textual * PESO_TEXTUAL)
        resultado.append({
            "reporte_id":    rid,
            "score_final":   round(score_final * 100, 1),
            "score_visual":  round(visual  * 100, 1),
            "score_textual": round(textual * 100, 1),
        })
    resultado.sort(key=lambda x: x["score_final"], reverse=True)
    return resultado


def enriquecer_con_datos(matches: list, umbral: float = 40.0) -> list:
    ids = [m["reporte_id"] for m in matches if m["score_final"] >= umbral]
    reportes_map = {r.pk: r for r in Reporte.objects.filter(pk__in=ids)}
    enriquecidos = []
    for m in matches:
        if m["score_final"] < umbral:
            continue
        r = reportes_map.get(m["reporte_id"])
        if not r:
            continue
        enriquecidos.append({
            **m,
            "nombre_mascota": r.nombre_mascota,
            "raza":           r.raza,
            "color":          r.color,
            "tipo_reporte":   r.tipo_reporte,
            "estado_reporte": r.estado_reporte,
            "fech_perdida":   str(r.fech_perdida),
            "latitud":        float(r.latitud),
            "longitud":       float(r.longitud),
            "foto_url_one":   r.foto_url_one,
            "descripcion":    r.descripcion,
        })
    return enriquecidos