from django.core.management.base import BaseCommand
from mascotas_app.models import Reporte, Contacto
from datetime import date, time

class Command(BaseCommand):
    help = 'Seed the database with demo reportes and contactos'

    def handle(self, *args, **options):
        if Reporte.objects.exists():
            self.stdout.write(self.style.WARNING('Database already has reportes. Skipping seed.'))
            return

        # Crear reportes de ejemplo
        reportes_data = [
            {
                'tipo_reporte': 'Perdido',
                'nombre_mascota': 'Max',
                'raza': 'Labrador',
                'color': 'Marrón',
                'tamano': 70.0,
                'fech_perdida': date.today(),
                'hora_perdida': time(14, 30),
                'latitud': -34.6037,
                'longitud': -58.3816,
                'descripcion': 'Perro perdido en el parque central, responde al nombre de Max.',
                'foto_url': '',
                'en_adopcion': False,
                'adoptado': False,
                'estado_reporte': 'Activo',
            },
            {
                'tipo_reporte': 'Encontrado',
                'nombre_mascota': 'Whiskers',
                'raza': 'Siamés',
                'color': 'Blanco con manchas grises',
                'tamano': 5.0,
                'fech_perdida': date.today(),
                'hora_perdida': time(10, 0),
                'latitud': -34.6118,
                'longitud': -58.3965,
                'descripcion': 'Gato encontrado cerca de la plaza, muy amigable.',
                'foto_url': '',
                'en_adopcion': False,
                'adoptado': False,
                'estado_reporte': 'Activo',
            },
            {
                'tipo_reporte': 'Perdido',
                'nombre_mascota': 'Luna',
                'raza': 'Beagle',
                'color': 'Blanco y negro',
                'tamano': 40.0,
                'fech_perdida': date.today(),
                'hora_perdida': time(16, 45),
                'latitud': -34.6200,
                'longitud': -58.4000,
                'descripcion': 'Perra perdida, lleva collar rojo, nombre Luna.',
                'foto_url': '',
                'en_adopcion': False,
                'adoptado': False,
                'estado_reporte': 'Activo',
            },
        ]

        reportes = []
        for reporte_data in reportes_data:
            reporte = Reporte.objects.create(**reporte_data)
            reportes.append(reporte)

        # Crear contactos de ejemplo
        contactos_data = [
            {
                'reporte': reportes[0],
                'telefono': '+54 11 1234-5678',
                'email': 'juan@example.com',
                'whatsapp_enable': True,
            },
            {
                'reporte': reportes[1],
                'telefono': '+54 11 8765-4321',
                'email': 'maria@example.com',
                'whatsapp_enable': False,
            },
        ]

        for contacto_data in contactos_data:
            Contacto.objects.create(**contacto_data)

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with demo data.'))