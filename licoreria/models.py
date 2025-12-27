from django.db import models

class Categorias(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Productos(models.Model):
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categorias, on_delete=models.CASCADE, related_name='productos', null=True, blank=True)
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
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    productos = models.ManyToManyField(Productos)

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
