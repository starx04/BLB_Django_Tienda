"""
Script simplificado para crear usuarios y datos de prueba
Ejecutar con: python setup_simple.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Group
from licoreria.models import Clientes, Empleados, Categorias, Marcas, Distribuidores, Productos

def crear_grupos():
    """Crear grupos de usuarios"""
    grupos = ['Cliente', 'Bodeguero', 'Supervisor', 'Administrador']
    for grupo_nombre in grupos:
        Group.objects.get_or_create(name=grupo_nombre)
    print("Grupos creados")

def crear_usuarios():
    """Crear usuarios de prueba"""
    usuarios_creados = []
    
    # Administrador
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@licoreria.com',
            password='admin123'
        )
        usuarios_creados.append(('ADMINISTRADOR', 'admin', 'admin123'))
        print("Usuario admin creado")
    
    # Bodeguero
    if not User.objects.filter(username='bodeguero').exists():
        bodeguero = User.objects.create_user(
            username='bodeguero',
            email='bodeguero@licoreria.com',
            password='bodeguero123'
        )
        bodeguero.groups.add(Group.objects.get(name='Bodeguero'))
        bodeguero.is_staff = True
        bodeguero.save()
        
        Empleados.objects.create(
            user=bodeguero,
            nombre='Juan Pérez',
            cargo='Bodeguero',
            sueldo=1200.00
        )
        usuarios_creados.append(('BODEGUERO', 'bodeguero', 'bodeguero123'))
        print("Usuario bodeguero creado")
    
    # Supervisor
    if not User.objects.filter(username='supervisor').exists():
        supervisor = User.objects.create_user(
            username='supervisor',
            email='supervisor@licoreria.com',
            password='supervisor123'
        )
        supervisor.groups.add(Group.objects.get(name='Supervisor'))
        supervisor.is_staff = True
        supervisor.save()
        
        Empleados.objects.create(
            user=supervisor,
            nombre='María González',
            cargo='Supervisor',
            sueldo=1500.00
        )
        usuarios_creados.append(('SUPERVISOR', 'supervisor', 'supervisor123'))
        print("Usuario supervisor creado")
    
    # Cliente
    if not User.objects.filter(username='cliente1').exists():
        cliente = User.objects.create_user(
            username='cliente1',
            email='cliente1@gmail.com',
            password='cliente123'
        )
        cliente.groups.add(Group.objects.get(name='Cliente'))
        cliente.save()
        
        Clientes.objects.create(
            user=cliente,
            nombre='Carlos Rodríguez',
            email='cliente1@gmail.com',
            telefono='0999888777'
        )
        usuarios_creados.append(('CLIENTE', 'cliente1', 'cliente123'))
        print("Usuario cliente1 creado")
    
    return usuarios_creados

def crear_datos_base():
    """Crear categorías, marcas y distribuidor"""
    # Categorías
    categorias = ['Whisky', 'Ron', 'Vodka', 'Vino', 'Cerveza']
    for cat_nombre in categorias:
        Categorias.objects.get_or_create(nombre=cat_nombre)
    print(f"{len(categorias)} categorías creadas")
    
    # Marcas
    marcas = ["Jack Daniel's", 'Bacardi', 'Absolut', 'Johnnie Walker', 'Smirnoff']
    for marca_nombre in marcas:
        Marcas.objects.get_or_create(nombre=marca_nombre)
    print(f"{len(marcas)} marcas creadas")
    
    # Distribuidor
    Distribuidores.objects.get_or_create(
        nombre='Distribuidora Nacional',
        defaults={
            'email': 'ventas@distribuidora.com',
            'telefono': '0999123456',
            'direccion': 'Av. Principal 123'
        }
    )
    print("Distribuidor creado")

def crear_productos():
    """Crear 15 productos de ejemplo"""
    distribuidor = Distribuidores.objects.first()
    
    productos = [
        # Whiskys
        ('Jack Daniels Old No. 7', 'Whisky', "Jack Daniel's", 45.99, 20, 40.0),
        ('Johnnie Walker Black Label', 'Whisky', 'Johnnie Walker', 52.99, 15, 40.0),
        ('Johnnie Walker Red Label', 'Whisky', 'Johnnie Walker', 35.99, 25, 40.0),
        
        # Rones
        ('Bacardi Carta Blanca', 'Ron', 'Bacardi', 28.99, 30, 37.5),
        ('Bacardi Carta Oro', 'Ron', 'Bacardi', 32.99, 25, 37.5),
        ('Bacardi Añejo', 'Ron', 'Bacardi', 38.99, 18, 40.0),
        
        # Vodkas
        ('Absolut Original', 'Vodka', 'Absolut', 29.99, 22, 40.0),
        ('Absolut Citron', 'Vodka', 'Absolut', 31.99, 18, 40.0),
        ('Smirnoff Red', 'Vodka', 'Smirnoff', 24.99, 28, 37.5),
        ('Smirnoff Ice', 'Vodka', 'Smirnoff', 18.99, 35, 5.0),
        
        # Vinos
        ('Vino Tinto Reserva', 'Vino', 'Johnnie Walker', 22.99, 20, 13.5),
        ('Vino Blanco Seco', 'Vino', 'Johnnie Walker', 19.99, 25, 12.5),
        
        # Cervezas
        ('Cerveza Premium Lager', 'Cerveza', 'Smirnoff', 2.99, 100, 4.5),
        ('Cerveza Artesanal IPA', 'Cerveza', 'Smirnoff', 3.99, 80, 6.0),
        ('Cerveza Light', 'Cerveza', 'Smirnoff', 2.49, 120, 3.5),
    ]
    
    productos_creados = 0
    for nombre, cat_nombre, marca_nombre, precio, stock, alcohol in productos:
        categoria = Categorias.objects.get(nombre=cat_nombre)
        marca = Marcas.objects.get(nombre=marca_nombre)
        
        if not Productos.objects.filter(nombre=nombre).exists():
            Productos.objects.create(
                nombre=nombre,
                categoria=categoria,
                marca=marca,
                distribuidor=distribuidor,
                precio=precio,
                stock=stock,
                grados_alcohol=alcohol
            )
            productos_creados += 1
    
    print(f"{productos_creados} productos creados")

def mostrar_credenciales(usuarios):
    """Mostrar credenciales de forma simple"""
    print("\n" + "="*60)
    print("CREDENCIALES DE ACCESO")
    print("="*60 + "\n")
    
    for rol, username, password in usuarios:
        print(f"{rol}:")
        print(f"  Usuario:     {username}")
        print(f"  Contraseña:  {password}")
        print()
    
    print("="*60)
    print("NOTAS:")
    print("- El ADMINISTRADOR tiene acceso total")
    print("- El BODEGUERO gestiona productos")
    print("- El SUPERVISOR gestiona prestamos y recompensas")
    print("- El CLIENTE puede comprar productos")
    print("="*60)

if __name__ == '__main__':
    try:
        print("\n--- Configurando sistema ---\n")
        crear_grupos()
        usuarios = crear_usuarios()
        crear_datos_base()
        crear_productos()
        mostrar_credenciales(usuarios)
        print("\n[OK] Configuracion completada!\n")
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
