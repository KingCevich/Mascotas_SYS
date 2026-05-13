from django.apps import AppConfig


class MascotasAppConfig(AppConfig):
    name = 'mascotas_app'

    def ready(self):
        import mascotas_app.signals