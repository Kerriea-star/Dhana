# Generated by Django 4.0.1 on 2022-02-01 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_administrator_bio_customer_bio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='administrator',
            name='profile_picture',
            field=models.ImageField(default='default.png', upload_to='profile_pictures', verbose_name='profile picture'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='profile_picture',
            field=models.ImageField(default='default.png', upload_to='profile_pictures', verbose_name='profile picture'),
        ),
    ]
