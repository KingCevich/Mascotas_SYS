import base64
import logging
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


def _notificar(usuario_id: int, tipo_evento: str, variables: dict, datos: dict = None):
    NOTIF_URL = getattr(settings, "NOTIFICACIONES_SERVICE_URL", "http://127.0.0.1:8005")

    try:
        requests.post(
            f"{NOTIF_URL}/api/notificaciones/enviar/",
            json={
                "usuario_id":        usuario_id,
                "tipo_evento":       tipo_evento,
                "variables":         variables,
                "datos_adicionales": datos or {},
            },
            timeout=5,
        )
    except Exception as e:
        logger.warning(f"No se pudo notificar al usuario {usuario_id}: {e}")


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def analizar_reporte_async(self, reporte_id: int, image_bytes_b64: str, usuario_id: int):
    from .models import Reporte
    from .ai_client import analizar_imagen_mascota, obtener_vectores_existentes
    from .similarity import buscar_coincidencias
    from .utils import combinar_scores

    try:
        reporte = Reporte.objects.get(pk=reporte_id)
    except Reporte.DoesNotExist:
        logger.error(f"Reporte {reporte_id} no encontrado")
        return

    nombre = reporte.nombre_mascota

    # 1. Llamar a la IA
    try:
        image_bytes         = base64.b64decode(image_bytes_b64)
        vectores_existentes = obtener_vectores_existentes()
        resultado_ia        = analizar_imagen_mascota(image_bytes, vectores_existentes)
    except Exception as exc:
        logger.error(f"Error IA reporte {reporte_id}: {exc}")
        _notificar(usuario_id, "ia_fallida", {"nombre": nombre}, {"reporte_id": reporte_id})
        raise self.retry(exc=exc)

    # 2. Guardar vector
    nuevo_vector = resultado_ia.get("new_vector")
    if nuevo_vector:
        reporte.foto_vector = nuevo_vector
        reporte.save(update_fields=["foto_vector"])
        logger.info(f"Vector guardado para reporte {reporte_id}")

    # 3. Combinar scores usando utils
    matches_visuales = {
        m["id"]: m["similarity"] / 100
        for m in resultado_ia.get("database_matches", [])
    }
    todos_textuales   = buscar_coincidencias(reporte, umbral=0.0, top_n=9999)
    matches_textuales = {m["reporte_id"]: m["score"] for m in todos_textuales}

    combinados        = combinar_scores(matches_visuales, matches_textuales)
    top_coincidencias = [c for c in combinados if c["score_final"] >= 40.0]

    # 4. Notificar
    breed_es = resultado_ia.get("ai_prediction", {}).get("breed_es", reporte.raza)

    if top_coincidencias:
        _notificar(
            usuario_id, "ia_completada",
            {"nombre": nombre, "cantidad": len(top_coincidencias), "score": top_coincidencias[0]["score_final"]},
            {"reporte_id": reporte_id, "raza_detectada": breed_es, "coincidencias": top_coincidencias[:5]},
        )
    else:
        _notificar(
            usuario_id, "ia_sin_coincidencias",
            {"nombre": nombre},
            {"reporte_id": reporte_id, "raza_detectada": breed_es},
        )

    logger.info(f"✅ Reporte {reporte_id} — {len(top_coincidencias)} coincidencias")
    return {"reporte_id": reporte_id, "coincidencias": len(top_coincidencias), "raza_detectada": breed_es}