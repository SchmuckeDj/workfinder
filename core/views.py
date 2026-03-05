from django.views.generic import ListView, DetailView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Job, Subscriber
from .forms import SubscriberForm


class HomeView(FormView):
    template_name = 'core/home.html'
    form_class = SubscriberForm
    success_url = reverse_lazy('core:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approved_jobs = Job.objects.filter(status='approved')
        context['jobs'] = approved_jobs
        context['jobs_count'] = approved_jobs.count()
        return context

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            f"¡Gracias {form.cleaned_data['name']}! Te notificaremos sobre nuevas oportunidades."
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Por favor revisa los datos ingresados.")
        return super().form_invalid(form)


class JobListView(ListView):
    model = Job
    template_name = 'job_list.html'
    context_object_name = 'jobs'
    paginate_by = 9

    def get_queryset(self):
        return Job.objects.filter(status='approved')


class JobDetailView(DetailView):
    model = Job
    template_name = 'job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return Job.objects.filter(status='approved')