from django.shortcuts import render
from .models import Producto

def index(request):
    productos = Producto.objects.all()
    return render(request, 'licoreria/index.html', {'productos': productos})
