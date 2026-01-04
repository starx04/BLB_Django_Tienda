from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views, api_views

urlpatterns = [
    # Auth Views
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/validate/', views.validar_registro, name='validar_registro'),
    path('accounts/register/', views.registro_empleado, name='registro_empleado'),

    # App Views
    path('', views.index, name='index'),
    path('productos/', views.productos, name='productos'),
    path('snacks/', views.snacks, name='snacks'),
    path('clientes/', views.clientes, name='clientes'),
    path('empleados/', views.empleados, name='empleados'),
    path('distribuidores/', views.distribuidores, name='distribuidores'),
    path('gastos/', views.gastos, name='gastos'),
    path('prestamos/', views.prestamos, name='prestamos'),
    path('ordenes/', views.ordenes, name='ordenes'),
    path('ordenes/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),
    path('categorias/', views.categorias, name='categorias'),
    path('agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('eliminar/<int:producto_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('checkout/', views.checkout_whatsapp, name='checkout_whatsapp'),
    
    # Endpoints de API
    path('api/licores/', api_views.LicoresAPI.as_view(), name='api_licores'),
    path('api/snacks/', api_views.SnacksAPI.as_view(), name='api_snacks'),
]
