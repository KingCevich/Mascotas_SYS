from django.shortcuts import render
from .models import Reporte, Contacto

# Create your views here.
def lista_reportes(request):
    reportes = Reporte.objects.all()
    return render(request, 'reportes.html', {'reportes': reportes})

def lista_contactos(request):
    contactos = Contacto.objects.all()
    return render(request, 'contactos.html', {'contactos': contactos})