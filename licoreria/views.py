from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import uuid
from decimal import Decimal

from .forms import (ClienteForm, ProductoForm, RegistroClienteForm, RecompensaForm, 
                    RegistroEmpleadoForm, StockUpdateForm, MultaForm, CoctelForm)
from .models import (Clientes, Productos, Categorias, Marcas, Distribuidores, 
                    Recompensas, Empleados, Cocteles, Multas, AuditLog, Ordenes, DetallesOrdenes)
from .utils import log_action
from .decorators import (rol_requerido, administrador_required, bodeguero_required, 
                        supervisor_required, cliente_required)
from . import api_views

# --- Vistas Públicas ---

def registro_cliente(request):
    """Permite que cualquier persona se registre como Cliente"""
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            # 1. Crear el usuario de Django
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['nombre']
            )
            # 2. Asignar al grupo Cliente
            grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
            user.groups.add(grupo_cliente)
            
            # 3. Crear el perfil en el modelo Clientes
            cliente_perfil = form.save()
            
            messages.success(request, 'Registro exitoso. Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroClienteForm()
    return render(request, 'registration/register_cliente.html', {'form': form})

# --- Dashboard General ---

def index(request):
    """Vista de Dashboard Unificado con soporte para múltiples roles y público general."""
    hoy = timezone.now().date()
    
    # 1. Datos para Cliente (Autenticado)
    cliente_perfil = None
    if request.user.is_authenticated:
        from .models import Clientes, Ordenes, Productos, Recompensas
        # Obtener o crear perfil si es staff, o solo obtener si es cliente
        try:
            cliente_perfil = get_cliente_perfil(request)
        except:
            pass

    # 2. Inicializar Variables de Contexto
    context = {
        'hoy': hoy,
        'cliente': cliente_perfil,
        'is_public': not request.user.is_authenticated
    }

    # 3. Datos por Roles (Solo si está autenticado)
    if request.user.is_authenticated:
        user_groups = [g.name for g in request.user.groups.all()]
        is_admin = request.user.is_superuser or 'Administrador' in user_groups
        is_bodeguero = 'Bodeguero' in user_groups
        is_supervisor = 'Supervisor' in user_groups
        is_cliente = 'Cliente' in user_groups or (not is_admin and not is_bodeguero and not is_supervisor)

        # Estadísticas para Administración / Negocio
        if is_admin or is_supervisor:
            context['ventas_hoy'] = Ordenes.objects.filter(fecha__date=hoy, pagada=True).aggregate(Sum('total'))['total__sum'] or 0
            context['solicitudes_pendientes'] = Ordenes.objects.filter(estado='SOLI').count()
            context['canjes_pendientes'] = Recompensas.objects.filter(estado_solicitud='PEND').count()
            
            # Gráfico de ventas (7 días)
            chart_labels = []
            chart_data = []
            for i in range(6, -1, -1):
                fecha = hoy - timezone.timedelta(days=i)
                chart_labels.append(fecha.strftime("%d/%m"))
                venta_dia = Ordenes.objects.filter(fecha__date=fecha, pagada=True).aggregate(Sum('total'))['total__sum'] or 0
                chart_data.append(float(venta_dia))
            context['chart_labels'] = chart_labels
            context['chart_data'] = chart_data

        # Estadísticas para Bodega
        if is_admin or is_bodeguero:
            context['productos_stock'] = Productos.objects.aggregate(Sum('stock'))['stock__sum'] or 0
            context['stock_bajo'] = Productos.objects.filter(stock__lt=5).count()

        # Estadísticas para Cliente
        if is_cliente or cliente_perfil:
            if cliente_perfil:
                context['mis_puntos'] = cliente_perfil.puntos_actuales_calculados
                context['mi_cupo'] = cliente_perfil.limite_prestamo
                context['mis_ordenes_recientes'] = Ordenes.objects.filter(cliente=cliente_perfil).order_by('-fecha')[:5]

        context['role_context'] = {
            'is_admin': is_admin,
            'is_bodeguero': is_bodeguero,
            'is_supervisor': is_supervisor,
            'is_cliente': is_cliente
        }

    return render(request, 'index.html', context)

# --- Funciones de Bodeguero (Productos) ---

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def gestion_productos(request):
    productos_list = Productos.objects.all().order_by('nombre')
    return render(request, 'bodeguero/productos_list.html', {'productos': productos_list})

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def actualizar_stock(request, tipo, item_id):
    """ Actualiza stock para Licores o Cócteles con Logging """
    if tipo == 'licor':
        item = get_object_or_404(Productos, id=item_id)
        redirect_to = 'gestion_productos'
    else:
        item = get_object_or_404(Cocteles, id=item_id)
        redirect_to = 'gestion_cocteles'
        
    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']
            motivo = form.cleaned_data.get('motivo', 'Actualización manual')
            if item.stock + cantidad < 0:
                messages.error(request, f'No se puede reducir el stock por debajo de 0. Stock actual: {item.stock}')
                return redirect(redirect_to)
                
            item.stock += cantidad
            item.save()
            
            log_action(request.user, f"Stock {item.nombre}: {cantidad}", "Inventario", 
                       detalles=f"Motivo: {motivo}. Nuevo total: {item.stock}", request=request)
            
            messages.success(request, f'Stock de {item.nombre} actualizado.')
            return redirect(redirect_to)
    return redirect(redirect_to)

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def producto_crear(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('gestion_productos')
    else:
        form = ProductoForm()
    return render(request, 'bodeguero/producto_form.html', {'form': form, 'titulo': 'Crear Producto'})

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def producto_editar(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('gestion_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'bodeguero/producto_form.html', {'form': form, 'titulo': 'Editar Producto'})

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def importar_licores(request):
    """Vista para la importación profesional de licores con OFF y Unsplash"""
    categorias = Categorias.objects.all()
    return render(request, 'bodeguero/importar_licores.html', {'categorias': categorias})

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def producto_eliminar(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('gestion_productos')
    return render(request, 'bodeguero/producto_confirm_delete.html', {'producto': producto})

# --- Módulo de Cócteles ---

def cocteles_catalogo(request):
    """Catálogo público de cócteles e ingredientes"""
    busqueda = request.GET.get('busqueda')
    cocteles = Cocteles.objects.all().order_by('nombre')
    
    if busqueda:
        cocteles = cocteles.filter(Q(nombre__icontains=busqueda) | Q(ingredientes__icontains=busqueda))
        
    return render(request, 'cliente/cocteles_catalog.html', {'cocteles': cocteles})

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def gestion_cocteles(request):
    """Administración de la lista de cócteles importados"""
    cocteles = Cocteles.objects.all().order_by('-fecha_creacion')
    return render(request, 'bodeguero/cocteles_list.html', {'cocteles': cocteles})

@login_required
@rol_requerido('Bodeguero', 'Administrador')
def eliminar_coctel(request, pk):
    coctel = get_object_or_404(Cocteles, pk=pk)
    if request.method == 'POST':
        nombre = coctel.nombre
        coctel.delete()
        messages.success(request, f'Cóctel {nombre} eliminado correctamente.')
        return redirect('gestion_cocteles')
    return render(request, 'bodeguero/coctel_confirm_delete.html', {'coctel': coctel})

# --- Auxiliares ---
def get_cliente_perfil(request):
    """
    Retorna el perfil de cliente del usuario logueado.
    Si es Admin/Supervisor y no tiene perfil, lo crea automáticamente.
    """
    if not request.user.is_authenticated:
        return None
        
    cliente = Clientes.objects.filter(Q(email=request.user.email) | Q(user=request.user)).first()
    
    if not cliente and (request.user.is_staff or request.user.is_superuser):
        # Auto-creación para administradores
        cliente = Clientes.objects.create(
            user=request.user,
            nombre=f"Admin: {request.user.username}",
            email=request.user.email or f"{request.user.username}@licoreria.internal",
            telefono="0000000000",
            limite_prestamo=1000.00 # Cupo administrativo alto
        )
    return cliente

# --- Vistas de Supervisor (Préstamos y Recompensas) ---

@login_required
@rol_requerido('Supervisor', 'Administrador')
def gestion_solicitudes(request):
    """Manejo de estados SOLI de Ordenes"""
    if request.method == 'POST':
        orden_id = request.POST.get('orden_id')
        accion = request.POST.get('accion')
        orden = get_object_or_404(Ordenes, id=orden_id)
        
        if accion == 'aprobar':
            orden.estado = 'PREST'
            orden.save()
            messages.success(request, f'Orden #{orden.codigo_orden} aprobada como préstamo activo.')
        elif accion == 'rechazar':
            orden.estado = 'CANC'
            orden.save()
            # Devolver stock
            for detalle in orden.detalles.all():
                if detalle.producto:
                    detalle.producto.stock += detalle.cantidad
                    detalle.producto.save()
                elif detalle.coctel:
                    detalle.coctel.stock += detalle.cantidad
                    detalle.coctel.save()
            messages.warning(request, f'Solicitud #{orden.codigo_orden} rechazada y stock devuelto.')
        return redirect('gestion_solicitudes')

    solicitudes = Ordenes.objects.filter(estado='SOLI').order_by('-fecha')
    return render(request, 'supervisor/solicitudes.html', {'solicitudes': solicitudes})


@login_required
@rol_requerido('Supervisor', 'Administrador')
def ver_solicitudes_global(request):
    """Vista global de todas las solicitudes de préstamo de todos los usuarios"""
    # Obtener todas las órdenes en estado SOLI (solicitudes pendientes)
    # Corrección: related_name='detalles'
    solicitudes = Ordenes.objects.filter(estado='SOLI').select_related('cliente', 'empleado').prefetch_related('detalles').order_by('-fecha')
    
    return render(request, 'global/solicitudes.html', {
        'solicitudes': solicitudes,
    })

@login_required
@rol_requerido('Supervisor', 'Administrador')
def gestion_prestamos(request):
    """Manejo de estados PREST de Ordenes"""
    prestamos = Ordenes.objects.filter(estado='PREST').order_by('-fecha')
    return render(request, 'supervisor/prestamos_activos.html', {'prestamos': prestamos})


@login_required
@rol_requerido('Supervisor', 'Administrador')
def ver_prestamos_global(request):
    """Vista global de todos los préstamos activos (ya aprobados)"""
    # Mostrar SOLO préstamos activos (PREST), las solicitudes están en su propia vista
    # Corrección: related_name='detalles'
    prestamos = Ordenes.objects.filter(
        estado='PREST'
    ).select_related('cliente', 'empleado').prefetch_related('detalles').order_by('-fecha')
    
    return render(request, 'global/prestamos.html', {
        'prestamos': prestamos,
    })

@login_required
def resumen_checkout(request):
    """Vista que muestra el resumen del carrito antes de decidir pago o préstamo"""
    carrito = request.session.get('cart', {})
    if not carrito:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('index')
    
    # Obtener el cliente de forma robusta
    cliente = get_cliente_perfil(request)
    if not cliente:
        messages.error(request, 'Debes completar tu perfil de cliente antes de comprar.')
        return redirect('index')

    items_resumen = []
    total = 0
    
    for key, cant in carrito.items():
        try:
            tipo, item_id = key.split('_')
            if tipo == 'lic':
                item = Productos.objects.select_related('categoria').get(id=item_id)
                seccion = "Licores"
            else:
                item = Cocteles.objects.get(id=item_id)
                seccion = "Cócteles"
            
            sub = item.precio * cant
            total += sub
            items_resumen.append({
                'item': item,
                'cantidad': cant,
                'subtotal': sub,
                'seccion': seccion
            })
        except:
            continue

    # Validar multas pendientes (Solo informativo)
    total_deuda = float(cliente.total_deuda_multas())
    if total_deuda > 0:
        messages.warning(request, f'Tienes multas pendientes por ${total_deuda:.2f} asociadas a órdenes anteriores.')
    
    has_fines = total_deuda > 0
    
    # [BLOQUEO ELIMINADO]: El usuario pidió que las multas no bloqueen el carrito globalmente
    # if Ordenes.objects.filter(cliente=cliente, estado='MULT').exists():
    #    ...

    # Calculo de Credito Disponible (Sin restar multas)
    limite_total = cliente.limite_credito_calculado
    deuda_ordenes = cliente.ordenes_set.filter(pagada=False).aggregate(total=Sum('total'))['total'] or Decimal('0')
    # credito_disponible = limite_total - (deuda_ordenes + Decimal(total_deuda)) 
    credito_disponible = limite_total - deuda_ordenes
    
    context = {
        'items': items_resumen,
        'total': total,
        'cliente': cliente,
        'fecha': timezone.now(),
        # 'es_administrativo': request.user.is_staff or request.user.is_superuser, # Legacy?
        'es_administrativo': request.user.is_staff or request.user.is_superuser,
        'has_fines': has_fines,
        'credito_disponible': credito_disponible
    }
    return render(request, 'resumen_checkout.html', context)

@login_required
def previsualizar_factura(request):
    """Vista de factura previa antes del pago final"""
    carrito = request.session.get('cart', {})
    if not carrito:
        return redirect('index')
    
    # Obtener el cliente de forma robusta
    cliente = get_cliente_perfil(request)
    if not cliente:
        messages.error(request, 'No se pudo identificar un perfil de cliente.')
        return redirect('index')

    items_resumen = []
    total = 0
    subtotal_general = 0
    iva_general = 0
    
    # Validar STOCK antes de cualquier cosa
    for key, cant in carrito.items():
        try:
            tipo, item_id = key.split('_')
            if tipo == 'lic':
                item_val = Productos.objects.get(id=item_id)
            else:
                item_val = Cocteles.objects.get(id=item_id)
            
            if cant > item_val.stock:
                messages.error(request, f'Stock insuficiente para {item_val.nombre}. Disponibles: {item_val.stock}')
                return redirect('ver_carrito')
            if item_val.stock <= 0:
                 messages.error(request, f'El producto {item_val.nombre} se ha agotado.')
                 return redirect('ver_carrito')
        except:
             continue # Si hay error de datos, se limpiará luego o ignorará

    for key, cant in carrito.items():
        try:
            tipo, item_id = key.split('_')
            if tipo == 'lic':
                item = Productos.objects.select_related('categoria').get(id=item_id)
            else:
                item = Cocteles.objects.get(id=item_id)
            
            sub = item.precio * cant
            total += sub
            items_resumen.append({
                'item': item,
                'cantidad': cant,
                'subtotal': sub,
                'tipo': tipo,
                'item_id': item_id
            })
        except:
            continue
            
    # Calculos básicos de factura
    # --- Lógica Descuentos ---
    descuento_aplicado = 0
    codigo_obj = None
    
    # Limpiar descuento previo si no es POST
    if request.method != 'POST':
        if 'descuento_id' in request.session:
            del request.session['descuento_id']
            
    if request.method == 'POST' and request.POST.get('aplicar_codigo'):
        codigo_str = request.POST.get('codigo_canje', '').strip()
        try:
            recompensa = Recompensas.objects.get(codigo_canje=codigo_str, utilizada=False, cliente=cliente)
            
            # --- Validacion de Compra Minima ---
            from .catalogo_recompensas import CATALOGO_RECOMPENSAS
            
            # Buscar regla en catalogo
            regla_item = next((
                r for r in CATALOGO_RECOMPENSAS 
                if r['tipo'] == recompensa.tipo and r['valor'] == recompensa.valor
            ), None)
            
            min_compra = Decimal(str(regla_item['min_compra'])) if regla_item and 'min_compra' in regla_item else Decimal('0')
            
            if total < min_compra:
                messages.error(request, f"Este cupón requiere una compra mínima de ${min_compra}.")
            else:
                # Validar si es tipo descuento
                if recompensa.tipo == 'DES':
                    descuento_aplicado = Decimal(recompensa.valor)
                    # No permitir totales negativos
                    if total < descuento_aplicado:
                         descuento_aplicado = total # Ajustar al maximo posible
                         
                    total -= descuento_aplicado
                    request.session['descuento_id'] = recompensa.id
                    messages.success(request, f"Cupón de ${descuento_aplicado} aplicado.")
                    
                elif recompensa.tipo == 'POR':
                    porcentaje = Decimal(recompensa.valor)
                    descuento_aplicado = total * (porcentaje / 100)
                    total -= descuento_aplicado
                    request.session['descuento_id'] = recompensa.id
                    messages.success(request, f"Descuento del {porcentaje}% (${descuento_aplicado:.2f}) aplicado.")
                    
                else:
                     messages.warning(request, "Este código corresponde a una recompensa física, no un descuento.")
                     
        except Recompensas.DoesNotExist:
            messages.error(request, "Código inválido, incorrecto o ya utilizado.")

    # Recalcular IVA y Subtotal con el nuevo total (si hubo descuento)
    # Total = Subtotal + IVA
    # Subtotal = Total / 1.15
    if total < 0: total = 0
    
    # Calculos básicos de factura
    iva_rate = Decimal('0.15') # 15% IVA
    subtotal_general = total / (1 + iva_rate)
    iva_general = total - subtotal_general

    licoreria_info = {
        'nombre': 'LICORERÍA PREMIUM BLB',
        'direccion': 'Ecuador, Calle Neon 777',
        'telefono': '+593 99 123 4567',
        'email': 'ventas@blb_premium.com',
        'ruc': '1792345678001'
    }

    # --- Lógica Multas ---
    vencidas = Multas.objects.filter(cliente=cliente, pagada=False)
    total_multas = Decimal(cliente.total_deuda_multas())
    # total += total_multas  <-- ELIMINADO: No cobrar multas en la orden actual

    # Fetch available rewards (coupons) for the client
    recompensas_disponibles = Recompensas.objects.filter(
        cliente=cliente, 
        utilizada=False, 
        estado_solicitud='APROB'
    ).filter(Q(tipo='DES') | Q(tipo='POR'))

    context = {
        'items': items_resumen,
        'subtotal': subtotal_general,
        'iva': iva_general,
        'total': total,
        'descuento_aplicado': descuento_aplicado,
        'total_multas': total_multas,
        'multas_lista': vencidas,
        'recompensas_disponibles': recompensas_disponibles,
        'cliente_nombre': cliente.nombre,
        'cliente_email': cliente.email,
        'cliente_telefono': cliente.telefono if cliente.telefono and cliente.telefono != '0000000000' else None,
        'user_username': request.user.username,
        'fecha': timezone.now(),
        'licoreria': licoreria_info,
        'codigo_factura': uuid.uuid4().hex[:8].upper()
    }
    return render(request, 'factura_previa.html', context)

@login_required
@transaction.atomic
def procesar_orden(request, tipo):
    """Procesa la orden como PAGO o PRESTAMO"""
    carrito = request.session.get('cart', {})
    if not carrito:
        return redirect('index')

    # Obtener el cliente de forma robusta
    cliente = get_cliente_perfil(request)
    if not cliente:
        messages.error(request, 'No se identificó un perfil de cliente vinculado.')
        return redirect('index')

    # Calcular total
    total_orden = Decimal('0.00')
    items_to_process = []
    
    for key, cant in carrito.items():
        try:
            t, item_id = key.split('_')
            if t == 'lic':
                item = Productos.objects.get(id=item_id)
            else:
                item = Cocteles.objects.get(id=item_id)
            
            # --- VALIDACIÓN FINAL DE STOCK ---
            if cant > item.stock:
                messages.error(request, f"¡CRÍTICO! Stock insuficiente para {item.nombre} al procesar. Disponibles: {item.stock}")
                return redirect('ver_carrito')
            
            subtotal = item.precio * cant
            total_orden += subtotal
            items_to_process.append((item, cant, item.precio))
        except:
            continue

    # Validar crédito y multas si no es administrativo
    es_admin = request.user.is_staff or request.user.is_superuser
    
    # Procesar Descuento si existe en sesión
    descuento_id = request.session.get('descuento_id')
    recompensa_usada = None
    
    if descuento_id:
        try:
            recompensa_usada = Recompensas.objects.get(id=descuento_id, utilizada=False)
            
            if recompensa_usada.tipo == 'DES':
                total_orden -= Decimal(str(recompensa_usada.valor))
            elif recompensa_usada.tipo == 'POR':
                descuento_val = total_orden * (Decimal(str(recompensa_usada.valor)) / 100)
                total_orden -= descuento_val
                
            if total_orden < 0: total_orden = Decimal('0.00')
        except Recompensas.DoesNotExist:
            request.session.pop('descuento_id', None)

    if tipo == 'PRESTAMO' and not es_admin:
        # 1. Bloqueo por multas pendientes
        deuda_multas = cliente.total_deuda_multas()
        if deuda_multas > 0:
            messages.error(request, f'Tienes multas pendientes por ${deuda_multas}. Debes pagarlas antes de solicitar nuevos préstamos.')
            return redirect('resumen_checkout')

        # 2. Bloqueo por límite de crédito REAL (Límite - Deuda Actual)
        limite_total = cliente.limite_credito_calculado
        deuda_ordenes = cliente.ordenes_set.filter(pagada=False).aggregate(total=Sum('total'))['total'] or Decimal('0')
        credito_disponible = limite_total - (deuda_ordenes + deuda_multas)
        
        if total_orden > credito_disponible:
            messages.error(request, f'Cupo Insuficiente. Intentas solicitar ${total_orden:.2f} pero solo dispones de ${credito_disponible:.2f} (Límite Total: ${limite_total:.2f}).')
            return redirect('resumen_checkout')

    # Generar código único con prefijo BLB-
    codigo_unico = f"BLB-{uuid.uuid4().hex[:6].upper()}"

    # Determinar estado
    if tipo == 'PRESTAMO':
        estado = 'SOLI'
        pagada = False
        mensaje = f'Solicitud de Préstamo {codigo_unico} creada.'
        # Si es prestamo no usamos el descuento aun? O si?
        # Decisión: Si es prestamo SOLICITUD, el descuento se "reserva" o se aplica solo al pagar?
        # Por simplicidad, lo aplicamos ya, porque el VALOR de la deuda es menor.
        # Pero si se RECHAZA, la recompensa deberia volver. 
        # IMPLEMENTACION SIMPLE: Marcar usada ya. Si se rechaza prestamo, la logica de rechazo deberia liberar recompensa.
        # (Complejidad alta, asumiremos que si es prestamo NO se permite descuento por ahora o se aplica directo)
        
    elif tipo == 'PAGO':
        estado = 'PAGD'
        pagada = True
        mensaje = f'Orden {codigo_unico} pagada exitosamente.'
        
        # --- MODIFICADO: NO Cobrar Multas Automáticamente ---
        # El usuario solicitó que las multas de otras órdenes NO se cobren aquí.
        # multas_pendientes = Multas.objects.filter(cliente=cliente, pagada=False)
        # total_multas = sum(float(m.monto) for m in multas_pendientes)
        # total_orden += total_multas 
        # multas_pendientes.update(pagada=True, fecha_pago=timezone.now())
        
        # Asignar puntos automáticamente si es pago directo
        cliente.agregar_puntos(total_orden)
        # Y aumentar cupo
        cliente.aumentar_cupo(total_orden)
    else:
        return redirect('resumen_checkout')

    # Crear Orden
    orden = Ordenes.objects.create(
        cliente=cliente,
        total=total_orden,
        estado=estado,
        pagada=pagada,
        puntos_asignados=pagada, # Si ya pagó, ya tiene puntos (o se asignaron arriba)
        codigo_orden=codigo_unico
    )

    # Vincular y marcar recompensa utilizada a la orden (Tanto Pago como Préstamo)
    if recompensa_usada:
        recompensa_usada.utilizada = True
        recompensa_usada.fecha_utilizacion = timezone.now()
        recompensa_usada.orden_relacionada = orden
        recompensa_usada.save()
        request.session.pop('descuento_id', None)

    # Crear Detalles y descontar stock
    for item, cant, precio in items_to_process:
        if isinstance(item, Productos):
            DetallesOrdenes.objects.create(
                orden=orden,
                producto=item,
                cantidad=cant,
                precio_unitario=precio
            )
            # El stock de Productos se descuenta vía señal post_save en DetallesOrdenes
        else:
            # Para Cocteles, ahora sí guardamos el detalle
            DetallesOrdenes.objects.create(
                orden=orden,
                coctel=item, # Guardamos en el campo coctel
                cantidad=cant,
                precio_unitario=precio
            )
            # Descontamos stock vía señal post_save en DetallesOrdenes (ahora soporta cocteles)
            pass

    # Limpiar carrito
    request.session['cart'] = {}
    
    messages.success(request, mensaje)
    return redirect('ordenes')

@login_required
@rol_requerido('Supervisor', 'Administrador')
def gestion_multas(request):
    """ Sistema de multas vinculadas al negocio """
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'pagar':
            multa_id = request.POST.get('pagar_id')
            multa = get_object_or_404(Multas, id=multa_id)
            multa.pagada = True
            multa.fecha_pago = timezone.now()
            multa.save()
            log_action(request.user, f"Pago de Multa: {multa.cliente.nombre}", "Sanciones", 
                       detalles=f"Monto: ${multa.monto}", request=request)
            messages.success(request, f'Pago de multa de ${multa.monto} registrado.')
            return redirect('gestion_multas')
            
        form = MultaForm(request.POST)
        if form.is_valid():
            multa = form.save()
            log_action(request.user, f"Nueva Multa: {multa.cliente.nombre}", "Sanciones", 
                       detalles=f"Tipo: {multa.get_tipo_display()}, Monto: ${multa.monto}", request=request)
            messages.success(request, 'Multa aplicada correctamente.')
            return redirect('gestion_multas')
    else:
        form = MultaForm()
    
    multas = Multas.objects.all().order_by('-fecha_generada')
    return render(request, 'supervisor/multas.html', {'multas': multas, 'form': form})


@login_required
@rol_requerido('Supervisor', 'Administrador')
def ver_multas_global(request):
    """Vista global de todas las multas de todos los usuarios"""
    # Obtener todas las multas ordenadas por fecha (más recientes primero)
    multas = Multas.objects.select_related('cliente', 'orden').order_by('-fecha_generada')
    
    return render(request, 'global/multas.html', {
        'multas': multas,
    })

@login_required
@administrador_required
def auditoria_logs(request):
    """ Visualización de logs de auditoría (Solo Admin) """
    logs = AuditLog.objects.all()[:200] # Mostrar últimos 200
    return render(request, 'admin/logs.html', {'logs': logs})

@login_required
@rol_requerido('Supervisor', 'Administrador', 'Bodeguero')
def gestion_recompensas(request):
    from .catalogo_recompensas import CATALOGO_RECOMPENSAS
    
    if request.method == 'POST':
        form = RecompensaForm(request.POST)
        if form.is_valid():
            recompensa = form.save(commit=False)
            recompensa.solicitada_por_cliente = False
            recompensa.estado_solicitud = 'APROB'  # Auto-aprobada si la crea el supervisor
            recompensa.save()
            messages.success(request, 'Recompensa otorgada.')
            return redirect('gestion_recompensas')
    else:
        form = RecompensaForm()
    
    # Separar solicitudes pendientes de clientes y recompensas aprobadas
    solicitudes_pendientes = Recompensas.objects.filter(
        solicitada_por_cliente=True,
        estado_solicitud='PEND'
    ).order_by('-fecha_solicitud')
    
    recompensas_aprobadas = Recompensas.objects.filter(
        estado_solicitud__in=['APROB', 'ENTR']
    ).order_by('-fecha_otorgada')
    
    recompensas_rechazadas = Recompensas.objects.filter(
        estado_solicitud='RECH'
    ).order_by('-fecha_solicitud')
    
    # Intento de obtener perfil de cliente para el supervisor (si quiere canjear)
    puntos_usuario = 0
    try:
        match_cliente = Clientes.objects.get(user=request.user)
        puntos_usuario = match_cliente.puntos_acumulados
    except Clientes.DoesNotExist:
        puntos_usuario = 0
        
    cupones = [r for r in CATALOGO_RECOMPENSAS if r.get('seccion') == 'efectivo']
    porcentajes = [r for r in CATALOGO_RECOMPENSAS if r.get('seccion') == 'porcentaje']

    # Identificar qué items del catálogo ya tiene el usuario activos (no utilizados)
    ids_activas = []
    if match_cliente:
        # Obtenemos recompensas activas (Aprobadas y no utilizadas)
        recompensas_activas = Recompensas.objects.filter(
            cliente=match_cliente, 
            utilizada=False, 
            estado_solicitud='APROB'
        )
        
        # Mapeo simple: Si existe una recompensa con mismo valor y costo, marcamos el ID del catálogo
        for item in CATALOGO_RECOMPENSAS:
            # Check si existe alguna recompensa que coincida con las características de este item
            matches = recompensas_activas.filter(
                tipo=item['tipo'],
                valor=item['valor'],
                costo_puntos=item['costo_puntos']
            ).exists()
            if matches:
                ids_activas.append(item['id'])
    
    return render(request, 'supervisor/recompensas.html', {
        'form': form,
        'catalogo': CATALOGO_RECOMPENSAS,
        'cupones': cupones,
        'porcentajes': porcentajes,
        'puntos': puntos_usuario,
        'ids_activas': ids_activas, # IDs de recompensas que el usuario ya tiene
        'solicitudes_pendientes': solicitudes_pendientes,
        'recompensas': recompensas_aprobadas,
        'recompensas_rechazadas': recompensas_rechazadas,
    })


@login_required
@rol_requerido('Supervisor', 'Administrador')
def ver_canjes_global(request):
    """Vista global de todos los canjes de puntos de todos los usuarios"""
    # Obtener todas las recompensas ordenadas por fecha de solicitud (más recientes primero)
    canjes = Recompensas.objects.select_related('cliente', 'supervisor_aprobador').order_by('-fecha_solicitud', '-fecha_otorgada')
    
    return render(request, 'global/canjes.html', {
        'canjes': canjes,
    })


@login_required
def ordenes_list(request):
    """Vista global de órdenes para Staff"""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('mis_compras')
    
    ordenes = Ordenes.objects.select_related('cliente').all().order_by('-fecha')
    
    # Calcular estadísticas
    stats = {
        'solicitudes': ordenes.filter(estado='SOLI').count(),
        'prestamos': ordenes.filter(estado='PREST').count(),
        'pagadas': ordenes.filter(estado='PAGD').count(),
        'pendientes_pago': ordenes.filter(pagada=False).exclude(estado='CANC').count()
    }
    
    return render(request, 'ordenes.html', {'ordenes': ordenes, 'stats': stats})

@login_required
@transaction.atomic
def aprobar_orden_solicitud(request, orden_id):
    """Aprueba una solicitud de préstamo y la convierte en préstamo activo"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permiso.')
        return redirect('index')
        
    orden = get_object_or_404(Ordenes, id=orden_id)
    
    if orden.estado == 'SOLI':
        orden.estado = 'PREST'
        # Intentar asignar el empleado actual
        try:
            orden.empleado = Empleados.objects.get(user=request.user)
        except Empleados.DoesNotExist:
            # Si es superusuario admin sin perfil de empleado, dejar nulo o manejar según lógica
            orden.empleado = None

        orden.save()
        
        log_action(request.user, f"Aprobó Solicitud: {orden.codigo_orden}", 
                   "Préstamos", detalles=f"Cliente: {orden.cliente.nombre}", request=request)
        messages.success(request, f'Solicitud {orden.codigo_orden} aprobada correctamente.')
    else:
        messages.warning(request, 'Esta orden no está en estado de solicitud.')
        
    return redirect('ordenes')


@login_required
def mis_compras(request):
    """Cliente ve sus propias compras"""
    cliente = get_cliente_perfil(request)
    if not cliente:
        return redirect('index')
    
    ordenes = Ordenes.objects.filter(cliente=cliente).order_by('-fecha')
    return render(request, 'cliente/mis_compras.html', {
        'ordenes': ordenes,
        'cliente': cliente
    })

@login_required
def marcar_orden_pagada(request, pk):
    orden = get_object_or_404(Ordenes, pk=pk)
    
    # Seguridad: solo el dueño de la orden o el personal administrativo puede marcarla como pagada
    es_personal = request.user.is_staff or request.user.is_superuser
    if not es_personal and request.user.email != orden.cliente.email:
        messages.error(request, "No tienes permiso para pagar esta orden.")
        return redirect('index')

    # VALIDACIÓN: No se puede pagar una solicitud pendiente
    if orden.estado == 'SOLI':
        messages.error(request, f"La Orden #{orden.codigo_orden} es una solicitud pendiente. Debe ser aprobada primero.")
        return redirect('gestion_solicitudes')

    if not orden.pagada:
        orden.pagada = True
        
        # Asignar puntos si no se han asignado
        if not orden.puntos_asignados:
            orden.cliente.agregar_puntos(orden.total)
            orden.puntos_asignados = True
        
        # Actualizar estado a PAGD
        orden.estado = 'PAGD'
        orden.save()
        
        # --- NUEVO: Marcar multas de ESTA orden como pagadas ---
        multas_asociadas = Multas.objects.filter(orden=orden, pagada=False)
        if multas_asociadas.exists():
            count = multas_asociadas.update(pagada=True, fecha_pago=timezone.now())
            messages.info(request, f'Se han regularizado {count} multas vinculadas a esta orden.')
        incremento = orden.cliente.aumentar_cupo(orden.total)
        if incremento > 0:
            messages.info(request, f"¡Aumento de crédito (+${incremento})! El nuevo límite de {orden.cliente.nombre} es ${orden.cliente.limite_prestamo}")

        log_action(request.user, f"Orden #{orden.id} Pagada", "Ventas", 
                   detalles=f"Total: ${orden.total}", request=request)
        messages.success(request, f'Orden #{orden.id} marcada como pagada.')
    # Si venía de la lista de préstamos, volver ahí
    if orden.estado == 'PAGD' and 'activos' in request.META.get('HTTP_REFERER', ''):
        return redirect('gestion_prestamos')
        
    return redirect('ordenes')

# --- Funciones de Cliente (Mis Compras y Préstamos) ---



@login_required
@cliente_required
def mis_prestamos(request):
    # Mostrar solo préstamos activos (PREST), no solicitudes
    try:
        cliente_perfil = Clientes.objects.get(email=request.user.email)
        # Buscar solo órdenes con estado PREST (préstamos activos)
        prestamos = Ordenes.objects.filter(cliente=cliente_perfil, estado='PREST').order_by('-fecha')
    except Clientes.DoesNotExist:
        prestamos = []
    
    return render(request, 'cliente/mis_prestamos.html', {'prestamos': prestamos})


@login_required
def mis_multas(request):
    """Cliente ve sus propias multas"""
    cliente = get_cliente_perfil(request)
    if not cliente:
        return redirect('index')
    
    multas = Multas.objects.filter(cliente=cliente).order_by('-fecha_generada')
    return render(request, 'cliente/mis_multas.html', {
        'multas': multas,
        'cliente': cliente
    })


@login_required
def mis_solicitudes(request):
    """Cliente ve sus propias solicitudes de préstamo pendientes"""
    cliente = get_cliente_perfil(request)
    if not cliente:
        return redirect('index')
    
    solicitudes = Ordenes.objects.filter(cliente=cliente, estado='SOLI').order_by('-fecha')
    return render(request, 'cliente/mis_solicitudes.html', {
        'solicitudes': solicitudes,
        'cliente': cliente
    })

# --- Gestión de Empleados (Solo Administrador) ---

@login_required
@administrador_required
def registro_empleado(request):
    """Ver todo el personal administrativo y crear nuevos (Solo Administrador)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        nombre = request.POST.get('nombre')
        cargo = request.POST.get('cargo')
        passw = request.POST.get('password')
        rol = request.POST.get('rol')  # 'Bodeguero', 'Supervisor', o 'Administrador'
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
        else:
            try:
                # Crear usuario
                user = User.objects.create_user(username=username, email=email, password=passw)
                
                # Definir si es staff (personal administrativo)
                if rol != 'Cliente':
                    user.is_staff = True
                
                # Si es administrador, darle permisos de superusuario
                if rol == 'Administrador':
                    user.is_superuser = True
                
                user.save()
                
                # Asignar grupo (excepto para administradores que ya son superusuarios)
                # O incluirlos a todos si queremos consistencia total
                try:
                    grupo, _ = Group.objects.get_or_create(name=rol)
                    user.groups.add(grupo)
                except Exception as e:
                    print(f"Error al asignar grupo: {e}")
                
                # Crear perfil según el rol
                if rol == 'Cliente':
                    Clientes.objects.create(
                        user=user,
                        nombre=nombre,
                        email=email,
                        telefono='0000000000' # Valor por defecto
                    )
                else:
                    # El cargo debe coincidir con el rol para evitar confusión en el listado
                    Empleados.objects.create(
                        user=user,
                        nombre=nombre,
                        cargo=rol # Usar el ROL como cargo principal
                    )
                
                messages.success(request, f'Cuenta de {rol} ({nombre}) creada exitosamente.')
                return redirect('registro_empleado')
            except Exception as e:
                messages.error(request, f'Error al crear personal: {str(e)}')
    
    # Listar TODO el personal administrativo (staff users)
    # Incluye administradores, supervisores, bodegueros
    empleados = Empleados.objects.all().select_related('user').order_by('-id')
    
    # También incluir administradores que no tienen registro en Empleados
    staff_users = User.objects.filter(is_staff=True).select_related('empleados')
    
    return render(request, 'admin/empleados.html', {
        'empleados': empleados,
        'staff_users': staff_users
    })

# --- Catálogo y Carrito (Acceso General para comprar) ---

@bodeguero_required
def importar_cocteles(request):
    categorias = Categorias.objects.all()
    return render(request, 'bodeguero/importar_cocteles.html', {'categorias': categorias})

def productos_catalogo(request):
    # Ya no excluimos nada, mostramos todo
    categorias = Categorias.objects.all()
    
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda')
    precio_max = request.GET.get('precio_max')
    
    productos_list = Productos.objects.all()
    
    # Filtros
    if busqueda:
        productos_list = productos_list.filter(Q(nombre__icontains=busqueda) | Q(marca__nombre__icontains=busqueda))
    if categoria_id:
        productos_list = productos_list.filter(categoria_id=categoria_id)
    if precio_max:
        try:
             productos_list = productos_list.filter(precio__lte=float(precio_max))
        except ValueError:
             pass
        
    categoria_activa_id = None
    if categoria_id:
        try:
            categoria_activa_id = int(categoria_id)
        except ValueError:
            pass

    # Lógica de Visualización:
    # 1. Si hay filtros activos (búsqueda, categoría o precio), mostrar lista plana.
    # 2. Si NO hay filtros, mostrar vista por categorías (Top 5 por categoría).
    
    modo_busqueda = True if (busqueda or categoria_id or precio_max) else False
    
    categorias_preview = []
    if not modo_busqueda:
        for cat in categorias:
            # Traer solo los primeros 5 productos de cada categoria
            prods = Productos.objects.filter(categoria=cat)[:5]
            if prods.exists():
                categorias_preview.append({
                    'categoria': cat,
                    'productos': prods
                })

    return render(request, 'productos.html', {
        'categorias': categorias,
        'productos_globales': productos_list, # Se usa si modo_busqueda es True
        'categorias_preview': categorias_preview, # Se usa si modo_busqueda es False
        'modo_busqueda': modo_busqueda,
        'categoria_activa_id': categoria_activa_id
    })



def agregar_carrito(request, tipo, item_id):
    carrito = request.session.get('cart', {})
    # Prefix: lic_ for Productos, coc_ for Cocteles
    key = f"{tipo}_{item_id}"
    
    if tipo == 'lic':
        item = get_object_or_404(Productos, id=item_id)
    elif tipo == 'coc':
        item = get_object_or_404(Cocteles, id=item_id)
    else:
        return JsonResponse({'message': 'Tipo inválido', 'error': True}, status=400)
    
    cantidad_actual = carrito.get(key, 0)
    if cantidad_actual + 1 > item.stock:
         messages.error(request, f'No hay más stock disponible de {item.nombre}')
         referer = request.META.get('HTTP_REFERER')
         return redirect(referer) if referer else redirect('ver_carrito')

    carrito[key] = cantidad_actual + 1
    request.session['cart'] = carrito
    
    total_items = sum(carrito.values())
    
    messages.success(request, f'¡{item.nombre} agregado al carrito!')
    
    # Redirigir a la misma página (Catálogo o Carrito)
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer) if referer else redirect('ver_carrito')

def quitar_uno_carrito(request, tipo, item_id):
    carrito = request.session.get('cart', {})
    key = f"{tipo}_{item_id}"
    
    if key in carrito:
        if carrito[key] > 1:
            carrito[key] -= 1
            messages.success(request, 'Cantidad actualizada.')
        else:
            del carrito[key]
            messages.success(request, 'Producto eliminado del carrito.')
        request.session['cart'] = carrito
        
    return redirect('ver_carrito')

def eliminar_item_carrito(request, tipo, item_id):
    carrito = request.session.get('cart', {})
    key = f"{tipo}_{item_id}"
    
    if key in carrito:
        del carrito[key]
        request.session['cart'] = carrito
        messages.success(request, 'Producto eliminado del carrito.')
        
    return redirect('ver_carrito')

def ver_carrito(request):
    carrito = request.session.get('cart', {})
    items_carrito = []
    total = 0
    
    for key, cant in carrito.items():
        try:
            tipo, item_id = key.split('_')
            if tipo == 'lic':
                item = Productos.objects.get(id=item_id)
                seccion = "Licores"
            else:
                item = Cocteles.objects.get(id=item_id)
                seccion = "Cócteles"
            
            subtotal = item.precio * cant
            total += subtotal
            
            # Validacion de Stock
            error_stock = False
            msg_stock = ""
            if cant > item.stock:
                error_stock = True
                msg_stock = f"Stock insuficiente (Máx: {item.stock})"
            
            items_carrito.append({
                'item': item,
                'cantidad': cant,
                'subtotal': subtotal,
                'tipo': tipo,
                'item_id': item_id,
                'seccion': seccion,
                'error_stock': error_stock,
                'msg_stock': msg_stock
            })
        except Exception as e:
            print(f"Error procesando item {key}: {e}")
            
    # Obtener perfil de cliente para validar límites
    cliente = None
    if request.user.is_authenticated:
        try:
            # Intentar obtener el cliente por email o por usuario vinculado
            try:
                cliente = Clientes.objects.get(email=request.user.email)
            except Clientes.DoesNotExist:
                cliente = Clientes.objects.get(user=request.user)
        except Clientes.DoesNotExist:
            pass
            
    # Calculos de Credito Disponible
    credito_disponible = Decimal('0.00')
    limite_total = Decimal('0.00')
    
    if cliente:
        # 1. Obtener limite dinamico
        limite_total = cliente.limite_credito_calculado
        
        # 2. Calcular deuda actual (Ordenes no pagadas)
        deuda_ordenes = cliente.ordenes_set.filter(pagada=False).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # 3. Calcular deuda multas
        deuda_multas = cliente.total_deuda_multas()
        
        # 4. Credito disponible real (Excluyendo multas por petición del usuario)
        # Las multas se gestionan aparte y no bloquean el cupo de compras normales
        deuda_total = deuda_ordenes 
        credito_disponible = limite_total - deuda_total
        
    hay_errores_stock = any(i['error_stock'] for i in items_carrito)
            
    return render(request, 'carrito.html', {
        'items': items_carrito, 
        'total': total, 
        'cliente': cliente,
        'credito_disponible': credito_disponible,
        'limite_total': limite_total,
        'deuda_total': deuda_total if cliente else 0,
        'hay_errores_stock': hay_errores_stock
    })







# --- Vistas de Apoyo ---
@login_required
@rol_requerido('Administrador', 'Supervisor')
def clientes_list(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado exitosamente.')
            return redirect('clientes')
    else:
        form = ClienteForm()
    
    clientes = Clientes.objects.filter(Q(user__isnull=True) | Q(user__is_staff=False))
    return render(request, 'clientes.html', {'clientes': clientes, 'form': form})

def detalle_cliente(request, cliente_id):
    """Ficha completa del cliente con todo su historial y solicitudes"""
    cliente = get_object_or_404(Clientes, id=cliente_id)
    
    # Seguridad: Si no es Staff/Admin, solo puede ver su propio perfil
    if not (request.user.is_staff or request.user.is_superuser):
        try:
            propio_perfil = Clientes.objects.get(user=request.user)
            if cliente.id != propio_perfil.id:
                 messages.error(request, "No tienes permiso para ver este perfil.")
                 return redirect('index')
        except Clientes.DoesNotExist:
             return redirect('index')
    
    # Órdenes recientes
    ordenes = Ordenes.objects.filter(cliente=cliente).order_by('-fecha')
    
    # Préstamos: Ahora son Órdenes en estado SOLI (solicitudes) o PREST (activos)
    solicitudes_prestamo = Ordenes.objects.filter(cliente=cliente, estado='SOLI').order_by('-fecha')
    prestamos_activos = Ordenes.objects.filter(cliente=cliente, estado='PREST').order_by('-fecha')
    
    # Recompensas: Solicitudes vs Reclamadas/Entregadas
    solicitudes_recompensas = Recompensas.objects.filter(cliente=cliente, estado_solicitud='PEND').order_by('-fecha_otorgada')
    recompensas_reclamadas = Recompensas.objects.filter(cliente=cliente, estado_solicitud__in=['APROB', 'ENTR']).order_by('-fecha_otorgada')
    
    # Multas
    multas = Multas.objects.filter(cliente=cliente).order_by('-fecha_generada')
    
    context = {
        'cliente': cliente,
        'ordenes': ordenes,
        'solicitudes_prestamo': solicitudes_prestamo,
        'prestamos_activos': prestamos_activos,
        'solicitudes_recompensas': solicitudes_recompensas,
        'recompensas_reclamadas': recompensas_reclamadas,
        'multas': multas,
        'total_gastado': cliente.total_gastado()
    }
    return render(request, 'detalle_cliente.html', context)

def catalogo_general(request):
    """Vista unificada de todos los productos (Licores y Cócteles)"""
    query = request.GET.get('q')
    
    productos = Productos.objects.all()
    cocteles = Cocteles.objects.all()
    
    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(categoria__nombre__icontains=query))
        cocteles = cocteles.filter(Q(nombre__icontains=query) | Q(categoria__icontains=query))
        
    context = {
        'productos': productos,
        'cocteles': cocteles,
        'query': query
    }
    return render(request, 'catalogo_general.html', context)

def catalogo_licores(request):
    """Vista filtrada solo para Licores (Productos)"""
    # Reutilizamos la lógica o template de productos, pero forzamos el contexto si es necesario.
    # El usuario pidió "Crea/Restaura la vista catalogo_licores: Filtra solo el modelo Productos."
    # La vista 'productos_catalogo' ya hace exactamente esto (muestra Productos).
    # Podemos simplemente llamar a productos_catalogo o redirigir, pero mejor copiamos/adaptamos para ser explícitos si se quiere un título distinto.
    
    # Para mantener consistencia con 'productos_catalogo' que ya lista productos:
    return productos_catalogo(request)

@login_required
def detalle_orden(request, orden_id):
    orden = get_object_or_404(Ordenes, id=orden_id)
    # Seguridad: solo el dueño o personal puede verla
    if not request.user.is_superuser and request.user.email != orden.cliente.email:
        if not request.user.groups.filter(name__in=['Supervisor', 'Bodeguero']).exists():
            return redirect('index')
            
    detalles = DetallesOrdenes.objects.filter(orden=orden)
    multas = orden.multas.all()
    
    # Buscar si se usó una recompensa de descuento en esta orden
    descuento_aplicado = Recompensas.objects.filter(orden_relacionada=orden, tipo__in=['DES', 'POR']).first()
    
    # Calcular subtotal de items para mostrar desglose si hay descuento
    subtotal_items = sum(d.subtotal for d in detalles)
    
    return render(request, 'detalles_ordenes.html', {
        'orden': orden, 
        'detalles': detalles, 
        'multas': multas,
        'descuento_aplicado': descuento_aplicado,
        'subtotal_items': subtotal_items
    })

# --- Vistas de Autenticación de Empleados (Basado en AUTENTICACION.md) ---

def validar_admin(request):
    """Primer paso: Validar clave de administrador"""
    if request.method == 'POST':
        admin_pass = request.POST.get('admin_pass')
        if admin_pass == 'axfer2304': # Clave definida en documentacion
            request.session['admin_validated'] = True
            return redirect('registro_empleado_publico')
        else:
            return render(request, 'registration/validate_admin.html', {'error': 'Clave de administrador incorrecta'})
    return render(request, 'registration/validate_admin.html')

def registro_empleado_publico(request):
    """Segundo paso: Registro real si se paso la validacion"""
    if not request.session.get('admin_validated'):
        return redirect('validar_registro')

    if request.method == 'POST':
        form = RegistroEmpleadoForm(request.POST)
        if form.is_valid():
            # Crear Usuario
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            user.is_staff = True
            
            # Asignar Grupo
            rol = form.cleaned_data['rol']
            grupo = Group.objects.get(name=rol)
            user.groups.add(grupo)
            user.save()
            
            # Crear perfil de empleado
            Empleados.objects.create(nombre=form.cleaned_data['username'], cargo=rol, sueldo=0)
            
            # Limpiar sesion de validacion
            del request.session['admin_validated']
            
            messages.success(request, f'Registro exitoso para {rol}. Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroEmpleadoForm()
    return render(request, 'registration/register.html', {'form': form})

# --- Vistas de Recompensas para Clientes ---

@login_required
def solicitar_recompensa(request):
    """Cliente solicita una recompensa"""
    from .catalogo_recompensas import CATALOGO_RECOMPENSAS
    from django.utils import timezone
    
    # Obtener perfil de forma segura para cualquier usuario (Staff/Admin/Cliente)
    cliente = get_cliente_perfil(request)
    
    # Si por alguna razón no se pudo crear/obtener un perfil (raro), manejarlo
    puntos_acumulados = cliente.puntos_actuales_calculados if cliente else 0
    total_gastado = cliente.total_gastado() if cliente else 0
    
    if request.method == 'POST':
        if not cliente:
             messages.error(request, 'Error: No se encontró un perfil de cliente asociado para procesar el canje.')
             return redirect('solicitar_recompensa')
             
        recompensa_id = request.POST.get('recompensa_id')
        
        # Buscar la recompensa en el catálogo
        recompensa_data = next((r for r in CATALOGO_RECOMPENSAS if r['id'] == int(recompensa_id)), None)
        
        if not recompensa_data:
            messages.error(request, 'Recompensa no válida.')
            return redirect('solicitar_recompensa')
        
        # Verificar si tiene suficientes puntos
        if cliente.puntos_actuales_calculados < recompensa_data['costo_puntos']:
            messages.error(request, f'No tienes suficientes puntos. Necesitas {recompensa_data["costo_puntos"]} puntos.')
            return redirect('solicitar_recompensa')
        
        # Crear solicitud de recompensa
        Recompensas.objects.create(
            cliente=cliente,
            tipo=recompensa_data['tipo'],
            valor=recompensa_data['valor'],
            costo_puntos=recompensa_data['costo_puntos'],
            descripcion=recompensa_data['descripcion'],
            solicitada_por_cliente=True,
            estado_solicitud='PEND',
            fecha_solicitud=timezone.now()
        )
        
        messages.success(request, f'Solicitud de canje enviada. Se descontarán {recompensa_data["costo_puntos"]} puntos al aprobar.')
        return redirect('mis_recompensas')
    
    cupones = [r for r in CATALOGO_RECOMPENSAS if r.get('seccion') == 'efectivo']
    porcentajes = [r for r in CATALOGO_RECOMPENSAS if r.get('seccion') == 'porcentaje']

    return render(request, 'cliente/solicitar_recompensa.html', {
        'cliente': cliente,
        'catalogo': CATALOGO_RECOMPENSAS, # Backward compatibility if needed
        'cupones': cupones,
        'porcentajes': porcentajes,
        'puntos': puntos_acumulados,
        'total_gastado': total_gastado,
    })
@login_required
def mis_recompensas(request):
    """Cliente ve sus recompensas"""
    try:
        cliente = Clientes.objects.get(email=request.user.email)
        recompensas = Recompensas.objects.filter(cliente=cliente).order_by('-fecha_solicitud', '-fecha_otorgada')
    except Clientes.DoesNotExist:
        recompensas = []
        cliente = None
    
    return render(request, 'cliente/mis_recompensas.html', {
        'recompensas': recompensas,
        'cliente': cliente
    })

def cocteles_catalogo(request):
    """Vista del catálogo exclusiva para Cócteles"""
    # Obtener todas las categorías únicas de cócteles (campo CharField)
    # Como es CharField, hacemos una query distinta o manual
    # O simplemente listamos todos si no hay categorización compleja
    
    cocteles_list = Cocteles.objects.all()
    
    # Filtros
    busqueda = request.GET.get('busqueda')
    precio_max = request.GET.get('precio_max')
    categoria = request.GET.get('categoria')
    
    if busqueda:
        cocteles_list = cocteles_list.filter(nombre__icontains=busqueda)
    
    if categoria:
        cocteles_list = cocteles_list.filter(categoria__icontains=categoria)
        
    if precio_max:
        try:
             cocteles_list = cocteles_list.filter(precio__lte=float(precio_max))
        except ValueError:
             pass

    # Obtener lista de categorías disponibles para el filtro (distinct)
    # SQLite no soporta distinct on fields facilmente en django antiguo, pero try:
    categorias_disponibles = Cocteles.objects.values_list('categoria', flat=True).distinct()
    # Filtrar nulos y vacios
    categorias_disponibles = [c for c in categorias_disponibles if c]

    return render(request, 'cocteles.html', {
        'cocteles': cocteles_list,
        'categorias': categorias_disponibles,
        'categoria_activa': categoria
    })

@login_required
def mis_registros_canjes(request):
    """Cliente ve su historial de solicitudes de canje personal"""
    cliente = get_cliente_perfil(request)
    if not cliente:
        return redirect('index')
        
    recompensas = Recompensas.objects.filter(cliente=cliente).order_by('-fecha_solicitud')
    
    return render(request, 'cliente/mis_registros_canjes.html', {
        'recompensas': recompensas,
        'cliente': cliente
    })

@login_required
@cliente_required
def confirmar_entrega_recompensa(request, recompensa_id):
    """Cliente confirma que recibió la recompensa"""
    recompensa = get_object_or_404(Recompensas, id=recompensa_id)
    
    # Verificar que sea del cliente
    try:
        cliente = Clientes.objects.get(email=request.user.email)
        if recompensa.cliente != cliente:
            messages.error(request, 'No tienes permiso para esta acción.')
            return redirect('mis_recompensas')
    except Clientes.DoesNotExist:
        return redirect('index')
    
    if recompensa.estado_solicitud == 'APROB':
        recompensa.estado_solicitud = 'ENTR'
        recompensa.fecha_confirmacion_entrega = timezone.now()
        recompensa.utilizada = True
        recompensa.save()
        messages.success(request, 'Entrega confirmada. ¡Gracias!')
    else:
        messages.warning(request, 'Esta recompensa no está lista para confirmar.')
    
    return redirect('mis_recompensas')

@login_required
@rol_requerido('Supervisor', 'Administrador')
def aprobar_recompensa(request, recompensa_id):
    """Supervisor aprueba o rechaza solicitud"""
    recompensa = get_object_or_404(Recompensas, id=recompensa_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        notas = request.POST.get('notas', '')
        
        try:
            empleado = Empleados.objects.get(user=request.user)
        except Empleados.DoesNotExist:
            empleado = None
        
        if accion == 'aprobar':
            # Intentar descontar puntos
            if recompensa.cliente.canjear_puntos(recompensa.costo_puntos):
                recompensa.estado_solicitud = 'APROB'
                recompensa.fecha_aprobacion = timezone.now()
                recompensa.supervisor_aprobador = empleado
                recompensa.notas_supervisor = notas
                recompensa.save()
                messages.success(request, f'Recompensa aprobada para {recompensa.cliente.nombre}. Se descontaron {recompensa.costo_puntos} puntos.')
            else:
                messages.error(request, f'El cliente ya no tiene puntos suficientes ({recompensa.cliente.puntos_acumulados} pts disponibles).')
        elif accion == 'rechazar':
            recompensa.estado_solicitud = 'RECH'
            recompensa.notas_supervisor = notas
            recompensa.save()
            messages.info(request, f'Recompensa rechazada para {recompensa.cliente.nombre}.')
        
        return redirect('gestion_recompensas')
    
    return render(request, 'supervisor/aprobar_recompensa.html', {'recompensa': recompensa})

# --- Panel de Fidelidad ---

@login_required
def panel_fidelidad(request):
    """Panel completo de fidelidad del cliente con historial de puntos"""
    # Obtener el cliente
    try:
        if request.user.is_staff or request.user.is_superuser:
            # Si es staff, crear perfil maestro si no existe
            cliente, created = Clientes.objects.get_or_create(
                email=request.user.email,
                defaults={
                    'nombre': request.user.get_full_name() or request.user.username,
                    'telefono': '0000000000'
                }
            )
        else:
            cliente = Clientes.objects.get(
                Q(email=request.user.email) | Q(user=request.user)
            )
    except Clientes.DoesNotExist:
        messages.error(request, 'No se encontró tu perfil de cliente.')
        return redirect('index')
    
    # Calcular estadísticas
    total_gastado = cliente.total_gastado()
    
    # Obtener historial de órdenes pagadas (donde se ganaron puntos)
    historial_ordenes = Ordenes.objects.filter(
        cliente=cliente
    ).order_by('-fecha')[:20]  # Últimas 20 órdenes
    
    total_ordenes = Ordenes.objects.filter(cliente=cliente).count()
    
    context = {
        'cliente': cliente,
        'total_gastado': total_gastado,
        'historial_ordenes': historial_ordenes,
        'total_ordenes': total_ordenes,
    }
    
    return render(request, 'cliente/panel_fidelidad.html', context)

@login_required
@transaction.atomic
def solicitar_canje(request):
    """Procesa el canje de puntos por recompensas"""
    from .catalogo_recompensas import CATALOGO_RECOMPENSAS
    
    if request.method == 'POST':
        item_id = int(request.POST.get('item_id'))
        
        # Buscar item en catálogo
        recompensa_data = next((item for item in CATALOGO_RECOMPENSAS if item['id'] == item_id), None)
        
        if not recompensa_data:
            messages.error(request, 'Recompensa no válida.')
            return redirect('solicitar_recompensa')
            
        cliente = get_cliente_perfil(request)
        if not cliente:
             messages.error(request, 'Error al identificar cliente.')
             return redirect('index')
             
        # 1. Validar Puntos
        if cliente.puntos_actuales_calculados < recompensa_data['costo_puntos']:
            messages.error(request, f'No tienes puntos suficientes. Requieres {recompensa_data["costo_puntos"]} pts.')
            return redirect('solicitar_recompensa')
            
        # 2. Restar Puntos
        if cliente.canjear_puntos(recompensa_data['costo_puntos']):
            # 3. Crear Registro con Código
            codigo = f"BLB-P-{uuid.uuid4().hex[:4].upper()}"
            recompensa = Recompensas.objects.create(
                cliente=cliente,
                tipo=recompensa_data['tipo'],
                descripcion=recompensa_data['descripcion'],
                valor=recompensa_data['valor'],
                costo_puntos=recompensa_data['costo_puntos'],
                solicitada_por_cliente=True,
                estado_solicitud='APROB', # Auto-aprobación inmediata
                codigo_canje=codigo,
                fecha_solicitud=timezone.now(),
                fecha_aprobacion=timezone.now() # Fecha de aprobación
            )
            
            # Mensaje Éxito (se debe visualizar como Neón en template)
            messages.success(request, '¡Canje exitoso! Tu recompensa está lista.')
            
        else:
            messages.error(request, 'Error al procesar el canje de puntos.')
            
    return redirect('mis_registros_canjes')

@login_required
def gestion_cobros(request):
    """Muestra órdenes en estado PREST para gestión de multas"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('index')
        
    ordenes_prestamo = Ordenes.objects.filter(estado='PREST').order_by('-fecha')
    
    return render(request, 'supervisor/gestion_cobros.html', {
        'ordenes': ordenes_prestamo
    })

@login_required
@transaction.atomic
def aplicar_multa(request, orden_id):
    """Crea una multa asociada a una orden/cliente"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permiso.')
        return redirect('index')
        
    orden = get_object_or_404(Ordenes, id=orden_id)
    
    if request.method == 'POST':
        monto = request.POST.get('monto')
        tipo = request.POST.get('tipo', 'TARD')
        descripcion = request.POST.get('descripcion', f"Recargo atraso Orden #{orden.id}")
        
        Multas.objects.create(
            cliente=orden.cliente,
            orden=orden,
            tipo=tipo,
            monto=monto,
            descripcion=descripcion
        )
        
        # Actualizar el total de la orden sumando la multa
        orden.total += Decimal(monto)
        orden.estado = 'MULT' # Cambiar estado a Multada
        orden.save()
        
        messages.success(request, f'Multa de ${monto} aplicada. El nuevo total de la orden es ${orden.total}')
        
    return redirect('detalle_orden', orden_id=orden.id)



@login_required
def cancelar_orden_solicitud(request, orden_id):
    """Permite al usuario o admin cancelar una solicitud de préstamo (SOLI) y devolver stock"""
    orden = get_object_or_404(Ordenes, id=orden_id)
    
    # Validar permisos (Staff o Dueño de la orden)
    es_dueno = False
    if orden.cliente:
        if orden.cliente.user == request.user:
            es_dueno = True
        elif orden.cliente.email == request.user.email:
             es_dueno = True
             
    if not (request.user.is_staff or request.user.is_superuser or es_dueno):
        messages.error(request, "No tienes permiso para cancelar esta solicitud.")
        return redirect('ordenes')

    if orden.estado == 'SOLI':
        # Devolver Stock
        for detalle in orden.detalles.all():
            if detalle.producto:
                detalle.producto.stock += detalle.cantidad
                detalle.producto.save()
            elif detalle.coctel:
                detalle.coctel.stock += detalle.cantidad
                detalle.coctel.save()
        
        orden.delete()
        messages.success(request, f"Solicitud #{orden.codigo_orden} cancelada y eliminada.")
    else:
        messages.error(request, "Solo se pueden eliminar órdenes en estado 'Solicitud'.")
        
    return redirect('ordenes')
