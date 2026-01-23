from django.test import TestCase, Client
from django.urls import reverse
import json

class OFFDetailedTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_off_extraction_details(self):
        """Prueba detallada de campos extraídos de Open Food Facts."""
        print("\n[TEST DETALLADO] Analizando extracción de datos de OFF...")
        url = reverse('api_licores_off')
        
        # Caso 1: Búsqueda por palabra clave (Whisky)
        print("\n--- CASO 1: Búsqueda por nombre ('Whisky') ---")
        response = self.client.get(url, {'search': 'whisky'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        results = data.get('results', [])
        self.assertTrue(len(results) > 0, "No se retornaron resultados para 'whisky'")
        
        # Analizar el primer resultado en detalle
        item = results[0]
        print(f"Campos extraídos para '{item.get('nombre')}':")
        print(f"  - Nombre: {item.get('nombre')}")
        print(f"  - Marca: {item.get('marca')}")
        print(f"  - Grados Alcohol: {item.get('grados_alcohol')}")
        print(f"  - Código EAN: {item.get('codigo_barras')}")
        print(f"  - Imagen URL: {item.get('imagen_url')}")
        print(f"  - Origen: {item.get('origen')}")
        print(f"  - Descripción técnica: {item.get('descripcion_tecnica')[:100]}...")

        # Validaciones de integridad
        self.assertIsNotNone(item.get('nombre'), "El nombre no debería ser nulo")
        self.assertIn('imagen_url', item, "Debe existir el campo de imagen")
        
    def test_off_ean_specific(self):
        """Prueba con un EAN específico conocido para validar precisión."""
        print("\n--- CASO 2: Búsqueda por EAN específico (Heineken - 40822938) ---")
        url = reverse('api_licores_off')
        response = self.client.get(url, {'search': '40822938'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        results = data.get('results', [])
        
        if len(results) > 0:
            item = results[0]
            print(f"  - Producto encontrado: {item.get('nombre')}")
            print(f"  - Marca: {item.get('marca')}")
            print(f"  - Imagen: {item.get('imagen_url')}")
            self.assertEqual(item.get('codigo_barras'), '40822938')
        else:
            print("  - [AVISO] El EAN de prueba ya no devolvió resultados (puede haber cambiado en OFF)")
