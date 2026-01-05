from django.contrib import admin
from django.utils.html import format_html
from .models import (Categorias, Productos, Clientes, Empleados, Ordenes, Prestamos, 
                     Distribuidores, DetallesOrdenes, Gastos, Recompensas, Marcas)

# Configuración Personalizada del Admin

class DetallesOrdenInline(admin.TabularInline):
    model = DetallesOrdenes
    extra = 1

@admin.register(Productos)
class ProductosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'estado_stock')
    list_filter = ('categoria', 'distribuidor')
    search_fields = ('nombre',)
    
    def estado_stock(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="color: red; font-weight: bold;">AGOTADO</span>')
        elif obj.stock < 5:
            return format_html('<span style="color: orange; font-weight: bold;">BAJO ({})</span>', obj.stock)
        return format_html('<span style="color: green;">OK ({})</span>', obj.stock)
    estado_stock.short_description = 'Estado'

@admin.register(Ordenes)
class OrdenesAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha', 'total', 'empleado')
    inlines = [DetallesOrdenInline]
    readonly_fields = ('total',)  # El total se calcula solo

@admin.register(Gastos)
class GastosAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'monto', 'fecha', 'categoria_gasto')
    list_filter = ('categoria_gasto', 'fecha')

@admin.register(Recompensas)
class RecompensasAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'valor', 'fecha_otorgada', 'utilizada', 'fecha_vencimiento')
    list_filter = ('tipo', 'utilizada', 'fecha_otorgada')
    search_fields = ('cliente__nombre', 'descripcion')
    readonly_fields = ('fecha_otorgada', 'fecha_utilizacion')

# Registro simple para los demás
admin.site.register(Categorias)
admin.site.register(Clientes)
admin.site.register(Empleados)
admin.site.register(Prestamos)
admin.site.register(Distribuidores)
admin.site.register(Marcas)
# admin.site.register(DetallesOrdenes) # Ya está inline en Ordenes

