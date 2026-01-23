from django.test import TestCase, Client
from django.urls import reverse
import json

class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_cocteles_api_live(self):
        """Verifica que la API de Cócteles extraiga datos reales y una imagen."""
        print("\n[TEST] Verificando CoctelesAPI (TheCocktailDB)...")
        url = reverse('api_cocteles')
        response = self.client.get(url, {'search': 'margarita'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) > 0, "No se encontraron resultados para 'margarita'")
        
        primer_item = data['results'][0]
        print(f"   -> Encontrado: {primer_item.get('nombre')}")
        self.assertIn('nombre', primer_item)
        self.assertIn('imagen_url', primer_item)
        self.assertTrue(primer_item['imagen_url'].startswith('http'), "La imagen no es una URL válida")
        print(f"   -> Imagen OK: {primer_item['imagen_url']}")

    def test_licores_off_api_live(self):
        """Verifica que la API de Licores (OFF) extraiga datos y una imagen de producto."""
        print("\n[TEST] Verificando LicoresOFFAPI (Open Food Facts)...")
        url = reverse('api_licores_off')
        # Buscamos 'whisky' que es común
        response = self.client.get(url, {'search': 'whisky'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('results', data)
        self.assertTrue(len(data['results']) > 0, "No se encontraron resultados para 'whisky' en OFF")
        
        # Verificar primer resultado
        primer_item = data['results'][0]
        print(f"   -> Encontrado: {primer_item.get('nombre')}")
        self.assertIn('nombre', primer_item)
        self.assertIn('imagen_url', primer_item)
        
        # OFF a veces no tiene imagen para todo, pero probamos con 'whisky' que suele tener
        if primer_item['imagen_url']:
            self.assertTrue(primer_item['imagen_url'].startswith('http'), "La imagen de OFF no es una URL válida")
            print(f"   -> Imagen OK: {primer_item['imagen_url']}")
        else:
            print("   -> (Aviso) El primer producto de OFF no tiene imagen. Probando otros...")
            tiene_imagen = any(r.get('imagen_url') for r in data['results'])
            self.assertTrue(tiene_imagen, "Ningún resultado de OFF trajo imagen para 'whisky'")

    def test_licores_off_ean_live(self):
        """Verifica búsqueda por código de barras (EAN)."""
        print("\n[TEST] Verificando LicoresOFFAPI por EAN (7790100067035 - Quilmes ejemplo)...")
        url = reverse('api_licores_off')
        # EAN común
        response = self.client.get(url, {'search': '7790100067035'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['results']) > 0, "No se encontró el producto por EAN")
        print(f"   -> EAN Encontrado: {data['results'][0].get('nombre')}")
