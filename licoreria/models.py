from django.db import models
from django.contrib.auth.models import User

class Categorias(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True, verbose_name="Imagen Representativa")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.nombre

class Marcas(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Marca")
    logo = models.ImageField(upload_to='marcas/', null=True, blank=True, verbose_name="Logo de la Marca")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    def __str__(self):
        return self.nombre

class Productos(models.Model):
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categorias, on_delete=models.CASCADE, related_name='productos', null=True, blank=True)
    distribuidor = models.ForeignKey('Distribuidores', on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    grados_alcohol = models.DecimalField(max_digits=4, decimal_places=1)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    
    # Campos Integración APIs Externas
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name="Código EAN/UPC")
    marca = models.ForeignKey(Marcas, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos', verbose_name="Marca")
    url_imagen_externa = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Imagen API")
    ingredientes = models.TextField(blank=True, null=True, help_text="Lista de ingredientes (para snacks)")
    id_externo_api = models.CharField(max_length=100, blank=True, null=True, help_text="ID referencia en API externa")

    def save(self, *args, **kwargs):
        # Auto-fetch image if missing and barcode exists
        if self.codigo_barras and not self.url_imagen_externa and not self.imagen:
            try:
                import requests
                # 1. Definir categorías de Snacks
                nombres_snacks = ['Snacks', 'Bocaditos', 'Comida', 'Papas', 'Frutos Secos', 'Dulces', 'Golosinas', 'Chocolates']
                is_snack = self.categoria and self.categoria.nombre in nombres_snacks
                
                if is_snack:
                    # Búsqueda en Open Food Facts (Snacks)
                    url = f"https://world.openfoodfacts.org/api/v0/product/{self.codigo_barras}.json"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 1:
                            product_data = data.get('product', {})
                            image_url = product_data.get('image_front_url')
                            if image_url:
                                self.url_imagen_externa = image_url
                
                else:
                    # Intento de búsqueda en Beer9 API (Licores) si no es snack
                    # Nota: Requiere configuración de RAPIDAPI_KEY en api_views.py o settings
                    from .api_views import RAPIDAPI_KEY
                    if RAPIDAPI_KEY and RAPIDAPI_KEY != "TU_CLAVE_DE_RAPIDAPI_AQUI":
                        url = f"https://beer9.p.rapidapi.com/search/{self.codigo_barras}"
                        headers = {
                            "X-RapidAPI-Key": RAPIDAPI_KEY,
                            "X-RapidAPI-Host": "beer9.p.rapidapi.com"
                        }
                        response = requests.get(url, headers=headers, timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            # Asumiendo que la API retorna un campo image o similar
                            # Ajusta según la estructura real de Beer9
                            if data and isinstance(data, list) and len(data) > 0:
                                self.url_imagen_externa = data[0].get('image') or data[0].get('imageUrl')

            except Exception as e:
                print(f"Error fetching external data for {self.nombre}: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

import uuid

class Clientes(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    codigo_unico = models.CharField(max_length=10, unique=True, blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            # Generar código único de 8 caracteres
            self.codigo_unico = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_unico})"

class Empleados(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    cargo = models.CharField(max_length=100)
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_unico = models.CharField(max_length=10, unique=True, blank=True, null=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            self.codigo_unico = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_unico})"


class ListasPrecios(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la Lista")
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class PrecioProducto(models.Model):
    lista = models.ForeignKey(ListasPrecios, on_delete=models.CASCADE, related_name='precios')
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE, related_name='precios_especiales')
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('lista', 'producto')

    def __str__(self):
        return f"{self.producto.nombre} - {self.lista.nombre}: ${self.precio}"

class Ordenes(models.Model):
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleados, on_delete=models.SET_NULL, null=True, blank=True, help_text="Vendedor que procesó la orden")
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Relación con Productos se maneja a través de DetallesOrdenes

    def __str__(self):
        return f"Orden {self.id} - {self.cliente.nombre}"

class Prestamos(models.Model):
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE)
    fecha_prestamo = models.DateField(auto_now_add=True)
    descripcion = models.TextField(help_text="Descripción de lo prestado (envases, dinero, etc.)")
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Valor monetario del préstamo")
    devuelto = models.BooleanField(default=False)

    def __str__(self):
        return f"Prestamo {self.id} - {self.cliente.nombre}"

class Distribuidores(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class DetallesOrdenes(models.Model):
    orden = models.ForeignKey(Ordenes, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Orden {self.orden.id})"

class Gastos(models.Model):
    CATEGORIAS_GASTOS = [
        ('PRO', 'Proveedores'),
        ('SER', 'Servicios Básicos'),
        ('NOM', 'Nómina'),
        ('OTR', 'Otros'),
    ]
    
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    categoria_gasto = models.CharField(max_length=3, choices=CATEGORIAS_GASTOS, default='OTR', verbose_name="Categoría")

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"

class Recompensas(models.Model):
    """Modelo para gestionar recompensas y regalos por consumo del cliente"""
    TIPO_RECOMPENSA = [
        ('PUN', 'Puntos'),
        ('DES', 'Descuento'),
        ('REG', 'Regalo/Producto Gratis'),
        ('BON', 'Bono Especial'),
    ]
    
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE, related_name='recompensas')
    tipo = models.CharField(max_length=3, choices=TIPO_RECOMPENSA, default='PUN', verbose_name="Tipo de Recompensa")
    descripcion = models.TextField(help_text="Descripción de la recompensa otorgada")
    valor = models.DecimalField(max_digits=10, decimal_places=2, help_text="Valor monetario o puntos")
    fecha_otorgada = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True, help_text="Fecha límite para usar la recompensa")
    utilizada = models.BooleanField(default=False)
    fecha_utilizacion = models.DateTimeField(null=True, blank=True)
    orden_relacionada = models.ForeignKey(Ordenes, on_delete=models.SET_NULL, null=True, blank=True, 
                                         help_text="Orden que generó esta recompensa")
    
    class Meta:
        verbose_name = "Recompensa"
        verbose_name_plural = "Recompensas"
        ordering = ['-fecha_otorgada']
    
    def __str__(self):
        estado = "Utilizada" if self.utilizada else "Disponible"
        return f"{self.cliente.nombre} - {self.get_tipo_display()} - {estado}"

