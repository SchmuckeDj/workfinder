from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import IncomingJob


@csrf_exempt
def incoming_job_api(request):

    if request.method == "POST":

        raw_text = request.POST.get("raw_text", "")

        image = request.FILES.get("image")

        job = IncomingJob.objects.create(
            raw_message=raw_text,
            image=image
        )

        return JsonResponse({
            "status": "ok",
            "id": job.id
        })

    return JsonResponse({"error": "Invalid request"})