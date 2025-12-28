from django.db.models import Q
from .models import Productos, Categorias, Ordenes, DetallesOrdenes, Clientes

def index(request):
    productos = Productos.objects.all()
    categorias = Categorias.objects.all()

    # Filtros
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda')

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    if busqueda:
        productos = productos.filter(Q(nombre__icontains=busqueda))

    # Calcular cantidad en carrito para la insignia (badge)
    carrito = request.session.get('cart', {})
    cantidad_carrito = sum(carrito.values())
    return render(request, 'index.html', {
        'productos': productos, 
        'categorias': categorias,
        'cart_count': cantidad_carrito
    })

def agregar_carrito(request, producto_id):
    carrito = request.session.get('cart', {})
    prod_id_str = str(producto_id)
    
    if prod_id_str in carrito:
        carrito[prod_id_str] += 1
    else:
        carrito[prod_id_str] = 1
    
    request.session['cart'] = carrito
    return redirect('index')

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
    
    return render(request, 'licoreria/carrito.html', {'items': items_carrito, 'total': total})

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
