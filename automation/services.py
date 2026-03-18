from core.models import Job


def create_job_from_incoming(incoming_job):

    text = incoming_job.raw_message or ""

    job = Job.objects.create(
        title="Vacante desde WhatsApp",
        company="Empresa no especificada",
        description=text,
        short_description=text[:200],
        location="No especificado",
        modality="presencial",
        status="approved"
    )

    return job