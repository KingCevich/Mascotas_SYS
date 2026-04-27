from django.urls import path, include
from .views import lista_reportes, lista_contactos, ReporteViewSet, ContactoViewSet
from . import views 
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'reportes', ReporteViewSet)
router.register(r'contactos', ContactoViewSet)

urlpatterns = [
    path('reportes/', lista_reportes, name='lista_reportes'),
    path('contactos/', lista_contactos, name='lista_contactos'),
    path('api/', include(router.urls)),
]