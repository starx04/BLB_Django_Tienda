from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Productos, Categorias, Ordenes, DetallesOrdenes, Clientes, Empleados, Distribuidores, Gastos, Prestamos

from django.db.models import Sum
from django.utils import timezone

def index(request):
    # Obtener fecha de hoy
    hoy = timezone.now().date()
    
    # Estadísticas Reales
    ventas_hoy = Ordenes.objects.filter(fecha__date=hoy).aggregate(Sum('total'))['total__sum'] or 0
    pedidos_nuevos = Ordenes.objects.filter(fecha__date=hoy).count()
    clientes_activos = Clientes.objects.count()
    productos_stock = Productos.objects.aggregate(Sum('stock'))['stock__sum'] or 0

    # Datos para la Gráfica (Últimos 7 días)
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

def productos(request):
    # Definir qué es un Snack para excluirlo
    nombres_snacks = ['Snacks', 'Bocaditos', 'Comida', 'Papas', 'Frutos Secos', 'Dulces']
    
    # Filtrar solo categorías que NO son snacks (es decir, Licores/Bebidas)
    categorias = Categorias.objects.exclude(nombre__in=nombres_snacks)
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda')
    
    context = {
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_id': categoria_id,
        'page_title': 'Catálogo de Licores'
    }

    if busqueda:
        # Búsqueda global (filtrando solo licores)
        productos_list = Productos.objects.filter(
            Q(nombre__icontains=busqueda) | Q(marca__nombre__icontains=busqueda) | Q(codigo_barras__icontains=busqueda)
        ).exclude(categoria__nombre__in=nombres_snacks)
        
        if categoria_id:
            productos_list = productos_list.filter(categoria_id=categoria_id)
        
        context['productos_globales'] = productos_list
        context['modo_busqueda'] = True

    elif categoria_id:
        # Filtro específico de categoría
        productos_list = Productos.objects.filter(categoria_id=categoria_id)
        context['productos_globales'] = productos_list
        context['modo_busqueda'] = True 

    else:
        # Modo Exploración: Top 5 de cada categoría
        categorias_preview = []
        for cat in categorias:
            prods = Productos.objects.filter(categoria=cat)[:5]
            if prods.exists():
                categorias_preview.append({
                    'categoria': cat,
                    'productos': prods
                })
        context['categorias_preview'] = categorias_preview
        context['modo_busqueda'] = False

    return render(request, 'productos.html', context)

def snacks(request):
    # Categorías consideradas Snacks
    nombres_snacks = ['Snacks', 'Bocaditos', 'Comida', 'Papas', 'Frutos Secos', 'Dulces']
    
    categorias = Categorias.objects.filter(nombre__in=nombres_snacks)
    
    # Filtros
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda')
    
    context = {
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_id': categoria_id,
        'page_title': 'Catálogo de Snacks'
    }

    if busqueda:
        productos_list = Productos.objects.filter(
            Q(nombre__icontains=busqueda) | Q(marca__nombre__icontains=busqueda) | Q(codigo_barras__icontains=busqueda)
        ).filter(categoria__nombre__in=nombres_snacks)
        
        if categoria_id:
            productos_list = productos_list.filter(categoria_id=categoria_id)
        
        context['productos_globales'] = productos_list
        context['modo_busqueda'] = True

    elif categoria_id:
        productos_list = Productos.objects.filter(categoria_id=categoria_id)
        context['productos_globales'] = productos_list
        context['modo_busqueda'] = True

    else:
        categorias_preview = []
        for cat in categorias:
            prods = Productos.objects.filter(categoria=cat)[:5]
            if prods.exists():
                categorias_preview.append({
                    'categoria': cat,
                    'productos': prods
                })
        context['categorias_preview'] = categorias_preview
        context['modo_busqueda'] = False

    return render(request, 'snacks.html', context)

from .forms import ClienteForm, EmpleadoForm

def clientes(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clientes')
    else:
        form = ClienteForm()

    clientes_list = Clientes.objects.all().order_by('-id')
    return render(request, 'clientes.html', {
        'clientes': clientes_list,
        'form': form
    })

def empleados(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('empleados')
    else:
        form = EmpleadoForm()

    empleados_list = Empleados.objects.all()
    return render(request, 'empleados.html', {
        'empleados': empleados_list,
        'form': form
    })

def distribuidores(request):
    distribuidores_list = Distribuidores.objects.all()
    return render(request, 'distribuidores.html', {'distribuidores': distribuidores_list})

def gastos(request):
    gastos_list = Gastos.objects.all()
    return render(request, 'gastos.html', {'gastos': gastos_list})

def prestamos(request):
    prestamos_list = Prestamos.objects.all()
    return render(request, 'prestamos.html', {'prestamos': prestamos_list})

def ordenes(request):
    ordenes_list = Ordenes.objects.all()
    return render(request, 'ordenes.html', {'ordenes': ordenes_list})

def categorias(request):
    categorias_list = Categorias.objects.all()
    return render(request, 'categorias.html', {'categorias': categorias_list})

def detalles_ordenes(request):
    detalles = DetallesOrdenes.objects.all()
    return render(request, 'detalles_ordenes.html', {'detalles': detalles})

from django.http import JsonResponse

def agregar_carrito(request, producto_id):
    carrito = request.session.get('cart', {})
    prod_id_str = str(producto_id)
    
    # Validar Stock
    producto = Productos.objects.get(id=producto_id)
    cantidad_actual = carrito.get(prod_id_str, 0)
    
    if cantidad_actual + 1 > producto.stock:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
             return JsonResponse({'message': 'Sin stock suficiente', 'error': True}, status=400)
        # Si no es AJAX, podrías mostrar un mensaje flash (pero por ahora redirigimos)
        return redirect('productos')

    if prod_id_str in carrito:
        carrito[prod_id_str] += 1
    else:
        carrito[prod_id_str] = 1
    
    request.session['cart'] = carrito
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
         total_items = sum(carrito.values())
         return JsonResponse({'message': 'Agregado', 'cart_count': total_items})
    
    return redirect('productos')

def ver_carrito(request):
    carrito = request.session.get('cart', {})
    items_carrito = []
    total = 0
    
    productos_db = Productos.objects.filter(id__in=carrito.keys())
    
    for producto in productos_db:
        cantidad = carrito[str(producto.id)]
        subtotal = producto.precio * cantidad
        total += subtotal
        items_carrito.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal
        })
    
    return render(request, 'carrito.html', {'items': items_carrito, 'total': total})

def eliminar_carrito(request, producto_id):
    carrito = request.session.get('cart', {})
    prod_id_str = str(producto_id)
    
    if prod_id_str in carrito:
        del carrito[prod_id_str]
        request.session['cart'] = carrito
        
    return redirect('ver_carrito')

def checkout_whatsapp(request):
    carrito = request.session.get('cart', {})
    if not carrito:
        return redirect('index')
        
    # Construir mensaje de WhatsApp
    mensaje = "Hola, me gustaría ordenar lo siguiente:%0A"
    productos_db = Productos.objects.filter(id__in=carrito.keys())
    total = 0
    
    for producto in productos_db:
        cantidad = carrito[str(producto.id)]
        subtotal = producto.precio * cantidad
        total += subtotal
        mensaje += f"- {cantidad}x {producto.nombre} (${subtotal})%0A"
    
    mensaje += f"%0ATotal a pagar: ${total}"
    
    # Redirigir a WhatsApp
    from django.conf import settings
    numero_whatsapp = getattr(settings, 'WHATSAPP_NUMBER', "593999999999")
    url = f"https://wa.me/{numero_whatsapp}?text={mensaje}"
    
    # Opcional: Limpiar carrito después de ordenar
    # request.session['cart'] = {}
    
    return redirect(url)
