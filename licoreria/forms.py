from django import forms
from .models import Clientes, Productos, Categorias, Marcas, Distribuidores, Prestamos, Recompensas
from django.contrib.auth.models import User, Group

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Clientes
        fields = ['nombre', 'email', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0999999999'}),
        }
        labels = {
            'nombre': 'Nombre del Cliente',
            'email': 'Correo Electrónico',
            'telefono': 'Número de Teléfono',
        }

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo debe contener números.")
        if len(telefono) < 7 or len(telefono) > 15:
            raise forms.ValidationError("El teléfono debe tener entre 7 y 15 dígitos.")
        return telefono

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Clientes.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

from .models import Empleados

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleados
        fields = ['nombre', 'cargo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Completo'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo (ej. Vendedor)'}),
        }
        labels = {
            'nombre': 'Nombre del Empleado',
            'cargo': 'Cargo',
        }

from .models import Prestamos

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamos
        fields = ['cliente', 'descripcion', 'valor', 'devuelto']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del préstamo...'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'devuelto': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        labels = {
            'cliente': 'Cliente',
            'descripcion': 'Detalle / Descripción',
            'valor': 'Valor ($)',
            'devuelto': '¿Ya fue devuelto?'
        }

class RegistroClienteForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar Contraseña'}))
    
    class Meta:
        model = Clientes
        fields = ['nombre', 'email', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu Nombre'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return cleaned_data

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Productos
        fields = ['nombre', 'categoria', 'marca', 'distribuidor', 'precio', 'stock', 'grados_alcohol', 'imagen', 'codigo_barras']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.Select(attrs={'class': 'form-select'}),
            'distribuidor': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'grados_alcohol': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RecompensaForm(forms.ModelForm):
    class Meta:
        model = Recompensas
        fields = ['cliente', 'tipo', 'descripcion', 'valor', 'fecha_vencimiento']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

