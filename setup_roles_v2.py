"""
Script de configuracion de roles v2 (Separando Administrador de Superusuario)
Ejecutar con: python setup_roles_v2.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from licoreria.models import Clientes, Empleados

def configuracion_final():
    # 1. Crear Grupos
    roles = ['Administrador', 'Supervisor', 'Bodeguero', 'Cliente']
    for rol in roles:
        Group.objects.get_or_create(name=rol)
        print(f"Grupo '{rol}' verificado.")

    # 2. Crear SUPERUSUARIO (Dueño Técnico)
    if not User.objects.filter(username='owner').exists():
        User.objects.create_superuser('owner', 'owner@licoreria.com', 'owner123')
        print("Superusuario 'owner' creado.")

    # 3. Crear ADMINISTRADOR (Gerente de la tienda)
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_user('admin', 'admin@licoreria.com', 'admin123')
        admin.groups.add(Group.objects.get(name='Administrador'))
        admin.is_staff = True # Para que pueda entrar a ciertas áreas de gestión
        admin.save()
        print("Administrador 'admin' creado (No es superusuario).")

    # 4. Crear los demás para pruebas
    users_data = [
        ('bodeguero', 'bodeguero123', 'Bodeguero'),
        ('supervisor', 'supervisor123', 'Supervisor'),
        ('cliente1', 'cliente123', 'Cliente'),
    ]

    for username, password, group_name in users_data:
        if not User.objects.filter(username=username).exists():
            u = User.objects.create_user(username, f"{username}@licoreria.com", password)
            u.groups.add(Group.objects.get(name=group_name))
            u.save()
            print(f"Usuario '{username}' ({group_name}) creado.")

    # Crear perfil de cliente para cliente1 para que pueda comprar
    if not Clientes.objects.filter(email='cliente1@licoreria.com').exists():
        Clientes.objects.create(
            nombre="Cliente de Prueba",
            email="cliente1@licoreria.com",
            telefono="0999999999"
        )

    print("\n" + "="*50)
    print("RESUMEN DE CREDENCIALES")
    print("="*50)
    print("SUPERUSUARIO: owner / owner123 (Control total)")
    print("ADMINISTRADOR: admin / admin123 (Crea personal y ve reportes)")
    print("BODEGUERO: bodeguero / bodeguero123")
    print("SUPERVISOR: supervisor / supervisor123")
    print("CLIENTE: cliente1 / cliente123")
    print("="*50)

if __name__ == '__main__':
    configuracion_final()
