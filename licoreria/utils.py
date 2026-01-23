from .models import AuditLog

def log_action(user, accion, modulo, detalles=None, request=None):
    """ Registra una acción en el AuditLog """
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
    AuditLog.objects.create(
        usuario=user if user.is_authenticated else None,
        accion=accion,
        modulo=modulo,
        detalles=detalles,
        ip_address=ip
    )


def check_loan_limit(cliente, nuevo_valor):
    """ Verifica si el cliente supera su límite de préstamo """
    from .models import Prestamos
    from django.db.models import Sum
    
    deuda_actual = Prestamos.objects.filter(cliente=cliente, devuelto=False).aggregate(Sum('valor'))['valor__sum'] or 0
    if (deuda_actual + nuevo_valor) > cliente.limite_prestamo:
        return False, f"Límite excedido. Deuda actual: ${deuda_actual}. Límite: ${cliente.limite_prestamo}"
    return True, "OK"

import random

def get_default_price(category_name=None):
    """Genera un precio sugerido basado en el tipo de producto"""
    base_prices = {
        'Whisky': (20.0, 75.0),
        'Ron': (12.0, 45.0),
        'Vodka': (10.0, 35.0),
        'Vino': (8.0, 60.0),
        'Cerveza': (1.5, 15.0),
        'DEFAULT': (10.0, 30.0)
    }
    
    # Manejo de nombres de categorías (insensible a mayúsculas)
    price_range = base_prices.get('DEFAULT')
    if category_name:
        for cat, r in base_prices.items():
            if cat.lower() in category_name.lower():
                price_range = r
                break
    
    # Generar precio con decimales realistas (.99, .50, etc)
    price = random.uniform(price_range[0], price_range[1])
    cents = random.choice([0.00, 0.50, 0.75, 0.90, 0.99])
    
    return round(int(price) + cents, 2)
