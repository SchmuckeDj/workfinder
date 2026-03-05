from django.db import models


class Job(models.Model):

    MODALITY_CHOICES = [
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]

    title = models.CharField(max_length=200, verbose_name="Puesto")
    company = models.CharField(max_length=200, verbose_name="Empresa")
    description = models.TextField(verbose_name="Descripción")
    short_description = models.CharField(max_length=300, verbose_name="Descripción corta")
    location = models.CharField(max_length=200, verbose_name="Lugar")
    salary = models.CharField(max_length=100, verbose_name="Sueldo", blank=True, null=True)

    modality = models.CharField(
        max_length=20,
        choices=MODALITY_CHOICES,
        default='presencial',
        verbose_name="Modalidad"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Estado"
    )

    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Oferta de trabajo"
        verbose_name_plural = "Ofertas de trabajo"
        ordering = ['-published_at']

    def __str__(self):
        return f"{self.title} — {self.company}"
class Subscriber(models.Model):

    name = models.CharField(max_length=150, verbose_name="Nombre")
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de suscripción")

    class Meta:
        verbose_name = "Suscriptor"
        verbose_name_plural = "Suscriptores"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} <{self.email}>"