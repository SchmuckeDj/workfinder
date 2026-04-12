from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

from core.models import Job, Subscriber
from automation.models import IncomingJob
from automation.services import create_job_from_incoming


# ─────────────────────────────────────────────
# Tests del endpoint de automatización
# ─────────────────────────────────────────────

class IncomingJobAPITest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = '/api/incoming-job/'
        self.token = 'test-secret-token'
        settings.AUTOMATION_API_TOKEN = self.token

    def _auth_headers(self):
        return {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    def test_rechaza_sin_token(self):
        response = self.client.post(self.url, {'raw_text': 'Oferta de prueba'})
        self.assertEqual(response.status_code, 401)

    def test_rechaza_token_incorrecto(self):
        response = self.client.post(
            self.url,
            {'raw_text': 'Oferta de prueba'},
            HTTP_AUTHORIZATION='Bearer token-malo',
        )
        self.assertEqual(response.status_code, 401)

    def test_rechaza_get(self):
        response = self.client.get(self.url, **self._auth_headers())
        self.assertEqual(response.status_code, 405)

    def test_rechaza_payload_vacio(self):
        response = self.client.post(self.url, {}, **self._auth_headers())
        self.assertEqual(response.status_code, 400)

    def test_crea_incoming_job_con_texto(self):
        response = self.client.post(
            self.url,
            {'raw_text': 'Se busca programador Python con 2 años de experiencia'},
            **self._auth_headers(),
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(IncomingJob.objects.filter(pk=data['id']).exists())


# ─────────────────────────────────────────────
# Tests de services.py — mock de Anthropic
# ─────────────────────────────────────────────

def _make_anthropic_response(json_text: str):
    """Construye un objeto response de Anthropic simulado."""
    mock_content = MagicMock()
    mock_content.text = json_text
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


class CreateJobFromIncomingTest(TestCase):

    @patch('automation.services._get_client')
    def test_crea_job_desde_texto(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response('''{
            "title": "Programador Python",
            "company": "TechCorp",
            "description": "Buscamos desarrollador backend.",
            "location": "Remoto",
            "salary": "RD$60,000",
            "modality": "remoto",
            "email": "hr@techcorp.com",
            "phone": "",
            "requirements": "Python, Django",
            "benefits": "Seguro médico",
            "experience": "2 años",
            "schedule": "Lunes a viernes"
        }''')

        incoming = IncomingJob.objects.create(
            raw_message="Se busca Programador Python en TechCorp, trabajo remoto."
        )

        job = create_job_from_incoming(incoming)

        self.assertEqual(job.title, "Programador Python")
        self.assertEqual(job.company, "TechCorp")
        self.assertEqual(job.status, Job.Status.APPROVED)
        self.assertEqual(job.modality, Job.Modality.REMOTO)

    @patch('automation.services._get_client')
    def test_json_invalido_usa_defaults(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response(
            'esto no es json válido'
        )

        incoming = IncomingJob.objects.create(raw_message="Texto de prueba cualquiera")
        job = create_job_from_incoming(incoming)

        self.assertEqual(job.title, "Vacante")
        self.assertEqual(job.status, Job.Status.APPROVED)

    @patch('automation.services._get_client')
    def test_claude_con_backticks_se_limpia(self, mock_get_client):
        """Claude a veces envuelve el JSON en backticks — debe limpiarse."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_anthropic_response(
            '```json\n{"title": "Dev", "company": "ACME", "description": "Desc", '
            '"location": "SD", "salary": "", "modality": "presencial", '
            '"email": "", "phone": "", "requirements": "", "benefits": "", '
            '"experience": "", "schedule": ""}\n```'
        )

        incoming = IncomingJob.objects.create(raw_message="Dev en ACME")
        job = create_job_from_incoming(incoming)

        self.assertEqual(job.title, "Dev")
        self.assertEqual(job.company, "ACME")

    def test_sin_texto_lanza_error(self):
        incoming = IncomingJob.objects.create(raw_message="")
        with self.assertRaises(ValueError):
            create_job_from_incoming(incoming)


# ─────────────────────────────────────────────
# Tests del flujo de suscripción
# ─────────────────────────────────────────────

class SubscriberFormTest(TestCase):

    def test_suscripcion_exitosa(self):
        response = self.client.post('/', {
            'name': 'Jose',
            'email': 'jose@example.com',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Subscriber.objects.filter(email='jose@example.com').exists())

    def test_email_duplicado_no_rompe(self):
        Subscriber.objects.create(name='Jose', email='jose@example.com')
        response = self.client.post('/', {
            'name': 'Jose',
            'email': 'jose@example.com',
        }, follow=True)
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(Subscriber.objects.filter(email='jose@example.com').count(), 1)


# ─────────────────────────────────────────────
# Tests de las vistas de Job
# ─────────────────────────────────────────────

class JobViewsTest(TestCase):

    def setUp(self):
        self.approved_job = Job.objects.create(
            title="Dev Senior",
            company="ACME",
            description="Descripción larga del puesto.",
            short_description="Descripción corta.",
            location="Santo Domingo",
            modality=Job.Modality.REMOTO,
            status=Job.Status.APPROVED,
        )
        self.pending_job = Job.objects.create(
            title="Dev Junior (pendiente)",
            company="ACME",
            description="Descripción.",
            short_description="Corta.",
            location="Santo Domingo",
            modality=Job.Modality.PRESENCIAL,
            status=Job.Status.PENDING,
        )

    def test_home_muestra_solo_aprobadas(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        jobs = response.context['jobs']
        self.assertIn(self.approved_job, jobs)
        self.assertNotIn(self.pending_job, jobs)

    def test_lista_muestra_solo_aprobadas(self):
        response = self.client.get('/ofertas/')
        self.assertEqual(response.status_code, 200)
        jobs = list(response.context['jobs'])
        self.assertIn(self.approved_job, jobs)
        self.assertNotIn(self.pending_job, jobs)

    def test_detalle_aprobada_accesible(self):
        response = self.client.get(f'/ofertas/{self.approved_job.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_detalle_pendiente_devuelve_404(self):
        response = self.client.get(f'/ofertas/{self.pending_job.pk}/')
        self.assertEqual(response.status_code, 404)
