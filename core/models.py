from django.db import models
from django.urls import reverse


class Job(models.Model):

    class Modality(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        REMOTO = 'remoto', 'Remoto'
        HIBRIDO = 'hibrido', 'Híbrido'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'

    title = models.CharField(max_length=200, verbose_name="Puesto")
    company = models.CharField(max_length=200, verbose_name="Empresa")
    description = models.TextField(verbose_name="Descripción")
    short_description = models.CharField(max_length=300, verbose_name="Descripción corta")
    location = models.CharField(max_length=200, verbose_name="Lugar")
    salary = models.CharField(max_length=100, verbose_name="Sueldo", blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    experience = models.CharField(max_length=200, blank=True, null=True)
    schedule = models.CharField(max_length=200, blank=True, null=True)
    application_link = models.URLField(blank=True, null=True, verbose_name="Link de aplicación")

    modality = models.CharField(
        max_length=20,
        choices=Modality.choices,
        default=Modality.PRESENCIAL,
        verbose_name="Modalidad"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
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


class Recurso(models.Model):

    class Tipo(models.TextChoices):
        CURSO = 'curso', 'Curso'
        LIBRO = 'libro', 'Libro'
        TOOL = 'tool', 'Herramienta'
        PROMO = 'promo', 'Oferta'

    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.CURSO, verbose_name="Tipo")
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.CharField(max_length=300, verbose_name="Descripción")
    url = models.URLField(verbose_name="Enlace de afiliado")
    image = models.ImageField(upload_to='recursos/', blank=True, null=True, verbose_name="Imagen")
    price = models.CharField(max_length=50, blank=True, default='', verbose_name="Precio")
    price_old = models.CharField(max_length=50, blank=True, default='', verbose_name="Precio anterior / tachado")
    cta_label = models.CharField(max_length=50, default='Ver curso', verbose_name="Texto del botón")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.title}"


class Articulo(models.Model):

    title = models.CharField(max_length=200, verbose_name="Título")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Slug", help_text="URL amigable, ej: entrevista-tecnica-7-dias")
    category = models.CharField(max_length=60, verbose_name="Categoría", help_text="Ej: Entrevistas, Salario, Carrera.")
    badge = models.CharField(max_length=40, default='Guía', verbose_name="Badge")
    description = models.TextField(verbose_name="Descripción corta")
    content = models.TextField(blank=True, default='', verbose_name="Contenido", help_text="Contenido HTML del artículo completo.")
    image = models.ImageField(upload_to='articulos/', blank=True, null=True, verbose_name="Imagen")
    read_time = models.CharField(max_length=30, default='5 min lectura', verbose_name="Tiempo de lectura")
    url = models.URLField(blank=True, default='', verbose_name="Enlace externo (opcional)")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")

    class Meta:
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        ordering = ['order', '-published_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('articulo_detail', kwargs={'slug': self.slug})


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
