from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Reporte, Contacto

@receiver(post_migrate)
def create_default_reportes(sender, **kwargs):
    if sender.name != 'mascotas_app':  # ← cambia por el nombre real de tu app
        return
    if Reporte.objects.exists():
        return

    reportes_data = [
        {
            "reporte": {
                "tipo_reporte": "Perdido",
                "nombre_mascota": "Max",
                "raza": "LABRADOR",
                "color": "Amarillo",
                "tamano": 30.5,
                "fech_perdida": "2025-05-01",
                "hora_perdida": "14:30:00",
                "latitud": -33.456200,
                "longitud": -70.648500,
                "descripcion": "Perro amigable con collar azul.",
                "foto_url": "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
                "en_adopcion": False, "adoptado": False, "estado_reporte": "Activo",
            },
            # contacto refleja al usuario dueño demo
            "contacto": {"telefono": "+56912345678", "email": "demo@auth.com", "whatsapp_enable": True}
        },
        {
            "reporte": {
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Luna",
                "raza": "MESTIZO",
                "color": "Negro con blanco",
                "tamano": 4.5,
                "fech_perdida": "2025-05-03",
                "hora_perdida": None,
                "latitud": -33.461000,
                "longitud": -70.655000,
                "descripcion": "Gata encontrada en calle Ossa, muy dócil.",
                "foto_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400",
                "en_adopcion": False, "adoptado": False, "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56911111111", "email": "dueno@demo.com", "whatsapp_enable": False}
        },
        {
            "reporte": {
                "tipo_reporte": "Perdido",
                "nombre_mascota": "Rocky",
                "raza": "BULLDOG",
                "color": "Café",
                "tamano": 25.0,
                "fech_perdida": "2025-05-05",
                "hora_perdida": "09:00:00",
                "latitud": -33.450000,
                "longitud": -70.640000,
                "descripcion": "Bulldog con manchas blancas, muy tranquilo.",
                "foto_url": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=400",
                "en_adopcion": False, "adoptado": False, "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56911111111", "email": "dueno@demo.com", "whatsapp_enable": True}
        },
        {
            "reporte": {
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Michi",
                "raza": "SIAMES",
                "color": "Beige",
                "tamano": 4.5,
                "fech_perdida": "2025-05-06",
                "hora_perdida": None,
                "latitud": -33.470000,
                "longitud": -70.660000,
                "descripcion": "Gato siamés encontrado en Las Condes. Busca hogar.",
                "foto_url": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d?w=400",
                "en_adopcion": True, "adoptado": False, "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56922222222", "email": "refugio@demo.com", "whatsapp_enable": True}
        },
        {
            "reporte": {
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Pelusa",
                "raza": "GOLDEN RETRIEVER",
                "color": "Dorado",
                "tamano": 28.0,
                "fech_perdida": "2025-05-07",
                "hora_perdida": None,
                "latitud": -33.458000,
                "longitud": -70.652000,
                "descripcion": "Perrita muy cariñosa, busca hogar permanente.",
                "foto_url": "https://images.unsplash.com/photo-1633722715463-d30f4f325e24?w=400",
                "en_adopcion": True, "adoptado": False, "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56922222222", "email": "refugio@demo.com", "whatsapp_enable": False}
        },
        {
            "reporte": {
                "tipo_reporte": "Avistado",
                "nombre_mascota": "Toby",
                "raza": "POODLE",
                "color": "Blanco",
                "tamano": 8.0,
                "fech_perdida": "2025-05-08",
                "hora_perdida": "17:00:00",
                "latitud": -33.465000,
                "longitud": -70.645000,
                "descripcion": "Poodle avistado cerca del metro.",
                "foto_url": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
                "en_adopcion": False, "adoptado": False, "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56944444444", "email": "municipalidad@demo.com", "whatsapp_enable": True}
        },
    ]

    for item in reportes_data:
        reporte = Reporte.objects.create(**item["reporte"])
        Contacto.objects.create(reporte=reporte, **item["contacto"])

    print("<<<<Reportes y contactos de prueba creados>>>>")