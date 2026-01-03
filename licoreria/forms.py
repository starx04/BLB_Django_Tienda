from django import forms
from .models import Clientes

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
