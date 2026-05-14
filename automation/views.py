import logging
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Count

from .models import IncomingJob
from core.models import Job

logger = logging.getLogger(__name__)


def _check_api_token(request):
    token = request.headers.get('Authorization', '')
    expected = f"Bearer {settings.AUTOMATION_API_TOKEN}"
    return token == expected and bool(settings.AUTOMATION_API_TOKEN)


@csrf_exempt
def incoming_job_api(request):
    """
    Recibe mensajes de WhatsApp (texto + imagen opcional) y los guarda
    como IncomingJob pendiente de revisión en el admin.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)

    if not _check_api_token(request):
        return JsonResponse({"error": "No autorizado."}, status=401)

    raw_text = request.POST.get("raw_text", "").strip()
    caption   = request.POST.get("caption", "").strip()
    source    = request.POST.get("source", "whatsapp").strip() or "whatsapp"
    image     = request.FILES.get("image")

    # Combinar caption + raw_text si vienen separados
    parts = [p for p in [caption, raw_text] if p]
    combined_text = "\n".join(parts)

    if not combined_text and not image:
        return JsonResponse({"error": "Se requiere raw_text, caption o image."}, status=400)

    try:
        job = IncomingJob.objects.create(
            raw_message=combined_text,
            image=image,
            source=source,
        )
        logger.info("IncomingJob #%s creado desde %s", job.id, request.META.get("REMOTE_ADDR"))
        return JsonResponse({"status": "ok", "id": job.id}, status=201)

    except Exception as exc:
        logger.exception("Error creando IncomingJob: %s", exc)
        return JsonResponse({"error": "Error interno del servidor."}, status=500)


@staff_member_required
def dashboard(request):
    """Panel interno — solo staff."""
    hoy = timezone.now().date()

    # Conteos IncomingJob
    incoming_qs = IncomingJob.objects.all()
    incoming_counts = {
        item['status']: item['total']
        for item in incoming_qs.values('status').annotate(total=Count('id'))
    }

    # Conteos Job
    job_qs = Job.objects.all()
    job_counts = {
        item['status']: item['total']
        for item in job_qs.values('status').annotate(total=Count('id'))
    }

    # Actividad de hoy
    hoy_incoming = incoming_qs.filter(created_at__date=hoy)
    hoy_procesados = hoy_incoming.filter(job_created=True).count()
    hoy_duplicados = hoy_incoming.filter(status=IncomingJob.Status.DUPLICATED).count()
    hoy_incompletos = hoy_incoming.filter(status=IncomingJob.Status.INCOMPLETE).count()
    hoy_pendientes = hoy_incoming.filter(status=IncomingJob.Status.PENDING).count()

    # Últimas 20 ofertas entrantes
    recientes = incoming_qs.select_related('duplicate_of').order_by('-created_at')[:20]

    context = {
        # IncomingJob por estado
        'total_incoming': incoming_qs.count(),
        'pending': incoming_counts.get('pending', 0),
        'approved': incoming_counts.get('approved', 0),
        'rejected': incoming_counts.get('rejected', 0),
        'duplicated': incoming_counts.get('duplicated', 0),
        'spam': incoming_counts.get('spam', 0),
        'incomplete': incoming_counts.get('incomplete', 0),

        # Jobs publicados
        'jobs_aprobados': job_counts.get('approved', 0),
        'jobs_pendientes': job_counts.get('pending', 0),
        'jobs_rechazados': job_counts.get('rejected', 0),

        # Hoy
        'hoy_procesados': hoy_procesados,
        'hoy_duplicados': hoy_duplicados,
        'hoy_incompletos': hoy_incompletos,
        'hoy_pendientes': hoy_pendientes,
        'hoy_total': hoy_incoming.count(),

        # Lista reciente
        'recientes': recientes,
        'hoy': hoy,
    }

    return render(request, 'automation/dashboard.html', context)
