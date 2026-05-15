from django.contrib import admin
from django.utils.html import format_html
from .models import IncomingJob
from .services import create_job_from_incoming
from core.email_service import send_job_alert


@admin.register(IncomingJob)
class IncomingJobAdmin(admin.ModelAdmin):

    list_display = (
        'preview_image',
        'source',
        'status',
        'job_created',
        'created_at',
    )

    list_filter = (
        'status',
        'source',
        'job_created',
    )

    search_fields = (
        'raw_message',
    )

    readonly_fields = (
        'preview_image',
        'created_at',
    )

    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" style="border-radius:6px;" />',
                obj.image.url
            )
        return "No image"

    preview_image.short_description = "Imagen"

    def save_model(self, request, obj, form, change):

        if obj.status == "approved" and not obj.job_created:
            try:
                job = create_job_from_incoming(obj)
                if job:
                    self.message_user(request, f'Oferta creada: "{job.title}" en {job.company}.')
                    send_job_alert(job)
                elif obj.status == IncomingJob.Status.DUPLICATED:
                    self.message_user(request, 'Duplicado detectado — no se creó oferta.', level='WARNING')
                else:
                    self.message_user(request, f'Oferta incompleta — no se creó (estado: {obj.status}).', level='WARNING')

            except Exception as e:
                self.message_user(request, f"Error procesando la oferta: {e}", level='ERROR')

        super().save_model(request, obj, form, change)
