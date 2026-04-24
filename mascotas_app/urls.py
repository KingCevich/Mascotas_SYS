from django.urls import path
from .views import lista_reportes, lista_contactos

urlpatterns = [
    path('reportes/', lista_reportes, name='lista_reportes'),
    path('contactos/', lista_contactos, name='lista_contactos'),
]