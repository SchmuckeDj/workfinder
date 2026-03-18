from django.db import models


class IncomingJob(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]

    raw_message = models.TextField()

    image = models.ImageField(
        upload_to="incoming_jobs/",
        null=True,
        blank=True
    )

    source = models.CharField(max_length=100, default='whatsapp')
    job_created = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source} - {self.status}"