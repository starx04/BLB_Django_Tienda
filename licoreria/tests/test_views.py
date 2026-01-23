from django.test import TestCase, Client
from django.urls import reverse
from licoreria.models import Categorias, Productos

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.categoria_vinos = Categorias.objects.create(nombre="Vinos")

        
        self.producto_vino = Productos.objects.create(
            nombre="Vino Tinto",
            categoria=self.categoria_vinos,
            precio=10.00,
            stock=50,
            grados_alcohol=12.0
        )
        


    def test_productos_catalogo_view(self):
        response = self.client.get(reverse('productos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vino Tinto")


    def test_productos_filter(self):
        response = self.client.get(reverse('productos'), {'categoria': self.categoria_vinos.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['categoria_activa_id'], self.categoria_vinos.id)

