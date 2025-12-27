from django.shortcuts import render
from .models import Productos

def index(request):
    productos = Productos.objects.all()
    return render(request, 'index.html', {'productos': productos})
