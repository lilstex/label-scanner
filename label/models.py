# from django.db import models
# from django.contrib.auth.models import AbstractUser

# # Create your models here.
# class User(AbstractUser):
#     name = models.CharField(max_length=200, null=True)
#     email = models.EmailField(unique=True, null=True)

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []

import uuid
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username='', **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            # Generate a timestamp string to make the username unique
            timestamp_str = timezone.now().strftime('%Y%m%d%H%M%S')
            # Append a unique identifier to ensure uniqueness
            unique_id = str(uuid.uuid4().hex)[:6]
            self.username = f'user_{timestamp_str}_{unique_id}'
            
        super().save(*args, **kwargs)


class Label(models.Model):
    image = models.ImageField(null=True)
    contents = models.TextField(blank=True)
    
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated', '-created']
