from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticación
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro_cliente, name='registro_cliente'),
    path('accounts/validate/', views.validar_admin, name='validar_registro'),
    path('accounts/register/', views.registro_empleado_publico, name='registro_empleado_publico'),
    path('empleados/crear/', views.registro_empleado, name='crear_empleado'),

    # General
    path('', views.index, name='index'),
    path('productos/', views.productos_catalogo, name='productos'),
    path('clientes/', views.clientes_list, name='clientes'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('ordenes/<int:orden_id>/', views.detalle_orden, name='detalle_orden'),

    # Carrito y Checkout
    path('agregar/<str:tipo>/<int:item_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('quitar-uno/<str:tipo>/<int:item_id>/', views.quitar_uno_carrito, name='quitar_uno_carrito'),
    path('eliminar-item/<str:tipo>/<int:item_id>/', views.eliminar_item_carrito, name='eliminar_item_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('checkout/resumen/', views.resumen_checkout, name='resumen_checkout'),
    path('checkout/factura/', views.previsualizar_factura, name='previsualizar_factura'),
    path('checkout/procesar/<str:tipo>/', views.procesar_orden, name='procesar_orden'),

    # Inventario General
    path('inventario/productos/', views.catalogo_general, name='catalogo_general'),

    # Bodeguero (Productos)
    path('gestion/productos/', views.gestion_productos, name='gestion_productos'),
    path('gestion/productos/nuevo/', views.producto_crear, name='producto_crear'),
    path('gestion/productos/editar/<int:pk>/', views.producto_editar, name='producto_editar'),
    path('gestion/productos/eliminar/<int:pk>/', views.producto_eliminar, name='producto_eliminar'),
    path('gestion/productos/stock/<str:tipo>/<int:item_id>/', views.actualizar_stock, name='actualizar_stock'),
    path('gestion/importar-cocteles/', views.importar_cocteles, name='importar_cocteles'),
    path('gestion/importar-licores/', views.importar_licores, name='importar_licores'),

    # Supervisor (Préstamos, Recompensas y Multas)

    path('gestion/recompensas/', views.gestion_recompensas, name='gestion_recompensas'),
    path('global/canjes/', views.ver_canjes_global, name='ver_canjes_global'),
    path('gestion/prestamos/solicitudes/', views.gestion_solicitudes, name='gestion_solicitudes'),
    path('global/solicitudes/', views.ver_solicitudes_global, name='ver_solicitudes_global'),
    path('gestion/prestamos/activos/', views.gestion_prestamos, name='gestion_prestamos'),
    path('global/prestamos/', views.ver_prestamos_global, name='ver_prestamos_global'),
    path('gestion/multas/', views.gestion_multas, name='gestion_multas'),
    path('global/multas/', views.ver_multas_global, name='ver_multas_global'),

    
    # Administrador (Empleados y Auditoría)
    path('gestion/personal/', views.registro_empleado, name='registro_empleado'),
    path('gestion/auditoria/', views.auditoria_logs, name='auditoria_logs'),
    
    # Órdenes
    path('ordenes/', views.ordenes_list, name='ordenes'),
    path('ordenes/aprobar/<int:orden_id>/', views.aprobar_orden_solicitud, name='aprobar_orden_solicitud'),
    path('ordenes/cancelar/<int:orden_id>/', views.cancelar_orden_solicitud, name='cancelar_orden_solicitud'),
    path('ordenes/pagar/<int:pk>/', views.marcar_orden_pagada, name='marcar_orden_pagada'),

    # Cócteles
    path('cocteles/', views.cocteles_catalogo, name='cocteles_catalogo'),
    path('gestion/cocteles/', views.gestion_cocteles, name='gestion_cocteles'),
    path('gestion/cocteles/eliminar/<int:pk>/', views.eliminar_coctel, name='eliminar_coctel'),

    # Cliente
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('mis-prestamos/', views.mis_prestamos, name='mis_prestamos'),
    path('mis-multas/', views.mis_multas, name='mis_multas'),
    path('mis-solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),
    path('mis-recompensas/', views.mis_recompensas, name='mis_recompensas'),
    path('mis-registros-canjes/', views.mis_registros_canjes, name='mis_registros_canjes'),
    path('panel-fidelidad/', views.panel_fidelidad, name='panel_fidelidad'),
    path('solicitar-recompensa/', views.solicitar_recompensa, name='solicitar_recompensa'),
    path('solicitar-canje/', views.solicitar_canje, name='solicitar_canje'),
    path('confirmar-entrega/<int:recompensa_id>/', views.confirmar_entrega_recompensa, name='confirmar_entrega'),
    
    # Gestión de Cobros y Multas
    path('gestion-cobros/', views.gestion_cobros, name='gestion_cobros'),
    path('aplicar-multa/<int:orden_id>/', views.aplicar_multa, name='aplicar_multa'),
    
    # Supervisor - Aprobar Recompensas
    path('gestion/recompensas/aprobar/<int:recompensa_id>/', views.aprobar_recompensa, name='aprobar_recompensa'),
    
    # APIs
    path('api/cocteles/', views.api_views.CoctelesAPI.as_view(), name='api_cocteles'),
    path('api/importar/licores/buscar/', views.api_views.BusquedaLicoresAPIView.as_view(), name='buscar_licores_api'),
    path('api/importar/cocteles/buscar/', views.api_views.BusquedaCoctelesAPIView.as_view(), name='buscar_cocteles_api'),
    path('api/licores-off/', views.api_views.LicoresOFFAPI.as_view(), name='api_licores_off'),
]
