"""
ai_client.py — Cliente HTTP que mascotas_serv usa para hablar con el microservicio IA
======================================================================================
Coloca este archivo en:  mascotas_serv/mascotas_app/ai_client.py

Uso desde views.py:
    from .ai_client import analizar_imagen_mascota, AI_SERVICE_URL
"""

import json
import requests
from django.conf import settings

# URL del microservicio FastAPI — configurable en settings.py
# Agrega esto a tu settings.py:
#   AI_SERVICE_URL = "http://localhost:8001"
AI_SERVICE_URL = getattr(settings, "AI_SERVICE_URL", "http://localhost:8006")

TIMEOUT_SEGUNDOS = 30  # MobileNetV2 puede tardar en la primera predicción


def analizar_imagen_mascota(image_bytes: bytes, reportes_existentes: list) -> dict:
    """
    Llama al microservicio de IA con la imagen de la mascota.

    Args:
        image_bytes        : bytes de la imagen a analizar
        reportes_existentes: lista de dicts [{id, vector}, ...]
                             con los vectores ya guardados en la BD

    Returns:
        {
          "ai_prediction": {"breed_es": ..., "breed_en": ..., "confidence": ...},
          "new_vector": [...],           # vector 1280-dim — guárdalo en Reporte.foto_vector
          "database_matches": [          # ordenados por similitud desc
            {"id": int, "similarity": float},  # similarity: 0–100
            ...
          ]
        }

    Raises:
        RuntimeError si el servicio no responde o retorna error.
    """
    endpoint = f"{AI_SERVICE_URL}/analyze"

    payload_vectores = json.dumps(reportes_existentes)

    try:
        response = requests.post(
            endpoint,
            files={"file": ("mascota.jpg", image_bytes, "image/jpeg")},
            data={"existing_vectors": payload_vectores},
            timeout=TIMEOUT_SEGUNDOS,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"No se pudo conectar al servicio de IA en {AI_SERVICE_URL}. "
            "¿Está corriendo? Ejecuta: uvicorn main:app --port 8001"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"El servicio de IA tardó más de {TIMEOUT_SEGUNDOS}s en responder."
        )
    except requests.exceptions.HTTPError as e:
        detalle = response.json().get("detail", str(e)) if response.content else str(e)
        raise RuntimeError(f"Error del servicio de IA: {detalle}")

    return response.json()


def obtener_vectores_existentes() -> list:
    """
    Carga todos los vectores guardados en la BD para pasarlos al microservicio.
    Solo trae reportes que ya tienen vector calculado.

    Retorna: [{id: int, vector: list[float]}, ...]
    """
    from .models import Reporte  # import local para evitar circular

    reportes = Reporte.objects.exclude(foto_vector__isnull=True).exclude(foto_vector=[])
    return [
        {"id": r.pk, "vector": r.foto_vector}
        for r in reportes
        if r.foto_vector  # doble check por si quedó lista vacía
    ]