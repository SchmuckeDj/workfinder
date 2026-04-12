"""
URLs raíz del proyecto WorkFinder.
ROOT_URLCONF apunta aquí desde settings.py.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# URLs de la app core definidas inline aquí como urls raíz
from core import views as core_views

app_name = None  # Sin namespace en el root urlconf

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.HomeView.as_view(), name='home'),
    path('ofertas/', core_views.JobListView.as_view(), name='job_list'),
    path('ofertas/<int:pk>/', core_views.JobDetailView.as_view(), name='job_detail'),
    path('api/', include('automation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
