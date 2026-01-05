# Sistema de Autenticación - Licorería Django

## 📋 Resumen

Se ha implementado un sistema completo de autenticación para empleados con las siguientes características:

### ✅ Características Implementadas

1. **Login de Empleados**
   - Solo empleados registrados pueden acceder al sistema
   - Página de login moderna con diseño consistente
   - Redirección automática al dashboard después del login

2. **Registro Protegido**
   - Sistema de "gatekeeper" con contraseña de administrador
   - Contraseña requerida: `axfer2304`
   - Flujo de dos pasos:
     1. Validación de contraseña de admin
     2. Formulario de registro de empleado

3. **Protección de Rutas**
   - Todas las vistas principales protegidas con `@login_required`
   - Usuarios no autenticados son redirigidos al login automáticamente

4. **Interfaz de Usuario**
   - Perfil de usuario visible en el sidebar
   - Avatar con inicial del nombre de usuario
   - Botón de cerrar sesión accesible

## 🔐 Flujo de Autenticación

### Para Iniciar Sesión:
1. Ir a `/accounts/login/`
2. Ingresar credenciales de empleado
3. Acceso al sistema completo

### Para Registrar Nuevo Empleado:
1. Ir a `/accounts/validate/`
2. Ingresar contraseña de admin: `axfer2304`
3. Completar formulario de registro
4. Iniciar sesión con las nuevas credenciales

## 📁 Archivos Creados/Modificados

### Templates Nuevos:
- `licoreria/templates/registration/login.html` - Página de login
- `licoreria/templates/registration/validate_admin.html` - Validación de admin
- `licoreria/templates/registration/register.html` - Formulario de registro

### Archivos Modificados:
- `licoreria/views.py` - Agregadas vistas de autenticación y decoradores `@login_required`
- `licoreria/urls.py` - Agregadas rutas de autenticación
- `config/settings.py` - Configuración de redirecciones de login/logout
- `licoreria/templates/base.html` - Agregado perfil de usuario y botón de logout

## 🛠️ Configuración en settings.py

```python
# Auth Settings
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'
```

## 🔗 URLs de Autenticación

- `/accounts/login/` - Iniciar sesión
- `/accounts/logout/` - Cerrar sesión
- `/accounts/validate/` - Validar contraseña de admin
- `/accounts/register/` - Registrar nuevo empleado

## 🎨 Diseño

El sistema de autenticación mantiene la estética premium del resto de la aplicación:
- Colores consistentes con el tema oscuro
- Iconos Phosphor modernos
- Animaciones suaves
- Diseño responsive

## 🔒 Seguridad

- Contraseña de admin hardcodeada: `axfer2304`
- Sistema de sesiones de Django para validación temporal
- Todas las rutas principales protegidas
- Formulario estándar de Django con validaciones incluidas

## 📝 Próximos Pasos Recomendados

1. **Migrar contraseña de admin a variables de entorno**
   ```python
   ADMIN_REGISTRATION_PASSWORD = os.getenv('ADMIN_REG_PASS', 'axfer2304')
   ```

2. **Relacionar User con Empleado**
   - Agregar campo `OneToOneField` en modelo `Empleados`
   - Vincular automáticamente al registrar

3. **Permisos granulares**
   - Implementar grupos de Django
   - Diferentes niveles de acceso (vendedor, gerente, admin)

4. **Recuperación de contraseña**
   - Implementar reset de password vía email

## 🚀 Cómo Probar

1. Crear un superusuario (opcional):
   ```bash
   python manage.py createsuperuser
   ```

2. O registrar un empleado:
   - Ir a `http://localhost:8000/accounts/validate/`
   - Ingresar: `axfer2304`
   - Completar formulario de registro

3. Iniciar sesión:
   - Ir a `http://localhost:8000/accounts/login/`
   - Usar credenciales creadas

4. Verificar acceso:
   - Todas las páginas ahora requieren autenticación
   - Ver perfil en sidebar
   - Probar cerrar sesión
