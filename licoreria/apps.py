from django.apps import AppConfig


class LicoreriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'licoreria'

    def ready(self):
        import licoreria.signals
        
        # Monkey-patching User model de forma segura
        from django.contrib.auth.models import User, Group

        def get_user_rol(self):
            """Propiedad dinámica para obtener el rol del usuario"""
            if self.is_superuser:
                return 'Administrador'
            
            # 1. Intentar por Grupos (Orden de prioridad: Administrador, Supervisor, Bodeguero, Cliente)
            priority_groups = ['Administrador', 'Supervisor', 'Bodeguero', 'Cliente']
            user_groups = [g.name for g in self.groups.all()]
            for gname in priority_groups:
                if gname in user_groups:
                    return gname
            
            # 2. Respaldo por Cargo en Empleados
            if hasattr(self, 'empleados') and self.empleados:
                cargo = self.empleados.cargo.title()
                if cargo in priority_groups:
                    return cargo
            
            return 'Sin rol'

        # Inyectar la propiedad en el modelo User de Django
        if not hasattr(User, 'rol'):
            User.add_to_class('rol', property(get_user_rol))
