from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Reporte, Contacto

@receiver(post_migrate)
def create_default_reportes(sender, **kwargs):
    if sender.name != 'mascotas_app':
        return
    if Reporte.objects.exists():
        return

    reportes_data = [
        # =========================================================
        # DUEÑO 1 (dueno@demo.com, usuario_id=1) – Reportes normales
        # =========================================================
        {
            "reporte": {
                "usuario_id": 1,
                "tipo_reporte": "Perdido",
                "nombre_mascota": "Max",
                "raza": "LABRADOR",
                "color": "Amarillo",
                "tamano": 30.5,
                "fech_perdida": "2025-05-01",
                "hora_perdida": "14:30:00",
                "latitud": -33.456200,
                "longitud": -70.648500,
                "descripcion": "Perro amigable con collar azul. Responde al nombre Max.",
                "foto_url_one": "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
                "en_adopcion": False,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56912345678", "email": "dueno@demo.com", "whatsapp_enable": True}
        },
        {
            "reporte": {
                "usuario_id": 1,
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Luna",
                "raza": "MESTIZO",
                "color": "Negro con blanco",
                "tamano": 4.5,
                "fech_perdida": "2025-05-03",
                "hora_perdida": None,
                "latitud": -33.461000,
                "longitud": -70.655000,
                "descripcion": "Gata encontrada en calle Ossa, muy dócil. Parece tener dueño.",
                "foto_url_one": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400",
                "en_adopcion": False,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56911111111", "email": "dueno@demo.com", "whatsapp_enable": False}
        },

        # =========================================================
        # DUEÑO 2 (juan@dueno.cl, usuario_id=8) – Reportes normales
        # =========================================================
        {
            "reporte": {
                "usuario_id": 8,
                "tipo_reporte": "Perdido",
                "nombre_mascota": "Toby",
                "raza": "POODLE",
                "color": "Blanco",
                "tamano": 8.0,
                "fech_perdida": "2025-06-01",
                "hora_perdida": "08:00:00",
                "latitud": -33.440000,
                "longitud": -70.630000,
                "descripcion": "Poodle blanco perdido cerca del parque. Lleva collar rojo.",
                "foto_url_one": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
                "en_adopcion": False,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56999887766", "email": "juan@dueno.cl", "whatsapp_enable": True}
        },
        {
            "reporte": {
                "usuario_id": 8,
                "tipo_reporte": "Avistado",
                "nombre_mascota": "Pelusa",
                "raza": "GOLDEN RETRIEVER",
                "color": "Dorado",
                "tamano": 28.0,
                "fech_perdida": "2025-06-02",
                "hora_perdida": None,
                "latitud": -33.450000,
                "longitud": -70.640000,
                "descripcion": "Golden retriever avistado cerca del mall. Muy amistoso.",
                "foto_url_one": "https://images.unsplash.com/photo-1633722715463-d30f4f325e24?w=400",
                "en_adopcion": False,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56999887766", "email": "juan@dueno.cl", "whatsapp_enable": False}
        },

        # =========================================================
        # REFUGIO DEMO (refugio@demo.com, usuario_id=2) – Adopciones y un reporte normal
        # =========================================================
        # -- ADOPCIÓN: Michi (descripción larga, sin coordenadas reales) --
        {
            "reporte": {
                "usuario_id": 2,
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Michi",
                "raza": "SIAMES",
                "color": "Beige",
                "tamano": 4.5,
                "fech_perdida": "2025-05-06",
                "hora_perdida": None,
                "latitud": 0,
                "longitud": 0,
                "descripcion": (
                    "Michi es un gato siamés de aproximadamente 2 años, rescatado de la calle. "
                    "Es extremadamente cariñoso y disfruta pasar horas en el regazo. "
                    "Se lleva bien con otros gatos y perros tranquilos. "
                    "Está esterilizado, vacunado y desparasitado. "
                    "Busca un hogar donde le den mucho amor y espacio para dormitar al sol."
                ),
                "foto_url_one": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d?w=400",
                "en_adopcion": True,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56922222222", "email": "refugio@demo.com", "whatsapp_enable": True}
        },
        # -- ADOPCIÓN: Rex (descripción larga) --
        {
            "reporte": {
                "usuario_id": 2,
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Rex",
                "raza": "PASTOR ALEMÁN",
                "color": "Negro y fuego",
                "tamano": 35.0,
                "fech_perdida": "2025-05-10",
                "hora_perdida": None,
                "latitud": 0,
                "longitud": 0,
                "descripcion": (
                    "Rex es un pastor alemán de 4 años, muy obediente y protector. "
                    "Sabe comandos básicos (sentado, quieto, junto) y disfruta los paseos largos. "
                    "Es ideal para una familia activa o una persona con experiencia en perros grandes. "
                    "Está castrado y al día con sus vacunas. "
                    "Necesita un hogar con patio amplio y tiempo para ejercicio diario."
                ),
                "foto_url_one": "https://images.unsplash.com/photo-1589941013453-ec89a33b3985?w=400",
                "en_adopcion": True,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56922222222", "email": "refugio@demo.com", "whatsapp_enable": False}
        },
        # -- REPORTE NORMAL del refugio: Bella (perdida) --
        {
            "reporte": {
                "usuario_id": 2,
                "tipo_reporte": "Perdido",
                "nombre_mascota": "Bella",
                "raza": "BORDER COLLIE",
                "color": "Blanco y negro",
                "tamano": 22.0,
                "fech_perdida": "2025-06-05",
                "hora_perdida": "16:00:00",
                "latitud": -33.462000,
                "longitud": -70.651000,
                "descripcion": "Border collie perdida durante paseo. Tiene microchip. Muy activa.",
                "foto_url_one": "https://images.unsplash.com/photo-1503256207526-0d5d80fa2f47?w=400",
                "en_adopcion": False,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56922222222", "email": "refugio@demo.com", "whatsapp_enable": True}
        },

        # =========================================================
        # FUNDACIÓN HUELLA ANIMAL (huella@demo.com, usuario_id=10) – Adopciones
        # =========================================================
        # -- ADOPCIÓN: Nala --
        {
            "reporte": {
                "usuario_id": 10,
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Nala",
                "raza": "CHIHUAHUA",
                "color": "Canela",
                "tamano": 2.5,
                "fech_perdida": "2025-06-10",
                "hora_perdida": None,
                "latitud": 0,
                "longitud": 0,
                "descripcion": (
                    "Nala es una chihuahua de 3 años, tamaño pequeño pero con un corazón enorme. "
                    "Es muy juguetona y le encanta seguir a su persona favorita por toda la casa. "
                    "Prefiere hogares sin niños pequeños y se adapta bien a departamentos. "
                    "Está esterilizada y vacunada. "
                    "Ideal para compañía y regaloneo constante."
                ),
                "foto_url_one": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=400",
                "en_adopcion": True,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56977777777", "email": "huella@demo.com", "whatsapp_enable": True}
        },
        # -- ADOPCIÓN: Simón --
        {
            "reporte": {
                "usuario_id": 10,
                "tipo_reporte": "Encontrado",
                "nombre_mascota": "Simón",
                "raza": "MAINE COON",
                "color": "Gris atigrado",
                "tamano": 7.0,
                "fech_perdida": "2025-06-12",
                "hora_perdida": None,
                "latitud": 0,
                "longitud": 0,
                "descripcion": (
                    "Simón es un imponente Maine Coon de 5 años, pelo gris atigrado y ojos verdes. "
                    "Es tranquilo, independiente pero muy leal. Disfruta trepar y observar desde lo alto. "
                    "Convive bien con otros gatos y perros mansos. "
                    "Está castrado y con sus controles al día. "
                    "Busca un hogar con espacio interior y mucha altura para explorar."
                ),
                "foto_url_one": "https://images.unsplash.com/photo-1608848461950-0fe51dfc41cb?w=400",
                "en_adopcion": True,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56977777777", "email": "huella@demo.com", "whatsapp_enable": False}
        },

        # =========================================================
        # VETERINARIA BÍO BÍO (vetbiobio@demo.com, usuario_id=11) – Reporte normal
        # =========================================================
        {
            "reporte": {
                "usuario_id": 11,
                "tipo_reporte": "Avistado",
                "nombre_mascota": "Copito",
                "raza": "BICHON FRISÉ",
                "color": "Blanco",
                "tamano": 6.0,
                "fech_perdida": "2025-06-15",
                "hora_perdida": "12:00:00",
                "latitud": -33.490000,
                "longitud": -70.680000,
                "descripcion": "Bichon frisé avistado deambulando, parece perdido. Sin collar.",
                "foto_url_one": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=400",
                "en_adopcion": False,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56988888888", "email": "vetbiobio@demo.com", "whatsapp_enable": True}
        },

        # =========================================================
        # MUNICIPALIDAD (municipalidad@demo.com, usuario_id=4) – Reporte normal
        # =========================================================
        {
            "reporte": {
                "usuario_id": 4,
                "tipo_reporte": "Avistado",
                "nombre_mascota": "Sombra",
                "raza": "QUILTRO",
                "color": "Negro",
                "tamano": 15.0,
                "fech_perdida": "2025-06-18",
                "hora_perdida": "10:00:00",
                "latitud": -33.455000,
                "longitud": -70.645000,
                "descripcion": "Perro quiltro negro visto rondando la plaza municipal. Parece hambriento.",
                "foto_url_one": "https://images.unsplash.com/photo-1568572933382-74d440642117?w=400",
                "en_adopcion": False,
                "adoptado": False,
                "estado_reporte": "Activo",
            },
            "contacto": {"telefono": "+56944444444", "email": "municipalidad@demo.com", "whatsapp_enable": True}
        },
    ]

    for item in reportes_data:
        reporte = Reporte.objects.create(**item["reporte"])
        Contacto.objects.create(reporte=reporte, **item["contacto"])

    print("<<<<Reportes y contactos de prueba creados>>>>")