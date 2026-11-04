from django import forms
from .models import UserRegistrationModel

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'id': 'password', 'placeholder': 'Create a password'}),
        required=True
    )
    # Change status to not required so it doesn't block the form validation
    status = forms.CharField(widget=forms.HiddenInput(), initial='waiting', required=False)

    class Meta:
        model = UserRegistrationModel
        fields = '__all__'