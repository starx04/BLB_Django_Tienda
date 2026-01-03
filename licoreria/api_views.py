from .models import Productos
from .serializers import ProductoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests

# API Interna: Licores y Tragos (Manejado por nosotros mismos)
class LicoresAPI(APIView):
    def get(self, request):
        categoria_licores = ['Licores', 'Tragos', 'Bebidas Alcoholicas'] # Ajustar según tu DB
        productos = Productos.objects.filter(categoria__nombre__in=categoria_licores)
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API Externa / Snacks (Simulación o consumo de otra fuente)
class SnacksAPI(APIView):
    def get(self, request):
        # Aquí podrías consumir una API externa real
        # Por ahora, filtremos los snacks de nuestra DB local como ejemplo
        categoria_snacks = ['Snacks', 'Bocaditos', 'Comida']
        productos = Productos.objects.filter(categoria__nombre__in=categoria_snacks)
        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Lógica para agregar snacks
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
