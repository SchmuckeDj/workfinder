"""
core/email_service.py
Envío de emails transaccionales de WorkFinder.
"""
import logging
from django.core.mail import EmailMultiAlternatives, send_mass_mail
from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Email de bienvenida al suscribirse
# ─────────────────────────────────────────────

def send_welcome_email(subscriber, top_jobs=None):
    if top_jobs is None:
        top_jobs = []

    subject = f"¡Bienvenido/a a WorkFinder, {subscriber.name}! 🎉"

    text_body = f"""
¡Hola {subscriber.name}!

Gracias por suscribirte a WorkFinder. Ya eres parte de nuestra comunidad
de profesionales que encuentran oportunidades reales.

Te avisaremos en cuanto lleguen nuevas ofertas que se ajusten a tu perfil.

OFERTAS DESTACADAS AHORA MISMO
-----------------------------------
"""
    if top_jobs:
        for job in top_jobs[:3]:
            salary_line = f"  Salario: {job.salary}" if job.salary else ""
            text_body += f"""
• {job.title} — {job.company}
  {job.location} · {job.get_modality_display()}
{salary_line}
  Ver oferta: {settings.SITE_URL}/ofertas/{job.pk}/
"""
    else:
        text_body += "\nPor el momento no hay ofertas activas, pero te avisaremos pronto.\n"

    text_body += f"\n---\n{settings.SITE_URL}\nPara darte de baja, responde con el asunto BAJA.\n"

    jobs_html = _build_jobs_html(top_jobs)

    html_body = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F5F4F0;font-family:sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F4F0;padding:32px 16px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:20px;overflow:hidden;border:1px solid #E4E2DC;max-width:100%;">
      {_header_html("NUEVO MIEMBRO")}
      <tr>
        <td style="padding:32px 32px 24px;">
          <p style="margin:0 0 12px;font-size:24px;font-weight:800;color:#141413;letter-spacing:-0.03em;">¡Hola, {subscriber.name}! 👋</p>
          <p style="margin:0;font-size:15px;color:#7A7870;line-height:1.7;">
            Ya eres parte de WorkFinder. Recibirás alertas con las mejores oportunidades laborales del mercado dominicano.
          </p>
        </td>
      </tr>
      <tr>
        <td style="padding:0 32px 24px;">
          <p style="margin:0 0 12px;font-size:11px;font-weight:700;color:#AEAC9F;text-transform:uppercase;letter-spacing:0.08em;">Ofertas activas ahora mismo</p>
          <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E4E2DC;border-radius:14px;overflow:hidden;">
            {jobs_html}
          </table>
        </td>
      </tr>
      {_cta_html("Ver todas las ofertas →")}
      {_footer_html()}
    </table>
  </td></tr>
</table>
</body></html>"""

    _send(subject, text_body, html_body, subscriber.email)


# ─────────────────────────────────────────────
# Alerta de nueva oferta a todos los suscriptores
# ─────────────────────────────────────────────

def send_job_alert(job):
    """
    Envía notificación de nueva oferta a todos los suscriptores.
    Usa send_mass_mail para enviar en batch sin abrir N conexiones SMTP.
    """
    from core.models import Subscriber
    subscribers = list(Subscriber.objects.all())
    if not subscribers:
        return

    subject = f"Nueva oferta: {job.title} en {job.company} 🚀"
    salary_line = f"\nSalario: {job.salary}" if job.salary else ""
    job_url = f"{settings.SITE_URL}/ofertas/{job.pk}/"

    messages = []
    for sub in subscribers:
        text = f"""
¡Hola {sub.name}!

Nueva oferta publicada en WorkFinder:

{job.title}
{job.company} · {job.location} · {job.get_modality_display()}{salary_line}

Ver oferta: {job_url}

---
{settings.SITE_URL}
Para darte de baja, responde con el asunto BAJA.
""".strip()

        html = _job_alert_html(sub, job)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[sub.email],
        )
        msg.attach_alternative(html, "text/html")
        messages.append(msg)

    try:
        from django.core.mail import get_connection
        connection = get_connection()
        connection.send_messages(messages)
        logger.info("Alerta de oferta #%s enviada a %d suscriptores", job.pk, len(messages))
    except Exception as exc:
        logger.exception("Error enviando alerta de oferta #%s: %s", job.pk, exc)


# ─────────────────────────────────────────────
# Helpers privados
# ─────────────────────────────────────────────

def _send(subject, text_body, html_body, to_email):
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info("Email enviado a %s: %s", to_email, subject)
    except Exception as exc:
        logger.exception("Error enviando email a %s: %s", to_email, exc)


def _header_html(badge_text):
    return f"""
<tr>
  <td style="background:#141413;padding:28px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td><p style="margin:0;color:white;font-size:20px;font-weight:800;letter-spacing:-0.03em;">WorkFinder</p>
          <p style="margin:4px 0 0;color:rgba(255,255,255,0.45);font-size:12px;">Tu próxima oportunidad te espera</p></td>
      <td style="text-align:right;">
        <span style="background:#2A5AF5;color:white;font-size:11px;font-weight:700;padding:4px 12px;border-radius:999px;letter-spacing:0.05em;">{badge_text}</span>
      </td>
    </tr></table>
  </td>
</tr>"""


def _cta_html(label):
    return f"""
<tr>
  <td style="padding:24px 32px 32px;text-align:center;">
    <a href="{settings.SITE_URL}/ofertas/"
       style="display:inline-block;background:#2A5AF5;color:white;font-size:14px;font-weight:600;
              padding:14px 32px;border-radius:999px;text-decoration:none;">
      {label}
    </a>
  </td>
</tr>"""


def _footer_html():
    return f"""
<tr>
  <td style="background:#F5F4F0;padding:20px 32px;border-top:1px solid #E4E2DC;">
    <p style="margin:0;font-size:11px;color:#AEAC9F;text-align:center;line-height:1.6;">
      Recibiste este email porque te suscribiste en {settings.SITE_URL}<br>
      Para darte de baja, responde con el asunto "BAJA"
    </p>
  </td>
</tr>"""


def _build_jobs_html(jobs):
    if not jobs:
        return """<tr><td style="padding:24px;text-align:center;font-family:sans-serif;font-size:14px;color:#7A7870;">
            Pronto tendremos ofertas para ti. ¡Te avisaremos!</td></tr>"""

    html = ""
    modality_colors = {'remoto': '#1A9E6A', 'hibrido': '#C97B1A', 'presencial': '#2A5AF5'}
    for job in jobs[:3]:
        color = modality_colors.get(job.modality, '#2A5AF5')
        salary_badge = f'<span style="background:#F5F4F0;padding:2px 8px;border-radius:999px;font-size:12px;color:#7A7870;">{job.salary}</span>' if job.salary else ""
        html += f"""
<tr>
  <td style="padding:16px;border-bottom:1px solid #E4E2DC;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td>
        <p style="margin:0 0 4px;font-size:15px;font-weight:700;color:#141413;">{job.title}</p>
        <p style="margin:0 0 8px;font-size:13px;color:#7A7870;">{job.company} · {job.location}</p>
        <span style="background:{color}18;color:{color};font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;text-transform:uppercase;">{job.get_modality_display()}</span>
        &nbsp;{salary_badge}
      </td>
      <td style="text-align:right;vertical-align:middle;white-space:nowrap;">
        <a href="{settings.SITE_URL}/ofertas/{job.pk}/"
           style="background:#141413;color:#fff;font-size:12px;font-weight:600;padding:8px 16px;border-radius:999px;text-decoration:none;display:inline-block;">
          Ver oferta →
        </a>
      </td>
    </tr></table>
  </td>
</tr>"""
    return html


def _job_alert_html(subscriber, job):
    modality_colors = {'remoto': '#1A9E6A', 'hibrido': '#C97B1A', 'presencial': '#2A5AF5'}
    color = modality_colors.get(job.modality, '#2A5AF5')
    salary_html = f'<p style="margin:8px 0 0;font-size:14px;color:#1A9E6A;font-weight:600;">💰 {job.salary}</p>' if job.salary else ""
    job_url = f"{settings.SITE_URL}/ofertas/{job.pk}/"

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F5F4F0;font-family:sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F4F0;padding:32px 16px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:20px;overflow:hidden;border:1px solid #E4E2DC;max-width:100%;">
      {_header_html("NUEVA OFERTA")}
      <tr>
        <td style="padding:32px 32px 24px;">
          <p style="margin:0 0 8px;font-size:15px;color:#7A7870;">Hola {subscriber.name}, hay una nueva oferta para ti:</p>
          <p style="margin:0 0 4px;font-size:24px;font-weight:800;color:#141413;letter-spacing:-0.03em;">{job.title}</p>
          <p style="margin:0;font-size:16px;color:#7A7870;font-weight:500;">{job.company}</p>
          {salary_html}
        </td>
      </tr>
      <tr>
        <td style="padding:0 32px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F4F0;border-radius:14px;">
            <tr><td style="padding:16px 20px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding-right:20px;">
                    <p style="margin:0;font-size:11px;color:#AEAC9F;text-transform:uppercase;letter-spacing:.05em;">Ubicación</p>
                    <p style="margin:4px 0 0;font-size:14px;font-weight:600;color:#141413;">📍 {job.location}</p>
                  </td>
                  <td style="border-left:1px solid #E4E2DC;padding-left:20px;">
                    <p style="margin:0;font-size:11px;color:#AEAC9F;text-transform:uppercase;letter-spacing:.05em;">Modalidad</p>
                    <p style="margin:4px 0 0;font-size:14px;font-weight:600;color:{color};">{job.get_modality_display()}</p>
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
        </td>
      </tr>
      <tr>
        <td style="padding:0 32px 32px;text-align:center;">
          <a href="{job_url}"
             style="display:inline-block;background:#2A5AF5;color:white;font-size:14px;font-weight:600;
                    padding:14px 32px;border-radius:999px;text-decoration:none;">
            Ver oferta completa →
          </a>
        </td>
      </tr>
      {_footer_html()}
    </table>
  </td></tr>
</table>
</body></html>"""
