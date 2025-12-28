from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import DetallesOrdenes

@receiver(post_save, sender=DetallesOrdenes)
def actualizar_al_guardar(sender, instance, created, **kwargs):
    # Usamos transaction.atomic para asegurar integridad
    with transaction.atomic():
        # 1. Actualizar Stock al crear
        if created:
            instance.producto.stock -= instance.cantidad
            instance.producto.save()
        
        # 2. Recalcular Total de la Orden
        orden = instance.orden
        # Sumamos todos los detalles actuales de esa orden
        nuevo_total = sum(d.cantidad * d.precio_unitario for d in orden.detalles.all())
        orden.total = nuevo_total
        orden.save()

@receiver(post_delete, sender=DetallesOrdenes)
def actualizar_al_borrar(sender, instance, **kwargs):
    with transaction.atomic():
        # 1. Devolver Stock
        instance.producto.stock += instance.cantidad
        instance.producto.save()

        # 2. Recalcular Total
        orden = instance.orden
        if orden.detalles.exists():
            nuevo_total = sum(d.cantidad * d.precio_unitario for d in orden.detalles.all())
        else:
            nuevo_total = 0
        orden.total = nuevo_total
        orden.save()
