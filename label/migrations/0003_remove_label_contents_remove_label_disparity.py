# Generated by Django 5.0 on 2023-12-08 09:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('label', '0002_remove_label_image_label_disparity_label_image_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='label',
            name='contents',
        ),
        migrations.RemoveField(
            model_name='label',
            name='disparity',
        ),
    ]