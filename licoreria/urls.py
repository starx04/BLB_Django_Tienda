from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('eliminar/<int:producto_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('checkout/', views.checkout_whatsapp, name='checkout_whatsapp'),
]
