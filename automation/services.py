import json
import logging

import anthropic
from django.conf import settings
from PIL import Image
import pytesseract

from core.models import Job

logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Cliente de Anthropic — usa ANTHROPIC_API_KEY del .env
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def create_job_from_incoming(incoming_job):
    """
    Procesa un IncomingJob: extrae texto (+ OCR si hay imagen),
    llama a Claude para parsear los campos y crea un Job aprobado.
    """
    text = incoming_job.raw_message or ""

    if incoming_job.image:
        try:
            image_text = extract_text_from_image(incoming_job.image.path)
            text = f"{text}\n{image_text}".strip()
        except Exception as exc:
            logger.warning("OCR falló para IncomingJob #%s: %s", incoming_job.pk, exc)

    if not text:
        raise ValueError("No hay texto disponible para procesar la oferta.")

    parsed = extract_job_with_ai(text)

    description = parsed.get("description") or text
    short_desc = description[:297] + "..." if len(description) > 300 else description

    job = Job.objects.create(
        title=parsed.get("title") or "Vacante",
        company=parsed.get("company") or "Empresa no especificada",
        description=description,
        short_description=short_desc,
        location=parsed.get("location") or "No especificado",
        salary=parsed.get("salary") or "",
        email=parsed.get("email") or "",
        phone=parsed.get("phone") or "",
        requirements=parsed.get("requirements") or "",
        benefits=parsed.get("benefits") or "",
        experience=parsed.get("experience") or "",
        schedule=parsed.get("schedule") or "",
        modality=parsed.get("modality") or Job.Modality.PRESENCIAL,
        status=Job.Status.APPROVED,
    )

    logger.info("Job #%s creado desde IncomingJob #%s", job.pk, incoming_job.pk)
    return job


def extract_text_from_image(image_path):
    """Extrae texto de una imagen usando Tesseract OCR."""
    image = Image.open(image_path)
    return pytesseract.image_to_string(image, lang="spa").strip()


def extract_job_with_ai(text):
    """
    Usa Claude Haiku para extraer campos estructurados de un texto de oferta laboral.
    Devuelve un dict con los campos o un dict con valores por defecto si falla.
    """
    prompt = f"""Extrae la información de esta oferta de trabajo y devuélvela en JSON.

TEXTO:
{text}

Responde ÚNICAMENTE con el JSON, sin backticks, sin texto adicional, sin explicaciones.
Formato exacto:
{{
  "title": "",
  "company": "",
  "description": "",
  "location": "",
  "salary": "",
  "modality": "",
  "email": "",
  "phone": "",
  "requirements": "",
  "benefits": "",
  "experience": "",
  "schedule": ""
}}

Reglas:
- No inventes datos que no estén en el texto
- Si un campo no existe, déjalo como string vacío ""
- "modality" solo puede ser: "presencial", "remoto" o "hibrido"
- "description" debe ser un resumen limpio y profesional de la oferta"""

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",  # rápido y económico
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()

        # Limpiar posibles backticks si Claude los añade de todas formas
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(
                "Claude devolvió JSON inválido. Respuesta: %s",
                content[:300]
            )
            return _default_parsed()

    except anthropic.APIStatusError as exc:
        logger.exception("Error de API Anthropic (status %s): %s", exc.status_code, exc)
        raise
    except anthropic.APIConnectionError as exc:
        logger.exception("Error de conexión con Anthropic: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Error inesperado llamando a Claude: %s", exc)
        raise


def _default_parsed():
    return {
        "title": "Vacante",
        "company": "Empresa no especificada",
        "description": "",
        "location": "No especificado",
        "salary": "",
        "modality": "presencial",
        "email": "",
        "phone": "",
        "requirements": "",
        "benefits": "",
        "experience": "",
        "schedule": "",
    }
