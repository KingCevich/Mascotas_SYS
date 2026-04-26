from django.shortcuts import render
from .models import Reporte, Contacto

from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.response import Response
from .serializers import ContactoSerializer, ReporteSerializer


# Create your views here.
def lista_reportes(request):
    reportes = Reporte.objects.all()
    return render(request, 'reportes.html', {'reportes': reportes})

def lista_contactos(request):
    contactos = Contacto.objects.all()
    return render(request, 'contactos.html', {'contactos': contactos})


class ReporteViewSet(viewsets.ModelViewSet):
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer

class ContactoViewSet(viewsets.ModelViewSet):
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