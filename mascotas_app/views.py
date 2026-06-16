from django.shortcuts import render
from .models import Reporte, Contacto

# from rest_framework.views import APIView
from rest_framework import status, viewsets, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import ContactoSerializer, ReporteSerializer
from .auth import get_token_from_request, validate_token
from .similarity import buscar_coincidencias
from .ai_client import analizar_imagen_mascota, obtener_vectores_existentes


# Create your views here.

PESO_VISUAL  = 0.65
PESO_TEXTUAL = 0.35
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _combinar_scores(matches_visuales: dict, matches_textuales: dict) -> list:
    """
    Fusiona los scores visuales (IA) y textuales (similarity.py) en un
    único score final ponderado por PESO_VISUAL y PESO_TEXTUAL.
 
    matches_visuales  : {reporte_id: similitud 0.0–1.0}
    matches_textuales : {reporte_id: score    0.0–1.0}
 
    Retorna lista ordenada de mayor a menor score_final.
    """
    todos_ids = set(matches_visuales) | set(matches_textuales)
    resultado = []
 
    for rid in todos_ids:
        visual  = matches_visuales.get(rid, 0.0)
        textual = matches_textuales.get(rid, 0.0)
 
        # Si solo hay un tipo de score, el peso del otro se redistribuye
        # para no penalizar reportes que no tienen foto todavía
        if rid not in matches_visuales:
            score_final = textual
        elif rid not in matches_textuales:
            score_final = visual
        else:
            score_final = (visual * PESO_VISUAL) + (textual * PESO_TEXTUAL)
 
        resultado.append({
            "reporte_id":    rid,
            "score_final":   round(score_final * 100, 1),   # 0–100 %
            "score_visual":  round(visual  * 100, 1),
            "score_textual": round(textual * 100, 1),
        })
 
    resultado.sort(key=lambda x: x["score_final"], reverse=True)
    return resultado
 
 
def _enriquecer_con_datos(matches: list, umbral: float = 40.0) -> list:
    """
    Agrega los datos del Reporte a cada match y filtra por umbral.
    """
    ids = [m["reporte_id"] for m in matches if m["score_final"] >= umbral]
    reportes_map = {
        r.pk: r for r in Reporte.objects.filter(pk__in=ids)
    }
 
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

#HTML 
def lista_reportes(request):
    reportes = Reporte.objects.all()
    return render(request, 'reportes.html', {'reportes': reportes})

def lista_contactos(request):
    contactos = Contacto.objects.all()
    return render(request, 'contactos.html', {'contactos': contactos})

#Permisos de realizacion de CRUD dependiendo de Rol del Usuario, solo Admin puede modificar o eliminar, cualquier usuario puede crear o leer
class TokenRequiredMixin:
    def initial(self, request, *args, **kwargs):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            token = get_token_from_request(request)
            valid, payload = validate_token(token)
            if not valid:
                raise exceptions.AuthenticationFailed(payload.get('error', 'Token inválido'))

            if request.method in ('PUT', 'PATCH', 'DELETE'):
                if payload.get('rol') != 'Admin':
                    raise exceptions.PermissionDenied('Solo un administrador puede modificar o eliminar.')

            request.auth_payload = payload
        return super().initial(request, *args, **kwargs)


class ReporteViewSet(TokenRequiredMixin, viewsets.ModelViewSet):
    serializer_class = ReporteSerializer

    def get_queryset(self):
        queryset = Reporte.objects.all()

        # Filtro por usuario_id (simple o múltiple con comas)
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            ids = [int(id) for id in usuario_id.split(',')]
            queryset = queryset.filter(usuario_id__in=ids)

        # Filtro por tipo de reporte
        tipo = self.request.query_params.get('tipo_reporte')
        if tipo:
            queryset = queryset.filter(tipo_reporte=tipo)

        # Filtro por adopción
        en_adopcion = self.request.query_params.get('en_adopcion')
        if en_adopcion is not None:
            queryset = queryset.filter(en_adopcion=en_adopcion.lower() == 'true')

        # Filtro por adoptado
        adoptado = self.request.query_params.get('adoptado')
        if adoptado is not None:
            queryset = queryset.filter(adoptado=adoptado.lower() == 'true')

        return queryset

    # -----------------------------------------------------------------------
    # POST /api/reportes/{id}/buscar-coincidencias/
    #
    # Endpoint principal de coincidencias.
    # Recibe una foto (opcional) y combina score visual + textual en uno solo.
    #
    # Con foto:    score_final = 65% visual (IA) + 35% textual (raza/color/geo)
    # Sin foto:    score_final = 100% textual
    # -----------------------------------------------------------------------
    @action(
        detail=True,
        methods=['post'],
        url_path='buscar-coincidencias',
        parser_classes=[MultiPartParser, FormParser],
    )
    def buscar_coincidencias_reporte(self, request, pk=None):
        """
        Busca coincidencias combinando análisis visual (IA) + datos textuales.
 
        Uso (multipart/form-data):
          POST /api/reportes/5/buscar-coincidencias/
          Body (opcional): file = <imagen de la mascota>
 
        Query params opcionales:
          umbral : score mínimo para aparecer en resultados (default 40 = 40%)
          top    : máximo de resultados (default 10)
 
        Flujo con foto:
          1. Manda la imagen al microservicio IA (FastAPI :8001)
          2. Obtiene vector visual + raza detectada
          3. Guarda el vector en Reporte.foto_vector
          4. Calcula score visual contra todos los reportes con foto
          5. Calcula score textual contra todos los reportes
          6. Combina ambos en un score_final ponderado
          7. Retorna lista unificada ordenada
 
        Flujo sin foto:
          - Solo calcula score textual (raza, color, tamaño, ubicación, tipo)
 
        Respuesta:
        {
          "reporte_consultado": { id, nombre_mascota, raza, tipo_reporte },
          "ai_prediction": { breed_es, breed_en, confidence } | null,
          "total_coincidencias": 3,
          "umbral_aplicado": 40.0,
          "coincidencias": [
            {
              "reporte_id": 7,
              "score_final": 88.4,     <- el número que le muestras al usuario
              "score_visual": 91.2,    <- aporte de la foto
              "score_textual": 82.0,   <- aporte de raza/color/geo
              "nombre_mascota": "Max",
              "raza": "Labrador Retriever",
              "color": "Amarillo",
              "tipo_reporte": "Encontrado",
              "estado_reporte": "Activo",
              "fech_perdida": "2025-05-01",
              "latitud": -33.456200,
              "longitud": -70.648500,
              "foto_url_one": "https://...",
              "descripcion": "..."
            },
            ...
          ]
        }
        """
        try:
            reporte = Reporte.objects.get(pk=pk)
        except Reporte.DoesNotExist:
            return Response({"error": "Reporte no encontrado"}, status=status.HTTP_404_NOT_FOUND)
 
        try:
            umbral = float(request.query_params.get('umbral', 40.0))
            top_n  = int(request.query_params.get('top', 10))
        except ValueError:
            return Response({"error": "Parámetros inválidos."}, status=status.HTTP_400_BAD_REQUEST)
 
        ai_prediction   = None
        matches_visuales = {}
 
        # --- Score visual (solo si mandan foto) ---
        if 'file' in request.FILES:
            image_bytes = request.FILES['file'].read()
            vectores_existentes = obtener_vectores_existentes()
 
            try:
                resultado_ia = analizar_imagen_mascota(image_bytes, vectores_existentes)
            except RuntimeError as e:
                return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
 
            ai_prediction = resultado_ia.get("ai_prediction")
 
            # Guardar vector en el reporte para futuras comparaciones
            nuevo_vector = resultado_ia.get("new_vector")
            if nuevo_vector:
                reporte.foto_vector = nuevo_vector
                reporte.save(update_fields=["foto_vector"])
 
            # El FastAPI retorna similarity en 0–100, normalizamos a 0–1
            matches_visuales = {
                m["id"]: m["similarity"] / 100
                for m in resultado_ia.get("database_matches", [])
            }
 
        # --- Score textual (siempre) ---
        # umbral=0 para traer todos y que el filtro final lo maneje _combinar
        todos_textuales = buscar_coincidencias(reporte, umbral=0.0, top_n=9999)
        matches_textuales = {
            m["reporte_id"]: m["score"]
            for m in todos_textuales
        }
 
        # --- Combinar y filtrar ---
        combinados = _combinar_scores(matches_visuales, matches_textuales)
        enriquecidos = _enriquecer_con_datos(combinados, umbral=umbral)
 
        return Response({
            "reporte_consultado": {
                "id":             reporte.pk,
                "nombre_mascota": reporte.nombre_mascota,
                "raza":           reporte.raza,
                "tipo_reporte":   reporte.tipo_reporte,
            },
            "ai_prediction":      ai_prediction,
            "total_coincidencias": len(enriquecidos[:top_n]),
            "umbral_aplicado":    umbral,
            "coincidencias":      enriquecidos[:top_n],
        })
 
    # -----------------------------------------------------------------------
    # POST /api/reportes/preview-coincidencias/
    #
    # Igual que el anterior pero ANTES de guardar el reporte.
    # El usuario llena el formulario, sube la foto, y ve posibles dueños
    # antes de publicar. No guarda nada en la BD.
    # -----------------------------------------------------------------------
    @action(
        detail=False,
        methods=['post'],
        url_path='preview-coincidencias',
        parser_classes=[MultiPartParser, FormParser],
    )
    def preview_coincidencias(self, request):
        """
        Busca coincidencias antes de publicar el reporte.
 
        Uso (multipart/form-data):
          POST /api/reportes/preview-coincidencias/
          Body:
            - file         : imagen (opcional)
            - tipo_reporte : "Perdido" | "Encontrado" | "Avistado"
            - raza         : texto
            - color        : texto
            - tamano       : número
            - latitud      : número
            - longitud     : número
            - (resto de campos del Reporte)
 
        No guarda nada. Retorna coincidencias + raza detectada por la IA.
        """
        # Validar datos del formulario
        serializer = ReporteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        reporte_temp = Reporte(**serializer.validated_data)
 
        try:
            umbral = float(request.query_params.get('umbral', 40.0))
            top_n  = int(request.query_params.get('top', 10))
        except ValueError:
            umbral, top_n = 40.0, 10
 
        ai_prediction    = None
        matches_visuales = {}
 
        # --- Score visual (si hay foto) ---
        if 'file' in request.FILES:
            image_bytes = request.FILES['file'].read()
            vectores_existentes = obtener_vectores_existentes()
 
            try:
                resultado_ia = analizar_imagen_mascota(image_bytes, vectores_existentes)
            except RuntimeError as e:
                return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
 
            ai_prediction = resultado_ia.get("ai_prediction")
            matches_visuales = {
                m["id"]: m["similarity"] / 100
                for m in resultado_ia.get("database_matches", [])
            }
 
        # --- Score textual ---
        todos_textuales = buscar_coincidencias(reporte_temp, umbral=0.0, top_n=9999)
        matches_textuales = {
            m["reporte_id"]: m["score"]
            for m in todos_textuales
        }
 
        # --- Combinar y filtrar ---
        combinados   = _combinar_scores(matches_visuales, matches_textuales)
        enriquecidos = _enriquecer_con_datos(combinados, umbral=umbral)
 
        return Response({
            "mensaje":             "Vista previa — nada fue guardado",
            "ai_prediction":       ai_prediction,
            "total_coincidencias": len(enriquecidos[:top_n]),
            "umbral_aplicado":     umbral,
            "coincidencias":       enriquecidos[:top_n],
        })
 


class ContactoViewSet(TokenRequiredMixin, viewsets.ModelViewSet):
    queryset = Contacto.objects.all()
    serializer_class = ContactoSerializer

