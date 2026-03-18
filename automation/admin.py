from django.contrib import admin
from django.utils.html import format_html
from .models import IncomingJob
from .services import create_job_from_incoming


@admin.register(IncomingJob)
class IncomingJobAdmin(admin.ModelAdmin):

    list_display = ('preview_image', 'source', 'status', 'created_at')
    list_filter = ('status', 'source')
    search_fields = ('raw_message',)

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

            create_job_from_incoming(obj)

            obj.job_created = True

        super().save_model(request, obj, form, change)