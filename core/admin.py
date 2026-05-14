from django.contrib import admin
from .models import Job, Recurso, Articulo, Subscriber


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'modality', 'status', 'published_at')
    list_filter = ('status', 'modality')
    search_fields = ('title', 'company', 'location')


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('title', 'tipo', 'price', 'is_active', 'order')
    list_filter = ('tipo', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'badge', 'is_active', 'order', 'published_at')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')
