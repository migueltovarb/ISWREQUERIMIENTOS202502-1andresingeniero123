from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Activity, Notification

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'document_id', 'phone', 'address', 'areas_of_interest')
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'document_id': 'ID de documento',
            'phone': 'Teléfono',
            'address': 'Dirección',
            'areas_of_interest': 'Áreas de interés',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.username:
            user.username = user.username.lower()
        if commit:
            user.save()
        return user

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'description', 'date', 'location', 'required_volunteers', 'profile_needed']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'title': 'Título',
            'description': 'Descripción',
            'date': 'Fecha',
            'location': 'Ubicación',
            'required_volunteers': 'Voluntarios requeridos',
            'profile_needed': 'Perfil necesario',
        }

class CustomAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            return username.lower()
        return username

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['activity', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }
