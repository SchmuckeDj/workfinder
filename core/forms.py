from django import forms
from .models import Subscriber


class SubscriberForm(forms.ModelForm):

    class Meta:
        model = Subscriber
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Tu nombre completo',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'tu@correo.com',
            }),
        }
        labels = {
            'name': 'Nombre',
            'email': 'Correo electrónico',
        }
        error_messages = {
            'email': {
                'unique': '¡Este correo ya está registrado!',
                'invalid': 'Por favor ingresa un correo válido.',
            }
        }