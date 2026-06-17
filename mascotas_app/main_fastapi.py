"""
main.py — Microservicio de IA para reconocimiento visual de mascotas

Corre en: uvicorn main:app --host 0.0.0.0 --port 8001 --reload

Endpoints:
  POST /analyze   — recibe imagen + vectores existentes → raza + similitudes
  GET  /health    — health check
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import json
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
    decode_predictions,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="API de Reconocimiento Visual de Mascota")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # en prod restringir a la IP de mascotas_serv
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Modelos (se cargan una sola vez al arrancar el servicio)
# ---------------------------------------------------------------------------
print("Cargando modelos MobileNetV2...")
model_vector     = MobileNetV2(weights="imagenet", include_top=False, pooling="avg")
model_classifier = MobileNetV2(weights="imagenet", include_top=True)
print("Modelos listos.")

# ---------------------------------------------------------------------------
# Diccionario de razas EN → ES
# ---------------------------------------------------------------------------
DICCIONARIO_RAZAS = {
    "Chihuahua":           "Chihuahua",
    "Pomeranian":          "Pomerania",
    "French_bulldog":      "Bulldog Francés",
    "beagle":              "Beagle",
    "golden_retriever":    "Golden Retriever",
    "Labrador_retriever":  "Labrador Retriever",
    "German_shepherd":     "Pastor Alemán",
    "miniature_schnauzer": "Schnauzer Miniatura",
    "shih-tzu":            "Shih Tzu",
    "Yorkshire_terrier":   "Yorkshire Terrier",
    "pug":                 "Carlino",
    "Siamese_cat":         "Gato Siamés",
    "Persian_cat":         "Gato Persa",
    "tabby":               "Gato Común",
    "Egyptian_cat":        "Gato Egipcio",
}


def traducir(nombre_en: str) -> str:
    return DICCIONARIO_RAZAS.get(nombre_en, nombre_en.replace("_", " ").title())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def prepare_image(image_bytes: bytes) -> np.ndarray:
    """Convierte bytes de imagen en tensor listo para MobileNetV2."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return preprocess_input(img_array)


def calcular_similitud(v1: list, v2: list) -> float:
    """Similitud coseno entre dos vectores. Retorna 0–100."""
    v1, v2 = np.array(v1), np.array(v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm == 0:
        return 0.0
    return float((np.dot(v1, v2) / norm) * 100)


    # ---------------------------------------------------------------------------
    # Endpoints
    # ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Verifica que el servicio esté vivo."""
    return {"status": "ok", "servicio": "IA Mascotas"}


@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    existing_vectors: str = Form("[]"),
):
    """
    Analiza una imagen de mascota.

    Parámetros (multipart/form-data):
      - file             : imagen (jpg, png, webp…)
      - existing_vectors : JSON con lista de {id, vector} de reportes existentes
                           Ejemplo: [{"id": 1, "vector": [0.1, 0.2, ...]}, ...]
                           Si se manda vacío ("[]") solo retorna predicción y vector.

    Respuesta:
    {
      "ai_prediction": {
        "breed_es": "Labrador Retriever",
        "breed_en": "Labrador_retriever",
        "confidence": 87.34          // % confianza del modelo
      },
      "new_vector": [...],            // vector de 1280 dimensiones — GUÁRDALO en la BD
      "database_matches": [           // coincidencias ordenadas por similitud desc
        {"id": 3, "similarity": 94.2},
        {"id": 7, "similarity": 81.5},
        ...
      ]
    }
    """
    # --- Leer y procesar imagen ---
    try:
        bytes_data = await file.read()
        if not bytes_data:
            raise HTTPException(status_code=400, detail="El archivo está vacío.")

        input_tensor = prepare_image(bytes_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al procesar la imagen: {e}")

    # --- Predicción de raza ---
    try:
        preds = model_classifier.predict(input_tensor, verbose=0)
        top_pred = decode_predictions(preds, top=1)[0][0]
        raza_en     = top_pred[1]
        confianza   = round(float(top_pred[2]) * 100, 2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en clasificación: {e}")

    # --- Extracción de vector de características ---
    try:
        vector_nuevo = model_vector.predict(input_tensor, verbose=0)[0].tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo vector: {e}")

    # --- Comparar con vectores existentes ---
    try:
        registry = json.loads(existing_vectors)
        if not isinstance(registry, list):
            raise ValueError("existing_vectors debe ser una lista JSON.")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"existing_vectors inválido: {e}")

    matches = []
    for item in registry:
        if "id" not in item or "vector" not in item:
            continue  # saltar items mal formados silenciosamente
        similitud = calcular_similitud(vector_nuevo, item["vector"])
        matches.append({
            "id":         item["id"],
            "similarity": round(similitud, 2),
        })

    matches.sort(key=lambda x: x["similarity"], reverse=True)

    return {
        "ai_prediction": {
            "breed_es":   traducir(raza_en),
            "breed_en":   raza_en,
            "confidence": confianza,
        },
        "new_vector":       vector_nuevo,
        "database_matches": matches,
    }