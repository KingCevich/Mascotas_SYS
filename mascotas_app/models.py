from django.db import models
TIPO_REPORTE = [
    ("Perdido", "Perdido"),
    ("Encontrado", "Encontrado"),
    ("Avistado","Avistado"),
]

ESTADO_REPORTE = [
    ("Activo", "Activa"),
    ("Resuelto", "Resuelto"),
    ("Inconcluso", "Inconcluso"),
]

class Reporte(models.Model):
    tipo_reporte = models.CharField(choices=TIPO_REPORTE)
    nombre_mascota = models.CharField(max_length=25)
    raza = models.CharField(max_length=30)
    color = models.CharField(max_length=50)
    tamano = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fech_perdida = models.DateField()
    hora_perdida = models.TimeField(null=True, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    descripcion = models.TextField(blank=True, null=True)
    foto_url = models.URLField(max_length=300, blank=True, null=True)
    en_adopcion = models.BooleanField(default=False)
    adoptado = models.BooleanField(default=False)
    estado_reporte = models.CharField(choices=ESTADO_REPORTE)

    def __str__(self):
        return f"{self.nombre_mascota} - ({self.get_tipo_reporte_display()}) - Estado: {self.get_estado_reporte_display()}"

    
class Contacto(models.Model):
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name="contactos")
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    whatsapp_enable = models.BooleanField(default=False)

    def __str__(self):
        return f"Contacto de {self.reporte.nombre_mascota}"