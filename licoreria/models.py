from django.db import models

class Categorias(models.Model):
    nombre = models.CharField(max_length=100)

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

    def __str__(self):
        return self.nombre

class Clientes(models.Model):
    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre

class Empleados(models.Model):
    nombre = models.CharField(max_length=150)
    cargo = models.CharField(max_length=100)
    sueldo = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

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
