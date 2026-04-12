import logging
from django.views.generic import ListView, DetailView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Job, Subscriber
from .forms import SubscriberForm
from .email_service import send_welcome_email

logger = logging.getLogger(__name__)


class HomeView(FormView):
    template_name = 'core/home.html'
    form_class = SubscriberForm
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approved_jobs = list(Job.objects.filter(status=Job.Status.APPROVED)[:6])
        context['jobs'] = approved_jobs
        context['jobs_count'] = len(approved_jobs)
        return context

    def form_valid(self, form):
        email = form.cleaned_data['email']
        name  = form.cleaned_data['name']

        if Subscriber.objects.filter(email=email).exists():
            messages.success(
                self.request,
                f"¡{name}, ya estás suscrito/a! Te avisaremos cuando lleguen nuevas ofertas."
            )
            return super().form_valid(self)

        subscriber = form.save()

        # Enviamos email con las 3 ofertas más recientes aprobadas
        top_jobs = list(Job.objects.filter(status=Job.Status.APPROVED)[:3])
        send_welcome_email(subscriber, top_jobs)

        messages.success(
            self.request,
            f"¡Bienvenido/a {name}! Revisa tu correo — te enviamos las mejores ofertas de hoy. 🎉"
        )
        return super().form_valid(self)

    def form_invalid(self, form):
        messages.error(self.request, "Por favor revisa los datos ingresados.")
        return super().form_invalid(form)


class JobListView(ListView):
    model = Job
    template_name = 'core/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 9

    def get_queryset(self):
        return Job.objects.filter(status=Job.Status.APPROVED)


class JobDetailView(DetailView):
    model = Job
    template_name = 'core/job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return Job.objects.filter(status=Job.Status.APPROVED)
