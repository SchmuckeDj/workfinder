from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from . import views

# Sin app_name porque este es el urls raíz
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomeView.as_view(), name='home'),
    path('ofertas/', views.JobListView.as_view(), name='job_list'),
    path('ofertas/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    # API automation
    path('api/', include('automation.urls')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)