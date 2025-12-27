from django.contrib import admin
from .models import Categorias, Productos, Clientes, Empleados

admin.site.register(Categorias)
admin.site.register(Productos)
admin.site.register(Clientes)
admin.site.register(Empleados)
