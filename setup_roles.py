"""
Script para crear grupos de permisos y usuarios de prueba
Ejecutar con: python setup_roles.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from licoreria.models import Productos, Clientes, Prestamos, Ordenes, Gastos, Empleados

def crear_grupos_y_permisos():
    """Crea los grupos de usuarios con sus permisos específicos"""
    
    # Limpiar grupos existentes
    Group.objects.all().delete()
    
    # ==================== GRUPO: CLIENTE ====================
    grupo_cliente, _ = Group.objects.get_or_create(name='Cliente')
    
    # Permisos para Cliente
    permisos_cliente = [
        # Ver productos
        Permission.objects.get(codename='view_productos'),
        Permission.objects.get(codename='view_categorias'),
        # Ver sus propias órdenes
        Permission.objects.get(codename='view_ordenes'),
        # Ver sus propios préstamos
        Permission.objects.get(codename='view_prestamos'),
    ]
    grupo_cliente.permissions.set(permisos_cliente)
    print("Grupo 'Cliente' creado con permisos")
    
    # ==================== GRUPO: BODEGUERO ====================
    grupo_bodeguero, _ = Group.objects.get_or_create(name='Bodeguero')
    
    # Permisos para Bodeguero (CRUD completo de productos)
    permisos_bodeguero = [
        # Productos
        Permission.objects.get(codename='add_productos'),
        Permission.objects.get(codename='change_productos'),
        Permission.objects.get(codename='delete_productos'),
        Permission.objects.get(codename='view_productos'),
        # Categorías
        Permission.objects.get(codename='view_categorias'),
        Permission.objects.get(codename='add_categorias'),
        Permission.objects.get(codename='change_categorias'),
        # Marcas
        Permission.objects.get(codename='view_marcas'),
        Permission.objects.get(codename='add_marcas'),
        Permission.objects.get(codename='change_marcas'),
        # Ver distribuidores
        Permission.objects.get(codename='view_distribuidores'),
    ]
    grupo_bodeguero.permissions.set(permisos_bodeguero)
    print("Grupo 'Bodeguero' creado con permisos")
    
    # ==================== GRUPO: SUPERVISOR ====================
    grupo_supervisor, _ = Group.objects.get_or_create(name='Supervisor')
    
    # Permisos para Supervisor (Gestión de préstamos y recompensas)
    permisos_supervisor = [
        # Préstamos
        Permission.objects.get(codename='add_prestamos'),
        Permission.objects.get(codename='change_prestamos'),
        Permission.objects.get(codename='delete_prestamos'),
        Permission.objects.get(codename='view_prestamos'),
        # Ver clientes
        Permission.objects.get(codename='view_clientes'),
        # Ver órdenes (para calcular recompensas)
        Permission.objects.get(codename='view_ordenes'),
        Permission.objects.get(codename='view_detallesordenes'),
        # Ver productos
        Permission.objects.get(codename='view_productos'),
    ]
    grupo_supervisor.permissions.set(permisos_supervisor)
    print("Grupo 'Supervisor' creado con permisos")
    
    print("\n" + "="*60)
    print("GRUPOS Y PERMISOS CREADOS EXITOSAMENTE")
    print("="*60)

def crear_usuarios_prueba():
    """Crea usuarios de prueba para cada rol"""
    
    print("\n" + "="*60)
    print("CREANDO USUARIOS DE PRUEBA")
    print("="*60 + "\n")
    
    usuarios_creados = []
    
    # ==================== ADMINISTRADOR (Superusuario) ====================
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@licoreria.com',
            password='admin123',
            first_name='Administrador',
            last_name='Principal'
        )
        usuarios_creados.append({
            'rol': 'ADMINISTRADOR',
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@licoreria.com'
        })
        print("Superusuario 'admin' creado")
    
    # ==================== BODEGUERO ====================
    if not User.objects.filter(username='bodeguero').exists():
        bodeguero = User.objects.create_user(
            username='bodeguero',
            email='bodeguero@licoreria.com',
            password='bodeguero123',
            first_name='Juan',
            last_name='Pérez'
        )
        bodeguero.groups.add(Group.objects.get(name='Bodeguero'))
        bodeguero.is_staff = True  # Puede acceder al admin
        bodeguero.save()
        usuarios_creados.append({
            'rol': 'BODEGUERO',
            'username': 'bodeguero',
            'password': 'bodeguero123',
            'email': 'bodeguero@licoreria.com'
        })
        print("Usuario 'bodeguero' creado")
    
    # ==================== SUPERVISOR ====================
    if not User.objects.filter(username='supervisor').exists():
        supervisor = User.objects.create_user(
            username='supervisor',
            email='supervisor@licoreria.com',
            password='supervisor123',
            first_name='María',
            last_name='González'
        )
        supervisor.groups.add(Group.objects.get(name='Supervisor'))
        supervisor.is_staff = True
        supervisor.save()
        usuarios_creados.append({
            'rol': 'SUPERVISOR',
            'username': 'supervisor',
            'password': 'supervisor123',
            'email': 'supervisor@licoreria.com'
        })
        print("Usuario 'supervisor' creado")
    
    # ==================== CLIENTE ====================
    if not User.objects.filter(username='cliente1').exists():
        cliente = User.objects.create_user(
            username='cliente1',
            email='cliente1@gmail.com',
            password='cliente123',
            first_name='Carlos',
            last_name='Rodríguez'
        )
        cliente.groups.add(Group.objects.get(name='Cliente'))
        cliente.save()
        
        # Crear registro en tabla Clientes
        from licoreria.models import Clientes
        Clientes.objects.create(
            nombre='Carlos Rodríguez',
            email='cliente1@gmail.com',
            telefono='0999888777'
        )
        
        usuarios_creados.append({
            'rol': 'CLIENTE',
            'username': 'cliente1',
            'password': 'cliente123',
            'email': 'cliente1@gmail.com'
        })
        print("Usuario 'cliente1' creado")
    
    return usuarios_creados

def mostrar_credenciales(usuarios):
    """Muestra las credenciales de acceso de forma clara"""
    print("\n" + "="*60)
    print("CREDENCIALES DE ACCESO")
    print("="*60 + "\n")
    
    for user in usuarios:
        print(f"👤 {user['rol']}")
        print(f"   Usuario:     {user['username']}")
        print(f"   Contraseña:  {user['password']}")
        print(f"   Email:       {user['email']}")
        print()
    
    print("="*60)
    print("💡 NOTAS IMPORTANTES:")
    print("="*60)
    print("• El ADMINISTRADOR tiene acceso total al sistema")
    print("• El BODEGUERO gestiona productos y stock")
    print("• El SUPERVISOR gestiona préstamos y recompensas")
    print("• El CLIENTE puede comprar y ver su historial")
    print("• Los clientes pueden registrarse públicamente")
    print("="*60)

if __name__ == '__main__':
    try:
        print("\n--- Iniciando configuracion de roles y permisos ---\n")
        crear_grupos_y_permisos()
        usuarios = crear_usuarios_prueba()
        mostrar_credenciales(usuarios)
        print("\n[OK] Configuracion completada exitosamente!\n")
    except Exception as e:
        print(f"\n[ERROR] Error durante la configuracion: {e}\n")
        import traceback
        traceback.print_exc()
