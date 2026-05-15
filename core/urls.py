from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from core import views as core_views

app_name = None

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.HomeView.as_view(), name='home'),
    path('ofertas/', core_views.JobListView.as_view(), name='job_list'),
    path('ofertas/<int:pk>/', core_views.JobDetailView.as_view(), name='job_detail'),
    path('recursos/', core_views.RecursoListView.as_view(), name='recursos'),
    path('blog/', core_views.ArticuloListView.as_view(), name='blog'),
    path('blog/<slug:slug>/', core_views.ArticuloDetailView.as_view(), name='articulo_detail'),
    path('api/', include('automation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
