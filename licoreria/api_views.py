from .models import Productos, Marcas, Cocteles, Categorias
from .serializers import ProductoSerializer, CoctelSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import logging
from .utils import log_action, get_default_price

logger = logging.getLogger(__name__)

# Headers globales para evitar bloqueos de APIs externas
HEADERS = {
    'User-Agent': 'LicoreriaNeonApp/1.0 (https://github.com/starx04/BLB_Django_Tienda; starx04@example.com) requests/2.31.0'
}

class CoctelesAPI(APIView):
    def get(self, request):
        """ Busca cocteles en TheCocktailDB (API para recetas y tragos). """
        query = request.query_params.get('search', '').strip()

        if query:
            log_action(request.user, f"Búsqueda de cóctel: {query}", "APIs", request=request)
            
            base_url = "https://www.thecocktaildb.com/api/json/v1/1/"
            url = f"{base_url}search.php"
            params = {"s": query} if len(query) > 1 else {"f": query}
            if query.lower() == 'random': url = f"{base_url}random.php"; params = {}

            try:
                response = requests.get(url, params=params, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    drinks = data.get('drinks', [])
                    formatted_results = []
                    if drinks:
                        for item in drinks:
                            ingredients = [f"{(item.get(f'strMeasure{i}') or '').strip()} {(item.get(f'strIngredient{i}') or '').strip()}".strip() 
                                           for i in range(1, 16) if item.get(f'strIngredient{i}')]
                            formatted_results.append({
                                "nombre": item.get('strDrink', 'Sin Nombre'),
                                "imagen_url": item.get('strDrinkThumb', ''),
                                "categoria": item.get('strCategory', 'Coctel'),
                                "ingredientes": ", ".join(ingredients),
                                "id_externo": item.get('idDrink'),
                                "es_alcoholico": item.get('strAlcoholic') == 'Alcoholic',
                                "instrucciones": item.get('strInstructions', '')
                            })
                    return Response({"source": "TheCocktailDB", "results": formatted_results})
                logger.error(f"Error TheCocktailDB API: Status {response.status_code}")
                return Response({"error": "Error de conexión con API externa"}, status=response.status_code)
            except Exception as e:
                logger.error(f"Excepción en CoctelesAPI: {str(e)}")
                return Response({"error": f"Error interno: {str(e)}"}, status=500)
        
        return Response({"results": []})

    def post(self, request):
        """ Guarda un cóctel importado. """
        id_externo = request.data.get('id_externo')
        if id_externo and Cocteles.objects.filter(id_externo=id_externo).exists():
            return Response({"error": "Este cóctel ya existe."}, status=400)

        serializer = CoctelSerializer(data=request.data)
        if serializer.is_valid():
            coctel = serializer.save()
            log_action(request.user, f"Importó cóctel: {coctel.nombre}", "Cócteles", 
                       detalles=f"Stock inicial: {coctel.stock}, Precio: {coctel.precio}", request=request)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LicoresOFFAPI(APIView):
    def get(self, request):
        """ Busca licores/snacks en OFF (Contexto Ecuador y Global). """
        query = request.query_params.get('search', '').strip()
        if not query: return Response({"error": "Query requerido"}, status=400)

        log_action(request.user, f"Búsqueda OFF: {query}", "APIs", request=request)
        results = []
        
        is_ean = query.isdigit() and len(query) >= 8
        
        try:
            if is_ean:
                off_url = f"https://world.openfoodfacts.org/api/v2/product/{query}.json"
                off_res = requests.get(off_url, timeout=10, verify=False, headers=HEADERS)
            else:
                off_url = f"https://world.openfoodfacts.org/cgi/search.pl"
                params = {
                    "search_terms": query,
                    "search_simple": 1,
                    "action": "process",
                    "json": 1,
                    "page_size": 10
                }
                print(f"DEBUG: Consultando OFF URL: {off_url} con Params: {params}")
                off_res = requests.get(off_url, params=params, timeout=10, verify=False, headers=HEADERS)

            if off_res.status_code == 200:
                off_data = off_res.json()
                
                if is_ean:
                    products_raw = [off_data["product"]] if "product" in off_data else []
                else:
                    products_raw = off_data.get("products", [])

                for p in products_raw:
                    prod_name = p.get('product_name') or p.get('product_name_es') or p.get('product_name_en') or 'Producto Desconocido'
                    brand = p.get('brands', 'Genérico').split(',')[0].strip()
                    nutriments = p.get('nutriments', {})
                    abv = nutriments.get('alcohol_100g') or p.get('alcohol_100g') or p.get('alcohol_base') or p.get('alcohol', 0)
                    
                    results.append({
                        "nombre": prod_name,
                        "marca": brand,
                        "grados_alcohol": abv,
                        "origen": p.get('origins', 'Ecuador'),
                        "cantidad": p.get('quantity', 'N/A'),
                        "codigo_barras": p.get('code', ''),
                        "imagen_url": p.get('image_url') or p.get('image_front_url') or p.get('image_small_url', ''),
                        "descripcion_tecnica": p.get('categories', '')
                    })
                
                return Response({"results": results})
            
            logger.error(f"Error OFF API: Status {off_res.status_code} para query {query}")
            return Response({"error": f"API OFF devolvió status {off_res.status_code}"}, status=off_res.status_code)
        except Exception as e:
            logger.error(f"Excepción en LicoresOFFAPI: {str(e)}")
            return Response({"error": f"Error interno: {str(e)}"}, status=500)

    def post(self, request):
        """ Guarda un producto importado de OFF. """
        # 1. Manejo de Categoría (Priorizar la seleccionada por el usuario)
        categoria_id = data.get('categoria')
        if not categoria_id:
            categoria_str = data.get('categoria_api', 'Otros Licores').split(',')[0].strip()
            # Limpiar tags de OFF si vienen como "en:whiskeys"
            if ':' in categoria_str:
                categoria_str = categoria_str.split(':')[-1].replace('-', ' ').title()
            
            categoria_obj, _ = Categorias.objects.get_or_create(nombre=categoria_str)
            data['categoria'] = categoria_obj.id
        # Si ya viene un ID de categoría, el serializer lo manejará correctamente.

        # 2. Manejo de Marca
        marca_nombre = data.get('marca', 'GENERICO').strip().upper()
        marca_obj, _ = Marcas.objects.get_or_create(nombre=marca_nombre)
        data['marca'] = marca_obj.id

        # 3. Datos Extra
        data['origen'] = data.get('origen', 'Ecuador')
        data['grados_alcohol'] = data.get('grados_alcohol', 0)

        serializer = ProductoSerializer(data=data)
        if serializer.is_valid():
            producto = serializer.save()
            log_action(request.user, f"Importó producto (OFF): {producto.nombre}", "Productos", 
                       detalles=f"Stock: {producto.stock}, Precio: {producto.precio}", request=request)
            return Response(serializer.data, status=201)

# Mapa de Categorías Locales (IDs obtenidos del sistema)
LOCAL_CAT_MAP = {
    'whisky': 12,
    'rum': 13,
    'ron': 13,
    'vodka': 14,
    'wine': 15,
    'vino': 15,
    'beer': 16,
    'cerveza': 16,
    'tragos': 2,
    'coctel': 2,
    'cocktail': 2,
    'alcoholic-beverages': 1,
}

def get_suggested_cat_id(tags):
    """Retorna el ID de la categoría local basado en tags/nombres"""
    if not tags: return 1
    tags_str = str(tags).lower()
    for key, val in LOCAL_CAT_MAP.items():
        if key in tags_str:
            return val
    return 1 # Default: Licores

class BusquedaLicoresAPIView(APIView):
    """Buscador para el apartado: Importar Licores"""
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])

        # Mapeo de categorías específicas solicitadas
        CATEGORY_MAP = {
            'whiskys': 'en:whiskies',
            'ron': 'en:rums',
            'vodka': 'en:vodkas',
            'ginebra': 'en:gins'
        }
        
        selected_cat = request.query_params.get('cat', '').lower()
        
        # La búsqueda es estrictamente por nombre, filtrada por bebidas alcohólicas a nivel global
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            'search_terms': query, 
            'json': 1, 
            'action': 'process',
            'fields': 'product_name,code,image_url,brands,categories,categories_tags,nutriments,origins,quantity',
            'page_size': 24,
            # Filtro estricto para bebidas alcohólicas (Obligatorio)
            'tagtype_0': 'categories',
            'tag_contains_0': 'contains',
            'tag_0': 'en:alcoholic-beverages'
        }
        
        # Añadir filtro de categoría específica si se selecciona
        if selected_cat in CATEGORY_MAP:
            params.update({
                'tagtype_1': 'categories',
                'tag_contains_1': 'contains',
                'tag_1': CATEGORY_MAP[selected_cat]
            })
        
        # Desactivar advertencias de SSL para entornos locales con certificados autofirmados
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        try:
            # Restauramos verify=False por posibles problemas de certificados en el entorno local
            res = requests.get(url, params=params, headers=HEADERS, timeout=10, verify=False)
            
            if res.status_code != 200:
                logger.error(f"Fallo BusquedaLicoresAPIView: OFF Status {res.status_code}")
                return Response({"error": f"La API de Open Food Facts no está respondiendo (Status {res.status_code})"}, 
                                status=status.HTTP_502_BAD_GATEWAY)
            
            data_json = res.json()
            productos = data_json.get('products', [])
            
            # Formatear resultados priorizando nombres legibles y datos automatizados
            formatted = []
            
            # Categorías a excluir explícitamente si estamos en "Todos"
            EXCLUDE_TAGS = ['en:snacks', 'en:salty-snacks', 'en:sweet-snacks', 'en:confectionery', 'en:food', 'en:meals']
            
            for p in productos:
                cats = p.get('categories_tags', [])
                
                # Si estamos en "Todos" (no cat seleccionada), excluimos comida/snacks
                if not selected_cat:
                    if any(tag in cats for tag in EXCLUDE_TAGS):
                        continue

                # Extraer datos básicos del producto OFF
                name = p.get('product_name') or p.get('product_name_es') or p.get('product_name_en') or 'Producto Desconocido'
                brand = p.get('brands', 'Genérico').split(',')[0].strip()
                code = p.get('code', '')
                
                # Buscar si ya existe en base de datos para sugerir el precio real
                producto_existente = Productos.objects.filter(codigo_barras=code).first()
                
                # Extraer graduación alcohólica
                nutriments = p.get('nutriments', {})
                abv = nutriments.get('alcohol_100g') or p.get('alcohol_100g') or p.get('alcohol_base') or p.get('alcohol', 0)

                # Generar precio y categoría sugerida
                cat_id_sugerido = get_suggested_cat_id(cats + [name, brand])
                
                # Obtener nombre legible de la categoría para el generador de precios
                cat_name_price = 'DEFAULT'
                for k in LOCAL_CAT_MAP:
                    if k in str(cats + [name, brand]).lower():
                        cat_name_price = k
                        break

                precio_sugerido = str(producto_existente.precio) if producto_existente else str(get_default_price(cat_name_price))
                cat_principal = cats[-1] if cats else 'en:alcoholic-beverages'

                formatted.append({
                    "id": code,
                    "nombre": name,
                    "marca": brand,
                    "imagen": p.get("image_url") or p.get("image_front_url"),
                    "tipo": "LICOR",
                    "descripcion_tecnica": p.get("categories", ""),
                    "categoria_api": cat_principal,
                    "categoria_sugerida": cat_id_sugerido,
                    "precio_sugerido": precio_sugerido,
                    "grados_alcohol": abv,
                    "origen": p.get('origins', 'Ecuador'),
                    "cantidad": p.get('quantity', 'N/A')
                })
            
            return Response(formatted)
        except Exception as e:
            logger.error(f"Fallo crítico en BusquedaLicoresAPIView (OFF): {str(e)}")
            return Response([], status=500)

class BusquedaCoctelesAPIView(APIView):
    """Buscador para el apartado: Importar Cócteles"""
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])

        url = "https://www.thecocktaildb.com/api/json/v1/1/search.php"
        params = {"s": query}
        
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                 logger.error(f"Error TheCocktailDB search: Status {res.status_code}")
                 return Response([])
                 
            data = res.json().get('drinks')
            if not data:
                return Response([])

            return Response([{
                "id": d.get("idDrink"),
                "nombre": d.get("strDrink"),
                "imagen": d.get("strDrinkThumb"),
                "tipo": "COCTEL",
                "categoria": d.get("strCategory"),
                "categoria_sugerida": 2, # Default: Tragos
                "precio_sugerido": str(get_default_price('DEFAULT')),
                "ingredientes": ", ".join([f"{(d.get(f'strMeasure{i}') or '').strip()} {(d.get(f'strIngredient{i}') or '').strip()}".strip() 
                                          for i in range(1, 16) if d.get(f'strIngredient{i}')]),
                "instrucciones": d.get("strInstructions", ""),
                "es_alcoholico": d.get("strAlcoholic") == "Alcoholic"
            } for d in data])
        except Exception as e:
            logger.error(f"Fallo crítico en BusquedaCoctelesAPIView: {str(e)}")
            return Response([], status=500)

