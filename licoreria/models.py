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
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name="Código EAN/UPC")
    marca = models.ForeignKey(Marcas, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos', verbose_name="Marca")
    
    # Soporte para APIs (OFF & Unsplash)
    url_imagen_externa = models.URLField(max_length=500, blank=True, null=True, verbose_name="URL Imagen Premium")
    origen = models.CharField(max_length=100, blank=True, null=True, verbose_name="País de Origen")
    descripcion_tecnica = models.TextField(blank=True, null=True, verbose_name="Descripción OFF")

    class Meta:
        unique_together = ('nombre', 'marca')
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

class Cocteles(models.Model):
    nombre = models.CharField(max_length=200)
    id_externo = models.CharField(max_length=100, unique=True, null=True, blank=True)
    instrucciones = models.TextField(blank=True, null=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)
    categoria = models.CharField(max_length=100, blank=True, null=True)
    ingredientes = models.TextField(blank=True, null=True)
    es_alcoholico = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock disponible")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

import uuid

class Clientes(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    codigo_unico = models.CharField(max_length=10, unique=True, blank=True, null=True, editable=False)
    puntos_acumulados = models.IntegerField(default=0, verbose_name="Puntos de Fidelidad", help_text="1 punto por cada $10 gastados")
    limite_prestamo = models.DecimalField(max_digits=10, decimal_places=2, default=25.00, verbose_name="Límite máximo de préstamo ($)")

    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            # Generar código único de 8 caracteres
            self.codigo_unico = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def total_gastado(self):
        """Calcula el total gastado en órdenes pagadas"""
        from django.db.models import Sum
        total = self.ordenes_set.filter(pagada=True).aggregate(Sum('total'))['total__sum'] or 0
        return total

    def aumentar_cupo(self, monto_compra):
        """
        Aumenta el límite de préstamo sumando el 25% del valor de la compra pagada.
        Fórmula: Nuevo = Actual + (Monto * 0.25)
        """
        from decimal import Decimal
        incremento = Decimal(monto_compra) * Decimal('0.25')
        if incremento > 0:
            self.limite_prestamo += incremento
            self.save()
            return incremento
        return 0

    def calcular_puntos_ganados(self, monto):
        """Calcula puntos ganados por un monto: 1 punto por cada $10"""
        return int(monto // 10)
    
    def agregar_puntos(self, monto):
        """Agrega puntos basados en el monto gastado [LEGACY: Ahora calculado dinámicamente]"""
        # Ya no acumulamos en el campo, se calcula por total_gastado
        pass
    
    def canjear_puntos(self, costo_puntos):
        """Valida si tiene puntos suficientes para canjear"""
        # La deducción ocurre al crear el objeto Recompensa que aumenta puntos_canjeados
        if self.puntos_actuales_calculados >= costo_puntos:
            return True
        return False

    def total_deuda_multas(self):
        """Calcula la deuda total por multas pendientes, excluyendo las de órdenes ya pagadas"""
        from django.db.models import Sum
        # Filtramos multas no pagadas Y que no pertenezcan a una orden ya pagada
        return self.multas.filter(pagada=False).exclude(orden__pagada=True).aggregate(total=Sum('monto'))['total'] or 0
    
    @property
    def limite_credito_calculado(self):
        """
        Calcula el límite de crédito dinámico:
        Base $50 + 15% del Total Gastado.
        """
        from decimal import Decimal
        base = Decimal('50.00')
        incremento = self.total_gastado() * Decimal('0.15')
        return base + incremento
    
    @property
    def puntos_totales_ganados(self):
        """Calcula el total histórico de puntos ganados (1 punto por cada $10 gastados)"""
        return int(self.total_gastado() // 10)

    @property
    def puntos_canjeados_total(self):
        """Calcula el total de puntos que ha canjeado el cliente"""
        from django.db.models import Sum
        # Sumar costo_puntos de recompensas que NO sean de tipo 'PUN' (si es que hay bonos) 
        # o simplemente todas las recompensas solicitadas/canjeadas.
        # Asumimos que 'recompensas' tiene un costo_puntos.
        # Filtramos recompensas que costaron puntos.
        return self.recompensas.aggregate(total=Sum('costo_puntos'))['total'] or 0

    @property
    def puntos_actuales_calculados(self):
        """Devuelve los puntos disponibles (Ganados - Canjeados)"""
        return self.puntos_totales_ganados - self.puntos_canjeados_total
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo_unico})"

class Empleados(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=150)
    cargo = models.CharField(max_length=100)
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
    ESTADOS_ORDEN = [
        ('SOLI', 'Solicitando Préstamo'),
        ('PREST', 'Con Préstamo'),
        ('PAGD', 'Pagado'),
        ('MULT', 'Multado'),
        ('CANC', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE)
    empleado = models.ForeignKey(Empleados, on_delete=models.SET_NULL, null=True, blank=True, help_text="Vendedor que procesó la orden")
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.CharField(max_length=5, choices=ESTADOS_ORDEN, default='SOLI', verbose_name="Estado")
    pagada = models.BooleanField(default=False, verbose_name="Pagada")
    puntos_asignados = models.BooleanField(default=False, verbose_name="Puntos Asignados")
    codigo_orden = models.CharField(max_length=8, unique=True, editable=False, default=uuid.uuid4)
    # Relación con Productos se maneja a través de DetallesOrdenes

    def save(self, *args, **kwargs):
        if not self.codigo_orden or len(self.codigo_orden) > 8:
             self.codigo_orden = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Orden #{self.codigo_orden} - {self.cliente.nombre} ({self.get_estado_display()})"




class Distribuidores(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class DetallesOrdenes(models.Model):
    orden = models.ForeignKey(Ordenes, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE, null=True, blank=True)
    coctel = models.ForeignKey(Cocteles, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        item_nombre = self.producto.nombre if self.producto else self.coctel.nombre
        return f"{self.cantidad} x {item_nombre} (Orden {self.orden.id})"


    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"

class Recompensas(models.Model):
    """Modelo para gestionar recompensas y regalos por consumo del cliente"""
    TIPO_RECOMPENSA = [
        ('PUN', 'Puntos'),
        ('DES', 'Descuento'),
        ('REG', 'Regalo/Producto Gratis'),
        ('BON', 'Bono Especial'),
        ('POR', 'Descuento Porcentual'),
    ]
    
    ESTADO_SOLICITUD = [
        ('PEND', 'Pendiente Aprobación'),
        ('APROB', 'Aprobada'),
        ('RECH', 'Rechazada'),
        ('ENTR', 'Entregada'),
    ]
    
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE, related_name='recompensas')
    tipo = models.CharField(max_length=3, choices=TIPO_RECOMPENSA, default='PUN', verbose_name="Tipo de Recompensa")
    descripcion = models.TextField(help_text="Descripción de la recompensa otorgada")
    valor = models.DecimalField(max_digits=10, decimal_places=2, help_text="Valor monetario o puntos")
    costo_puntos = models.IntegerField(default=0, verbose_name="Costo en Puntos", help_text="Puntos necesarios para canjear")
    fecha_otorgada = models.DateTimeField(auto_now_add=True)
    codigo_canje = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="Código único para canjear en caja/factura")
    fecha_vencimiento = models.DateField(null=True, blank=True, help_text="Fecha límite para usar la recompensa")
    utilizada = models.BooleanField(default=False)
    fecha_utilizacion = models.DateTimeField(null=True, blank=True)
    orden_relacionada = models.ForeignKey(Ordenes, on_delete=models.SET_NULL, null=True, blank=True, 
                                         help_text="Orden que generó esta recompensa")
    
    # Campos para workflow de solicitud
    solicitada_por_cliente = models.BooleanField(default=False, help_text="True si el cliente solicitó la recompensa")
    estado_solicitud = models.CharField(max_length=5, choices=ESTADO_SOLICITUD, default='PEND', verbose_name="Estado de Solicitud")
    fecha_solicitud = models.DateTimeField(null=True, blank=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    supervisor_aprobador = models.ForeignKey(Empleados, on_delete=models.SET_NULL, null=True, blank=True, related_name='recompensas_aprobadas')
    notas_supervisor = models.TextField(blank=True, null=True, verbose_name="Notas del Supervisor")
    fecha_confirmacion_entrega = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Recompensa"
        verbose_name_plural = "Recompensas"
        ordering = ['-fecha_otorgada']
    
    def __str__(self):
        if self.solicitada_por_cliente:
            return f"{self.cliente.nombre} - {self.get_tipo_display()} - {self.get_estado_solicitud_display()}"
        estado = "Utilizada" if self.utilizada else "Disponible"
        return f"{self.cliente.nombre} - {self.get_tipo_display()} - {estado}"

class Multas(models.Model):
    TIPOS_MULTA = [
        ('TARD', 'Pago Tardío de Orden'),
        ('DEVOL', 'Retraso en Devolución de Préstamo'),
        ('DANO', 'Daño a Instalaciones/Equipos'),
        ('COMP', 'Comportamiento Inadecuado'),
        ('OTRO', 'Otras Sanciones'),
    ]
    
    cliente = models.ForeignKey(Clientes, on_delete=models.CASCADE, related_name='multas')
    orden = models.ForeignKey('Ordenes', on_delete=models.SET_NULL, null=True, blank=True, related_name='multas', help_text="Orden que originó la multa")
    tipo = models.CharField(max_length=5, choices=TIPOS_MULTA, default='TARD')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()
    fecha_generada = models.DateTimeField(auto_now_add=True)
    pagada = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Multa {self.get_tipo_display()} - {self.cliente.nombre}: ${self.monto}"

class AuditLog(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=255)
    modulo = models.CharField(max_length=100)
    detalles = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"[{self.fecha.strftime('%Y-%m-%d %H:%M')}] {self.usuario} - {self.accion}"

class ProductoImportado(models.Model):
    ORIGEN_CHOICES = [('LICORES', 'OpenFoodFacts'), ('COCTELES', 'TheCocktailDB')]
    
    nombre = models.CharField(max_length=255)
    sku_api = models.CharField(max_length=100, unique=True) # ID o Código de barras
    imagen_url = models.URLField(max_length=500, null=True, blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES)
    fecha_importacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.origen}] {self.nombre}"
