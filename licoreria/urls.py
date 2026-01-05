from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticación
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro_cliente, name='registro_cliente'),
    path('admin/empleado/nuevo/', views.registro_empleado, name='crear_empleado'),

    # General
    path('', views.index, name='index'),
    path('productos/', views.productos_catalogo, name='productos'),
    path('snacks/', views.snacks_catalogo, name='snacks'),
    path('clientes/', views.clientes_list, name='clientes'),
    path('ordenes/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),

    # Carrito y Checkout
    path('agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('eliminar/<int:producto_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('checkout/', views.checkout, name='checkout'),

    # Bodeguero (Productos)
    path('gestion/productos/', views.gestion_productos, name='gestion_productos'),
    path('gestion/productos/nuevo/', views.producto_crear, name='producto_crear'),
    path('gestion/productos/editar/<int:pk>/', views.producto_editar, name='producto_editar'),
    path('gestion/productos/eliminar/<int:pk>/', views.producto_eliminar, name='producto_eliminar'),

    # Supervisor (Préstamos y Recompensas)
    path('gestion/prestamos/', views.gestion_prestamos, name='gestion_prestamos'),
    path('gestion/recompensas/', views.gestion_recompensas, name='gestion_recompensas'),

    # Cliente
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('mis-prestamos/', views.mis_prestamos, name='mis_prestamos'),
]
