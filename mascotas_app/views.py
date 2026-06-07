from django.shortcuts import render
from .models import Reporte, Contacto

from rest_framework.views import APIView
from rest_framework import status, viewsets, exceptions
from rest_framework.response import Response
from .serializers import ContactoSerializer, ReporteSerializer
from .auth import get_token_from_request, validate_token


# Create your views here.
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

class ContactoViewSet(TokenRequiredMixin, viewsets.ModelViewSet):
    queryset = Contacto.objects.all()
    serializer_class = ContactoSerializer


# class ReporteAPIView(APIView):
#     def get(self, request):
#         reportes = Reporte.objects.all()
#         serializer = ReporteSerializer(reportes, many=True)
#         return Response(serializer.data)
    
#     def post(self, request):
#         serializer = ReporteSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     def put(self, request, pk):
#         try:
#             reporte = Reporte.objects.get(pk=pk)
#         except Reporte.DoesNotExist:
#             return Response({"error":"reporte no encontrado"}, status=status.HTTP_404_NOT_FOUND)

#         serializer = ReporteSerializer(reporte, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     def delete(self, request, pk):
#         try:
#             reporte = Reporte.objects.get(pk=pk)
#         except Reporte.DoesNotExist:
#             return Response({"error":"reporte no encontrado"}, status=status.HTTP_404_NOT_FOUND)

#         reporte.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)