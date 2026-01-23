from rest_framework import serializers
from .models import Productos, Cocteles

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Productos
        fields = '__all__'

class CoctelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cocteles
        fields = '__all__'

