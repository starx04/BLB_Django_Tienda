from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import DetallesOrdenes, Ordenes

@receiver(post_save, sender=Ordenes)
def asignar_puntos_al_pagar(sender, instance, **kwargs):
    """Asigna 1 punto por cada $10 cuando la orden se marca como pagada"""
    if instance.pagada and not instance.puntos_asignados:
        from django.db import transaction
        
        # Usar on_commit para asegurar que la transacción de pago se completó
        def asignar():
            # Volver a verificar dentro de la transacción
            # Usar select_for_update para evitar condiciones de carrera si es necesario
            # Pero para simplicidad aquí:
            if not instance.puntos_asignados:
                puntos_ganados = instance.cliente.agregar_puntos(float(instance.total))
                # Actualizar la orden sin disparar post_save de nuevo (o verificar puntos_asignados)
                Ordenes.objects.filter(pk=instance.pk).update(puntos_asignados=True)
                print(f"Puntos asignados: {puntos_ganados} a cliente {instance.cliente.nombre}")

        transaction.on_commit(asignar)

@receiver(post_save, sender=DetallesOrdenes)
def actualizar_al_guardar(sender, instance, created, **kwargs):
    # Usamos transaction.atomic para asegurar integridad
    with transaction.atomic():
        # 1. Actualizar Stock al crear
        if created:
            if instance.producto:
                instance.producto.stock -= instance.cantidad
                instance.producto.save()
            elif instance.coctel:
                instance.coctel.stock -= instance.cantidad
                instance.coctel.save()
        
        # 2. Recalcular Total de la Orden
        orden = instance.orden
        # Sumamos todos los detalles actuales de esa orden
        nuevo_total = sum(d.cantidad * d.precio_unitario for d in orden.detalles.all())
        # Actualizamos sin disparar señales innecesarias de Orden si es posible, 
        # pero aquí Ordenes.save() está bien (controlado por el dispatcher)
        Ordenes.objects.filter(pk=orden.pk).update(total=nuevo_total)

@receiver(post_delete, sender=DetallesOrdenes)
def actualizar_al_borrar(sender, instance, **kwargs):
    with transaction.atomic():
        # 1. Devolver Stock
        if instance.producto:
            instance.producto.stock += instance.cantidad
            instance.producto.save()
        elif instance.coctel:
            instance.coctel.stock += instance.cantidad
            instance.coctel.save()

        # 2. Recalcular Total
        orden = instance.orden
        if orden.detalles.exists():
            nuevo_total = sum(d.cantidad * d.precio_unitario for d in orden.detalles.all())
        else:
            nuevo_total = 0
        Ordenes.objects.filter(pk=orden.pk).update(total=nuevo_total)
