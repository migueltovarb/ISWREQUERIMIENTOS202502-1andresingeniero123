from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Activity

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'document_id', 'phone', 'address', 'areas_of_interest')

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'description', 'date', 'location', 'required_volunteers', 'profile_needed']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
