from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Productos, Categorias, Ordenes, DetallesOrdenes, Clientes, Empleados, Distribuidores, Gastos, Prestamos

def index(request):
    return render(request, 'index.html')

def productos(request):
    categorias = Categorias.objects.all()

    # Filtros
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda')
    
    context = {
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_id': categoria_id
    }

    if busqueda:
        # Búsqueda global (ignora agrupación)
        productos_list = Productos.objects.filter(Q(nombre__icontains=busqueda) | Q(marca__nombre__icontains=busqueda) | Q(codigo_barras__icontains=busqueda))
        if categoria_id:
            productos_list = productos_list.filter(categoria_id=categoria_id)
        
        context['productos_globales'] = productos_list
        context['modo_busqueda'] = True

    elif categoria_id:
        # Filtro específico de categoría (mostrar todos de esa categoría)
        productos_list = Productos.objects.filter(categoria_id=categoria_id)
        context['productos_globales'] = productos_list
        context['modo_busqueda'] = True # Usamos el mismo layout de grilla completa

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

from .forms import ClienteForm

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
    empleados_list = Empleados.objects.all()
    return render(request, 'empleados.html', {'empleados': empleados_list})

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

def agregar_carrito(request, producto_id):
    carrito = request.session.get('cart', {})
    prod_id_str = str(producto_id)
    
    if prod_id_str in carrito:
        carrito[prod_id_str] += 1
    else:
        carrito[prod_id_str] = 1
    
    request.session['cart'] = carrito
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
    
    # Redirigir a WhatsApp (número ficticio, cambiar por real)
    numero_whatsapp = "593999999999" 
    url = f"https://wa.me/{numero_whatsapp}?text={mensaje}"
    
    # Opcional: Limpiar carrito después de ordenar
    # request.session['cart'] = {}
    
    return redirect(url)
