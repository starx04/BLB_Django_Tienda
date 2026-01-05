# Script para crear un usuario de prueba
# Ejecutar con: python manage.py shell < create_test_user.py

from django.contrib.auth.models import User

# Verificar si el usuario ya existe
if not User.objects.filter(username='empleado1').exists():
    user = User.objects.create_user(
        username='empleado1',
        password='test1234',
        email='empleado1@licoreria.com'
    )
    print(f"✅ Usuario creado exitosamente:")
    print(f"   Username: empleado1")
    print(f"   Password: test1234")
else:
    print("⚠️  El usuario 'empleado1' ya existe")
