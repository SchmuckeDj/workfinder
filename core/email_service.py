"""
core/email_service.py
Envío de emails transaccionales de WorkFinder.
"""
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


def send_welcome_email(subscriber, top_jobs=None):
    """
    Envía email de bienvenida al suscriptor recién registrado.
    Incluye hasta 3 ofertas destacadas si se proporcionan.

    Args:
        subscriber: instancia de Subscriber
        top_jobs:   queryset o lista de Job (máx 3), puede ser None
    """
    if top_jobs is None:
        top_jobs = []

    subject = f"¡Bienvenido/a a WorkFinder, {subscriber.name}! 🎉"

    # ── Texto plano ──
    text_body = f"""
¡Hola {subscriber.name}!

Gracias por suscribirte a WorkFinder. Ya eres parte de nuestra comunidad
de profesionales que encuentran oportunidades reales.

Te avisaremos en cuanto lleguen nuevas ofertas que se ajusten a tu perfil.

OFERTAS DESTACADAS EN ESTE MOMENTO
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

    text_body += f"""
-----------------------------------
¿Quieres darte de baja? Responde este email con el asunto "BAJA".

{settings.SITE_NAME} · {settings.SITE_URL}
"""

    # ── HTML ──
    jobs_html = ""
    if top_jobs:
        for job in top_jobs[:3]:
            salary_badge = (
                f'<span style="background:#F5F4F0;padding:2px 8px;border-radius:999px;'
                f'font-size:12px;color:#7A7870;">{job.salary}</span>'
            ) if job.salary else ""

            modality_color = {
                'remoto': '#1A9E6A',
                'hibrido': '#C97B1A',
                'presencial': '#2A5AF5',
            }.get(job.modality, '#2A5AF5')

            jobs_html += f"""
<tr>
  <td style="padding:16px;border-bottom:1px solid #E4E2DC;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td>
          <p style="margin:0 0 4px;font-family:sans-serif;font-size:15px;
                    font-weight:700;color:#141413;">{job.title}</p>
          <p style="margin:0 0 8px;font-family:sans-serif;font-size:13px;
                    color:#7A7870;">{job.company} · {job.location}</p>
          <span style="background:{modality_color}18;color:{modality_color};
                       font-size:11px;font-weight:700;padding:2px 8px;
                       border-radius:999px;text-transform:uppercase;
                       letter-spacing:0.04em;">{job.get_modality_display()}</span>
          &nbsp;{salary_badge}
        </td>
        <td style="text-align:right;vertical-align:middle;white-space:nowrap;">
          <a href="{settings.SITE_URL}/ofertas/{job.pk}/"
             style="background:#141413;color:#fff;font-family:sans-serif;
                    font-size:12px;font-weight:600;padding:8px 16px;
                    border-radius:999px;text-decoration:none;display:inline-block;">
            Ver oferta →
          </a>
        </td>
      </tr>
    </table>
  </td>
</tr>
"""
    else:
        jobs_html = """
<tr>
  <td style="padding:24px;text-align:center;font-family:sans-serif;
             font-size:14px;color:#7A7870;">
    Pronto tendremos ofertas para ti. ¡Te avisaremos!
  </td>
</tr>
"""

    html_body = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F5F4F0;font-family:sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F4F0;padding:32px 16px;">
  <tr><td align="center">
    <table width="560" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:20px;overflow:hidden;
                  border:1px solid #E4E2DC;max-width:100%;">

      <!-- Header -->
      <tr>
        <td style="background:#141413;padding:28px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td>
                <p style="margin:0;color:white;font-size:20px;font-weight:800;
                           letter-spacing:-0.03em;">WorkFinder</p>
                <p style="margin:4px 0 0;color:rgba(255,255,255,0.45);font-size:12px;">
                  Tu próxima oportunidad te espera
                </p>
              </td>
              <td style="text-align:right;">
                <span style="background:#2A5AF5;color:white;font-size:11px;font-weight:700;
                             padding:4px 12px;border-radius:999px;letter-spacing:0.05em;">
                  NUEVO MIEMBRO
                </span>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Saludo -->
      <tr>
        <td style="padding:32px 32px 24px;">
          <p style="margin:0 0 12px;font-size:24px;font-weight:800;color:#141413;
                     letter-spacing:-0.03em;">¡Hola, {subscriber.name}! 👋</p>
          <p style="margin:0;font-size:15px;color:#7A7870;line-height:1.7;">
            Ya eres parte de WorkFinder. Desde ahora recibirás alertas con las
            mejores oportunidades laborales del mercado dominicano.
          </p>
        </td>
      </tr>

      <!-- Match badge -->
      <tr>
        <td style="padding:0 32px 24px;">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#EBF0FF;border-radius:14px;border:1px solid #C1CEFF;">
            <tr>
              <td style="padding:16px 20px;">
                <table cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding-right:16px;">
                      <p style="margin:0;font-size:28px;font-weight:800;color:#1A9E6A;
                                 line-height:1;">97%</p>
                      <p style="margin:2px 0 0;font-size:11px;color:#7A7870;
                                 text-transform:uppercase;letter-spacing:0.05em;">Match</p>
                    </td>
                    <td style="border-left:1px solid #C1CEFF;padding-left:16px;">
                      <p style="margin:0;font-size:13px;color:#2A5AF5;font-weight:600;">
                        Tu perfil tiene alta compatibilidad
                      </p>
                      <p style="margin:4px 0 0;font-size:12px;color:#7A7870;">
                        Las mejores ofertas llegan a quienes se suscriben primero.
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Ofertas -->
      <tr>
        <td style="padding:0 32px 8px;">
          <p style="margin:0 0 12px;font-size:11px;font-weight:700;color:#AEAC9F;
                     text-transform:uppercase;letter-spacing:0.08em;">
            Ofertas activas ahora mismo
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border:1px solid #E4E2DC;border-radius:14px;overflow:hidden;">
            {jobs_html}
          </table>
        </td>
      </tr>

      <!-- CTA -->
      <tr>
        <td style="padding:24px 32px 32px;text-align:center;">
          <a href="{settings.SITE_URL}/ofertas/"
             style="display:inline-block;background:#2A5AF5;color:white;
                    font-size:14px;font-weight:600;padding:14px 32px;
                    border-radius:999px;text-decoration:none;
                    box-shadow:0 8px 32px rgba(42,90,245,0.28);">
            Ver todas las ofertas →
          </a>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background:#F5F4F0;padding:20px 32px;border-top:1px solid #E4E2DC;">
          <p style="margin:0;font-size:11px;color:#AEAC9F;text-align:center;line-height:1.6;">
            Recibiste este email porque te suscribiste en {settings.SITE_URL}<br>
            Para darte de baja, responde con el asunto "BAJA"
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info("Email de bienvenida enviado a %s", subscriber.email)
    except Exception as exc:
        logger.exception("Error enviando email a %s: %s", subscriber.email, exc)
        # No re-lanzamos: el email nunca debe romper el flujo de suscripción
