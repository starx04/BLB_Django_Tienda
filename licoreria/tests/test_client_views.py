from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from licoreria.models import Clientes

class ClienteListTest(TestCase):
    def setUp(self):
        # Create normal user
        self.user_client = User.objects.create_user(username='client', password='password')
        self.cliente = Clientes.objects.create(user=self.user_client, nombre="Client User", email="client@example.com")
        
        # Create admin user
        self.user_admin = User.objects.create_user(username='admin', password='password', is_staff=True, is_superuser=True)
        self.admin_cliente = Clientes.objects.create(user=self.user_admin, nombre="Admin User", email="admin@example.com")
        
        # Create legacy client (no user)
        self.legacy_cliente = Clientes.objects.create(nombre="Legacy Client", email="legacy@example.com", user=None)
        
        # Setup client
        self.client = Client()
        self.client.force_login(self.user_admin)

    def test_admin_excluded_from_client_list(self):
        url = reverse('clientes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        clientes_ctx = response.context['clientes']
        
        # Verify normal client is present
        self.assertIn(self.cliente, clientes_ctx)
        
        # Verify legacy client is present
        self.assertIn(self.legacy_cliente, clientes_ctx)
        
        # Verify admin client is NOT present
        self.assertNotIn(self.admin_cliente, clientes_ctx)
