from django.db import models


class IncomingJob(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'

    raw_message = models.TextField(verbose_name="Mensaje original")

    image = models.ImageField(
        upload_to="incoming_jobs/",
        null=True,
        blank=True,
        verbose_name="Imagen adjunta",
    )

    source = models.CharField(max_length=100, default='whatsapp', verbose_name="Fuente")
    job_created = models.BooleanField(default=False, verbose_name="Oferta creada")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Estado",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Recibido en")

    class Meta:
        verbose_name = "Oferta entrante"
        verbose_name_plural = "Ofertas entrantes"
        ordering = ['-created_at']

    def __str__(self):
        preview = self.raw_message[:60] + "..." if len(self.raw_message) > 60 else self.raw_message
        return f"[{self.source}] {self.created_at:%d/%m/%Y %H:%M} — {preview}"
