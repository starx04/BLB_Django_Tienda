"""
Decoradores personalizados para control de acceso basado en roles
"""
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def es_cliente(user):
    """Verifica si el usuario pertenece al grupo Cliente"""
    return user.groups.filter(name='Cliente').exists()

def es_bodeguero(user):
    """Verifica si el usuario pertenece al grupo Bodeguero"""
    return user.groups.filter(name='Bodeguero').exists() or user.is_superuser

def es_supervisor(user):
    """Verifica si el usuario pertenece al grupo Supervisor"""
    return user.groups.filter(name='Supervisor').exists() or user.is_superuser

def es_administrador(user):
    """Verifica si el usuario pertenece al grupo Administrador"""
    return user.groups.filter(name='Administrador').exists() or user.is_superuser

def es_empleado(user):
    """Verifica si el usuario es empleado (Bodeguero o Supervisor)"""
    return (user.groups.filter(name__in=['Bodeguero', 'Supervisor']).exists() 
            or user.is_superuser)

# Decoradores específicos por rol
cliente_required = user_passes_test(es_cliente, login_url='index')
bodeguero_required = user_passes_test(es_bodeguero, login_url='index')
supervisor_required = user_passes_test(es_supervisor, login_url='index')
administrador_required = user_passes_test(es_administrador, login_url='index')
empleado_required = user_passes_test(es_empleado, login_url='index')

def rol_requerido(*roles_permitidos):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos
    Uso: @rol_requerido('Cliente', 'Bodeguero', 'Administrador')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Superusuario siempre tiene acceso
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verificar si el usuario tiene alguno de los roles permitidos
            user_groups = request.user.groups.values_list('name', flat=True)
            
            if any(rol in user_groups for rol in roles_permitidos):
                return view_func(request, *args, **kwargs)
            
            # Si no tiene permiso, mostrar mensaje y redirigir
            messages.error(request, f'No tienes permisos para acceder a esta sección. Rol requerido: {", ".join(roles_permitidos)}')
            return redirect('index')
        
        return wrapper
    return decorator
