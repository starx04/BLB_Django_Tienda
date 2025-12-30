from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('productos/', views.productos, name='productos'),
    path('clientes/', views.clientes, name='clientes'),
    path('empleados/', views.empleados, name='empleados'),
    path('distribuidores/', views.distribuidores, name='distribuidores'),
    path('gastos/', views.gastos, name='gastos'),
    path('prestamos/', views.prestamos, name='prestamos'),
    path('ordenes/', views.ordenes, name='ordenes'),
    path('categorias/', views.categorias, name='categorias'),
    path('detalles_ordenes/', views.detalles_ordenes, name='detalles_ordenes'),
    path('agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('eliminar/<int:producto_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('checkout/', views.checkout_whatsapp, name='checkout_whatsapp'),
]
