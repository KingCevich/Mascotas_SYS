import base64
import logging
import requests

from django.shortcuts import render
from django.conf import settings
from rest_framework import status, viewsets, exceptions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Reporte, Contacto
from .serializers import ContactoSerializer, ReporteSerializer
from .auth import get_token_from_request, validate_token
from .similarity import buscar_coincidencias
from .ai_client import analizar_imagen_mascota, obtener_vectores_existentes
from .utils import combinar_scores, enriquecer_con_datos

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: notificar eventos síncronos (reporte creado / fallido)
# ---------------------------------------------------------------------------

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
            timeout=3,
        )
    except Exception as e:
        logger.warning(f"No se pudo notificar: {e}")


# ---------------------------------------------------------------------------
# HTML views
# ---------------------------------------------------------------------------

def lista_reportes(request):
    return render(request, 'reportes.html', {'reportes': Reporte.objects.all()})

def lista_contactos(request):
    return render(request, 'contactos.html', {'contactos': Contacto.objects.all()})


# ---------------------------------------------------------------------------
# Auth mixin
# ---------------------------------------------------------------------------

class TokenRequiredMixin:
    def initial(self, request, *args, **kwargs):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            token = get_token_from_request(request)

            # #temporal
            # if not token:
            #     super().initial(request, *args, **kwargs)
            #     return
            
            valid, payload = validate_token(token)
            if not valid:
                raise exceptions.AuthenticationFailed(payload.get('error', 'Token inválido'))
            if request.method in ('PUT', 'PATCH', 'DELETE'):
                if payload.get('rol') != 'Admin':
                    raise exceptions.PermissionDenied('Solo un administrador puede modificar o eliminar.')
            request.auth_payload = payload
        return super().initial(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# ViewSet Reportes
# ---------------------------------------------------------------------------

class ReporteViewSet(TokenRequiredMixin, viewsets.ModelViewSet):
    serializer_class = ReporteSerializer

    def get_queryset(self):
        qs = Reporte.objects.all()
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            ids = [int(i) for i in usuario_id.split(',')]
            qs = qs.filter(usuario_id__in=ids)
        tipo = self.request.query_params.get('tipo_reporte')
        if tipo:
            qs = qs.filter(tipo_reporte=tipo)
        en_adopcion = self.request.query_params.get('en_adopcion')
        if en_adopcion is not None:
            qs = qs.filter(en_adopcion=en_adopcion.lower() == 'true')
        adoptado = self.request.query_params.get('adoptado')
        if adoptado is not None:
            qs = qs.filter(adoptado=adoptado.lower() == 'true')
        return qs

    def create(self, request, *args, **kwargs):
        """
        POST /api/reportes/
        Guarda el reporte, responde inmediato y encola la IA con Celery.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_bytes = None
        if 'file' in request.FILES:
            image_bytes = request.FILES['file'].read()

        reporte    = serializer.save()
        if not image_bytes and reporte.foto_url_one:
            try:
                import requests as req
                r = req.get(reporte.foto_url_one, timeout=10)
                if r.status_code == 200:
                    image_bytes = r.content
            except Exception as e:
                logger.warning(f"No se pudo descargar imagen: {e}")
                
        usuario_id = getattr(request, 'auth_payload', {}).get('user_id') \
             or getattr(request, 'auth_payload', {}).get('usuario_id') \
             or request.data.get('usuario_id')


        # Notificar que el reporte se publicó
        if usuario_id:
            _notificar(usuario_id, "reporte_creado",
                       {"nombre": reporte.nombre_mascota},
                       {"reporte_id": reporte.pk})

        # Encolar IA en background si hay foto
        ia_async = False
        if image_bytes and usuario_id:
            try:
                from .tasks import analizar_reporte_async
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                analizar_reporte_async.delay(reporte.pk, image_b64, usuario_id)

                ia_async = True

            except Exception as e:


                logger.warning(f"No se pudo encolar tarea IA: {e}")

        return Response(
            {
                "reporte": self.get_serializer(reporte).data,
                "mensaje": "Reporte publicado. La IA analizará la foto en unos segundos."
                           if ia_async else "Reporte publicado.",
                "ia_async": ia_async,
            },
            status=status.HTTP_201_CREATED,
        )

    # -----------------------------------------------------------------------
    # POST /api/reportes/{id}/buscar-coincidencias/
    # Búsqueda manual y síncrona — el usuario la pide explícitamente
    # -----------------------------------------------------------------------
    @action(detail=True, methods=['post'], url_path='buscar-coincidencias',
            parser_classes=[MultiPartParser, FormParser])
    def buscar_coincidencias_reporte(self, request, pk=None):
        try:
            reporte = Reporte.objects.get(pk=pk)
        except Reporte.DoesNotExist:
            return Response({"error": "Reporte no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        try:
            umbral = float(request.query_params.get('umbral', 40.0))
            top_n  = int(request.query_params.get('top', 10))
        except ValueError:
            return Response({"error": "Parámetros inválidos."}, status=status.HTTP_400_BAD_REQUEST)

        ai_prediction    = None
        matches_visuales = {}

        if 'file' in request.FILES:
            image_bytes = request.FILES['file'].read()
            try:
                resultado_ia  = analizar_imagen_mascota(image_bytes, obtener_vectores_existentes())
            except RuntimeError as e:
                return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            ai_prediction = resultado_ia.get("ai_prediction")
            nuevo_vector  = resultado_ia.get("new_vector")
            if nuevo_vector:
                reporte.foto_vector = nuevo_vector
                reporte.save(update_fields=["foto_vector"])

            matches_visuales = {m["id"]: m["similarity"] / 100
                                for m in resultado_ia.get("database_matches", [])}

        todos_textuales   = buscar_coincidencias(reporte, umbral=0.0, top_n=9999)
        matches_textuales = {m["reporte_id"]: m["score"] for m in todos_textuales}

        combinados   = combinar_scores(matches_visuales, matches_textuales)
        enriquecidos = enriquecer_con_datos(combinados, umbral=umbral)

        return Response({
            "reporte_consultado": {
                "id": reporte.pk, "nombre_mascota": reporte.nombre_mascota,
                "raza": reporte.raza, "tipo_reporte": reporte.tipo_reporte,
            },
            "ai_prediction":       ai_prediction,
            "total_coincidencias": len(enriquecidos[:top_n]),
            "umbral_aplicado":     umbral,
            "coincidencias":       enriquecidos[:top_n],
        })

    # -----------------------------------------------------------------------
    # POST /api/reportes/preview-coincidencias/
    # -----------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='preview-coincidencias',
            parser_classes=[MultiPartParser, FormParser])
    def preview_coincidencias(self, request):
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

        if 'file' in request.FILES:
            image_bytes = request.FILES['file'].read()
            try:
                resultado_ia = analizar_imagen_mascota(image_bytes, obtener_vectores_existentes())
            except RuntimeError as e:
                return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            ai_prediction    = resultado_ia.get("ai_prediction")
            matches_visuales = {m["id"]: m["similarity"] / 100
                                for m in resultado_ia.get("database_matches", [])}

        todos_textuales   = buscar_coincidencias(reporte_temp, umbral=0.0, top_n=9999)
        matches_textuales = {m["reporte_id"]: m["score"] for m in todos_textuales}

        combinados   = combinar_scores(matches_visuales, matches_textuales)
        enriquecidos = enriquecer_con_datos(combinados, umbral=umbral)

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