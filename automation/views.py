import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import IncomingJob

logger = logging.getLogger(__name__)


def _check_api_token(request):
    """Valida el token de autorización en el header."""
    token = request.headers.get('Authorization', '')
    expected = f"Bearer {settings.AUTOMATION_API_TOKEN}"
    return token == expected and bool(settings.AUTOMATION_API_TOKEN)


@csrf_exempt
def incoming_job_api(request):
    """
    Recibe mensajes de WhatsApp (texto + imagen opcional) y los guarda
    como IncomingJob pendiente de revisión en el admin.

    Requiere header: Authorization: Bearer <AUTOMATION_API_TOKEN>
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)

    # Fix: autenticación por token
    if not _check_api_token(request):
        return JsonResponse({"error": "No autorizado."}, status=401)

    raw_text = request.POST.get("raw_text", "").strip()
    image = request.FILES.get("image")

    if not raw_text and not image:
        return JsonResponse({"error": "Se requiere raw_text o image."}, status=400)

    try:
        job = IncomingJob.objects.create(
            raw_message=raw_text,
            image=image,
        )
        logger.info("IncomingJob #%s creado desde %s", job.id, request.META.get("REMOTE_ADDR"))
        return JsonResponse({"status": "ok", "id": job.id}, status=201)

    except Exception as exc:
        logger.exception("Error creando IncomingJob: %s", exc)
        return JsonResponse({"error": "Error interno del servidor."}, status=500)
