# Generated by Django 5.0 on 2023-12-08 09:28

import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('label', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='label',
            name='image',
        ),
        migrations.AddField(
            model_name='label',
            name='disparity',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='label',
            name='image_url',
            field=cloudinary.models.CloudinaryField(max_length=255, null=True, verbose_name='image'),
        ),
    ]