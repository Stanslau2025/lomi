from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Agent


@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    },
)
class AgentRegistrationAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin-password",
        )

    def test_admin_registered_agent_gets_linked_user_and_can_login_as_agent(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/agents/",
            {
                "full_name": "Amina Agent",
                "email": "amina@example.com",
                "password": "agent-password",
                "plan": "free",
                "subscription_days": 30,
                "status": "active",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        agent = Agent.objects.get(email="amina@example.com")
        self.assertIsNotNone(agent.user)
        self.assertEqual(agent.user.email, agent.email)

        self.client.force_authenticate(user=None)
        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "amina@example.com", "password": "agent-password"},
            format="json",
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.data["role"], "agent")
        self.assertEqual(login_response.data["agentId"], str(agent.id))

    def test_existing_customer_email_logs_in_as_agent_with_agent_password(self):
        customer = User.objects.create_user(
            username="existing-customer",
            email="existing@example.com",
            password="customer-password",
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/agents/",
            {
                "full_name": "Existing Agent",
                "email": "existing@example.com",
                "password": "agent-password",
                "plan": "free",
                "subscription_days": 30,
                "status": "active",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        agent = Agent.objects.get(email="existing@example.com")
        self.assertEqual(agent.user, customer)

        self.client.force_authenticate(user=None)
        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "existing@example.com", "password": "agent-password"},
            format="json",
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.data["role"], "agent")
        self.assertEqual(login_response.data["agentId"], str(agent.id))
