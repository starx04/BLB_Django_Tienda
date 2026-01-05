from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings

from .models import (Productos, Categorias, Ordenes, DetallesOrdenes, Clientes, 
                     Empleados, Distribuidores, Gastos, Prestamos, Recompensas)
from .forms import (ClienteForm, EmpleadoForm, PrestamoForm, RegistroClienteForm, 
                    ProductoForm, RecompensaForm)
from .decorators import (rol_requerido, administrador_required, bodeguero_required, 
                        supervisor_required, cliente_required)

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

@login_required
def index(request):
    hoy = timezone.now().date()
    
    # Si es cliente, redirigir a su vista específica o mostrar dashboard limitado
    if request.user.groups.filter(name='Cliente').exists():
        return redirect('mis_compras')

    # Estadísticas para Empleados/Admin
    ventas_hoy = Ordenes.objects.filter(fecha__date=hoy).aggregate(Sum('total'))['total__sum'] or 0
    pedidos_nuevos = Ordenes.objects.filter(fecha__date=hoy).count()
    clientes_activos = Clientes.objects.count()
    productos_stock = Productos.objects.aggregate(Sum('stock'))['stock__sum'] or 0

    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        fecha = hoy - timezone.timedelta(days=i)
        chart_labels.append(fecha.strftime("%d/%m"))
        venta_dia = Ordenes.objects.filter(fecha__date=fecha).aggregate(Sum('total'))['total__sum'] or 0
        chart_data.append(float(venta_dia))

    context = {
        'ventas_hoy': ventas_hoy,
        'pedidos_nuevos': pedidos_nuevos,
        'clientes_activos': clientes_activos,
        'productos_stock': productos_stock,
        'chart_labels': chart_labels,
        'chart_data': chart_data
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
def producto_eliminar(request, pk):
    producto = get_object_or_404(Productos, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('gestion_productos')
    return render(request, 'bodeguero/producto_confirm_delete.html', {'producto': producto})

# --- Funciones de Supervisor (Préstamos y Recompensas) ---

@login_required
@rol_requerido('Supervisor', 'Administrador')
def gestion_prestamos(request):
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Préstamo registrado.')
            return redirect('gestion_prestamos')
    else:
        form = PrestamoForm()
    prestamos_list = Prestamos.objects.all().order_by('-fecha_prestamo')
    return render(request, 'supervisor/prestamos.html', {'prestamos': prestamos_list, 'form': form})

@login_required
@rol_requerido('Supervisor', 'Administrador')
def gestion_recompensas(request):
    if request.method == 'POST':
        form = RecompensaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recompensa otorgada.')
            return redirect('gestion_recompensas')
    else:
        form = RecompensaForm()
    recompensas_list = Recompensas.objects.all().order_by('-fecha_otorgada')
    return render(request, 'supervisor/recompensas.html', {'recompensas': recompensas_list, 'form': form})

# --- Funciones de Cliente (Mis Compras y Préstamos) ---

@login_required
@cliente_required
def mis_compras(request):
    # Buscar el perfil de cliente asociado al usuario actual por email
    try:
        cliente_perfil = Clientes.objects.get(email=request.user.email)
        compras = Ordenes.objects.filter(cliente=cliente_perfil).order_by('-fecha')
    except Clientes.DoesNotExist:
        compras = []
    return render(request, 'cliente/mis_compras.html', {'compras': compras})

@login_required
@cliente_required
def mis_prestamos(request):
    try:
        cliente_perfil = Clientes.objects.get(email=request.user.email)
        prestamos = Prestamos.objects.filter(cliente=cliente_perfil).order_by('-fecha_prestamo')
    except Clientes.DoesNotExist:
        prestamos = []
    return render(request, 'cliente/mis_prestamos.html', {'prestamos': prestamos})

# --- Gestión de Empleados (Solo Administrador) ---

@login_required
@administrador_required
def registro_empleado(request):
    """Solo el administrador puede crear Bodegueros y Supervisores"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        passw = request.POST.get('password')
        rol = request.POST.get('rol') # 'Bodeguero' o 'Supervisor'
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe.')
        else:
            user = User.objects.create_user(username=username, email=email, password=passw)
            user.is_staff = True
            grupo = Group.objects.get(name=rol)
            user.groups.add(grupo)
            user.save()
            
            # Crear perfil de empleado
            Empleados.objects.create(nombre=username, cargo=rol, sueldo=0)
            
            messages.success(request, f'Empleado {username} creado como {rol}.')
            return redirect('index')
            
    return render(request, 'admin/crear_empleado.html')

# --- Catálogo y Carrito (Acceso General para comprar) ---

@login_required
def productos_catalogo(request):
    nombres_snacks = ['Snacks', 'Bocaditos', 'Comida', 'Papas', 'Frutos Secos', 'Dulces']
    categorias = Categorias.objects.exclude(nombre__in=nombres_snacks)
    
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda')
    
    productos_list = Productos.objects.exclude(categoria__nombre__in=nombres_snacks)
    if busqueda:
        productos_list = productos_list.filter(Q(nombre__icontains=busqueda) | Q(marca__nombre__icontains=busqueda))
    if categoria_id:
        productos_list = productos_list.filter(categoria_id=categoria_id)
        
    return render(request, 'productos.html', {
        'categorias': categorias,
        'productos_globales': productos_list,
        'modo_busqueda': True if (busqueda or categoria_id) else False
    })

@login_required
def snacks_catalogo(request):
    nombres_snacks = ['Snacks', 'Bocaditos', 'Comida', 'Papas', 'Frutos Secos', 'Dulces']
    productos_list = Productos.objects.filter(categoria__nombre__in=nombres_snacks)
    return render(request, 'snacks.html', {'productos_globales': productos_list})

@login_required
def agregar_carrito(request, producto_id):
    carrito = request.session.get('cart', {})
    prod_id_str = str(producto_id)
    producto = get_object_or_404(Productos, id=producto_id)
    
    cantidad_actual = carrito.get(prod_id_str, 0)
    if cantidad_actual + 1 > producto.stock:
         return JsonResponse({'message': 'Sin stock suficiente', 'error': True}, status=400)

    carrito[prod_id_str] = cantidad_actual + 1
    request.session['cart'] = carrito
    
    total_items = sum(carrito.values())
    return JsonResponse({'message': 'Agregado', 'cart_count': total_items})

@login_required
def ver_carrito(request):
    carrito = request.session.get('cart', {})
    items_carrito = []
    total = 0
    for p_id, cant in carrito.items():
        prod = Productos.objects.get(id=p_id)
        subtotal = prod.precio * cant
        total += subtotal
        items_carrito.append({'producto': prod, 'cantidad': cant, 'subtotal': subtotal})
    return render(request, 'carrito.html', {'items': items_carrito, 'total': total})

@login_required
def eliminar_carrito(request, producto_id):
    carrito = request.session.get('cart', {})
    if str(producto_id) in carrito:
        del carrito[str(producto_id)]
        request.session['cart'] = carrito
    return redirect('ver_carrito')

@login_required
def checkout(request):
    """Crea la orden real en la base de datos"""
    carrito = request.session.get('cart', {})
    if not carrito:
        return redirect('index')
    
    try:
        cliente = Clientes.objects.get(email=request.user.email)
    except Clientes.DoesNotExist:
        messages.error(request, 'Debes completar tu perfil de cliente antes de comprar.')
        return redirect('index')
        
    # Crear Orden
    orden = Ordenes.objects.create(cliente=cliente, total=0)
    total_orden = 0
    
    for p_id, cant in carrito.items():
        prod = Productos.objects.get(id=p_id)
        subtotal = prod.precio * cant
        total_orden += subtotal
        
        DetallesOrdenes.objects.create(
            orden=orden,
            producto=prod,
            cantidad=cant,
            precio_unitario=prod.precio
        )
        
        # Descontar Stock
        prod.stock -= cant
        prod.save()
    
    orden.total = total_orden
    orden.save()
    
    # Limpiar carrito
    request.session['cart'] = {}
    
    messages.success(request, f'Orden #{orden.id} creada exitosamente por ${total_orden}.')
    return redirect('mis_compras')

# --- Vistas de Apoyo ---
@login_required
@rol_requerido('Administrador', 'Supervisor')
def clientes_list(request):
    clientes = Clientes.objects.all()
    return render(request, 'clientes.html', {'clientes': clientes})

@login_required
def detalle_orden(request, orden_id):
    orden = get_object_or_404(Ordenes, id=orden_id)
    # Seguridad: solo el dueño o personal puede verla
    if not request.user.is_superuser and request.user.email != orden.cliente.email:
        if not request.user.groups.filter(name__in=['Supervisor', 'Bodeguero']).exists():
            return redirect('index')
            
    detalles = DetallesOrdenes.objects.filter(orden=orden)
    return render(request, 'detalles_ordenes.html', {'orden': orden, 'detalles': detalles})
