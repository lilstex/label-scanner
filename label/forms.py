from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User, Label


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(MyUserCreationForm, self).__init__(*args, **kwargs)
        
        # Hide the non-existent username field
        if 'username' in self.fields:
            self.fields['username'].widget = forms.HiddenInput()

    def clean_username(self):
        return None

# class LabelForm(ModelForm):
#     class Meta:
#         model = Label
#         fields = '__all__'
        

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email']
