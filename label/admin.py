from django.contrib import admin

# Register your models here.
from .models import Label, User

admin.site.register(User)
admin.site.register(Label)