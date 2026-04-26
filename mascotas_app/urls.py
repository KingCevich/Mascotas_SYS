from django.urls import path, include
from .views import lista_reportes, lista_contactos, ReporteViewSet
from . import views 
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'reportes', ReporteViewSet)
router.register(r'contactos', views.ContactoViewSet)

urlpatterns = [
    path('reportes/', lista_reportes, name='lista_reportes'),
    path('contactos/', lista_contactos, name='lista_contactos'),
    path('api/', include(router.urls)),
]