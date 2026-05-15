import json
import logging
import re
import unicodedata

import anthropic
from django.conf import settings

from core.models import Job

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def extract_text_from_image(image_path):
    if not OCR_AVAILABLE:
        return ""
    image = Image.open(image_path)
    return pytesseract.image_to_string(image, lang="spa").strip()


def clean_ocr_text(text):
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\x80-\xFF]', ' ', text)
    lines = text.splitlines()
    lines = [l for l in lines if len(l.strip()) >= 3]
    lines = [re.sub(r' {2,}', ' ', l) for l in lines]
    text = "\n".join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Validación de campos extraídos
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_PHONE_RE = re.compile(r'[\d\s\-\+\(\)]{7,20}')
_URL_RE = re.compile(r'https?://[^\s]+')

SPAM_INDICATORS = [
    'gana dinero fácil', 'multinivel', 'mlm', 'sin experiencia necesaria ilimitado',
    'trabaja desde casa sin horario', 'inversión inicial', 'recluta amigos',
]

GARBAGE_TITLES = {'vacante', 'empleo', 'trabajo', 'oferta', 'oportunidad'}


def validate_parsed(parsed):
    issues = []

    title = (parsed.get("title") or "").strip()
    if not title or title.lower() in GARBAGE_TITLES:
        issues.append("título genérico o vacío")
        title = "Vacante"
    parsed["title"] = title

    company = (parsed.get("company") or "").strip()
    if not company or len(company) < 2:
        issues.append("empresa no detectada")
        company = "Empresa no especificada"
    parsed["company"] = company

    email = (parsed.get("email") or "").strip()
    if email and not _EMAIL_RE.match(email):
        issues.append(f"email inválido descartado: {email!r}")
        email = ""
    parsed["email"] = email

    phone = (parsed.get("phone") or "").strip()
    if phone and not _PHONE_RE.search(phone):
        issues.append(f"teléfono inválido descartado: {phone!r}")
        phone = ""
    parsed["phone"] = phone

    salary = (parsed.get("salary") or "").strip()
    if salary and not re.search(r'\d', salary):
        issues.append(f"salario sin dígitos descartado: {salary!r}")
        salary = ""
    parsed["salary"] = salary

    modality = (parsed.get("modality") or "").lower().strip()
    if modality not in ("presencial", "remoto", "hibrido", "híbrido"):
        modality = "presencial"
    parsed["modality"] = modality.replace("híbrido", "hibrido")

    app_link = (parsed.get("application_link") or "").strip()
    if app_link and not _URL_RE.match(app_link):
        app_link = ""
    parsed["application_link"] = app_link

    desc_lower = (parsed.get("description") or "").lower()
    for indicator in SPAM_INDICATORS:
        if indicator in desc_lower:
            issues.append(f"indicador de spam: {indicator!r}")
            break

    return parsed, issues


# ---------------------------------------------------------------------------
# Parser básico (fallback sin IA)
# ---------------------------------------------------------------------------

def _basic_parser(text):
    """Extrae campos mínimos con regex cuando Claude no está disponible."""
    NOISE = {"Premium", "Confidencial", "•", "·", "–", "—"}

    # Extraer URL antes de limpiar
    url_match = re.search(r'https?://[^\s]+', text)
    application_link = url_match.group(0) if url_match else ""

    # Limpiar líneas: quitar ruido, línea URL, bullets vacíos
    lines = []
    for l in text.splitlines():
        l = l.strip()
        if not l or l.startswith("URL:"):
            continue
        if l in NOISE:
            continue
        for w in NOISE:
            l = l.replace(w, "").strip()
        if len(l) < 2:
            continue
        lines.append(l)

    title   = lines[0] if lines else "Vacante"
    company = lines[1] if len(lines) > 1 else "Empresa no especificada"
    if not company or len(company) < 2:
        company = "Empresa no especificada"

    description = "\n".join(lines[2:]) if len(lines) > 2 else ""

    email_match  = re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    phone_match  = re.search(r'(\+?1?\s?)?(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})', text)
    salary_match = re.search(r'RD?\$[\s\d,\.]+|[\d,\.]+\s*(pesos|dólares|USD)', text, re.IGNORECASE)
    loc_match    = re.search(
        r'(Santo Domingo|Santiago|La Romana|San Pedro|Punta Cana|Puerto Plata|Higüey|Bavaro|Bávaro)[^\n,]*',
        text, re.IGNORECASE
    )

    modality = "presencial"
    if re.search(r'\bremoto\b|\bremote\b|\bwork from home\b', text, re.IGNORECASE):
        modality = "remoto"
    elif re.search(r'\bhíbrido\b|\bhibrido\b', text, re.IGNORECASE):
        modality = "hibrido"

    parsed = {
        "title":            title[:200],
        "company":          company[:200],
        "description":      description[:1500] or text[:500],
        "location":         loc_match.group(0).strip()[:200] if loc_match else "República Dominicana",
        "salary":           salary_match.group(0) if salary_match else "",
        "modality":         modality,
        "email":            email_match.group(0) if email_match else "",
        "phone":            phone_match.group(0) if phone_match else "",
        "requirements":     "",
        "benefits":         "",
        "experience":       "",
        "schedule":         "",
        "application_link": application_link,
    }

    parsed, _ = validate_parsed(parsed)
    return parsed


# ---------------------------------------------------------------------------
# Detección de duplicados
# ---------------------------------------------------------------------------

def _normalize(text):
    text = unicodedata.normalize("NFD", text.lower())
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _word_similarity(a, b):
    words_a = {w for w in a.split() if len(w) > 3}
    words_b = {w for w in b.split() if len(w) > 3}
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def find_duplicate(incoming_job, parsed):
    from automation.models import IncomingJob

    title_norm = _normalize(parsed.get("title") or "")
    company_norm = _normalize(parsed.get("company") or "")
    raw_norm = _normalize(incoming_job.raw_message)

    candidates = IncomingJob.objects.exclude(pk=incoming_job.pk).exclude(
        status=IncomingJob.Status.SPAM
    ).order_by('-created_at')[:200]

    for candidate in candidates:
        if _normalize(candidate.raw_message) == raw_norm:
            return candidate

        if title_norm and company_norm:
            if title_norm in _normalize(candidate.raw_message) and \
               company_norm in _normalize(candidate.raw_message):
                return candidate

        sim = _word_similarity(raw_norm, _normalize(candidate.raw_message))
        if sim >= 0.75:
            return candidate

    return None


# ---------------------------------------------------------------------------
# Extracción con IA
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """Eres un extractor de datos de ofertas laborales para República Dominicana.

Analiza el siguiente texto (puede incluir OCR de imagen con posibles errores) y extrae los campos indicados.

TEXTO:
{text}

INSTRUCCIONES:
- Devuelve ÚNICAMENTE un JSON válido, sin backticks, sin texto adicional.
- No inventes datos. Si un campo no existe en el texto, usa "".
- Para "company": busca el nombre del negocio/empresa/empleador.
- Para "salary": incluye el número y moneda (ej: "RD$25,000 mensual").
- Para "phone": extrae el número dominicano completo (ej: "809-555-1234").
- Para "email": solo si hay un email claramente escrito en el texto.
- Para "experience": años o nivel (ej: "2 años", "no requerida").
- Para "requirements": lista los requisitos separados por coma o punto y coma.
- Para "application_link": URL completa si existe en el texto.
- Para "modality": solo "presencial", "remoto" o "hibrido".
- Limpia errores de OCR obvios.

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
  "schedule": "",
  "application_link": ""
}}"""


def extract_job_with_ai(text):
    prompt = EXTRACTION_PROMPT.format(text=text)

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            logger.error("Claude devolvió JSON inválido: %s", content[:300])
            return _basic_parser(text)

        parsed, issues = validate_parsed(parsed)
        if issues:
            logger.warning("Campos problemáticos en extracción: %s", issues)

        return parsed

    except Exception as exc:
        logger.warning("Claude no disponible (%s), usando parser básico.", exc)
        return _basic_parser(text)


# ---------------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------------

def create_job_from_incoming(incoming_job):
    from automation.models import IncomingJob

    text = incoming_job.raw_message or ""

    if incoming_job.image:
        try:
            image_text = extract_text_from_image(incoming_job.image.path)
            image_text = clean_ocr_text(image_text)
            text = f"{text}\n{image_text}".strip()
        except Exception as exc:
            logger.warning("OCR falló para IncomingJob #%s: %s", incoming_job.pk, exc)

    if not text:
        incoming_job.status = IncomingJob.Status.INCOMPLETE
        incoming_job.save(update_fields=["status"])
        raise ValueError("No hay texto disponible para procesar la oferta.")

    parsed = extract_job_with_ai(text)

    duplicate = find_duplicate(incoming_job, parsed)
    if duplicate:
        incoming_job.status = IncomingJob.Status.DUPLICATED
        incoming_job.duplicate_of = duplicate
        incoming_job.save(update_fields=["status", "duplicate_of"])
        logger.info("IncomingJob #%s marcado como duplicado de #%s", incoming_job.pk, duplicate.pk)
        return None

    if parsed["title"] == "Vacante" and parsed["company"] == "Empresa no especificada":
        incoming_job.status = IncomingJob.Status.INCOMPLETE
        incoming_job.save(update_fields=["status"])
        logger.warning("IncomingJob #%s marcado como incompleto", incoming_job.pk)
        return None

    description = parsed.get("description") or text
    short_desc = description[:297] + "..." if len(description) > 300 else description

    job = Job.objects.create(
        title=parsed["title"],
        company=parsed["company"],
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
        application_link=parsed.get("application_link") or "",
        modality=parsed.get("modality") or Job.Modality.PRESENCIAL,
        status=Job.Status.APPROVED,
    )

    incoming_job.job_created = True
    incoming_job.save(update_fields=["job_created"])

    logger.info("Job #%s creado desde IncomingJob #%s", job.pk, incoming_job.pk)
    return job
