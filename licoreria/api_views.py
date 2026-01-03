from .models import Productos
from .serializers import ProductoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests

# CLAVE DE RAPIDAPI REQUERIDA (Necesitas registrarte en RapidAPI y suscribirte a WineVybe/Beer9)
# Pon tu clave aquí cuando la tengas:
RAPIDAPI_KEY = "TU_CLAVE_DE_RAPIDAPI_AQUI" 

class LicoresAPI(APIView):
    def get(self, request):
        busqueda_externa = request.query_params.get('search', None)

        if busqueda_externa:
            # --- Lógica de Búsqueda Externa (WineVybe / Beer9 API) ---
            url = "https://beer9.p.rapidapi.com/"
            # Nota: La estructura exacta del endpoint depende de la documentación de Beer9.
            # Asumimos una búsqueda estándar por nombre.
            
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "beer9.p.rapidapi.com"
            }
            
            # Si no hay clave, retornamos error amigable
            if RAPIDAPI_KEY == "TU_CLAVE_DE_RAPIDAPI_AQUI":
                return Response({"error": "Falta configurar la RAPIDAPI_KEY en api_views.py"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Solicitud a la API externa
            try:
                # Ajusta '/search' según la doc específica de Beer9 si es diferente
                response = requests.get(f"{url}search/{busqueda_externa}", headers=headers)
                data = response.json()
                return Response(data)
            except Exception as e:
                return Response({"error": f"Error conectando con WineVybe: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            # --- Lógica Local (Base de Datos Propia) ---
            categoria_licores = ['Licores', 'Tragos', 'Bebidas Alcoholicas']
            # Filtramos case-insensitive
            productos = Productos.objects.filter(categoria__nombre__in=categoria_licores)
            serializer = ProductoSerializer(productos, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SnacksAPI(APIView):
    def get(self, request):
        busqueda_externa = request.query_params.get('search', None)

        if busqueda_externa:
            # --- Lógica de Búsqueda Externa (Open Food Facts) ---
            # No requiere API Key
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                'search_terms': busqueda_externa,
                'search_simple': 1,
                'action': 'process',
                'json': 1
            }

            try:
                response = requests.get(url, params=params)
                data = response.json()
                
                # Procesamos un poco la respuesta para que sea más limpia
                productos_encontrados = []
                for item in data.get('products', [])[:10]: # Limitamos a 10 resultados
                    productos_encontrados.append({
                        'product_name': item.get('product_name', 'Desconocido'),
                        'brands': item.get('brands', 'N/A'),
                        'categories': item.get('categories', ''),
                        'image_thumb_url': item.get('image_thumb_url', ''),
                        'ingredients_text': item.get('ingredients_text', 'No especificado')
                    })
                
                return Response({'source': 'OpenFoodFacts', 'results': productos_encontrados})
                
            except Exception as e:
                return Response({"error": f"Error conectando con Open Food Facts: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            # --- Lógica Local (Base de Datos Propia) ---
            categoria_snacks = ['Snacks', 'Bocaditos', 'Comida']
            productos = Productos.objects.filter(categoria__nombre__in=categoria_snacks)
            serializer = ProductoSerializer(productos, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
