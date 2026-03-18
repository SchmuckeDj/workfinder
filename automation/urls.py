from django.urls import path
from . import views

urlpatterns = [
    path('incoming-job/', views.incoming_job_api, name='incoming_job'),
]