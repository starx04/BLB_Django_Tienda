from django.test import TestCase
from licoreria.models import Categorias, Productos, Marcas

class ModelTests(TestCase):
    def setUp(self):
        self.categoria = Categorias.objects.create(nombre="Vinos")
        self.marca = Marcas.objects.create(nombre="Concha y Toro")
        self.producto = Productos.objects.create(
            nombre="Casillero del Diablo",
            categoria=self.categoria,
            marca=self.marca,
            precio=10.00,
            stock=100,
            grados_alcohol=13.5
        )

    def test_categoria_creacion(self):
        self.assertEqual(self.categoria.nombre, "Vinos")
        self.assertEqual(str(self.categoria), "Vinos")

    def test_producto_creacion(self):
        self.assertEqual(self.producto.stock, 100)
        self.assertEqual(self.producto.categoria, self.categoria)
