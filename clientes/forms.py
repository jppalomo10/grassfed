from django import forms
from core.models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['Telefono', 'Nombre', 'Direccion', 'Correo', 'NIT']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['Telefono'].widget.attrs['placeholder'] = 'Ej: 50212345678'
        self.fields['Nombre'].widget.attrs['placeholder'] = 'Nombre completo o razón social'
        self.fields['Direccion'].widget.attrs['placeholder'] = 'Dirección de entrega'
        self.fields['Correo'].widget.attrs['placeholder'] = 'correo@ejemplo.com (opcional)'
        self.fields['NIT'].widget.attrs['placeholder'] = 'CF o número de NIT'
        self.fields['NIT'].initial = 'CF'
        # Phone is PK — disable on edit (passed via instance)
        if self.instance and self.instance.pk:
            self.fields['Telefono'].disabled = True
