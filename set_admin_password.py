"""
Script para establecer contraseña del superusuario admin
Ejecutar con: python set_admin_password.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

try:
    user = User.objects.get(username='admin')
    user.set_password('admin123')
    user.save()
    print("✅ Contraseña establecida para el usuario 'admin'")
    print("   Username: admin")
    print("   Password: admin123")
except User.DoesNotExist:
    print("❌ Usuario 'admin' no encontrado")
